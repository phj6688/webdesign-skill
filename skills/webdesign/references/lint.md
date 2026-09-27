# The linter

The linter is original code. Its thresholds and rule names come from impeccable
(Apache-2.0) and taste-skill (MIT); see `NOTICE.md`.

`scripts/slop_lint.py` reads frontend source and reports the tells that can be decided
from the source alone. It runs no browser, makes no network call, and needs only the
Python standard library.

It is a floor, not a verdict. A clean run means none of these 26 patterns appear. It
does not mean the page is good. Contrast, rhythm, hierarchy and taste still need the
screenshots and the critique.

## Run it

```
python3 scripts/slop_lint.py src/
python3 scripts/slop_lint.py src/ --json
python3 scripts/slop_lint.py src/ --rules em-dash,banned-font
python3 scripts/slop_lint.py src/ --exclude 'src/legacy/*'
python3 scripts/slop_lint.py --list-rules
```

It reads `.html`, `.htm`, `.jsx`, `.tsx`, `.js`, `.ts`, `.vue`, `.svelte`, `.astro`,
`.css` and `.scss`. It skips `node_modules`, `.git`, `dist`, `build`, `.next`, `out`,
`coverage` and `vendor`.

It also skips a minified file: one whose name matches `*.min.*`, or whose median line
runs past 500 characters. One long line, such as an inline data URI, never causes a skip.
Every skipped file is named in the output as `skipped (<reason>): <path>`. A file you
named on the command line that gets skipped makes the run exit 1, because a check you
asked for did not happen.

| Exit | Meaning |
|---|---|
| 0 | clean, or advisory findings only |
| 2 | at least one error or warning |
| 1 | usage error, or a target it cannot read |

With `--json` it prints one object: `findings` (file, line, col, rule, severity,
message, fix, evidence), `summary` and `version`. The summary counts every finding by
severity, and adds `findings_shown` and `skipped_files`.

`--max-findings N` limits how many findings are printed. The exit code still counts all
of them, so a hidden error still fails the run.

## The rules

| Rule | Severity | Catches | Fix |
|---|---|---|---|
| `em-dash` | error | Em dash or en dash in UI copy. | Use a comma, a colon, parentheses, or two sentences. |
| `scroll-listener` | error | Scroll listener drives layout or motion. | Use IntersectionObserver or a CSS scroll-driven animation. |
| `h-screen-hero` | error | Viewport-locked height breaks on mobile browser chrome. | Use min-h-[100dvh] in Tailwind, or min-height: 100dvh in CSS. |
| `pure-black-white` | warning | Pure black or pure white used as a colour value. | Use a near-black or near-bone tone from the palette instead. |
| `banned-font` | warning | Over-used default font family in the first position of the stack. | Pick a family with a voice, and keep the generic name as a fallback. |
| `eyebrow-density` | warning | Too many uppercase tracked eyebrow labels for the section count. | Keep at most one eyebrow per three sections, and delete the rest. |
| `section-number-label` | warning | Enumerated section label reads as a template, not as content. | Delete the number, or give the section a real name. |
| `scroll-cue` | warning | Scroll cue text tells the visitor to do what they already do. | Delete the cue, and let the content edge signal more below. |
| `filler-verb` | warning | Filler marketing verb carries no information. | Name the concrete outcome instead of the verb. |
| `placeholder-identity` | warning | Placeholder person or brand name left in the copy. | Use a real name, or cut the element until content exists. |
| `fake-round-number` | warning | Invented round statistic reads as filler. | Use a measured number, or remove the statistic. |
| `tight-leading` | warning | Line height below 1.3 on non-display text. | Use 1.5 or more for body text, and keep tight leading for display only. |
| `tiny-text` | warning | Body text set below 12px. | Use 16px for body text. 12px is the floor. |
| `undersized-ui-text` | warning | Functional UI text set below 11px. | Keep functional text at 11px or more, and 12px or more where it fits. |
| `wide-tracking-body` | warning | Letter spacing above 0.05em on lowercase body text. | Keep tracking near 0 for body text, and reserve it for uppercase labels. |
| `extreme-tracking` | warning | Letter spacing tighter than -0.04em collides the glyphs. | Keep tracking at -0.03em or looser. |
| `gradient-text` | warning | Gradient clipped to text is an AI-era default. | Use one solid colour, and spend the boldness on layout instead. |
| `no-reduced-motion` | warning | File declares animation but honours no reduced-motion preference. | Add a prefers-reduced-motion media query, or call useReducedMotion. |
| `banned-palette` | warning | Hex value from the over-used AI premium-consumer palette. | Pick a palette from the brief, not the cream-and-terracotta default. |
| `middle-dot-run` | warning | Three or more middle-dot separators in one text run. | Use two items with a comma, or a real list element. |
| `lucide-icons` | warning | Lucide icon set is the AI-default icon look. | Use the project icon set, or one icon library at one stroke weight. |
| `hand-rolled-icon` | advisory | Hand-drawn inline icon path with no icon library in the file. | Check the glyph against a real icon set, or keep one consistent source. |
| `three-column-cards` | advisory | Three-column card row is the default AI section shape. | Vary the rhythm: two columns, an offset pair, or a list. |
| `nested-card` | advisory | Card with a shadow inside another card with a shadow. | Flatten one level, and keep a single elevation per surface. |
| `version-label-hero` | advisory | Version or access badge in the hero region. | Move the badge out of the hero, or delete it. |
| `system-font-display` | advisory | System display font in the first position of the stack. | Pick a real display family, and keep the system name as a fallback. |

`pure-black-white` scales with use: one occurrence in a file is advisory, two or more is
a warning. A single pure value is often a deliberate edge case; a pattern of them is a
palette that was never chosen.

## What it cannot see

Know the limits so you do not over-trust a clean run.

- **Rendered values.** It reads what the source says, not what the browser computes. A
  class assembled at runtime from variables is invisible to it. Text sizes in `em` or
  `%` depend on the parent, so the size rules judge only `px` and `rem`. Contrast depends on what
  sits underneath, so it is not checked here at all. Use `check_contrast.py` for the
  tokens and the screenshots for the page.
- **JSX text.** There is no full JSX parser. Text is found between tags and expressions
  and inherits the nearest opening tag for context. A quoted token with no spaces
  inside JSX text, such as `<p>"word"</p>`, is read as a string literal rather than as
  copy, so a dash joining two words inside those quotes is missed.
- **Dashes on code lines.** An em or en dash inside a string literal is not reported
  when its line also holds `import`, `require(`, `from "` or `content:`, because the
  linter treats that line as code. A string of UI copy on such a line is missed.
- **Which text is functional.** The size rules decide body text from functional text by
  tag, class name, role, click handler and `cursor: pointer`. Text inside a JavaScript
  expression, such as `{isUser ? 'YOU' : 'AI'}`, has no case the linter can read.
- **Px tracking.** `extreme-tracking` resolves `em`, `rem` and Tailwind arbitrary values,
  not pixel tracking measured against a font size.
- **Structure.** `nested-card` runs on `.html` only, and gives up on markup whose
  nesting it cannot trust. `three-column-cards` is a narrow pattern match, not a layout
  analysis.

## Suppress a finding, with a reason

Some findings are correct and still wrong for this page: a brand whose own typeface is
on the banned list, a genuine timezone-distributed studio, a real sequence that really
is numbered. Suppress those explicitly, with the reason in the comment:

```html
<!-- slop-lint-disable banned-font: the brand's own typeface, on its own domain -->
```

```jsx
{/* slop-lint-disable section-number-label: a real four-step install sequence */}
```

```css
/* slop-lint-disable-file pure-black-white: print stylesheet */
```

A suppression on a line covers that line; on the line above, it covers the next line.
`slop-lint-disable-file <rule>` anywhere in the file covers the whole file. It works in
HTML comments, `//`, `/* */` and `{/* */}`.

List every suppression and its reason in the hand-over. A suppression with no reason is
a finding you decided not to fix, and the reader deserves to know which.

## Run it on the whole project, then on the change

On a first pass over an existing project the count can be large. That is information,
not a failure of the linter. Fix the errors first, then the warnings in the files you
are changing. Do not rewrite untouched files to satisfy it unless that is the task.
