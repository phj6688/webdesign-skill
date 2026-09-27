#!/usr/bin/env python3
"""Check the colour pairs a DESIGN.md declares against WCAG contrast floors.

This measures tokens, not rendered pixels. It catches a palette that cannot pass before
any page is built on it. A page can still fail on top of a passing palette (text over an
image, an alpha overlay), so the rendered check in references/verify.md still applies.

Usage:
  check_contrast.py DESIGN.md [DESIGN.md ...] [--json]

Exit status: 0 every pair passes, 2 at least one pair fails, 1 usage or parse error.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

# When a file declares no pairs, these are checked for whichever tokens exist. The
# alternatives let the checker read the reference systems, which say "primary" where
# this skill's schema says "accent". Each pair resolves as a unit: mixing "on-primary"
# with "accent" would measure two colours that were never meant to meet.
_INK = ["ink", "text", "body", "foreground"]
_MUTED = ["ink-muted", "muted", "body-muted", "ink-mute"]
_CANVAS = ["canvas", "background", "bg"]
_ACCENT = ["accent", "primary"]


def _product(fgs: list[str], bgs: list[str]) -> list[tuple[str, str]]:
    return [(f, b) for f in fgs for b in bgs]


DEFAULT_PAIRS: list[tuple[list[tuple[str, str]], float]] = [
    (_product(_INK, _CANVAS), 4.5),
    (_product(_MUTED, _CANVAS), 4.5),
    (_product(_INK, ["surface"]), 4.5),
    ([("on-accent", "accent"), ("on-primary", "primary")], 4.5),
    (_product(_ACCENT, _CANVAS), 3.0),
]
THEME_KEYS = ("colors", "colors-dark")
REF = re.compile(r"^\{colors(?:-dark)?\.([\w.-]+)\}$")


class ParseError(Exception):
    pass


def split_frontmatter(text: str) -> str:
    if not text.startswith("---"):
        raise ParseError("no YAML frontmatter")
    parts = text.split("\n---", 1)
    if len(parts) < 2:
        raise ParseError("frontmatter is not closed")
    return parts[0][3:]


def _strip_comment(line: str) -> str:
    """Drops a trailing YAML comment, but not a '#' inside quotes or a hex colour."""
    quote = None
    for i, ch in enumerate(line):
        if quote:
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
        elif ch == "#" and (i == 0 or line[i - 1] in " \t"):
            return line[:i].rstrip()
    return line.rstrip()


def _unquote(key: str) -> str:
    """Drops one pair of matching quotes around a block-map key. YAML reads the quotes
    as syntax, so a key written "50" must read as 50 here, as it does under PyYAML."""
    if len(key) >= 2 and key[0] == key[-1] and key[0] in "\"'":
        return key[1:-1]
    return key


def _parse_flow(text: str):
    """Parses a YAML flow collection or scalar: [a, [b, c]], {k: v}, "quoted"."""
    pos = 0

    def skip() -> None:
        nonlocal pos
        while pos < len(text) and text[pos] in " \t\n":
            pos += 1

    def value():
        nonlocal pos
        skip()
        if pos >= len(text):
            raise ParseError(f"unexpected end of flow value in {text!r}")
        ch = text[pos]
        if ch == "[":
            pos += 1
            items = []
            skip()
            if pos < len(text) and text[pos] == "]":
                pos += 1
                return items
            while True:
                items.append(value())
                skip()
                if pos < len(text) and text[pos] == ",":
                    pos += 1
                    continue
                if pos < len(text) and text[pos] == "]":
                    pos += 1
                    return items
                raise ParseError(f"unclosed flow sequence in {text!r}")
        if ch == "{":
            pos += 1
            mapping: dict = {}
            skip()
            if pos < len(text) and text[pos] == "}":
                pos += 1
                return mapping
            while True:
                key = scalar(stop=":")
                skip()
                if pos >= len(text) or text[pos] != ":":
                    raise ParseError(f"missing ':' in flow mapping {text!r}")
                pos += 1
                mapping[str(key)] = value()
                skip()
                if pos < len(text) and text[pos] == ",":
                    pos += 1
                    continue
                if pos < len(text) and text[pos] == "}":
                    pos += 1
                    return mapping
                raise ParseError(f"unclosed flow mapping in {text!r}")
        return scalar(stop=",]}")

    def scalar(stop: str):
        nonlocal pos
        skip()
        if pos < len(text) and text[pos] in "\"'":
            quote = text[pos]
            end = text.find(quote, pos + 1)
            if end < 0:
                raise ParseError(f"unclosed quote in {text!r}")
            out = text[pos + 1:end]
            pos = end + 1
            return out
        start = pos
        depth = 0
        while pos < len(text):
            ch = text[pos]
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
            elif depth == 0 and ch in stop:
                break
            pos += 1
        return text[start:pos].strip()

    result = value()
    skip()
    if pos != len(text):
        raise ParseError(f"trailing text after flow value in {text!r}")
    return result


RELEVANT_KEYS = ("colors", "colors-dark", "contrast")
CONTRAST_SHAPE = "a list of [fg, bg, floor] entries"


def _unclosed(text: str) -> bool:
    return text.count("[") + text.count("{") > text.count("]") + text.count("}")


def _fallback_parse(block: str) -> dict:
    """Reads the three keys the checker needs without PyYAML.

    `colors`, `colors-dark` and `contrast` are parsed strictly, in block or flow form,
    and a shape this parser cannot read raises, so a declared pair is never dropped in
    silence. Every other key is skipped whole, however it is written, because the
    checker never reads it and prose descriptions are where hand-written YAML is most
    irregular.
    """
    data: dict = {}
    current = None
    pending = ""
    for raw in block.splitlines():
        if pending:
            pending += " " + _strip_comment(raw).strip()
            if _unclosed(pending):
                continue
            data[current] = _parse_flow(pending)
            pending = ""
            continue
        if not raw.strip():
            continue
        # YAML lets a block sequence sit at the same column as its key. Such a line is
        # an item of the current key, not a new key, or its pairs would drop silently.
        if raw.startswith("-") and current is not None:
            if current not in RELEVANT_KEYS:
                continue
            if data.get(current) is None:
                data[current] = []
            if not isinstance(data[current], list):
                raise ParseError(f"mixed block forms under {current!r}")
            entry = _strip_comment(raw)[1:].strip()
            if _unclosed(entry):
                raise ParseError(f"multi-line flow item under {current!r} is not supported")
            data[current].append(_parse_flow(entry) if entry[:1] in "[{" else entry.strip("\"'"))
            continue
        if not raw.startswith((" ", "\t")):
            key, sep, rest = raw.partition(":")
            current = key.strip()
            if current not in RELEVANT_KEYS:
                continue
            if not sep:
                raise ParseError(f"cannot read frontmatter line {raw!r}")
            rest = _strip_comment(rest).strip()
            if rest.startswith(("[", "{")):
                if _unclosed(rest):
                    pending = rest
                    continue
                data[current] = _parse_flow(rest)
            elif rest:
                shape = CONTRAST_SHAPE if current == "contrast" else "a map or a list"
                raise ParseError(f"{current!r} must be {shape}, got {rest!r}")
            else:
                data[current] = None
            continue
        if current not in RELEVANT_KEYS:
            continue
        item = _strip_comment(raw).strip()
        if not item:
            continue
        if item.startswith("-"):
            entry = item[1:].strip()
            if data.get(current) is None:
                data[current] = []
            if not isinstance(data[current], list):
                raise ParseError(f"mixed block forms under {current!r}")
            if _unclosed(entry):
                raise ParseError(f"multi-line flow item under {current!r} is not supported")
            data[current].append(_parse_flow(entry) if entry[:1] in "[{" else entry.strip("\"'"))
            continue
        k, sep, v = item.partition(":")
        if not sep:
            raise ParseError(f"cannot read line under {current!r}: {raw!r}")
        if data.get(current) is None:
            data[current] = {}
        if not isinstance(data[current], dict):
            raise ParseError(f"mixed block forms under {current!r}")
        v = v.strip()
        if not v:
            raise ParseError(f"nested map under {current}.{k.strip()} is not supported")
        if v[:1] in "[{" and _unclosed(v):
            raise ParseError(f"multi-line flow value for {k.strip()!r} is not supported")
        data[current][_unquote(k.strip())] = _parse_flow(v) if v[:1] in "[{" else v.strip("\"'")
    if pending:
        raise ParseError(f"unclosed flow collection under {current!r}")
    return data


def parse_frontmatter(block: str) -> dict:
    """Reads the colour maps and the contrast list.

    PyYAML is used when present. The fallback reads the subset the DESIGN.md schema
    uses, including inline flow lists and maps.
    """
    try:
        import yaml  # type: ignore[import-untyped]
    except ImportError:
        return _fallback_parse(block)
    try:
        data = yaml.safe_load(block) or {}
    except yaml.YAMLError as exc:
        reason = str(exc).splitlines()[0]
        # Hand-written frontmatter often breaks YAML in a prose field the checker never
        # reads. Retrying with the strict subset parser keeps the result the same with
        # or without PyYAML, and the note keeps the broken YAML visible.
        try:
            data = _fallback_parse(block)
        except ParseError:
            raise ParseError(f"invalid YAML frontmatter: {reason}") from exc
        data["__note__"] = f"frontmatter is not valid YAML ({reason}); colours read by the subset parser"
        return data
    if not isinstance(data, dict):
        raise ParseError("frontmatter is not a mapping")
    return data


def _srgb_to_linear(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _linear_to_srgb(c: float) -> float:
    return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


def oklch_to_linear_rgb(lum: float, chroma: float, hue: float) -> tuple[float, ...]:
    a = chroma * math.cos(math.radians(hue))
    b = chroma * math.sin(math.radians(hue))
    l_ = (lum + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m_ = (lum - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s_ = (lum - 0.0894841775 * a - 1.2914855480 * b) ** 3
    return (
        4.0767416621 * l_ - 3.3077115913 * m_ + 0.2309699292 * s_,
        -1.2684380046 * l_ + 2.6097574011 * m_ - 0.3413193965 * s_,
        -0.0041960863 * l_ - 0.7034186147 * m_ + 1.7076147010 * s_,
    )


def _number(token: str, percent_scale: float = 100.0) -> float:
    token = token.strip()
    if token.endswith("%"):
        return float(token[:-1]) / percent_scale
    return float(token)


def _alpha(token: str | None) -> float:
    if token is None:
        return 1.0
    return min(1.0, max(0.0, _number(token, 100.0)))


def parse_rgba(value: str) -> tuple[tuple[float, float, float], float, bool]:
    """Returns gamma-encoded sRGB in 0..1, the alpha, and whether it left the gamut."""
    v = value.strip().lower()
    if v.startswith("#"):
        h = v[1:]
        if len(h) in (3, 4):
            h = "".join(ch * 2 for ch in h)
        if len(h) not in (6, 8) or not re.fullmatch(r"[0-9a-f]+", h):
            raise ParseError(f"bad hex colour {value!r}")
        rgb = tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
        alpha = int(h[6:8], 16) / 255 if len(h) == 8 else 1.0
        return rgb, alpha, False  # type: ignore[return-value]
    m = re.fullmatch(r"rgba?\(([^)]*)\)", v)
    if m:
        parts = [p for p in re.split(r"[\s,/]+", m.group(1).strip()) if p]
        if len(parts) not in (3, 4):
            raise ParseError(f"bad rgb colour {value!r}")
        rgb = tuple(
            (_number(p) if p.endswith("%") else float(p) / 255) for p in parts[:3]
        )
        return rgb, _alpha(parts[3] if len(parts) == 4 else None), False  # type: ignore[return-value]
    m = re.fullmatch(r"oklch\(([^)]*)\)", v)
    if m:
        main, _, alpha_part = m.group(1).partition("/")
        parts = main.split()
        if len(parts) != 3:
            raise ParseError(f"bad oklch colour {value!r}")
        lum = _number(parts[0])
        chroma = _number(parts[1], 250.0) if parts[1].endswith("%") else float(parts[1])
        hue = float(parts[2].removesuffix("deg")) if parts[2] != "none" else 0.0
        lin = oklch_to_linear_rgb(lum, chroma, hue)
        # A small overshoot is rounding. A large one means the declared colour cannot be
        # displayed, so the measured contrast would describe a different colour.
        clamped = any(c < -0.002 or c > 1.002 for c in lin)
        rgb = tuple(_linear_to_srgb(min(1.0, max(0.0, c))) for c in lin)
        alpha = _alpha(alpha_part.strip() or None)
        return rgb, alpha, clamped  # type: ignore[return-value]
    raise ParseError(f"unsupported colour {value!r}")


def parse_colour(value: str) -> tuple[tuple[float, float, float], bool]:
    """Returns linear sRGB and whether the colour had to be clamped into gamut.

    Refuses a translucent colour, because its contrast depends on what sits under it.
    Use measure_pair for a pair that may carry alpha.
    """
    rgb, alpha, clamped = parse_rgba(value)
    if alpha < 1.0:
        raise ParseError(f"{value!r} is translucent; measure it against its ground")
    return tuple(_srgb_to_linear(c) for c in rgb), clamped  # type: ignore[return-value]


def measure_pair(fg_val: str, bg_val: str) -> tuple[float | None, str, str, list[str]]:
    """Contrast of fg over bg. A translucent foreground is composited over the ground
    first, the way a browser paints it, in gamma-encoded sRGB. A translucent ground has
    no single colour until you know what is under it, so it cannot pass here."""
    fg, fg_a, fg_clamped = parse_rgba(fg_val)
    bg, bg_a, bg_clamped = parse_rgba(bg_val)
    notes = []
    if fg_clamped or bg_clamped:
        notes.append("out of sRGB gamut, clamped before measuring")

    def hexed(rgb: tuple[float, ...]) -> str:
        return "#" + "".join(f"{round(c * 255):02x}" for c in rgb)

    if bg_a < 1.0:
        notes.append("ground is translucent, check the rendered page instead")
        return None, hexed(fg), hexed(bg), notes
    if fg_a < 1.0:
        fg = tuple(fg_a * f + (1 - fg_a) * b for f, b in zip(fg, bg))
        notes.append(f"foreground alpha {fg_a:.2f}, composited over the ground")
    fg_lin = tuple(_srgb_to_linear(c) for c in fg)
    bg_lin = tuple(_srgb_to_linear(c) for c in bg)
    return contrast(fg_lin, bg_lin), hexed(fg), hexed(bg), notes  # type: ignore[arg-type]


def luminance(lin: tuple[float, float, float]) -> float:
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def contrast(fg: tuple[float, float, float], bg: tuple[float, float, float]) -> float:
    hi, lo = sorted((luminance(fg), luminance(bg)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def to_hex(lin: tuple[float, float, float]) -> str:
    return "#" + "".join(f"{round(_linear_to_srgb(c) * 255):02x}" for c in lin)


def _text_keys(palette: dict) -> dict:
    """The colour map keyed by text. PyYAML reads a key written 50 as an int, while the
    stdlib parser and a {colors.50} reference both give the text "50"."""
    return {str(key): value for key, value in palette.items()}


def resolve(name: str | int | float, palette: dict, seen: frozenset = frozenset()) -> str | None:
    # A declared name can be the int 900 under PyYAML and is always text under the
    # stdlib parser; the palette is keyed by text, so the lookup is too.
    name = str(name).strip()
    value = palette.get(name)
    if value is None:
        return None
    ref = REF.match(str(value).strip())
    if ref:
        if name in seen:
            raise ParseError(f"token reference loop at {name!r}")
        return resolve(ref.group(1), palette, seen | {name})
    return str(value)


def find_pair(alternatives: list[tuple[str, str]], palette: dict) -> tuple[str, str] | None:
    for fg, bg in alternatives:
        if fg in palette and bg in palette:
            return fg, bg
    return None


def _floor(value) -> float | None:
    """A floor as a finite number, or None. The stdlib parser reads every scalar as a
    string, so a numeric string counts; a YAML boolean does not."""
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


# The stdlib parser keeps a YAML null as its text, where PyYAML gives None. Refusing
# the text too gives a null name the same error on both parser paths.
YAML_NULLS = frozenset({"~", "null", "Null", "NULL"})


def _token_name(value) -> bool:
    """Whether a contrast entry names a token. PyYAML reads a key such as 900 as an
    int and the stdlib parser reads it as a string, so a number counts; a YAML
    boolean or null does not."""
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        return False
    text = str(value).strip()
    return bool(text) and text not in YAML_NULLS


def declared_pairs(data: dict) -> list[tuple[str, str, float]]:
    """The contrast list as (fg, bg, floor) rows.

    Each entry is checked before it is unpacked: a scalar list raises a TypeError, and
    a three-letter string unpacks into three one-letter token names.
    """
    declared = data.get("contrast")
    if declared is None:
        return []
    if not isinstance(declared, list):
        raise ParseError(f"'contrast' must be {CONTRAST_SHAPE}, got {declared!r}")
    pairs = []
    for entry in declared:
        if not isinstance(entry, (list, tuple)) or len(entry) != 3:
            raise ParseError(f"contrast entry {entry!r} is not a [fg, bg, floor] list")
        fg, bg, floor = entry
        if not (_token_name(fg) and _token_name(bg)):
            raise ParseError(f"contrast entry {entry!r} needs two token names")
        number = _floor(floor)
        if number is None:
            raise ParseError(f"contrast entry {entry!r} needs a number as its floor")
        pairs.append((fg, bg, number))
    return pairs


def check_file(path: Path) -> dict:
    data = parse_frontmatter(split_frontmatter(path.read_text(encoding="utf-8")))
    declared = declared_pairs(data)
    results = []
    for theme_key in THEME_KEYS:
        palette = data.get(theme_key)
        if not isinstance(palette, dict) or not palette:
            continue
        palette = _text_keys(palette)
        # The dark map inherits any token it does not override, so a pair can mix an
        # overridden background with an inherited ink. Both maps are keyed by text
        # before the merge, or a dark "50" would sit beside a light 50, not replace it.
        if theme_key == "colors-dark" and isinstance(data.get("colors"), dict):
            palette = {**_text_keys(data["colors"]), **palette}
        pairs = []
        if declared:
            pairs.extend(declared)
        else:
            for alternatives, floor in DEFAULT_PAIRS:
                found = find_pair(alternatives, palette)
                if found:
                    pairs.append((found[0], found[1], floor))
        for fg, bg, floor in pairs:
            fg_val, bg_val = resolve(fg, palette), resolve(bg, palette)
            row = {"theme": theme_key, "fg": fg, "bg": bg, "floor": floor}
            if fg_val is None or bg_val is None:
                missing = fg if fg_val is None else bg
                row.update(ratio=None, ok=False, note=f"token {missing!r} not defined")
                results.append(row)
                continue
            ratio, fg_hex, bg_hex, notes = measure_pair(fg_val, bg_val)
            row.update(
                ratio=None if ratio is None else round(ratio, 2),
                ok=ratio is not None and ratio >= floor,
                fg_hex=fg_hex,
                bg_hex=bg_hex,
                note="; ".join(notes),
            )
            results.append(row)
    if not results:
        raise ParseError("no colour pairs found to check")
    report = {"file": str(path), "pairs": results, "ok": all(r["ok"] for r in results)}
    if data.get("__note__"):
        report["note"] = data["__note__"]
    return report


class _Parser(argparse.ArgumentParser):
    """Exit 1 on a usage error. Exit 2 is reserved for a failing pair."""

    def error(self, message: str):  # type: ignore[override]
        self.print_usage(sys.stderr)
        self.exit(1, f"{self.prog}: error: {message}\n")


def main(argv: list[str] | None = None) -> int:
    ap = _Parser(description=__doc__.split("\n\n")[0])
    ap.add_argument("files", nargs="+", type=Path)
    ap.add_argument("--json", action="store_true", help="print one JSON object")
    args = ap.parse_args(argv)

    reports, errors = [], []
    for path in args.files:
        try:
            reports.append(check_file(path))
        except (OSError, ParseError, ValueError) as exc:
            errors.append({"file": str(path), "error": str(exc)})

    if args.json:
        print(json.dumps({"reports": reports, "errors": errors}, indent=2))
    else:
        for rep in reports:
            print(rep["file"])
            if rep.get("note"):
                print(f"  note: {rep['note']}")
            for r in rep["pairs"]:
                mark = "ok  " if r["ok"] else "FAIL"
                ratio = "  n/a" if r["ratio"] is None else f"{r['ratio']:5.2f}"
                pair = f"{r['fg']} on {r['bg']}"
                line = f"  {mark} {r['theme']:<11} {pair:<34} {ratio} >= {r['floor']}"
                if r.get("note"):
                    line += f"  ({r['note']})"
                print(line)
        for err in errors:
            print(f"{err['file']}: error: {err['error']}", file=sys.stderr)

    if errors:
        return 1
    return 0 if all(rep["ok"] for rep in reports) else 2


if __name__ == "__main__":
    sys.exit(main())
