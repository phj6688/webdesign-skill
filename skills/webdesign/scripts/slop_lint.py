#!/usr/bin/env python3
"""slop_lint: a deterministic linter for AI design-slop patterns in frontend source.

RULES below is the single source of truth for rule ids, severities, messages, fix
hints and file-extension scope. The parser builds a small set of document facts
once per file (text nodes, string literals, tags, class lists, CSS rules) and each
rule reads those facts, so a rule stays narrow instead of drifting into a
whole-file grep.

Standard library only. No network, no subprocess.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import math
import os
import re
import statistics
import sys
from bisect import bisect_left, bisect_right
from dataclasses import dataclass, field

VERSION = "1.1.0"

EM_DASH = chr(0x2014)
EN_DASH = chr(0x2013)
MIDDLE_DOT = chr(0xB7)
ARROW_DOWN = chr(0x2193)

MARKUP_EXTS = (".html", ".htm", ".jsx", ".tsx", ".vue", ".svelte", ".astro")
SCRIPT_EXTS = (".js", ".ts", ".jsx", ".tsx", ".vue", ".svelte", ".astro")
STYLE_EXTS = (".css", ".scss", ".html", ".htm", ".vue", ".svelte", ".astro")
TEXT_EXTS = tuple(sorted(set(MARKUP_EXTS + SCRIPT_EXTS)))
CLASS_EXTS = tuple(sorted(set(MARKUP_EXTS + STYLE_EXTS)))
ALL_EXTS = tuple(sorted(set(MARKUP_EXTS + SCRIPT_EXTS + STYLE_EXTS)))
HTML_EXTS = (".html", ".htm")

SEVERITIES = ("error", "warning", "advisory")

SKIP_DIRS = frozenset({
    "node_modules", ".git", "dist", "build", ".next", "out",
    "coverage", "vendor", "__pycache__",
})

MAX_FILE_BYTES = 2_000_000
# A bundle is long lines almost everywhere. One data URI line in a hand-written
# page leaves the median short, so the page is still linted.
MINIFIED_MEDIAN = 500
# Rules that read a whole line for context see at most this much of a long line.
LINE_WINDOW = 1000
EVIDENCE_LEN = 120
ROOT_PX = 16.0


@dataclass(frozen=True)
class Rule:
    rule_id: str
    severity: str
    message: str
    fix: str
    exts: tuple[str, ...]
    note: str = ""


RULES: tuple[Rule, ...] = (
    Rule(
        "em-dash", "error",
        "Em dash or en dash in UI copy.",
        "Use a comma, a colon, parentheses, or two sentences.",
        TEXT_EXTS,
    ),
    Rule(
        "pure-black-white", "warning",
        "Pure black or pure white used as a colour value.",
        "Use a near-black or near-bone tone from the palette instead.",
        ALL_EXTS,
        note="dynamic: advisory at 1 occurrence per file, warning at 2 or more",
    ),
    Rule(
        "scroll-listener", "error",
        "Scroll listener drives layout or motion.",
        "Use IntersectionObserver or a CSS scroll-driven animation.",
        SCRIPT_EXTS,
    ),
    Rule(
        "h-screen-hero", "error",
        "Viewport-locked height breaks on mobile browser chrome.",
        "Use min-h-[100dvh] in Tailwind, or min-height: 100dvh in CSS.",
        CLASS_EXTS,
    ),
    Rule(
        "banned-font", "warning",
        "Over-used default font family in the first position of the stack.",
        "Pick a family with a voice, and keep the generic name as a fallback.",
        ALL_EXTS,
    ),
    Rule(
        "eyebrow-density", "warning",
        "Too many uppercase tracked eyebrow labels for the section count.",
        "Keep at most one eyebrow per three sections, and delete the rest.",
        CLASS_EXTS,
    ),
    Rule(
        "section-number-label", "warning",
        "Enumerated section label reads as a template, not as content.",
        "Delete the number, or give the section a real name.",
        TEXT_EXTS,
    ),
    Rule(
        "scroll-cue", "warning",
        "Scroll cue text tells the visitor to do what they already do.",
        "Delete the cue, and let the content edge signal more below.",
        TEXT_EXTS,
    ),
    Rule(
        "filler-verb", "warning",
        "Filler marketing verb carries no information.",
        "Name the concrete outcome instead of the verb.",
        TEXT_EXTS,
    ),
    Rule(
        "placeholder-identity", "warning",
        "Placeholder person or brand name left in the copy.",
        "Use a real name, or cut the element until content exists.",
        TEXT_EXTS,
    ),
    Rule(
        "fake-round-number", "warning",
        "Invented round statistic reads as filler.",
        "Use a measured number, or remove the statistic.",
        TEXT_EXTS,
    ),
    Rule(
        "tight-leading", "warning",
        "Line height below 1.3 on non-display text.",
        "Use 1.5 or more for body text, and keep tight leading for display only.",
        CLASS_EXTS,
    ),
    Rule(
        "tiny-text", "warning",
        "Body text set below 12px.",
        "Use 16px for body text. 12px is the floor.",
        CLASS_EXTS,
        note="reads px and rem against a 16px root, never em or %; functional text "
             "goes to undersized-ui-text",
    ),
    Rule(
        "undersized-ui-text", "warning",
        "Functional UI text set below 11px.",
        "Keep functional text at 11px or more, and 12px or more where it fits.",
        CLASS_EXTS,
        note="links, buttons, nav items, labels, table cells, time, inputs and "
             "selects; reads px and rem against a 16px root",
    ),
    Rule(
        "wide-tracking-body", "warning",
        "Letter spacing above 0.05em on lowercase body text.",
        "Keep tracking near 0 for body text, and reserve it for uppercase labels.",
        CLASS_EXTS,
    ),
    Rule(
        "extreme-tracking", "warning",
        "Letter spacing tighter than -0.04em collides the glyphs.",
        "Keep tracking at -0.03em or looser.",
        CLASS_EXTS,
    ),
    Rule(
        "gradient-text", "warning",
        "Gradient clipped to text is an AI-era default.",
        "Use one solid colour, and spend the boldness on layout instead.",
        CLASS_EXTS,
    ),
    Rule(
        "no-reduced-motion", "warning",
        "File declares animation but honours no reduced-motion preference.",
        "Add a prefers-reduced-motion media query, or call useReducedMotion.",
        ALL_EXTS,
    ),
    Rule(
        "banned-palette", "warning",
        "Hex value from the over-used AI premium-consumer palette.",
        "Pick a palette from the brief, not the cream-and-terracotta default.",
        ALL_EXTS,
    ),
    Rule(
        "middle-dot-run", "warning",
        "Three or more middle-dot separators in one text run.",
        "Use two items with a comma, or a real list element.",
        TEXT_EXTS,
    ),
    Rule(
        "lucide-icons", "warning",
        "Lucide icon set is the AI-default icon look.",
        "Use the project icon set, or one icon library at one stroke weight.",
        SCRIPT_EXTS,
    ),
    Rule(
        "hand-rolled-icon", "advisory",
        "Hand-drawn inline icon path with no icon library in the file.",
        "Check the glyph against a real icon set, or keep one consistent source.",
        MARKUP_EXTS,
    ),
    Rule(
        "three-column-cards", "advisory",
        "Three-column card row is the default AI section shape.",
        "Vary the rhythm: two columns, an offset pair, or a list.",
        MARKUP_EXTS,
    ),
    Rule(
        "nested-card", "advisory",
        "Card with a shadow inside another card with a shadow.",
        "Flatten one level, and keep a single elevation per surface.",
        HTML_EXTS,
    ),
    Rule(
        "version-label-hero", "advisory",
        "Version or access badge in the hero region.",
        "Move the badge out of the hero, or delete it.",
        MARKUP_EXTS,
    ),
    Rule(
        "system-font-display", "advisory",
        "System display font in the first position of the stack.",
        "Pick a real display family, and keep the system name as a fallback.",
        CLASS_EXTS,
    ),
)

RULES_BY_ID = {rule.rule_id: rule for rule in RULES}


@dataclass
class Finding:
    file: str
    line: int
    col: int
    rule: str
    severity: str
    message: str
    fix: str
    evidence: str

    def as_dict(self) -> dict:
        return {
            "file": self.file,
            "line": self.line,
            "col": self.col,
            "rule": self.rule,
            "severity": self.severity,
            "message": self.message,
            "fix": self.fix,
            "evidence": self.evidence,
        }


# Document facts compare by identity: a tag points at other tags, and value
# equality would walk that graph.
@dataclass(eq=False)
class TextNode:
    offset: int
    text: str
    tag: str
    anc: str
    owner: object = field(default=None, repr=False)


@dataclass
class StrLit:
    offset: int
    text: str
    quote: str
    line_text: str


@dataclass(eq=False)
class Tag:
    name: str
    offset: int
    end: int
    closing: bool
    self_closing: bool
    attrs: dict
    classes: tuple
    tag_id: str
    # own: this tag's class and id text. anc: own plus the own text of at most
    # four ancestors. A tag never copies an ancestor's anc, so the context stays
    # bounded at any nesting depth.
    own: str
    anc: str
    parents: tuple
    # A click handler, an interactive role or a pointer cursor on this tag
    # (ui_attr), or on it or one of four ancestors (ui_chain).
    ui_attr: bool = False
    ui_chain: bool = False
    close: int = -1
    closed: bool = False
    after_top: object = field(default=None, repr=False)
    after_ctx: str = ""


@dataclass
class Decl:
    prop: str
    value: str
    offset: int


@dataclass(eq=False)
class CssRule:
    sel: str
    sel_path: str
    offset: int
    decls: list
    owner: object = field(default=None, repr=False)


@dataclass(eq=False)
class ClassList:
    offset: int
    text: str
    tokens: tuple
    tag: str
    owner: object = field(default=None, repr=False)


TAG_NAME_RE = re.compile(r"</?([A-Za-z][A-Za-z0-9:._-]*)")
ATTR_RE = re.compile(
    r"""([@:A-Za-z_][-A-Za-z0-9_:.$]*)\s*=\s*"""
    r"""(?:"([^"]*)"|'([^']*)'|(\{(?:[^{}]|\{[^{}]*\})*\})|([^\s"'`<>]+))""",
)
QUOTED_RE = re.compile(r"""["'`]([^"'`]*)["'`]""")
CLASS_ATTRS = ("class", "classname", ":class", "class:list", "v-bind:class")
CLASS_HINT_RE = re.compile(r"class|clsx\(|\bcn\(|cva\(|twmerge", re.IGNORECASE)
JSX_TEXT_RE = re.compile(r">([^<>{}]{1,400})<")
JSX_TEXT_REJECT = set("=&|;()!*\\+`$#")
# Every stretch of JSX between tag and expression delimiters, with no operator
# filter. The em-dash rule reads these: a dash is copy even beside a '!'.
RAW_RUN_RE = re.compile(r"[>}]([^<>{}]+)(?=[<{])")
STRING_OPEN_BEFORE = set("=(,:[{;+-*/!?&|%<>~^\n\t ")

RAW_TEXT_TAGS = frozenset({"script", "style", "pre", "code", "textarea"})
VOID_TAGS = frozenset({
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
})
SCRIPT_PRIMARY = frozenset({".js", ".ts", ".jsx", ".tsx"})
TAG_SCAN_LIMIT = 20000
TAG_STOP_RE = re.compile(r"""[>"'`{}=]""")
JS_STRING_RES = {
    '"': re.compile(r'"(?:[^"\\\n]|\\.)*"'),
    "'": re.compile(r"'(?:[^'\\\n]|\\.)*'"),
    "`": re.compile(r"`(?:[^`\\]|\\.)*`", re.DOTALL),
}
_CLOSE_RE_CACHE: dict = {}


def close_tag_re(name: str) -> re.Pattern:
    pat = _CLOSE_RE_CACHE.get(name)
    if pat is None:
        pat = re.compile(r"</" + re.escape(name) + r"\s*>", re.IGNORECASE)
        _CLOSE_RE_CACHE[name] = pat
    return pat


class NextChar:
    """First index of one character at or after a position.

    The answer from one search holds for every later position up to the hit, so
    a forward scan pays for each stretch of source once.
    """

    def __init__(self, src: str, char: str):
        self.src = src
        self.char = char
        self.pos = -1
        self.hit = -1

    def at(self, pos: int) -> int:
        stale = self.pos < 0 or pos < self.pos or (0 <= self.hit < pos)
        if stale:
            self.pos = pos
            self.hit = self.src.find(self.char, pos)
        return self.hit


def parse_attrs(text: str, base: int) -> dict:
    out: dict = {}
    for m in ATTR_RE.finditer(text):
        key = m.group(1).lower()
        if key in out:
            continue
        for group in (2, 3, 4, 5):
            if m.group(group) is not None:
                raw = m.group(group)
                off = m.start(group)
                braced = group == 4
                if braced:
                    raw = raw[1:-1]
                    off += 1
                out[key] = {"value": raw, "off": base + off, "braced": braced}
                break
    return out


def class_text_of(value: str) -> str:
    quoted = QUOTED_RE.findall(value)
    if quoted:
        return " ".join(quoted)
    return value


def split_tokens(text: str) -> tuple:
    return tuple(tok for tok in text.split() if tok)


def tw_base(token: str) -> str:
    """Strip Tailwind variant prefixes so a token compares as a bare utility."""
    token = token.strip().lstrip("!")
    head, sep, tail = token.partition("[")
    if sep:
        return head.rsplit(":", 1)[-1] + "[" + tail
    return token.rsplit(":", 1)[-1]


def _tag_end(src: str, i: int, end: int) -> tuple:
    """Index of the '>' that ends a tag, or -1 and the index the scan stopped at.

    A quoted attribute value is skipped with one str.find, so a data URI of any
    length is cheap. Everything else draws on a fixed budget.
    """
    budget = TAG_SCAN_LIMIT
    depth = 0
    while i < end and budget > 0:
        m = TAG_STOP_RE.search(src, i, min(end, i + budget))
        if m is None:
            return -1, min(end, i + budget)
        budget -= m.start() - i + 1
        i = m.start()
        c = src[i]
        if c == ">":
            if depth == 0:
                return i, i + 1
        elif c == "{":
            depth += 1
        elif c == "}":
            depth = max(0, depth - 1)
        elif c == "=":
            if depth == 0:
                j = i + 1
                while j < end and src[j] in " \t\r\n":
                    j += 1
                if j < end and src[j] in "\"'":
                    close = src.find(src[j], j + 1, end)
                    if close >= 0:
                        i = close + 1
                        continue
        elif depth > 0:
            lit = JS_STRING_RES[c].match(src, i, end)
            if lit:
                i = lit.end()
                continue
        i += 1
    return -1, min(i, end)


def read_tag(src: str, start: int, end: int, next_gt: NextChar) -> tuple:
    """(info, after) for the tag at start, or (None, resume) when there is none.

    A '<' with no '>' anywhere ahead resumes one character on, which the cached
    search keeps cheap. A scan that spends its budget resumes past the window it
    read, so a run of unclosed tags costs linear time.
    """
    m = TAG_NAME_RE.match(src, start, end)
    if not m:
        return None, start + 1
    gt = next_gt.at(m.end())
    if gt < 0 or gt >= end:
        return None, start + 1
    found, stop = _tag_end(src, m.end(), end)
    if found < 0:
        return None, max(start + 1, stop)
    raw = src[start:found + 1]
    body = raw[:-1].rstrip()
    info = {
        "name": m.group(1).lower(),
        "closing": src[start + 1] == "/",
        "self_closing": body.endswith("/"),
        "attrs": parse_attrs(src[m.end():found], m.end()),
    }
    return info, found + 1


def pop_stack(stack: list, name: str, at: int) -> bool:
    for idx in range(len(stack) - 1, -1, -1):
        if stack[idx].name == name:
            stack[idx].closed = True
            for tag in stack[idx:]:
                tag.close = at
            del stack[idx:]
            return True
    return False


def close_stack(stack: list, at: int) -> None:
    for tag in stack:
        tag.close = at
    stack.clear()


def stack_context(stack: list) -> str:
    return " ".join(tag.own for tag in stack[-4:] if tag.own)


CLICK_ATTRS = ("onclick", "@click", "on:click", "v-on:click")
UI_ROLES = frozenset({
    "button", "link", "tab", "menuitem", "menuitemcheckbox", "menuitemradio",
    "option", "switch", "checkbox", "radio",
})


def ui_attrs(attrs: dict) -> bool:
    """True when an element's attributes make it something a visitor operates."""
    if any(key in attrs for key in CLICK_ATTRS):
        return True
    if attrs.get("role", {}).get("value", "").strip().lower() in UI_ROLES:
        return True
    style = attrs.get("style", {}).get("value", "")
    return "cursor:pointer" in "".join(style.split()).lower()


def astro_frontmatter(src: str):
    if not src.startswith("---"):
        return None
    stop = src.find("\n---", 3)
    if stop < 0:
        return None
    return 3, stop


class Doc:
    def __init__(self, path: str, rel: str, src: str, ext: str):
        self.path = path
        self.rel = rel
        self.src = src
        self.ext = ext
        self.script_primary = ext in SCRIPT_PRIMARY
        self.line_starts = [0]
        for m in re.finditer("\n", src):
            self.line_starts.append(m.end())
        self.comments: list = []
        self.strings: list = []
        self.text_nodes: list = []
        self.tags: list = []
        self.css_rules: list = []
        self.class_lists: list = []
        self.raw_runs: list = []
        self.fences: list = []
        self.nesting_ok = True
        self.code_src = src
        self.bare_src = src
        self.next_gt = NextChar(src, ">")
        self.cache: dict = {}
        self._class_offsets: set = set()
        self._class_spans: list = []

    def line_col(self, offset: int) -> tuple:
        idx = bisect_right(self.line_starts, offset) - 1
        idx = max(0, min(idx, len(self.line_starts) - 1))
        return idx + 1, offset - self.line_starts[idx] + 1

    def line_text(self, offset: int) -> str:
        idx = bisect_right(self.line_starts, offset) - 1
        idx = max(0, min(idx, len(self.line_starts) - 1))
        start = self.line_starts[idx]
        if idx + 1 < len(self.line_starts):
            stop = self.line_starts[idx + 1] - 1
        else:
            stop = len(self.src)
        if stop - start > LINE_WINDOW:
            half = LINE_WINDOW // 2
            start = max(start, offset - half)
            stop = min(stop, offset + half)
        return self.src[start:stop]

    def in_fence(self, offset: int) -> bool:
        return any(a <= offset < b for a, b in self.fences)

    def add_comment(self, start: int, end: int) -> None:
        self.comments.append((start, end))

    def add_string(self, offset: int, text: str, quote: str) -> None:
        self.strings.append(StrLit(offset, text, quote, self.line_text(offset)))

    def add_text(self, offset: int, text: str, stack: list) -> None:
        if not text.strip():
            return
        owner = stack[-1] if stack else None
        name = owner.name if owner else ""
        self.text_nodes.append(
            TextNode(offset, text, name, stack_context(stack), owner)
        )

    def add_tag(self, info: dict, start: int, end: int, stack: list) -> Tag:
        attrs = info["attrs"]
        tag_id = attrs.get("id", {}).get("value", "")
        classes: tuple = ()
        entry = None
        for key in CLASS_ATTRS:
            if key in attrs:
                entry = attrs[key]
                classes = split_tokens(class_text_of(entry["value"]))
                break
        own = (" ".join(classes) + " " + tag_id).strip().lower()
        parent_ctx = stack_context(stack)
        tag = Tag(
            name=info["name"],
            offset=start,
            end=end,
            closing=info["closing"],
            self_closing=info["self_closing"],
            attrs=attrs,
            classes=classes,
            tag_id=tag_id,
            own=own,
            anc=(own + " " + parent_ctx).strip(),
            parents=tuple(t.name for t in stack[-4:]),
        )
        tag.ui_attr = ui_attrs(attrs)
        tag.ui_chain = tag.ui_attr or any(t.ui_attr for t in stack[-4:])
        self.tags.append(tag)
        if entry is not None and not info["closing"]:
            if entry["braced"] and self.script_primary:
                # The strings inside className={...} become class lists once the
                # scan is done, owned by this tag.
                stop = entry["off"] + len(entry["value"])
                self._class_spans.append((entry["off"], stop, tag))
            elif classes:
                text = class_text_of(entry["value"])
                self.class_lists.append(
                    ClassList(entry["off"], text, classes, tag.name, tag)
                )
                self._class_offsets.add(entry["off"])
        if "style" in attrs and not info["closing"]:
            self._add_inline_style(tag, attrs["style"])
        return tag

    def _add_inline_style(self, tag: Tag, entry: dict) -> None:
        decls = []
        cursor = entry["off"]
        for chunk in entry["value"].split(";"):
            if ":" in chunk:
                prop, _, value = chunk.partition(":")
                decls.append(Decl(prop.strip().lower(), value.strip(), cursor))
            cursor += len(chunk) + 1
        if decls:
            sel = (tag.name + " ." + " .".join(tag.classes)).strip()
            if tag.tag_id:
                sel += " #" + tag.tag_id
            self.css_rules.append(CssRule(sel, sel, tag.offset, decls, tag))

    def build_masks(self) -> None:
        self.code_src = blank_regions(self.src, self.comments)
        spans = [(s.offset, s.offset + len(s.text)) for s in self.strings]
        self.bare_src = blank_regions(self.code_src, spans)
        marks = [m.start() for m in re.finditer("```", self.src)]
        for idx in range(0, len(marks) - 1, 2):
            self.fences.append((marks[idx], marks[idx + 1] + 3))
        if len(marks) % 2 == 1:
            self.fences.append((marks[-1], len(self.src)))

    def add_string_class_lists(self) -> None:
        """Class lists held in string literals.

        This runs after the tag scan, so a JSX className="..." string, which the
        tag already recorded, is skipped by its offset instead of counted twice.
        A string inside className={...} belongs to that tag and is no longer copy.
        Any other string counts when its line looks like class code, and stays
        copy too: 'Bug-class.' in a tooltip matches that hint and is still prose.
        """
        spans = sorted(self._class_spans, key=lambda span: span[0])
        starts = [span[0] for span in spans]
        for lit in self.strings:
            if lit.offset in self._class_offsets or not lit.text.strip():
                continue
            owner = None
            idx = bisect_right(starts, lit.offset) - 1
            if idx >= 0 and lit.offset < spans[idx][1]:
                owner = spans[idx][2]
            elif not CLASS_HINT_RE.search(lit.line_text):
                continue
            tokens = split_tokens(lit.text)
            if not tokens:
                continue
            name = owner.name if owner else ""
            self.class_lists.append(ClassList(lit.offset, lit.text, tokens, name, owner))
            if owner is not None:
                self._class_offsets.add(lit.offset)
        self.class_lists.sort(key=lambda cl: cl.offset)


def blank_regions(src: str, regions: list) -> str:
    if not regions:
        return src
    buf = list(src)
    size = len(buf)
    for start, end in regions:
        for idx in range(max(0, start), min(end, size)):
            if buf[idx] != "\n":
                buf[idx] = " "
    return "".join(buf)


def scan_js(doc: Doc, start: int, end: int) -> None:
    src = doc.src
    i = start
    while i < end:
        c = src[i]
        if c == "/" and i + 1 < end:
            nxt = src[i + 1]
            if nxt == "/":
                stop = src.find("\n", i, end)
                stop = end if stop < 0 else stop
                doc.add_comment(i, stop)
                i = stop
                continue
            if nxt == "*":
                stop = src.find("*/", i + 2, end)
                stop = end if stop < 0 else stop + 2
                doc.add_comment(i, stop)
                i = stop
                continue
        if c in "\"'`":
            if c == "'" and not _quote_opens_here(src, i, start):
                i += 1
                continue
            j = i + 1
            closed = False
            while j < end:
                if src[j] == "\\":
                    j += 2
                    continue
                if src[j] == c:
                    closed = True
                    break
                if c != "`" and src[j] == "\n":
                    break
                j += 1
            if not closed:
                i += 1
                continue
            doc.add_string(i + 1, src[i + 1:j], c)
            i = j + 1
            continue
        i += 1


def _quote_opens_here(src: str, i: int, start: int) -> bool:
    """An apostrophe inside JSX prose must not open a string literal."""
    j = i - 1
    while j >= start and src[j] in " \t":
        j -= 1
    if j < start:
        return True
    return src[j] in STRING_OPEN_BEFORE


def scan_jsx_tags(doc: Doc, start: int, end: int) -> None:
    bare = doc.bare_src
    stack: list = []
    i = start
    while i < end:
        lt = bare.find("<", i, end)
        if lt < 0:
            break
        nxt = bare[lt + 1] if lt + 1 < end else ""
        if not (nxt.isalpha() or nxt == "/"):
            i = lt + 1
            continue
        info, after = read_tag(doc.src, lt, end, doc.next_gt)
        if info is None:
            i = after
            continue
        tag = doc.add_tag(info, lt, after, stack)
        if info["closing"]:
            pop_stack(stack, info["name"], lt)
        elif info["self_closing"] or info["name"] in VOID_TAGS:
            tag.close = after
        else:
            stack.append(tag)
        tag.after_top = stack[-1] if stack else None
        tag.after_ctx = stack_context(stack)
        i = after
    close_stack(stack, end)


def scan_jsx_text(doc: Doc, start: int, end: int) -> None:
    """JSX text has no parser here, so a text run belongs to the element that the
    tag before it left open."""
    bare = doc.bare_src
    offsets = [tag.offset for tag in doc.tags]
    for m in JSX_TEXT_RE.finditer(bare, start, end):
        body = m.group(1)
        if not body.strip() or JSX_TEXT_REJECT & set(body):
            continue
        if not any(ch.isalpha() for ch in body):
            continue
        owner = None
        ctx = ""
        idx = bisect_right(offsets, m.start(1)) - 1
        if idx >= 0:
            owner = doc.tags[idx].after_top
            ctx = doc.tags[idx].after_ctx
        real = doc.src[m.start(1):m.end(1)]
        name = owner.name if owner else ""
        doc.text_nodes.append(TextNode(m.start(1), real, name, ctx, owner))
    for m in RAW_RUN_RE.finditer(bare, start, end):
        doc.raw_runs.append((m.start(1), m.end(1)))


def scan_markup(doc: Doc, start: int, end: int) -> None:
    src = doc.src
    stack: list = []
    i = start
    while i < end:
        lt = src.find("<", i, end)
        if lt < 0:
            doc.add_text(i, src[i:end], stack)
            break
        if lt > i:
            doc.add_text(i, src[i:lt], stack)
        if src.startswith("<!--", lt):
            stop = src.find("-->", lt + 4, end)
            i = end if stop < 0 else stop + 3
            doc.add_comment(lt, i)
            continue
        if src.startswith("<!", lt) or src.startswith("<?", lt):
            stop = src.find(">", lt, end)
            i = end if stop < 0 else stop + 1
            continue
        info, after = read_tag(src, lt, end, doc.next_gt)
        if info is None:
            i = after
            continue
        tag = doc.add_tag(info, lt, after, stack)
        name = info["name"]
        if info["closing"]:
            if not pop_stack(stack, name, lt):
                doc.nesting_ok = False
            i = after
            continue
        if info["self_closing"] or name in VOID_TAGS:
            tag.close = after
            i = after
            continue
        if name in RAW_TEXT_TAGS:
            m = close_tag_re(name).search(src, after, end)
            inner_end = m.start() if m else end
            tag.close = inner_end
            tag.closed = m is not None
            _scan_raw_block(doc, tag, after, inner_end)
            i = m.end() if m else end
            continue
        stack.append(tag)
        i = after
    close_stack(stack, end)


def _scan_raw_block(doc: Doc, tag: Tag, start: int, end: int) -> None:
    if end <= start:
        return
    if tag.name == "style":
        parse_css(doc, start, end)
    elif tag.name == "script":
        kind = tag.attrs.get("type", {}).get("value", "").lower()
        if "json" not in kind:
            scan_js(doc, start, end)


def _skip_parens(src: str, i: int, end: int) -> int:
    depth = 0
    while i < end:
        c = src[i]
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return i + 1
        elif c in "\"'":
            i += 1
            while i < end and src[i] != c:
                i += 2 if src[i] == "\\" else 1
        i += 1
    return end


CSS_COMMENT_RE = re.compile(r"/\*.*?\*/|^[ \t]*//[^\n]*", re.DOTALL | re.MULTILINE)


def strip_css_comments(raw: str) -> str:
    """Blank comments at equal length, so a comment above a selector or a
    declaration neither joins its text nor moves its offset."""
    return CSS_COMMENT_RE.sub(lambda m: re.sub(r"[^\n]", " ", m.group(0)), raw)


def _add_decl(block: dict, src: str, start: int, end: int) -> None:
    raw = strip_css_comments(src[start:end])
    if ":" not in raw:
        return
    prop, _, value = raw.partition(":")
    name = prop.strip().lower()
    if not name or name.startswith("@") or "{" in name or "}" in name:
        return
    offset = start + (len(prop) - len(prop.lstrip()))
    block["decls"].append(Decl(name, value.strip(), offset))


def parse_css(doc: Doc, start: int, end: int) -> None:
    src = doc.src
    blocks: list = []
    chunk = start
    i = start
    while i < end:
        c = src[i]
        if c == "/" and i + 1 < end and src[i + 1] == "*":
            stop = src.find("*/", i + 2, end)
            stop = end if stop < 0 else stop + 2
            doc.add_comment(i, stop)
            i = stop
            continue
        if c == "/" and i + 1 < end and src[i + 1] == "/":
            stop = src.find("\n", i, end)
            stop = end if stop < 0 else stop
            doc.add_comment(i, stop)
            i = stop
            continue
        if c == "(":
            i = _skip_parens(src, i, end)
            continue
        if c in "\"'":
            j = i + 1
            while j < end and src[j] != c:
                j += 2 if src[j] == "\\" else 1
            i = min(j + 1, end)
            continue
        if c == "{":
            raw_sel = strip_css_comments(src[chunk:i])
            sel = " ".join(raw_sel.split())
            # An enclosing @media or @supports prelude is not part of the
            # selector: "(display: grid)" must not read as a display class.
            path = " ".join(
                b["sel"] for b in blocks if b["sel"] and not b["sel"].startswith("@")
            )
            blocks.append({
                "sel": sel,
                "path": (path + " " + sel).strip(),
                "offset": chunk + (len(raw_sel) - len(raw_sel.lstrip())),
                "decls": [],
            })
            chunk = i + 1
        elif c == "}":
            if blocks:
                _add_decl(blocks[-1], src, chunk, i)
                blk = blocks.pop()
                doc.css_rules.append(
                    CssRule(blk["sel"], blk["path"], blk["offset"], blk["decls"])
                )
            chunk = i + 1
        elif c == ";":
            if blocks:
                _add_decl(blocks[-1], src, chunk, i)
            chunk = i + 1
        i += 1


def build_doc(path: str, rel: str, src: str, ext: str) -> Doc:
    doc = Doc(path, rel, src, ext)
    size = len(src)
    if ext in (".css", ".scss"):
        parse_css(doc, 0, size)
        doc.build_masks()
    elif ext in SCRIPT_PRIMARY:
        scan_js(doc, 0, size)
        doc.build_masks()
        scan_jsx_tags(doc, 0, size)
        scan_jsx_text(doc, 0, size)
    elif ext == ".astro":
        front = astro_frontmatter(src)
        body_start = 0
        if front:
            scan_js(doc, front[0], front[1])
            body_start = front[1] + 4
        scan_markup(doc, body_start, size)
        doc.build_masks()
    else:
        scan_markup(doc, 0, size)
        doc.build_masks()
    doc.add_string_class_lists()
    return doc


LEN_RE = re.compile(r"^(-?\d*\.?\d+)\s*(px|rem|em|%|pt|vh|vw|dvh)?$")
URLISH_RE = re.compile(r"://|www\.")
IMPORTISH_RE = re.compile(r"\bimport\b|\brequire\s*\(|\bfrom\s+['\"]")
PATH_START = ("http", "/", "./", "../", "#", "@", "data:", "mailto:")


def clip(text: str) -> str:
    flat = " ".join(str(text).split())
    if len(flat) <= EVIDENCE_LEN:
        return flat
    return flat[:EVIDENCE_LEN - 3] + "..."


def mk(doc: Doc, rule_id: str, offset: int, evidence: str,
       extra: str = "", severity: str = "", fix: str = "") -> Finding:
    rule = RULES_BY_ID[rule_id]
    line, col = doc.line_col(offset)
    message = rule.message if not extra else rule.message + " " + extra
    return Finding(
        file=doc.rel,
        line=line,
        col=col,
        rule=rule_id,
        severity=severity or rule.severity,
        message=message,
        fix=fix or rule.fix,
        evidence=clip(evidence),
    )


def parse_len(value: str):
    raw = value.replace("!important", "").strip().rstrip(";").strip()
    m = LEN_RE.match(raw)
    if not m:
        return None
    try:
        return float(m.group(1)), (m.group(2) or "")
    except ValueError:
        return None


def bracket_value(token: str) -> str:
    start = token.find("[")
    stop = token.rfind("]")
    if start < 0 or stop <= start:
        return ""
    return token[start + 1:stop]


def first_family(value: str) -> str:
    raw = value.replace("!important", "").split(",")[0]
    raw = raw.strip().strip(";").strip().strip("\"'")
    if raw.lower().startswith("var("):
        return ""
    return " ".join(raw.replace("_", " ").split()).lower()


def token_offset(cl: ClassList, token: str) -> int:
    idx = cl.text.find(token)
    return cl.offset + (idx if idx >= 0 else 0)


def is_ui_copy(lit: StrLit, loose: bool = False) -> bool:
    text = lit.text.strip()
    if len(text) < 3 or not any(ch.isalpha() for ch in text):
        return False
    if text.startswith(PATH_START) or "://" in text:
        return False
    if IMPORTISH_RE.search(lit.line_text):
        return False
    if not loose and " " not in text:
        return False
    return True


def ui_strings(doc: Doc, loose: bool = False) -> list:
    out = []
    for lit in doc.strings:
        if lit.offset in doc._class_offsets:
            continue
        if is_ui_copy(lit, loose):
            out.append((lit.offset, lit.text))
    return out


def visible_items(doc: Doc, loose: bool = True) -> list:
    items = [(n.offset, n.text) for n in doc.text_nodes]
    items.extend(ui_strings(doc, loose))
    items.sort()
    return items


def snippet(text: str, idx: int) -> str:
    return text[max(0, idx - 40):idx + 60]


def token_before(text: str, idx: int) -> str:
    head = text[:idx].rstrip()
    if not head:
        return ""
    return re.split(r"[\s(]+", head)[-1].strip(".,;:\"'").lower()


# A keyword counts at the start or the end of a class-name segment: 'navbar' and
# 'sidenav' read as nav, 'canvas' does not. A few words that begin with a
# keyword but mean something else are ruled out by name.
KW_NOT_BEFORE = {"tab": "(?!le|ul)", "tag": "(?!line)", "meta": "(?!l)"}


def kw_regex(words: tuple) -> re.Pattern:
    alts = []
    for word in words:
        esc = re.escape(word)
        alts.append(r"(?<![a-z0-9])" + esc + KW_NOT_BEFORE.get(word, ""))
        alts.append(esc + r"(?![a-z0-9])")
    return re.compile("|".join(alts), re.IGNORECASE)


COMBINATOR_RE = re.compile(r"\s*[>+~]\s*|\s+")
TYPE_RE = re.compile(r"[a-z][a-z0-9-]*")
CLASS_NAME_RE = re.compile(r"\.([a-z0-9_-]+)")
HEADING_TAGS = frozenset({"h1", "h2", "h3", "h4", "h5", "h6"})


def split_selectors(sel: str) -> list:
    """A selector list split at its top-level commas, lowercased."""
    parts = []
    depth = 0
    last = 0
    for idx, ch in enumerate(sel):
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth = max(0, depth - 1)
        elif ch == "," and depth == 0:
            parts.append(sel[last:idx])
            last = idx + 1
    parts.append(sel[last:])
    return [part.strip().lower() for part in parts if part.strip()]


def compounds(selector: str) -> list:
    return [part for part in COMBINATOR_RE.split(selector) if part]


def compound_type(compound: str) -> str:
    m = TYPE_RE.match(compound)
    return m.group(0) if m else ""


def _text_index(doc: Doc) -> tuple:
    index = doc.cache.get("text_index")
    if index is None:
        if doc.script_primary:
            runs = [(start, doc.src[start:stop]) for start, stop in doc.raw_runs]
        else:
            runs = [(node.offset, node.text) for node in doc.text_nodes]
        offsets = []
        texts = []
        sums = [0]
        for offset, text in runs:
            flat = " ".join(text.split())
            offsets.append(offset)
            texts.append(flat)
            sums.append(sums[-1] + len(flat))
        index = (offsets, texts, sums)
        doc.cache["text_index"] = index
    return index


def _text_span(doc: Doc, tag: Tag) -> tuple:
    stop = tag.close if tag.close >= 0 else tag.end
    if tag.self_closing or stop <= tag.end:
        return 0, 0
    offsets = _text_index(doc)[0]
    return bisect_left(offsets, tag.end), bisect_left(offsets, stop)


def element_text_len(doc: Doc, tag: Tag) -> int:
    """Characters of visible text inside an element, whitespace collapsed."""
    lo, hi = _text_span(doc, tag)
    sums = _text_index(doc)[2]
    return sums[hi] - sums[lo]


def element_all_caps(doc: Doc, tag: Tag) -> bool:
    """True when the element's text has letters and none of them is lowercase."""
    lo, hi = _text_span(doc, tag)
    texts = _text_index(doc)[1]
    letters = [ch for text in texts[lo:hi] for ch in text if ch.isalpha()]
    return len(letters) >= 2 and not any(ch.islower() for ch in letters)


def _tag_offsets(doc: Doc) -> list:
    offsets = doc.cache.get("tag_offsets")
    if offsets is None:
        offsets = [tag.offset for tag in doc.tags]
        doc.cache["tag_offsets"] = offsets
    return offsets


DASH_RE = re.compile(
    "(?P<em>" + EM_DASH + r"|&mdash;|&#0*8212;|&#[xX]0*2014;)"
    "|(?P<en>" + EN_DASH + r"|&ndash;|&#0*8211;|&#[xX]0*2013;)"
)
DASH_ATTRS = ("alt", "title", "aria-label", "placeholder")


def _dash_runs(doc: Doc) -> list:
    """(offset, text to search, text to quote, is code) for every run a reader sees."""
    runs = []
    if doc.script_primary:
        # Strings stay blank in these runs: a string reaches the rule through
        # ui_strings, which keeps the whitespace test for UI copy.
        for start, stop in doc.raw_runs:
            runs.append((start, doc.bare_src[start:stop], doc.src[start:stop], True))
    else:
        for node in doc.text_nodes:
            runs.append((node.offset, node.text, node.text, False))
    for offset, text in ui_strings(doc):
        runs.append((offset, text, text, False))
    for tag in doc.tags:
        if tag.closing:
            continue
        for key in DASH_ATTRS:
            entry = tag.attrs.get(key)
            if entry and not entry["braced"] and entry["value"].strip():
                runs.append((entry["off"], entry["value"], entry["value"], False))
    return runs


def _in_regex_literal(doc: Doc, at: int) -> bool:
    src = doc.bare_src
    lo = src.rfind("/", max(0, at - 200), at)
    hi = src.find("/", at + 1, at + 200)
    if lo < 0 or hi < 0:
        return False
    body = src[lo + 1:hi]
    return not any(ch.isspace() or ch in "<>" for ch in body)


def _range_dash(text: str, start: int, stop: int) -> bool:
    left = text[:start].rstrip()
    right = text[stop:].lstrip()
    return bool(left and right) and left[-1].isdigit() and right[0].isdigit()


def check_em_dash(doc: Doc) -> list:
    hits: dict = {}
    for base, search, real, code in _dash_runs(doc):
        for m in DASH_RE.finditer(search):
            at = base + m.start()
            if at in hits or doc.in_fence(at):
                continue
            line = doc.line_text(at)
            if IMPORTISH_RE.search(line) or "content:" in line.replace(" ", ""):
                continue
            around = real[:m.start()].split()[-1:] + real[m.end():].split()[:1]
            if any(URLISH_RE.search(part) for part in around):
                continue
            if code and _in_regex_literal(doc, at):
                continue
            extra = fix = ""
            if m.group("en") and _range_dash(real, m.start(), m.end()):
                extra = "En dash in a number range."
                fix = "Use a plain hyphen for a range."
            hits[at] = mk(doc, "em-dash", at, snippet(real, m.start()), extra, fix=fix)
    return [hits[at] for at in sorted(hits)]


BW_HEX_RE = re.compile(r"#(?:000000|ffffff|000|fff)(?![0-9a-fA-F])", re.IGNORECASE)
BW_RGB_RE = re.compile(
    r"rgb\(\s*0\s*,\s*0\s*,\s*0\s*\)|rgb\(\s*255\s*,\s*255\s*,\s*255\s*\)",
    re.IGNORECASE,
)
BW_PROPS = ("color", "background", "background-color")
BW_TW = frozenset({"bg-black", "bg-white", "text-black", "text-white"})


def check_pure_black_white(doc: Doc) -> list:
    hits = []
    for rule in doc.css_rules:
        for decl in rule.decls:
            if decl.prop not in BW_PROPS:
                continue
            for pattern in (BW_HEX_RE, BW_RGB_RE):
                m = pattern.search(decl.value)
                if m:
                    hits.append((decl.offset, decl.prop + ": " + decl.value))
                    break
    for cl in doc.class_lists:
        for token in cl.tokens:
            if tw_base(token) in BW_TW:
                hits.append((token_offset(cl, token), token))
    if not hits:
        return []
    severity = "warning" if len(hits) >= 2 else "advisory"
    extra = "%d occurrence(s) in this file." % len(hits)
    hits.sort()
    return [
        mk(doc, "pure-black-white", off, ev, extra, severity)
        for off, ev in hits
    ]


SCROLL_ADD_RE = re.compile(r"(?<![\w$])addEventListener\s*\(\s*(['\"`])scroll\1")
SCROLL_PROP_RE = re.compile(r"(?<![\w$.])(?:window|document)\s*\.\s*onscroll\s*=(?!=)")
GLOBAL_TARGETS = frozenset({"window", "document"})


def _listener_target(code: str, start: int):
    """'' for a bare call, the name before the dot, or None for an expression."""
    j = start - 1
    while j >= 0 and code[j].isspace():
        j -= 1
    if j < 0 or code[j] != ".":
        return ""
    j -= 1
    if j >= 0 and code[j] == "?":
        j -= 1
    while j >= 0 and code[j].isspace():
        j -= 1
    k = j
    while k >= 0 and (code[k].isalnum() or code[k] in "_$"):
        k -= 1
    return code[k + 1:j + 1] or None


def check_scroll_listener(doc: Doc) -> list:
    """A page-level scroll handler, not a scroll container's own listener."""
    code = doc.code_src
    out = []
    for m in SCROLL_ADD_RE.finditer(code):
        target = _listener_target(code, m.start())
        if target == "" or target in GLOBAL_TARGETS:
            out.append(mk(doc, "scroll-listener", m.start(),
                          doc.line_text(m.start()).strip()))
    for m in SCROLL_PROP_RE.finditer(code):
        out.append(mk(doc, "scroll-listener", m.start(), m.group(0)))
    out.sort(key=lambda f: (f.line, f.col))
    return out


VH_TOKENS = frozenset({"h-screen", "min-h-screen", "h-[100vh]", "min-h-[100vh]"})
VH_PROPS = ("height", "min-height")
VH_LOCK_RE = re.compile(r"(?<![\w.])100vh\b", re.IGNORECASE)
DYNAMIC_VH_RE = re.compile(r"(?<![\w.])100[dsl]vh\b", re.IGNORECASE)


def check_h_screen_hero(doc: Doc) -> list:
    out = []
    for cl in doc.class_lists:
        for token in cl.tokens:
            if tw_base(token) in VH_TOKENS:
                out.append(mk(doc, "h-screen-hero", token_offset(cl, token), token))
    for rule in doc.css_rules:
        for idx, decl in enumerate(rule.decls):
            if decl.prop not in VH_PROPS or not VH_LOCK_RE.search(decl.value):
                continue
            # 100vh with a later dynamic unit on the same property is the
            # fallback for browsers without dvh, not a viewport lock.
            later = rule.decls[idx + 1:]
            if any(d.prop == decl.prop and DYNAMIC_VH_RE.search(d.value) for d in later):
                continue
            out.append(mk(
                doc, "h-screen-hero", decl.offset,
                rule.sel + " { " + decl.prop + ": " + decl.value + " }",
            ))
    return out


BANNED_FONTS = frozenset({
    "instrument serif", "instrument sans", "plus jakarta sans", "space grotesk",
    "open sans", "geist mono", "geist sans", "mona sans", "montserrat",
    "helvetica", "fraunces", "recoleta", "poppins", "roboto", "nunito",
    "geist", "inter", "arial", "lato",
})
NEXT_FONT_RE = re.compile(
    r"import\s*\{([^}]*)\}\s*from\s*['\"]next/font/[^'\"]*['\"]"
)


def _banned_family(name: str) -> str:
    """The whole first family must match, so 'Inter Tight' is not 'Inter'."""
    return name if name in BANNED_FONTS else ""


def check_banned_font(doc: Doc) -> list:
    out = []
    seen = set()

    def add(offset: int, family: str, evidence: str) -> None:
        line = doc.line_col(offset)[0]
        if (line, family) in seen:
            return
        seen.add((line, family))
        out.append(mk(doc, "banned-font", offset, evidence,
                      "Family: " + family + "."))

    for rule in doc.css_rules:
        for decl in rule.decls:
            if decl.prop != "font-family" and not decl.prop.startswith("--"):
                continue
            family = _banned_family(first_family(decl.value))
            if family:
                add(decl.offset, family, decl.prop + ": " + decl.value)
    for cl in doc.class_lists:
        for token in cl.tokens:
            base = tw_base(token)
            if not base.startswith("font-["):
                continue
            family = _banned_family(first_family(bracket_value(base)))
            if family:
                add(token_offset(cl, token), family, token)
    for m in NEXT_FONT_RE.finditer(doc.code_src):
        for name in m.group(1).split(","):
            family = _banned_family(" ".join(name.replace("_", " ").split()).lower())
            if family:
                add(m.start(1), family, m.group(0))
    return out


NAMED_TRACKING = {
    "tracking-tighter": -0.05,
    "tracking-tight": -0.025,
    "tracking-normal": 0.0,
    "tracking-wide": 0.025,
    "tracking-wider": 0.05,
    "tracking-widest": 0.1,
}


def tw_tracking_em(base: str):
    """Letter spacing of a Tailwind tracking utility in em, or None."""
    if base in NAMED_TRACKING:
        return NAMED_TRACKING[base]
    if base.startswith("tracking-["):
        parsed = parse_len(bracket_value(base))
        if parsed and parsed[1] in ("em", "rem"):
            return parsed[0]
    return None


def is_all_caps(text: str) -> bool:
    body = text.strip()
    words = body.split()
    if not 1 <= len(words) <= 4:
        return False
    letters = [ch for ch in body if ch.isalpha()]
    if len(letters) < 2:
        return False
    return not any(ch.islower() for ch in letters)


def count_sections(doc: Doc) -> int:
    total = 0
    for tag in doc.tags:
        if tag.name == "section" and not tag.closing:
            total += 1
    for cl in doc.class_lists:
        if cl.tag == "section":
            continue
        if any("section" in token.lower() for token in cl.tokens):
            total += 1
    return total


EYEBROW_REACH = 3


def _heading_follows(doc: Doc, tag: Tag) -> bool:
    """An eyebrow sits above a heading: an h1-h6 is one of the next few elements."""
    start = tag.close if tag.closed else tag.end
    idx = bisect_left(_tag_offsets(doc), start)
    seen = 0
    for pos in range(idx, len(doc.tags)):
        other = doc.tags[pos]
        if other.closing:
            continue
        if other.name in HEADING_TAGS:
            return True
        seen += 1
        if seen >= EYEBROW_REACH:
            break
    return False


def _eyebrow_css_classes(rule: CssRule) -> set:
    names = set()
    for selector in split_selectors(rule.sel_path):
        parts = compounds(selector)
        if parts:
            names.update(CLASS_NAME_RE.findall(parts[-1]))
    return names


def check_eyebrow_density(doc: Doc) -> list:
    found: dict = {}

    def add(tag, offset: int, evidence: str) -> None:
        if tag is not None and id(tag) not in found:
            found[id(tag)] = (offset, evidence, tag)

    for cl in doc.class_lists:
        bases = {tw_base(token) for token in cl.tokens}
        tracked = any((tw_tracking_em(base) or 0.0) > 0 for base in bases)
        if "uppercase" in bases and tracked:
            add(cl.owner, cl.offset, cl.text)
    css_classes: set = set()
    for rule in doc.css_rules:
        props = {decl.prop: decl.value for decl in rule.decls}
        if not props.get("text-transform", "").lower().startswith("uppercase"):
            continue
        parsed = parse_len(props.get("letter-spacing", ""))
        if not (parsed and parsed[1] in ("em", "rem") and parsed[0] > 0.1):
            continue
        if rule.owner is not None:
            add(rule.owner, rule.offset, rule.sel)
        else:
            css_classes |= _eyebrow_css_classes(rule)
    if css_classes:
        for tag in doc.tags:
            if tag.closing:
                continue
            if css_classes & {name.lower() for name in tag.classes}:
                add(tag, tag.offset, " ".join(tag.classes))
    for node in doc.text_nodes:
        if node.tag in ("p", "span", "div") and is_all_caps(node.text):
            add(node.owner, node.offset, node.text)
    eyebrows = sorted(
        (offset, evidence)
        for offset, evidence, tag in found.values()
        if _heading_follows(doc, tag)
    )
    if not eyebrows:
        return []
    sections = count_sections(doc)
    ceiling = math.ceil(sections / 3) if sections else 1
    if len(eyebrows) <= ceiling:
        return []
    extra = "%d eyebrows, %d sections, ceiling %d." % (
        len(eyebrows), sections, ceiling)
    return [mk(doc, "eyebrow-density", eyebrows[0][0], eyebrows[0][1], extra)]


# Slash and middle dot may follow any two or three digit number. A spaced hyphen
# or a period needs a leading zero, so "404 - Page not found" is not a label, and
# an unspaced hyphen ("24-hour") never counts.
SECTION_NUM_RE = re.compile(
    r"(?:\d{2,3}\s*[/" + MIDDLE_DOT + r"]\s*|0\d{1,2}\s+-\s+|0\d{1,2}\.\s*)[A-Za-z]"
)
STAGE_RE = re.compile(
    r"(Stage|Step|Phase|Pass)\s+(0?\d|One|Two|Three|Four)\b", re.IGNORECASE
)
LABEL_MAX_WORDS = 5


def check_section_number_label(doc: Doc) -> list:
    out = []
    for offset, text in visible_items(doc):
        body = text.strip()
        words = [word for word in body.split() if any(ch.isalnum() for ch in word)]
        if not words or len(words) > LABEL_MAX_WORDS:
            continue
        if SECTION_NUM_RE.match(body) or STAGE_RE.match(body):
            lead = len(text) - len(text.lstrip())
            out.append(mk(doc, "section-number-label", offset + lead, body))
    return out


SCROLL_CUE_RE = re.compile(
    r"scroll\s+to\s+(explore|discover|walk)|scroll\s+down", re.IGNORECASE
)
LONE_SCROLL = frozenset({
    "scroll", ARROW_DOWN + " scroll", "scroll " + ARROW_DOWN,
})


def check_scroll_cue(doc: Doc) -> list:
    out = []
    for offset, text in visible_items(doc):
        m = SCROLL_CUE_RE.search(text)
        if m:
            out.append(mk(doc, "scroll-cue", offset + m.start(), m.group(0)))
    for node in doc.text_nodes:
        # A bare "scroll" is a cue only as markup text. In a string it is an
        # event name, which is why string literals stay out of this branch.
        if node.text.strip().lower() in LONE_SCROLL:
            out.append(mk(doc, "scroll-cue", node.offset, node.text))
    out.sort(key=lambda f: (f.line, f.col))
    return out


LEVERAGE_NOUNS = frozenset({
    "the", "a", "an", "your", "our", "its", "his", "her", "their", "high",
    "low", "more", "less", "financial", "operating", "net", "excess", "much",
})
FILLER_TERMS = (
    ("elevate", r"\belevat(e|es|ed|ing)\b"),
    ("seamless", r"\bseamless(ly)?\b"),
    ("unleash", r"\bunleash(es|ed|ing)?\b"),
    ("next-gen", r"\bnext[- ]gen\b"),
    ("next generation", r"\bnext[- ]generation\b"),
    ("revolutionize", r"\brevolutioniz(e|es|ed|ing)\b"),
    ("revolutionise", r"\brevolutionis(e|es|ed|ing)\b"),
    ("supercharge", r"\bsupercharg(e|es|ed|ing)\b"),
    ("empower", r"\bempower(s|ed|ing)?\b"),
    ("leverage", r"\bleverag(e|es|ed|ing)\b"),
    ("game-changing", r"\bgame[- ]changing\b"),
    ("cutting-edge", r"\bcutting[- ]edge\b"),
    ("delve", r"\bdelv(e|es|ed|ing)\b"),
    ("effortlessly", r"\beffortless(ly)?\b"),
    ("robust", r"\brobust\b"),
    ("unlock the power", r"\bunlock the power\b"),
)
FILLER_COMPILED = tuple(
    (term, re.compile(pattern, re.IGNORECASE)) for term, pattern in FILLER_TERMS
)


def check_filler_verb(doc: Doc) -> list:
    out = []
    seen = set()
    # A string with no whitespace is an identifier such as variant="elevated",
    # not copy, so only strings with a space are read here.
    for offset, text in visible_items(doc, loose=False):
        for term, pattern in FILLER_COMPILED:
            if term in seen:
                continue
            m = pattern.search(text)
            if not m:
                continue
            if term == "leverage" and token_before(text, m.start()) in LEVERAGE_NOUNS:
                continue
            seen.add(term)
            out.append(mk(doc, "filler-verb", offset + m.start(),
                          snippet(text, m.start()), "Term: " + term + "."))
    out.sort(key=lambda f: (f.line, f.col))
    return out


PLACEHOLDER_TERMS = (
    ("john doe", r"\bjohn\s+doe\b"),
    ("jane doe", r"\bjane\s+doe\b"),
    ("sarah chan", r"\bsarah\s+chan\b"),
    ("jack su", r"\bjack\s+su\b"),
    ("acme", r"\backme\b"),
    ("nexus", r"\bnexus\b"),
    ("smartflow", r"\bsmartflow\b"),
    ("cloudly", r"\bcloudly\b"),
    ("lorem ipsum", r"\blorem\s+ipsum\b"),
)
PLACEHOLDER_COMPILED = tuple(
    (term, re.compile(pattern, re.IGNORECASE))
    for term, pattern in PLACEHOLDER_TERMS
)


def check_placeholder_identity(doc: Doc) -> list:
    out = []
    seen = set()
    for offset, text in visible_items(doc):
        for term, pattern in PLACEHOLDER_COMPILED:
            for m in pattern.finditer(text):
                if term == "nexus":
                    tail = text[m.end():m.end() + 1]
                    head = text[max(0, m.start() - 1):m.start()]
                    if tail in "-_./" or head in "-_./":
                        continue
                line = doc.line_col(offset + m.start())[0]
                if (line, term) in seen:
                    continue
                seen.add((line, term))
                out.append(mk(doc, "placeholder-identity", offset + m.start(),
                              snippet(text, m.start()), "Name: " + term + "."))
    out.sort(key=lambda f: (f.line, f.col))
    return out


FAKE_LITERAL_RE = re.compile(r"\b99\.9{1,2}%|\b10x\b|\b100x\b|\b1234567\b", re.IGNORECASE)
TEN_PCT_RE = re.compile(r"\b(\d{1,2}0|100)%")
# Whole class tokens, or tokens split at '-' or '_': stat-card and kpi_value
# count, status-bar does not.
STAT_CLASS_RE = re.compile(
    r"(?:^|[\s_-])(?:stats?|statistics?|metrics?|kpis?)(?=$|[\s_-])"
)


def check_fake_round_number(doc: Doc) -> list:
    out = []
    for offset, text in visible_items(doc):
        for m in FAKE_LITERAL_RE.finditer(text):
            out.append(mk(doc, "fake-round-number", offset + m.start(),
                          snippet(text, m.start())))
    for node in doc.text_nodes:
        if not STAT_CLASS_RE.search(node.anc):
            continue
        for m in TEN_PCT_RE.finditer(node.text):
            out.append(mk(doc, "fake-round-number", node.offset + m.start(),
                          snippet(node.text, m.start()),
                          "Round percentage inside a stat block."))
    out.sort(key=lambda f: (f.line, f.col))
    return out


TIGHT_TW = frozenset({"leading-none", "leading-[1]", "leading-[1.0]"})
TIGHT_EXEMPT_RE = kw_regex((
    "display", "hero", "headline", "title", "heading", "btn", "button", "label",
    "badge", "tag", "chip", "pill", "nav", "logo", "icon", "kbd",
))
SHORT_TEXT_MAX = 50


def _tight_selector_exempt(selector: str) -> bool:
    parts = compounds(selector)
    types = [compound_type(part) for part in parts]
    if types and types[-1] in HEADING_TAGS:
        return True
    # "h2 + p" styles the paragraph after a heading, so only descendant and
    # child context from a heading counts.
    siblings = "+" in selector or "~" in selector
    if not siblings and HEADING_TAGS & set(types):
        return True
    return bool(TIGHT_EXEMPT_RE.search(selector))


def _tight_element_exempt(doc: Doc, tag: Tag) -> bool:
    if tag.name in HEADING_TAGS or TIGHT_EXEMPT_RE.search(tag.own):
        return True
    return element_text_len(doc, tag) <= SHORT_TEXT_MAX


def check_tight_leading(doc: Doc) -> list:
    out = []
    for rule in doc.css_rules:
        if rule.owner is not None:
            if _tight_element_exempt(doc, rule.owner):
                continue
        else:
            selectors = split_selectors(rule.sel_path)
            if not selectors or all(_tight_selector_exempt(s) for s in selectors):
                continue
        for decl in rule.decls:
            if decl.prop != "line-height":
                continue
            parsed = parse_len(decl.value)
            if parsed and parsed[1] == "" and parsed[0] < 1.3:
                out.append(mk(doc, "tight-leading", decl.offset,
                              rule.sel + " { line-height: " + decl.value + " }"))
    for cl in doc.class_lists:
        tight = [token for token in cl.tokens if tw_base(token) in TIGHT_TW]
        if not tight or TIGHT_EXEMPT_RE.search(cl.text):
            continue
        if cl.owner is not None and _tight_element_exempt(doc, cl.owner):
            continue
        for token in tight:
            out.append(mk(doc, "tight-leading", token_offset(cl, token), token))
    return out


UI_TAGS = frozenset({"a", "button", "nav", "label", "th", "td", "time", "input", "select"})
QUIET_TAGS = frozenset({"footer", "figcaption", "small"})
EXEMPT_TAGS = frozenset({"sup", "sub", "code", "pre", "kbd"})
UI_KW_RE = kw_regex(("btn", "button", "nav", "link", "label", "tab", "menu"))
EXEMPT_KW_RE = kw_regex(("legal", "smallprint", "small-print", "kbd", "code"))
EXEMPT_LINE_RE = kw_regex(("legal", "smallprint", "small-print"))
QUIET_KW_RE = kw_regex(("caption", "badge", "tag", "chip", "meta", "shortcut", "footer"))
QUIET_LINE_RE = kw_regex(("caption", "badge", "tag", "chip", "meta", "kbd", "shortcut"))
BODY_FLOOR_PX = 12.0
UI_FLOOR_PX = 11.0


def size_context(types: set, words: str, line: str, upper: bool,
                 operable: bool = False) -> str:
    """'ui' for functional text, 'body' for running text, else 'exempt'.

    Functional text answers to undersized-ui-text at 11px. Running text answers
    to tiny-text at 12px, unless it is a caption, badge, footer or uppercase
    label, which neither rule judges.
    """
    if types & EXEMPT_TAGS or "sr-only" in words or EXEMPT_KW_RE.search(words):
        return "exempt"
    if EXEMPT_LINE_RE.search(line):
        return "exempt"
    if operable or types & UI_TAGS or UI_KW_RE.search(words):
        return "ui"
    if upper or types & QUIET_TAGS or QUIET_KW_RE.search(words):
        return "exempt"
    if QUIET_LINE_RE.search(line):
        return "exempt"
    return "body"


def font_px(value: str):
    """A font size in px from px or rem. em and % depend on the parent, so None."""
    raw = value.strip().lower()
    if raw.startswith("length:"):
        raw = raw[len("length:"):]
    parsed = parse_len(raw)
    if not parsed:
        return None
    number, unit = parsed
    if unit == "px":
        return number
    if unit == "rem":
        return number * ROOT_PX
    return None


def _element_size_context(doc: Doc, tag: Tag, line: str, upper: bool) -> str:
    # A formatted JSX start tag spans several lines, so the whole tag counts as
    # the line: key={tag} two lines above the className still marks a chip.
    line = line + " " + doc.src[tag.offset:min(tag.end, tag.offset + LINE_WINDOW)]
    types = {tag.name} | set(tag.parents)
    upper = (
        upper
        or "uppercase" in {tw_base(name) for name in tag.classes}
        or element_all_caps(doc, tag)
    )
    return size_context(types, tag.anc, line, upper, tag.ui_chain)


def _selector_size_context(sel_path: str, line: str, upper: bool,
                           operable: bool) -> str:
    kinds = set()
    for selector in split_selectors(sel_path) or [""]:
        types = {compound_type(part) for part in compounds(selector)}
        kinds.add(size_context(types, selector, line, upper, operable))
    for kind in ("body", "ui"):
        if kind in kinds:
            return kind
    return "exempt"


def _size_hits(doc: Doc) -> list:
    """(offset, evidence, px, context) for every px or rem font size in the file."""
    hits = doc.cache.get("size_hits")
    if hits is not None:
        return hits
    hits = []
    for rule in doc.css_rules:
        values = {decl.prop: decl.value.lower() for decl in rule.decls}
        upper = "uppercase" in values.get("text-transform", "")
        # A pointer cursor marks the rule's element as something to click.
        operable = values.get("cursor", "").strip() == "pointer"
        for decl in rule.decls:
            if decl.prop != "font-size":
                continue
            px = font_px(decl.value)
            if px is None:
                continue
            line = doc.line_text(decl.offset)
            if rule.owner is not None:
                kind = _element_size_context(doc, rule.owner, line, upper)
            else:
                kind = _selector_size_context(rule.sel_path, line, upper, operable)
            evidence = rule.sel + " { font-size: " + decl.value + " }"
            hits.append((decl.offset, evidence, px, kind))
    for cl in doc.class_lists:
        bases = [tw_base(token) for token in cl.tokens]
        upper = "uppercase" in bases
        for token, base in zip(cl.tokens, bases):
            if not base.startswith("text-["):
                continue
            px = font_px(bracket_value(base))
            if px is None:
                continue
            line = doc.line_text(cl.offset)
            if cl.owner is not None:
                kind = _element_size_context(doc, cl.owner, line, upper)
            else:
                kind = size_context(set(), cl.text.lower(), line, upper)
            hits.append((token_offset(cl, token), token, px, kind))
    doc.cache["size_hits"] = hits
    return hits


def check_tiny_text(doc: Doc) -> list:
    return [
        mk(doc, "tiny-text", offset, evidence)
        for offset, evidence, px, kind in _size_hits(doc)
        if kind == "body" and px < BODY_FLOOR_PX
    ]


def check_undersized_ui_text(doc: Doc) -> list:
    return [
        mk(doc, "undersized-ui-text", offset, evidence)
        for offset, evidence, px, kind in _size_hits(doc)
        if kind == "ui" and px < UI_FLOOR_PX
    ]


WIDE_EXEMPT_RE = kw_regex((
    "shortcut", "kbd", "label", "badge", "caption", "overline", "eyebrow", "tag",
    "chip", "nav", "btn", "button",
))
BODY_TYPES = frozenset({"p", "body", "li", "article", "main", "blockquote"})
BODY_SEGMENTS = frozenset({"prose", "body", "content", "text"})
WIDE_EM = 0.05
WIDE_TEXT_MIN = 30
SMALL_PX = 12.0


def _bodyish_selector(selector: str) -> bool:
    parts = compounds(selector)
    if not parts:
        return False
    subject = parts[-1]
    if compound_type(subject) in BODY_TYPES:
        return True
    for name in CLASS_NAME_RE.findall(subject):
        if BODY_SEGMENTS & set(re.split(r"[-_]+", name)):
            return True
    return False


def _wide_css_target(rule: CssRule) -> bool:
    for selector in split_selectors(rule.sel_path):
        if _bodyish_selector(selector) and not WIDE_EXEMPT_RE.search(selector):
            return True
    return False


def _small_font_rule(rule: CssRule) -> bool:
    for decl in rule.decls:
        if decl.prop == "font-size":
            px = font_px(decl.value)
            if px is not None and px <= SMALL_PX:
                return True
    return False


def _small_classes(bases: list) -> bool:
    for base in bases:
        if base == "text-xs":
            return True
        if base.startswith("text-["):
            px = font_px(bracket_value(base))
            if px is not None and px <= SMALL_PX:
                return True
    return False


def _wide_element_exempt(doc: Doc, tag: Tag, bases: list) -> bool:
    bases = list(bases) + [tw_base(name) for name in tag.classes]
    if _small_classes(bases) or tag.name == "kbd" or "kbd" in tag.parents:
        return True
    if WIDE_EXEMPT_RE.search(tag.own):
        return True
    return element_text_len(doc, tag) <= WIDE_TEXT_MIN


def check_wide_tracking_body(doc: Doc) -> list:
    out = []
    for rule in doc.css_rules:
        props = {decl.prop: decl.value.lower() for decl in rule.decls}
        if "uppercase" in props.get("text-transform", ""):
            continue
        if "uppercase" in rule.sel_path.lower() or _small_font_rule(rule):
            continue
        if rule.owner is not None:
            bases = [tw_base(name) for name in rule.owner.classes]
            if "uppercase" in bases or _wide_element_exempt(doc, rule.owner, bases):
                continue
        elif not _wide_css_target(rule):
            continue
        for decl in rule.decls:
            if decl.prop != "letter-spacing":
                continue
            parsed = parse_len(decl.value)
            if parsed and parsed[1] in ("em", "rem") and parsed[0] > WIDE_EM:
                out.append(mk(doc, "wide-tracking-body", decl.offset,
                              rule.sel + " { letter-spacing: " + decl.value + " }"))
    for cl in doc.class_lists:
        bases = [tw_base(token) for token in cl.tokens]
        # Tracking on text of unknown length (a string outside any element)
        # cannot be judged, so it needs an owning element.
        if "uppercase" in bases or cl.owner is None:
            continue
        wide = [
            token for token, base in zip(cl.tokens, bases)
            if (tw_tracking_em(base) or 0.0) > WIDE_EM
        ]
        if not wide or _wide_element_exempt(doc, cl.owner, bases):
            continue
        for token in wide:
            out.append(mk(doc, "wide-tracking-body", token_offset(cl, token), token))
    return out


def check_extreme_tracking(doc: Doc) -> list:
    out = []
    for rule in doc.css_rules:
        for decl in rule.decls:
            if decl.prop != "letter-spacing":
                continue
            parsed = parse_len(decl.value)
            if parsed and parsed[1] in ("em", "rem") and parsed[0] < -0.04:
                out.append(mk(doc, "extreme-tracking", decl.offset,
                              rule.sel + " { letter-spacing: " + decl.value + " }"))
    for cl in doc.class_lists:
        for token in cl.tokens:
            em = tw_tracking_em(tw_base(token))
            if em is not None and em < -0.04:
                out.append(mk(doc, "extreme-tracking",
                              token_offset(cl, token), token))
    return out


CLIP_PROPS = ("background-clip", "-webkit-background-clip")
# Tailwind v3 names gradients bg-gradient-to-*; v4 adds bg-linear-*, bg-radial
# and bg-conic.
GRADIENT_TW = ("bg-gradient-to-", "bg-linear-", "bg-radial", "bg-conic")


def check_gradient_text(doc: Doc) -> list:
    out = []
    for rule in doc.css_rules:
        gradient = any("gradient" in decl.value.lower() for decl in rule.decls)
        if not gradient:
            continue
        for decl in rule.decls:
            if decl.prop in CLIP_PROPS and "text" in decl.value.lower():
                out.append(mk(doc, "gradient-text", decl.offset,
                              rule.sel + " { " + decl.prop + ": " + decl.value + " }"))
                break
    for cl in doc.class_lists:
        bases = [tw_base(token) for token in cl.tokens]
        has_gradient = any(base.startswith(GRADIENT_TW) for base in bases)
        if has_gradient and "bg-clip-text" in bases and "text-transparent" in bases:
            out.append(mk(doc, "gradient-text", cl.offset, cl.text))
    return out


MOTION_IMPORT_RE = re.compile(
    r"['\"](motion/react|framer-motion|gsap)(/[^'\"]*)?['\"]"
)
# A media query or matchMedia string (GSAP's gsap.matchMedia takes the same
# string), the Motion hook, or MotionConfig set to follow or force the setting.
REDUCED_RE = re.compile(
    r"prefers-reduced-motion|useReducedMotion"
    r"|reducedMotion\s*[=:]\s*\{?\s*['\"`](?:user|always)['\"`]"
)
KEYFRAMES_RE = re.compile(r"@keyframes\b", re.IGNORECASE)


def check_no_reduced_motion(doc: Doc) -> list:
    if REDUCED_RE.search(doc.code_src):
        return []
    signals = []
    m = KEYFRAMES_RE.search(doc.code_src)
    if m:
        signals.append((m.start(), m.group(0)))
    m = MOTION_IMPORT_RE.search(doc.code_src)
    if m:
        signals.append((m.start(), m.group(0)))
    for rule in doc.css_rules:
        for decl in rule.decls:
            if decl.prop == "animation" or decl.prop.startswith("animation-"):
                signals.append((decl.offset, decl.prop + ": " + decl.value))
            elif decl.prop.startswith("transition") and "transform" in decl.value:
                signals.append((decl.offset, decl.prop + ": " + decl.value))
    if not signals:
        return []
    signals.sort()
    return [mk(doc, "no-reduced-motion", signals[0][0], signals[0][1])]


BANNED_PALETTE = (
    "f5f1ea", "f7f5f1", "fbf8f1", "efeae0", "ece6db", "faf7f1", "e8dfcb",
    "b08947", "b6553a", "9a2436", "9c6e2a", "bc7c3a", "7d5621", "d97757",
    "1a1714", "1a1814", "1b1814",
)
BANNED_PALETTE_RE = re.compile(
    r"#(" + "|".join(BANNED_PALETTE) + r")(?![0-9a-fA-F])", re.IGNORECASE
)


def check_banned_palette(doc: Doc) -> list:
    out = []
    seen = set()
    for m in BANNED_PALETTE_RE.finditer(doc.code_src):
        key = (doc.line_col(m.start())[0], m.group(0).lower())
        if key in seen:
            continue
        seen.add(key)
        out.append(mk(doc, "banned-palette", m.start(),
                      doc.line_text(m.start()).strip(),
                      "Hex: " + m.group(0) + "."))
    return out


def check_middle_dot_run(doc: Doc) -> list:
    out = []
    for offset, text in visible_items(doc):
        if text.count(MIDDLE_DOT) < 3:
            continue
        out.append(mk(doc, "middle-dot-run", offset + text.find(MIDDLE_DOT), text))
    return out


LUCIDE_RE = re.compile(r"['\"]lucide(-react)?(/[^'\"]*)?['\"]")


def check_lucide_icons(doc: Doc) -> list:
    out = []
    seen = set()
    for m in LUCIDE_RE.finditer(doc.code_src):
        line_text = doc.line_text(m.start())
        if not IMPORTISH_RE.search(line_text):
            continue
        line = doc.line_col(m.start())[0]
        if line in seen:
            continue
        seen.add(line)
        out.append(mk(doc, "lucide-icons", m.start(), line_text.strip()))
    return out


ICON_LIB_RE = re.compile(
    r"['\"]("
    r"lucide[^'\"]*|react-icons[^'\"]*|@?heroicons[^'\"]*|@phosphor-icons[^'\"]*|"
    r"phosphor-react|feather-icons|react-feather|@tabler/icons[^'\"]*|"
    r"@iconify[^'\"]*|simple-icons|boxicons|remixicon"
    r")['\"]",
    re.IGNORECASE,
)
ICON_VIEWBOXES = frozenset({"0 0 24 24", "0 0 16 16"})


def check_hand_rolled_icon(doc: Doc) -> list:
    if ICON_LIB_RE.search(doc.code_src):
        return []
    paths = [t for t in doc.tags if t.name == "path" and not t.closing]
    out = []
    for tag in doc.tags:
        if tag.name != "svg" or tag.closing:
            continue
        box = " ".join(tag.attrs.get("viewbox", {}).get("value", "").split())
        if box not in ICON_VIEWBOXES:
            continue
        m = close_tag_re("svg").search(doc.src, tag.end)
        stop = m.start() if m else len(doc.src)
        for path in paths:
            if not tag.end <= path.offset < stop:
                continue
            if len(path.attrs.get("d", {}).get("value", "")) > 40:
                out.append(mk(doc, "hand-rolled-icon", tag.offset, tag.anc or "svg",
                              "viewBox " + box + "."))
                break
    return out


def check_three_column_cards(doc: Doc) -> list:
    out = []
    card_lines = [
        doc.line_col(cl.offset)[0]
        for cl in doc.class_lists
        if any("card" in token.lower() for token in cl.tokens)
    ]
    for cl in doc.class_lists:
        if not any(tw_base(token) == "grid-cols-3" for token in cl.tokens):
            continue
        line = doc.line_col(cl.offset)[0]
        own = any("card" in token.lower() for token in cl.tokens)
        near = any(line <= other <= line + 15 for other in card_lines)
        if own or near:
            out.append(mk(doc, "three-column-cards", cl.offset, cl.text))
    return out


def check_nested_card(doc: Doc) -> list:
    if doc.ext not in HTML_EXTS or not doc.nesting_ok:
        return []
    stack: list = []
    outer_open = 0
    out = []
    for tag in doc.tags:
        if tag.name in RAW_TEXT_TAGS:
            continue
        if tag.closing:
            for idx in range(len(stack) - 1, -1, -1):
                if stack[idx][0] == tag.name:
                    outer_open -= sum(1 for entry in stack[idx:] if entry[1])
                    del stack[idx:]
                    break
            continue
        if tag.self_closing or tag.name in VOID_TAGS:
            continue
        cls = " ".join(tag.classes).lower()
        inner = "card" in cls and "shadow" in cls
        outer = inner and "rounded-" in cls
        if inner and outer_open:
            out.append(mk(doc, "nested-card", tag.offset, cls))
        stack.append((tag.name, outer))
        outer_open += outer
    return out


VERSION_LABEL_RE = re.compile(
    r"^\s*(v\d+(\.\d+)*|BETA|ALPHA|EARLY ACCESS|INVITE[- ]ONLY|PREVIEW)\s*$"
)
HERO_ATTR_RE = re.compile(
    r"(class|classname|id)\s*=\s*[^>]{0,200}hero", re.IGNORECASE
)


def check_version_label_hero(doc: Doc) -> list:
    out = []
    for node in doc.text_nodes:
        if not VERSION_LABEL_RE.match(node.text):
            continue
        line = doc.line_col(node.offset)[0]
        hero = "hero" in node.anc
        if not hero:
            for probe in range(max(1, line - 5), line + 1):
                offset = doc.line_starts[probe - 1]
                if HERO_ATTR_RE.search(doc.line_text(offset)):
                    hero = True
                    break
        if hero:
            out.append(mk(doc, "version-label-hero", node.offset, node.text))
    return out


SYSTEM_DISPLAY_FONTS = ("impact", "arial black", "comic sans ms", "papyrus")


def check_system_font_display(doc: Doc) -> list:
    out = []
    for rule in doc.css_rules:
        for decl in rule.decls:
            if decl.prop != "font-family":
                continue
            if first_family(decl.value) in SYSTEM_DISPLAY_FONTS:
                out.append(mk(doc, "system-font-display", decl.offset,
                              decl.prop + ": " + decl.value))
    return out


CHECKS = {
    "em-dash": check_em_dash,
    "pure-black-white": check_pure_black_white,
    "scroll-listener": check_scroll_listener,
    "h-screen-hero": check_h_screen_hero,
    "banned-font": check_banned_font,
    "eyebrow-density": check_eyebrow_density,
    "section-number-label": check_section_number_label,
    "scroll-cue": check_scroll_cue,
    "filler-verb": check_filler_verb,
    "placeholder-identity": check_placeholder_identity,
    "fake-round-number": check_fake_round_number,
    "tight-leading": check_tight_leading,
    "tiny-text": check_tiny_text,
    "undersized-ui-text": check_undersized_ui_text,
    "wide-tracking-body": check_wide_tracking_body,
    "extreme-tracking": check_extreme_tracking,
    "gradient-text": check_gradient_text,
    "no-reduced-motion": check_no_reduced_motion,
    "banned-palette": check_banned_palette,
    "middle-dot-run": check_middle_dot_run,
    "lucide-icons": check_lucide_icons,
    "hand-rolled-icon": check_hand_rolled_icon,
    "three-column-cards": check_three_column_cards,
    "nested-card": check_nested_card,
    "version-label-hero": check_version_label_hero,
    "system-font-display": check_system_font_display,
}


DISABLE_RE = re.compile(r"slop-lint-disable(-file)?\s+([A-Za-z0-9_-]+)")
COMMENT_MARKERS = ("<!--", "//", "/*", "{/*", "#", "*")


def collect_suppressions(src: str) -> tuple:
    file_level = set()
    line_level: dict = {}
    for number, line in enumerate(src.split("\n"), start=1):
        for m in DISABLE_RE.finditer(line):
            prefix = line[:m.start()]
            if not any(mark in prefix for mark in COMMENT_MARKERS):
                continue
            rule_id = m.group(2)
            if m.group(1):
                file_level.add(rule_id)
                continue
            line_level.setdefault(number, set()).add(rule_id)
            line_level.setdefault(number + 1, set()).add(rule_id)
    return file_level, line_level


def apply_suppressions(doc: Doc, findings: list) -> list:
    if "slop-lint-disable" not in doc.src:
        return findings
    file_level, line_level = collect_suppressions(doc.src)
    kept = []
    for finding in findings:
        if finding.rule in file_level:
            continue
        if finding.rule in line_level.get(finding.line, ()):
            continue
        kept.append(finding)
    return kept


SKIP_HINTS = {
    "minified": "named *.min.* or median line over %d chars; lint the unminified "
                "source instead" % MINIFIED_MEDIAN,
    "too large": "over %d bytes" % MAX_FILE_BYTES,
    "unsupported extension": "reads only " + " ".join(ALL_EXTS),
}


def looks_minified(name: str, src: str) -> bool:
    """A *.min.* name, or a median line length over MINIFIED_MEDIAN.

    One long line never decides it: a hand-written page with an inline data URI
    is still a page and still gets linted.
    """
    if fnmatch.fnmatch(name, "*.min.*"):
        return True
    return statistics.median(len(line) for line in src.split("\n")) > MINIFIED_MEDIAN


def excluded(path: str, patterns: list) -> bool:
    name = os.path.basename(path)
    for pattern in patterns:
        if fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(name, pattern):
            return True
    return False


def iter_targets(paths: list, patterns: list) -> tuple:
    """(path, named on the command line) pairs, and the targets that do not exist."""
    files = []
    errors = []
    for target in paths:
        if os.path.isfile(target):
            if not excluded(target, patterns):
                files.append((target, True))
            continue
        if os.path.isdir(target):
            for root, dirs, names in os.walk(target):
                dirs[:] = sorted(
                    d for d in dirs
                    if d not in SKIP_DIRS and not excluded(os.path.join(root, d), patterns)
                )
                for name in sorted(names):
                    if os.path.splitext(name)[1].lower() not in ALL_EXTS:
                        continue
                    full = os.path.join(root, name)
                    if not excluded(full, patterns):
                        files.append((full, False))
            continue
        errors.append(target)
    return files, errors


def load_source(path: str) -> tuple:
    """(source, "") for a file to lint, or (None, reason) for a skipped one."""
    ext = os.path.splitext(path)[1].lower()
    if ext not in ALL_EXTS:
        return None, "unsupported extension"
    with open(path, "rb") as handle:
        raw = handle.read(MAX_FILE_BYTES + 1)
    if len(raw) > MAX_FILE_BYTES:
        return None, "too large"
    src = raw.decode("utf-8", errors="replace")
    if looks_minified(os.path.basename(path), src):
        return None, "minified"
    return src, ""


def lint_source(path: str, src: str, rule_ids: list) -> list:
    ext = os.path.splitext(path)[1].lower()
    doc = build_doc(path, path, src, ext)
    findings = []
    for rule_id in rule_ids:
        if ext not in RULES_BY_ID[rule_id].exts:
            continue
        findings.extend(CHECKS[rule_id](doc))
    return apply_suppressions(doc, findings)


def lint_file(path: str, rule_ids: list):
    """Findings for one file, or None when the file is out of scope or skipped."""
    src, _reason = load_source(path)
    if src is None:
        return None
    return lint_source(path, src, rule_ids)


def summarise(findings: list, scanned: int, skipped: list, shown: int) -> dict:
    summary = {severity: 0 for severity in SEVERITIES}
    for finding in findings:
        summary[finding.severity] = summary.get(finding.severity, 0) + 1
    summary["findings"] = len(findings)
    summary["findings_shown"] = shown
    summary["files_scanned"] = scanned
    summary["files_with_findings"] = len({f.file for f in findings})
    summary["files_skipped"] = len(skipped)
    summary["skipped_files"] = skipped
    summary["truncated"] = shown < len(findings)
    return summary


def print_human(shown: list, summary: dict, stream) -> None:
    current = ""
    for finding in shown:
        if finding.file != current:
            current = finding.file
            stream.write("\n" + current + "\n")
        stream.write("  %s:%d: [%s] %s  %s\n" % (
            finding.file, finding.line, finding.severity.upper(),
            finding.rule, finding.message,
        ))
        stream.write("    fix: %s\n" % finding.fix)
    stream.write("\n")
    for entry in summary["skipped_files"]:
        stream.write("skipped (%s): %s\n" % (entry["reason"], entry["file"]))
    line = "%d error, %d warning, %d advisory in %d of %d files" % (
        summary["error"], summary["warning"], summary["advisory"],
        summary["files_with_findings"], summary["files_scanned"],
    )
    if summary["files_skipped"]:
        line += ", %d skipped" % summary["files_skipped"]
    stream.write(line + "\n")
    if summary["truncated"]:
        stream.write("output truncated by --max-findings: %d of %d findings shown\n" % (
            summary["findings_shown"], summary["findings"]))


def print_rules(as_json: bool, stream) -> None:
    if as_json:
        payload = [
            {
                "rule": rule.rule_id,
                "severity": rule.severity,
                "message": rule.message,
                "fix": rule.fix,
                "extensions": list(rule.exts),
                "note": rule.note,
            }
            for rule in RULES
        ]
        json.dump({"rules": payload, "version": VERSION}, stream, indent=2)
        stream.write("\n")
        return
    stream.write("slop_lint %s: %d rules\n" % (VERSION, len(RULES)))
    for severity in SEVERITIES:
        group = [rule for rule in RULES if rule.severity == severity]
        stream.write("\n%s (%d)\n" % (severity, len(group)))
        for rule in group:
            stream.write("  %-22s %s\n" % (rule.rule_id, rule.message))
            stream.write("  %-22s fix: %s\n" % ("", rule.fix))
            stream.write("  %-22s ext: %s\n" % ("", " ".join(rule.exts)))
            if rule.note:
                stream.write("  %-22s note: %s\n" % ("", rule.note))


class Parser(argparse.ArgumentParser):
    def error(self, message: str):
        sys.stderr.write("slop_lint: %s\n" % message)
        raise SystemExit(1)


def build_parser() -> argparse.ArgumentParser:
    parser = Parser(
        prog="slop_lint.py",
        description="Deterministic linter for AI design-slop patterns in frontend source.",
        epilog=(
            "Exit codes: 0 clean or advisory only, 2 error or warning findings, "
            "1 usage error, unreadable target, or a named file that was skipped. "
            "Suppress a rule with a comment holding 'slop-lint-disable <rule-id>' "
            "on the line or the line above, or 'slop-lint-disable-file <rule-id>' "
            "anywhere in the file."
        ),
    )
    parser.add_argument("paths", nargs="*", help="files or directories to scan")
    parser.add_argument("--json", action="store_true", dest="as_json",
                        help="emit one JSON object instead of human output")
    parser.add_argument("--rules", default="",
                        help="comma separated rule ids to run (default: all)")
    parser.add_argument("--exclude", action="append", default=[], metavar="GLOB",
                        help="glob to skip, repeatable")
    parser.add_argument("--max-findings", type=int, default=0, metavar="N",
                        help="print at most N findings (0 means no limit); the exit "
                             "code still counts every finding")
    parser.add_argument("--list-rules", action="store_true",
                        help="print the rule registry and exit")
    parser.add_argument("--version", action="version", version=VERSION)
    return parser


def select_rules(spec: str, parser: argparse.ArgumentParser) -> list:
    if not spec:
        return [rule.rule_id for rule in RULES]
    wanted = [part.strip() for part in spec.split(",") if part.strip()]
    unknown = [name for name in wanted if name not in RULES_BY_ID]
    if unknown:
        parser.error("unknown rule id: " + ", ".join(unknown))
    return [rule.rule_id for rule in RULES if rule.rule_id in wanted]


def main(argv: list) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.list_rules:
        print_rules(args.as_json, sys.stdout)
        return 0
    if not args.paths:
        parser.error("at least one path is required")
    if args.max_findings < 0:
        parser.error("--max-findings must be zero or more")
    rule_ids = select_rules(args.rules, parser)
    targets, missing = iter_targets(args.paths, args.exclude)
    for target in missing:
        sys.stderr.write("slop_lint: cannot read %s\n" % target)
    failed = bool(missing)
    findings = []
    skipped = []
    scanned = 0
    for path, named in targets:
        try:
            src, reason = load_source(path)
            if src is None:
                skipped.append({"file": path, "reason": reason})
                # A file named on the command line that was not linted must not
                # pass as clean.
                if named:
                    sys.stderr.write("slop_lint: %s was not linted: %s (%s)\n" % (
                        path, reason, SKIP_HINTS[reason]))
                    failed = True
                continue
            found = lint_source(path, src, rule_ids)
        except OSError as exc:
            sys.stderr.write("slop_lint: cannot read %s (%s)\n" % (path, exc))
            failed = True
            continue
        scanned += 1
        findings.extend(found)
    findings.sort(key=lambda f: (f.file, f.line, f.col, f.rule))
    shown = findings[:args.max_findings] if args.max_findings else findings
    summary = summarise(findings, scanned, skipped, len(shown))
    if args.as_json:
        json.dump(
            {
                "findings": [f.as_dict() for f in shown],
                "summary": summary,
                "version": VERSION,
            },
            sys.stdout,
            indent=2,
        )
        sys.stdout.write("\n")
    else:
        print_human(shown, summary, sys.stdout)
    if failed:
        return 1
    if summary["error"] or summary["warning"]:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
