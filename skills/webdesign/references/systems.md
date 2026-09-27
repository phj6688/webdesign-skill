# Picking the system

Sources: taste-skill (MIT) for the package map, awesome-design-md (MIT) for the
document schema, impeccable (Apache-2.0) for writing the system last. Restated and
merged; see `NOTICE.md`.

Three sources, in priority order. Take the first one that applies.

1. **The project's own system.** A `DESIGN.md`, a token file, a Tailwind theme, a CSS
   custom-property layer, a documented palette. It beats everything else in this skill.
   Build inside it. Report a conflict with the floor; do not resolve it silently.
2. **An official package,** when the brief reads as one.
3. **A token set you commit to now,** starting from an archetype in `systems/` or from
   a reference system you fetch.

## Official packages

If the brief reads as one of these, install the real package and use it. Do not
recreate its CSS by hand. Do not import its tokens and then override most of them. One
system per project: never Fluent and Carbon in one tree, never shadcn components inside
a Material app.

| The brief reads as | Use |
|---|---|
| Microsoft, enterprise SaaS | `@fluentui/react-components` or `@fluentui/web-components` |
| Material, Google-adjacent | `@material/web` with Material 3 tokens |
| IBM-style enterprise analytics | `@carbon/react` and `@carbon/styles` |
| Shopify app surface | Polaris web components or Polaris React |
| Atlassian-style work tool | `@atlaskit/*` with `@atlaskit/tokens` |
| GitHub-style developer tool | `@primer/css` or `@primer/react-brand` |
| UK public sector | `govuk-frontend` |
| US public sector, trust-first | `uswds` |
| accessible React foundation | `@radix-ui/themes` |
| SaaS where you own the components | shadcn/ui, never left in its default state |
| fast local-business MVP | Bootstrap 5.3 |

Check `package.json` before importing anything. If the package is missing, print the
install command first. Never assume a library exists.

## Aesthetics that have no package

These are directions, not systems. Build them with native CSS, Tailwind and a maintained
component library. Say honestly in a code comment what is borrowed inspiration.

- **Glass.** `backdrop-filter`, a 1px inner border, an inset highlight. Always a solid
  fallback under `prefers-reduced-transparency`, and enough contrast without the blur.
- **Bento.** CSS Grid with mixed cell sizes. Cell count equals content count.
- **Brutalism.** Native CSS, raw borders, hard edges, deliberate.
- **Editorial.** An asymmetric grid, generous whitespace, a serif only when it earns it.
- **Kinetic type.** CSS animation, scroll-driven animation, a scroll library for pinning.
- **Apple's Liquid Glass.** Apple documents it for Apple platforms only. There is no
  official web stylesheet for it. A web version is an approximation, so label it as one.

## Archetypes on disk

`systems/` holds a small set of original token sets, named by what they are rather than
by a brand. Each is a complete `DESIGN.md` in the schema below. Copy one to the project
root as `DESIGN.md`, then change it to fit the brief. Treat each as a starting point to
commit to and then diverge from, not as a finished identity.

| System | Modes | What it is |
|---|---|---|
| `restrained-product` | Persuade, Operate | cool neutral, one cobalt accent, type-led hierarchy |
| `editorial-reading` | Read | cool paper, blue-black ink, teal links, a serif that earns its place |
| `committed-forest` | Persuade, Experience | forest green across 30 to 60% of the surface, bone, one amber highlight |
| `amber-terminal` | Operate, Read | the house system: warm near-black, amber, burnt-orange headings, dark only |

Every archetype declares its colour pairs in a `contrast` list, and every pair is
measured:

```
python3 scripts/check_contrast.py systems/*.md
python3 scripts/check_contrast.py DESIGN.md
```

Run it on your own `DESIGN.md` after every palette change. It resolves `{colors.x}`
references, checks the dark map with the light map as its fallback, and flags any OKLCH
value outside the sRGB gamut, because a clamped colour is not the colour you declared.
With no `contrast` list it checks the usual pairs for whichever tokens exist, so it also
reads a fetched reference system.

The checker measures tokens, not the page. Text over an image, or over a translucent
overlay, still needs the rendered check in [verify.md](verify.md).

The checker already earned its place once. The first draft of `committed-forest` used
its amber as the action colour on the light ground, and the check measured it at 1.7 to
1. That is why amber is now confined to the green band, where it measures above 6 to 1.

## Reference systems from real sites

`scripts/fetch_system.sh <slug>` downloads one of 74 design-system documents from
`VoltAgent/awesome-design-md`, pinned to a fixed commit. Each one describes the publicly
visible styling of a real product's site: its colour roles, type ramp, spacing, radius,
elevation ladder and components, with real values.

```
scripts/fetch_system.sh --list
scripts/fetch_system.sh stripe            # writes .design-ref/stripe.DESIGN.md
scripts/fetch_system.sh linear.app --out docs/refs
```

Use a fetched system for **technique**, not for identity. The useful parts are the shape
of a type ramp that works, how a mature product stacks its shadows, which component
states it bothers to design, and how its density changes between marketing and product
surfaces.

Measure a fetched system before you borrow from it. Across the 74 at the pinned commit,
seven put white text on their brand colour at 3.3 to 4.5 to 1, under the 4.5 to 1 that
button text below 24px needs; five of them sit between 3.3 and 3.5. Thirteen set a muted
text token under 4.5 to 1 on their page ground, most of them light grey on white. Those
are failures to leave behind, not details to copy.

Read the report with the file's roles in mind, because the default pairs are a guess at
them. When a brand's `primary` is a button fill rather than a text colour, a failing
`primary on canvas` pair asks the wrong question. A muted token meant for dark tiles
fails against a white ground without being wrong where it is used.

```
scripts/fetch_system.sh cursor
python3 scripts/check_contrast.py .design-ref/cursor.DESIGN.md
```

Two cautions, both real:

- **Trade dress.** The documents are extracted from public CSS, but a page that a
  visitor could mistake for another company's site is a trademark and trade-dress
  problem, whatever the licence on the document says. Rename every token, change the
  accent, and never put the brand's name in the output.
- **Typefaces.** Most of these systems name a proprietary typeface: Sohne, Copernicus,
  StyreneB, Linear Display, Universal Sans, Notion Sans and others. The document does
  not license the font. Use the substitute the file names in its font section.

The format has two generations. Most files carry YAML frontmatter with `colors`,
`typography`, `rounded`, `spacing` and `components`. Ten older ones (kraken,
lamborghini, lovable, mastercard, runwayml, sanity, spotify, starbucks, tesla,
theverge) have numbered prose sections and inline hex values instead. Key names are not
consistent across files, and line height is sometimes a ratio and sometimes pixels.
Read the file; do not parse it blind.

## The DESIGN.md schema

Write the project's own system in this shape, at the project root. It is the same shape
the reference systems use, so a fetched reference and your own system compare side by
side.

```yaml
---
name: project-name
description: One paragraph. What the system is for and what it refuses to be.
modes: [persuade]            # the visitor modes it serves
dials: {variance: 7, motion: 5, density: 4}
colors:
  canvas: "oklch(98% 0.005 250)"
  surface: "oklch(96% 0.006 250)"
  ink: "oklch(22% 0.02 250)"
  ink-muted: "oklch(45% 0.02 250)"
  hairline: "oklch(90% 0.008 250)"
  accent: "oklch(62% 0.19 255)"
  accent-pressed: "oklch(54% 0.19 255)"
  on-accent: "oklch(99% 0 0)"
typography:
  display-lg: {fontFamily: "…", fontSize: 56px, fontWeight: 600,
               lineHeight: 1.05, letterSpacing: -0.03em}
  body: {fontFamily: "…", fontSize: 16px, fontWeight: 400,
         lineHeight: 1.6, letterSpacing: 0}
rounded: {sm: 4px, md: 8px, lg: 12px, pill: 999px}
spacing: {2xs: 4px, xs: 8px, sm: 12px, md: 16px, lg: 24px, xl: 32px, 2xl: 48px, 3xl: 80px}
components:
  button-primary: {backgroundColor: "{colors.accent}", textColor: "{colors.on-accent}",
                   typography: "{typography.body}", rounded: "{rounded.md}",
                   padding: "10px 18px"}
---
```

Body sections, in this order: Overview, Colors, Typography, Layout, Elevation, Shapes,
Components, Do and Do Not, Responsive Behaviour, Known Gaps.

Components refer to tokens with `{group.name}` references. Never inline a hex value in a
component entry. A component that inlines its values is how drift starts.

## Write it last

Split the document in two. Commit to the tokens, the frontmatter, at step 2: that is what
the build is measured against, and `check_contrast.py` reads it. Write the prose sections
at the end, from what you actually built. A rulebook written before the build gets
defended against reality instead of describing it, so the Overview, the Do and Do Not
list and the Known Gaps wait until there is something real to describe. If the build
changed a token, change the frontmatter to match; do not bend the build back.

When the user asked for a single file, the tokens ship as custom properties on `:root`
in that file. The frontmatter from step 2 still exists while you build, so
`check_contrast.py` has something to measure; remove that working `DESIGN.md` at the
end unless the user wants it kept.

On an existing project, the order reverses: read its system first, build inside it, and
update the document only where the build genuinely changed the system.
