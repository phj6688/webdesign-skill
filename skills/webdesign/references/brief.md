# Reading the brief

Sources: taste-skill (MIT) for the design read, the dials and the redesign protocol;
impeccable (Apache-2.0) for the visitor modes. Restated and merged; see `NOTICE.md`.

Skipping this step is the most expensive mistake available. A model that jumps to an
aesthetic spends its one chance at a first impression on a default.

## The design read

Before any code, write one line:

> Reading this as a `<page kind>` for `<audience>`, in a `<vibe>` language, built on
> `<system or token set>`.

Worked examples:

- Reading this as a B2B SaaS landing page for a procurement panel, in a restrained
  language, built on the project's existing Tailwind tokens.
- Reading this as a solo designer's portfolio for hiring managers, in an editorial
  language, built on a committed two-typeface token set.
- Reading this as a public-sector service redesign for the general population, in a
  plain language, built on GOV.UK Frontend.

## Signals to read first

1. **Page kind.** Landing, portfolio, editorial, app shell, docs, redesign.
2. **Vibe words the user used.** Their words, not your paraphrase. "Calm",
   "brutalist", "premium", "serious", "playful", "editorial" each point somewhere
   different.
3. **Reference signals.** URLs they linked, screenshots they pasted, products they
   named, competitors they mentioned.
4. **Audience.** The audience picks the aesthetic. Your taste does not.
5. **Brand assets that already exist.** A logo, a colour, a typeface, photography. On a
   redesign these are starting material, not optional input.
6. **Quiet constraints.** Accessibility-first audiences, public sector, regulated
   industries, trust-first commerce, products for children. These override aesthetic
   preference every time.

## Visitor mode

Pick one. It governs density, motion, copy register and how much risk is appropriate.

| Mode | Job | Surfaces | Tone of the design |
|---|---|---|---|
| Persuade | decide and act | landing, pricing, campaign | one memorable move, everything else quiet |
| Operate | complete a task | app UI, dashboard, editor, settings | dense, predictable, no surprises |
| Read | understand something | docs, article, changelog | measure and rhythm carry it |
| Experience | be inside the work | portfolio, gallery, showcase | the work is the interface |

Pick from the surface, not the product. A developer tool's landing page is Persuade. A
fashion house's docs are Read.

## The three dials

Declare these explicitly. Silently using the baseline counts as not declaring them.

```
VARIANCE: 8    1 = perfect symmetry      10 = asymmetric and loose
MOTION:   6    1 = static                10 = choreographed
DENSITY:  4    1 = gallery               10 = cockpit
```

Baseline is `8 / 6 / 4`. Move them from the read:

| The brief reads as | VARIANCE | MOTION | DENSITY |
|---|---|---|---|
| minimal, calm, editorial | 5 to 6 | 3 to 4 | 2 to 3 |
| premium consumer, brand-led | 7 to 8 | 5 to 7 | 3 to 4 |
| playful, experimental, agency | 9 to 10 | 8 to 10 | 3 to 4 |
| landing or portfolio, no strong signal | 7 to 9 | 6 to 8 | 3 to 5 |
| trust-first, public sector, accessibility-critical | 3 to 4 | 2 to 3 | 4 to 5 |
| app UI, dashboard, admin | 3 to 5 | 2 to 4 | 6 to 8 |
| redesign, preserve the brand | match existing | +1 | match existing |
| redesign, overhaul the visuals | +2 | +2 | match existing |

What the dials actually mean:

- **VARIANCE 1 to 3.** Symmetrical grid, equal fractions, equal padding, centred.
- **VARIANCE 4 to 7.** Deliberate offsets, mixed image aspect ratios, mixed alignment.
- **VARIANCE 8 to 10.** Fractional grids like `2fr 1fr 1fr`, masonry, large empty
  zones. Above 4, every asymmetric layout must collapse to a single column below 768px,
  declared in the same component.
- **MOTION 1 to 3.** Hover and active states only, no autoplay.
- **MOTION 4 to 7.** CSS transitions, staggered load-in, transform and opacity only.
- **MOTION 8 to 10.** Scroll-driven reveals, pinning, scrubbing. Isolate them in leaf
  client components with real cleanup.
- **DENSITY 1 to 3.** Section padding 8rem to 12rem.
- **DENSITY 4 to 7.** Section padding 4rem to 6rem.
- **DENSITY 8 to 10.** Tight padding, hairlines instead of cards, tabular numerals for
  every number.

Two consistency rules that follow from the dials:

- **Motion claimed is motion shown.** If MOTION is above 4, the page must actually
  move. If you cannot ship working motion in the available scope, set MOTION to 3 and
  ship a clean static page. Half-built motion is worse than none.
- **Density is a page property, not a section property.** One page does not move
  between gallery and cockpit.

## Ambiguity

Ask exactly one question, and only when the read genuinely forks into two different
builds. Never send a list of questions. If you can infer it from context, do not ask.

A good single question names both branches:

> Should this feel closer to restrained and product-led, or closer to expressive and
> art-directed?

## Redesign protocol

Misreading the mode is the biggest source of bad redesign output. Detect it first.

- **Greenfield.** Nothing to preserve.
- **Preserve.** Modernise without breaking the brand. Audit first, extract the tokens,
  then evolve.
- **Overhaul.** New visual language over existing content and structure. Treat the
  visuals as greenfield. Treat the content and the information architecture as fixed.

If it is ambiguous, ask once: does this redesign keep the existing brand, or start
visually from scratch?

### Audit before touching anything

Write down: the brand tokens in use, the page tree and primary navigation, which
content blocks are doing real work, the signature patterns worth keeping, the patterns
to retire, the current dial reading, and the SEO baseline. Losing search rankings is
the top redesign risk, so record the ranking pages, the meta titles, the structured
data and the social cards before you change a route.

### Never change silently

Route slugs and anchor ids. Primary navigation labels. Form field names and order,
because analytics and autofill depend on them. The logo or wordmark. Legal and consent
copy. Each of these needs the user to say yes first.

### Modernisation levers, in order of value per unit of risk

1. Typography. The biggest visual lift for the least structural risk.
2. Spacing and rhythm.
3. Colour recalibration. Desaturate, unify the neutrals, keep the brand accent.
4. The motion layer.
5. Recomposing the hero and the key sections.
6. Replacing a block outright. Only when it cannot be saved.

Stop as soon as the brief is satisfied. When the structure and the content are sound, a
targeted pass over levers 1 to 4 gets most of the value for a fraction of the risk.
