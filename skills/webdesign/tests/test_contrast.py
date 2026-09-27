#!/usr/bin/env python3
"""Regression tests for scripts/check_contrast.py.

The reference values are the published WCAG boundary cases, so a change to the colour
maths that drifts from the standard fails here before it can pass a bad palette.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
sys.path.insert(0, str(SKILL / "scripts"))

import check_contrast as cc  # noqa: E402

FIXTURES = HERE / "contrast_fixtures"
SCRIPT = SKILL / "scripts" / "check_contrast.py"
failures: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    print(f"{'PASS' if condition else 'FAIL'}  {name}{'  ' + detail if detail else ''}")
    if not condition:
        failures.append(name)


def ratio(fg: str, bg: str) -> float:
    return cc.contrast(cc.parse_colour(fg)[0], cc.parse_colour(bg)[0])


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True)


def message(res: subprocess.CompletedProcess) -> str:
    """The error text without the file path, which names the fixture folder."""
    return res.stderr.rpartition(": error: ")[2]


for fg, bg, want in [
    ("#000000", "#ffffff", 21.0),
    ("#767676", "#ffffff", 4.54),
    ("#777777", "#ffffff", 4.48),
    ("#fff", "#000", 21.0),
    ("rgb(118 118 118)", "#ffffff", 4.54),
    ("oklch(0% 0 0)", "oklch(100% 0 0)", 21.0),
]:
    got = ratio(fg, bg)
    check(f"ratio {fg} on {bg}", abs(got - want) < 0.02, f"got {got:.2f} want {want}")

red, red_clamped = cc.parse_colour("oklch(62.8% 0.2577 29.23)")
check("oklch pure red round-trips", cc.to_hex(red) == "#ff0000" and not red_clamped, cc.to_hex(red))
_, oog = cc.parse_colour("oklch(70% 0.4 150)")
check("out-of-gamut oklch is flagged", oog)

systems = sorted((SKILL / "systems").glob("*.md"))
check("archetype systems exist", len(systems) >= 4, f"{len(systems)} found")
res = run(*map(str, systems))
check("every archetype passes its declared pairs", res.returncode == 0, res.stdout[-300:])

res = run(str(FIXTURES / "fails.md"))
check("a failing palette exits 2", res.returncode == 2, f"exit {res.returncode}")
check("the failing pair is named", "FAIL" in res.stdout and "ink on canvas" in res.stdout)

res = run(str(FIXTURES / "refs.md"))
check("token references resolve", res.returncode == 0, res.stdout.strip()[-120:])

res = run(str(FIXTURES / "loop.md"))
check("a reference loop is an error, exit 1", res.returncode == 1, f"exit {res.returncode}")

res = run(str(FIXTURES / "missing.md"))
check("a missing token fails, exit 2", res.returncode == 2 and "not defined" in res.stdout)

res = run(str(FIXTURES / "nofront.md"))
check("no frontmatter is an error, exit 1", res.returncode == 1, f"exit {res.returncode}")

res = run(str(FIXTURES / "fails.md"), "--json")
check("--json parses", res.stdout.strip().startswith("{") and '"reports"' in res.stdout)


res = run(str(FIXTURES / "alpha.md"), "--json")
rows = json.loads(res.stdout)["reports"][0]["pairs"] if res.stdout.strip() else []
ratios = [r["ratio"] for r in rows]
check("translucent tokens are composited, not read as opaque",
      res.returncode == 2 and len(ratios) == 3 and all(r is not None and 2.2 < r < 2.6 for r in ratios),
      f"ratios {ratios}")

res = run(str(FIXTURES / "glass.md"))
check("a translucent ground cannot pass", res.returncode == 2 and "translucent" in res.stdout)

res = run(str(FIXTURES / "badyaml.md"))
check("invalid YAML is an error, not a traceback",
      res.returncode == 1 and "Traceback" not in res.stderr, f"exit {res.returncode}")

res = run("--no-such-flag", str(FIXTURES / "refs.md"))
check("a usage error exits 1", res.returncode == 1, f"exit {res.returncode}")

res = run(str(FIXTURES / "linked.md"), "--json")
pairs = [(r["fg"], r["bg"]) for r in json.loads(res.stdout)["reports"][0]["pairs"]]
check("aliased pairs resolve together", ("on-primary", "accent") not in pairs
      and ("on-primary", "primary") in pairs, f"{pairs}")

# The same inline file through the stdlib parser, with PyYAML blocked, must still see
# the declared caption pair. CI's fixtures job runs without PyYAML.
probe = (
    "import builtins, sys\n"
    "real = builtins.__import__\n"
    "def fake(name, *a, **k):\n"
    "    if name == 'yaml':\n"
    "        raise ImportError('blocked')\n"
    "    return real(name, *a, **k)\n"
    "builtins.__import__ = fake\n"
    f"sys.path.insert(0, {str(SKILL / 'scripts')!r})\n"
    "import check_contrast\n"
    f"sys.exit(check_contrast.main([{str(FIXTURES / 'inline.md')!r}]))\n"
)
res = subprocess.run([sys.executable, "-c", probe], capture_output=True, text=True)
check("stdlib parser reads an inline contrast list",
      res.returncode == 2 and "caption on canvas" in res.stdout, f"exit {res.returncode}")
probe_zero = probe.replace("inline.md", "zeroindent.md")
res = subprocess.run([sys.executable, "-c", probe_zero], capture_output=True, text=True)
check("stdlib parser reads a zero-indent contrast list",
      res.returncode == 2 and "caption on canvas" in res.stdout, f"exit {res.returncode}")
res = run(str(FIXTURES / "zeroindent.md"))
check("PyYAML path agrees on the zero-indent file",
      res.returncode == 2 and "caption on canvas" in res.stdout, f"exit {res.returncode}")
res = run(str(FIXTURES / "inline.md"))
check("PyYAML path agrees on the inline file",
      res.returncode == 2 and "caption on canvas" in res.stdout, f"exit {res.returncode}")

# A malformed contrast list is an error that names the bad entry, on both parser
# paths: never a traceback, and never a pair read one character at a time. A null
# name arrives as None from PyYAML and as the text "~" from the stdlib parser, and
# both must get the same error.
for name, wants in [
    ("scalar.md", ("'contrast' must be a list of [fg, bg, floor] entries", "5")),
    ("stringitem.md", ("'ink'",)),
    ("twoitem.md", ("['ink', 'canvas']",)),
    ("nullname.md", ("'ink'", "needs two token names")),
]:
    stdlib = subprocess.run([sys.executable, "-c", probe.replace("inline.md", name)],
                            capture_output=True, text=True)
    for parser, res in (("PyYAML path", run(str(FIXTURES / name))), ("stdlib parser", stdlib)):
        check(f"{parser}: {name} is an error naming the entry, not a traceback",
              res.returncode == 1 and "Traceback" not in res.stderr
              and all(want in message(res) for want in wants),
              f"exit {res.returncode}: {res.stderr.strip()[-160:]}")

# A numeric scale such as 50 to 900 reads as ints under PyYAML and as strings under
# the stdlib parser, and both must resolve.
stdlib = subprocess.run([sys.executable, "-c", probe.replace("inline.md", "numeric.md")],
                        capture_output=True, text=True)
for parser, res in (("PyYAML path", run(str(FIXTURES / "numeric.md"))), ("stdlib parser", stdlib)):
    check(f"{parser}: numeric token names resolve",
          res.returncode == 0 and "900 on 50" in res.stdout,
          f"exit {res.returncode}: {(res.stdout + res.stderr).strip()[-160:]}")

for entry in (["ink", "canvas", "high"], ["ink", "canvas", True], ["ink", None, 4.5],
              ["ink", "null", 4.5], [True, "canvas", 4.5]):
    try:
        cc.declared_pairs({"contrast": [entry]})
        refused = False
    except cc.ParseError:
        refused = True
    check(f"contrast entry {entry!r} is refused", refused)

print(f"\n{len(failures)} failure(s)")
sys.exit(1 if failures else 0)
