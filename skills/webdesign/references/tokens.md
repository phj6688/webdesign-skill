# Tokens

Sources: impeccable (Apache-2.0) for the ramp, the floors, the colour strategies and the
motion table; taste-skill (MIT) for the breakpoints. Restated and merged; see
`NOTICE.md`.

Decide these before you write a component. A page assembled from ad hoc values cannot be
corrected afterwards, because there is nothing to correct it against.

## Why a ramp beats free values

One real design system replaced a tail of 86 distinct font sizes, including six
near-identical steps between 13.7px and 15.4px that no reader could tell apart. Nobody
chose those 86 values. They accumulated. A declared ramp makes drift visible, which is
the whole point.

Commit to a ramp, then make every literal in the codebase land on a step.

## Type

A 21-step ramp at a 16px root covers nearly every real interface. Use the steps you
need and delete the rest.

| px | rem | Typical role |
|---|---|---|
| 8 | 0.5 | legal smallprint only |
| 9 | 0.5625 | legal smallprint only |
| 10 | 0.625 | non-interactive micro-label |
| 11 | 0.6875 | floor for functional text |
| 12 | 0.75 | caption; hard floor for any body text |
| 13 | 0.8125 | caption, dense meta |
| 14 | 0.875 | secondary body, button, nav |
| 15 | 0.9375 | dense body |
| 16 | 1 | body default |
| 18 | 1.125 | lead body |
| 20 | 1.25 | subhead |
| 24 | 1.5 | heading |
| 28 | 1.75 | heading |
| 32 | 2 | display small |
| 40 | 2.5 | display |
| 48 | 3 | display |
| 56 | 3.5 | display |
| 64 | 4 | display large |
| 72 | 4.5 | hero |
| 80 | 5 | hero |
| 88 | 5.5 | hero ceiling |

Rules that go with it:

- Body text defaults to 16px on the web. Go lower only for a dense role or a platform
  convention, and never below 12px: the linter's `tiny-text` rule fails anything under
  it.
- Functional text (link, button, nav, label, table cell, timestamp) never goes below
  11px; the linter's `undersized-ui-text` rule fails it. Landing on the ramp does not
  exempt a value.
- Prose measure 65 to 75 characters. Serif tolerates slightly more.
- Line height moves inversely with measure. 1.5 to 1.7 for body. Never below 1.3.
- Light text on a dark surface compensates on three axes at once: more line height, more
  tracking, one step more weight.
- Paragraph spacing or a first-line indent, never both. Two marks for one boundary.
- Heading and body must separate by at least 1.25x at every step, or the hierarchy is
  flat and the page reads as one block.
- Tracking floor -0.04em. Display type ceiling around 6rem.
- Per role, declare family, size, weight, line height and letter spacing. A role with
  only a size is not a role.

## Colour

Declare new palettes in OKLCH. Lightness and chroma then move predictably, which is what
makes a tonal ramp possible by hand.

Build roles, not swatches:

```
canvas              the page ground
surface             a raised plane
surface-elevated    a further raised plane
ink                 primary text
ink-muted           secondary text
ink-subtle          tertiary text
hairline            a border or divider
accent              one action colour
accent-pressed      its pressed state
on-accent           text on the accent
success warning error info
```

Contrast floors, measured on the result:

| Element | Minimum |
|---|---|
| body text and placeholder text | 4.5:1 |
| large text, 24px or 18.7px bold | 3:1 |
| controls, icons, focus indicators | 3:1 |

More rules:

- On a coloured surface, derive secondary text from the surface hue or the foreground.
  Never from grey, because grey on colour reads as broken rather than quiet.
- Prefer an explicit colour over a stack of translucent overlays. Alpha makes contrast
  depend on whatever sits underneath, so it stops being checkable.
- When deriving an OKLCH ramp, vary lightness and reduce chroma near white and near
  black. A ramp that holds chroma flat goes muddy at both ends.
- Data series need distinct lightness, plus a second channel: shape, label or pattern.
  Colour is never the only code.
- No pure `#000000` and no pure `#ffffff` as a surface or a text colour.

### Pick a colour strategy before picking colours

| Strategy | What it means | Fits |
|---|---|---|
| Restrained | neutrals plus one accent | Operate, Read |
| Committed | one saturated colour across 30 to 60% of the surface | Persuade |
| Full palette | three or four named roles carrying meaning | Experience, data-heavy |
| Drenched | the surface itself is the colour | Experience, campaign |

## Space

A 4px base gives the middle steps an 8px-only scale misses: 4px and 12px are the ones
that matter most, inside controls and between tight pairs.

```
2xs  4px     icon to label, hairline gaps
xs   8px     inside a control
sm   12px    between a tight pair, such as a label and its input
md   16px    between related elements
lg   24px    between groups
xl   32px    between blocks
2xl  48px    inside a section
3xl  80px    between sections
4xl  112px   between major sections
```

- Tight inside a group, generous between groups. Proximity carries meaning before any
  container does.
- More space above a heading than below it. This is measurable and it is wrong more
  often than any other spacing rule.
- Use `gap` for sibling rhythm rather than child margins. Margins collapse and fight.
- At least 16px horizontal padding on body text. 24 to 32px reads better.
- Inside a bordered or tinted container, at least 8px padding, and 12 to 16px is better.
- Rhythm comes from deliberate contrast between tight and generous, not from one
  uniform interval everywhere. Uniform spacing reads as a spreadsheet.

## Radius

```
none  0
xs    2px
sm    4px
md    8px
lg    12px
xl    16px
pill  999px
```

Pick one system and write down the rule. Card radii in the 12 to 16px band read as
intentional. Pills belong on small controls. A 1px border under a wide soft shadow is a
ghost edge: pick the border or pick the shadow.

## Elevation

A shadow needs an offset and a blur. A zero-offset coloured halo is decoration.

A worked five-level ladder, as an example of the shape rather than values to copy:

```
0  flat            no shadow, a hairline border
1  inset hairline  0 0 0 1px rgb(0 0 0 / 0.08) inset
2  subtle          0 1px 2px rgb(0 0 0 / 0.04), plus the inset hairline
3  card            0 4px 12px rgb(0 0 0 / 0.08), plus the inset hairline
4  modal           0 16px 48px -8px rgb(0 0 0 / 0.16)
```

Stacked small offsets read as real light. One 8px generic blur reads as a default. Tint
the shadow to the surface hue.

## Motion

| Duration | Use |
|---|---|
| 100 to 150ms | immediate feedback on an action |
| 150 to 300ms | a routine state change |
| 300 to 500ms | a layout, overlay or view transition |
| 500 to 800ms | one deliberately authored entrance |

- Exit faster than you enter.
- `cubic-bezier(0.16, 1, 0.3, 1)` is the confident arrival curve. Do not reach for
  bounce or elastic by reflex.
- Ease out from an already-visible default, so a failed script cannot hide content.
- Every animation needs a `prefers-reduced-motion` branch with a real alternative.

## Breakpoints

Test at 375, 768 and 1280. Those are the three the capture script shoots.

```
sm   640px
md   768px
lg   1024px
xl   1280px
2xl  1536px
```

Cap the content container around 1200 to 1400px. Use `min-h-[100dvh]` for a full-height
hero, never `h-screen` or `100vh`, because the mobile address bar moves and the layout
jumps. Touch targets 44x44px minimum.

## The document

Write the design system down, as YAML frontmatter plus prose, in a `DESIGN.md` at the
project root. The schema and the reason for writing it last are in
[systems.md](systems.md).
