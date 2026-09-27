---
name: editorial-reading
description: A long-form reading system for articles, documentation, essays and changelogs. A cool paper ground, a deep blue-black ink and one teal accent for links. The measure and the rhythm do the work. It refuses the cream-and-brass palette and ornamental labels.
modes: [read]
dials: {variance: 5, motion: 2, density: 3}
colors:
  canvas: "oklch(97.2% 0.006 220)"
  surface: "oklch(94.8% 0.008 220)"
  ink: "oklch(21% 0.02 235)"
  ink-muted: "oklch(44% 0.018 235)"
  hairline: "oklch(88% 0.01 225)"
  accent: "oklch(46% 0.075 195)"
  accent-pressed: "oklch(39% 0.068 195)"
  on-accent: "oklch(97.2% 0.006 220)"
colors-dark:
  canvas: "oklch(18.5% 0.01 235)"
  surface: "oklch(22.5% 0.012 235)"
  ink: "oklch(91% 0.008 220)"
  ink-muted: "oklch(72% 0.012 225)"
  hairline: "oklch(31% 0.012 235)"
  accent: "oklch(74% 0.1 190)"
  accent-pressed: "oklch(68% 0.1 190)"
  on-accent: "oklch(18.5% 0.01 235)"
contrast:
  - [ink, canvas, 4.5]
  - [ink-muted, canvas, 4.5]
  - [ink, surface, 4.5]
  - [ink-muted, surface, 4.5]
  - [on-accent, accent, 4.5]
  - [accent, canvas, 4.5]
  - [accent-pressed, canvas, 4.5]
typography:
  display: {fontFamily: "Source Serif 4", fontSize: 48px, fontWeight: 600, lineHeight: 1.1, letterSpacing: -0.02em}
  heading: {fontFamily: "Source Serif 4", fontSize: 28px, fontWeight: 600, lineHeight: 1.25, letterSpacing: -0.01em}
  subhead: {fontFamily: "Source Serif 4", fontSize: 20px, fontWeight: 600, lineHeight: 1.35, letterSpacing: 0}
  body: {fontFamily: "Source Serif 4", fontSize: 19px, fontWeight: 400, lineHeight: 1.7, letterSpacing: 0}
  ui: {fontFamily: "Public Sans", fontSize: 15px, fontWeight: 500, lineHeight: 1.4, letterSpacing: 0}
  caption: {fontFamily: "Public Sans", fontSize: 14px, fontWeight: 400, lineHeight: 1.5, letterSpacing: 0}
  code: {fontFamily: "JetBrains Mono", fontSize: 15px, fontWeight: 400, lineHeight: 1.6, letterSpacing: 0}
rounded: {sm: 3px, md: 6px}
spacing: {xs: 8px, sm: 16px, md: 24px, lg: 36px, xl: 56px, 2xl: 88px}
components:
  link: {textColor: "{colors.accent}", typography: "{typography.body}", textDecoration: "underline 1px, offset 3px"}
  code-block: {backgroundColor: "{colors.surface}", textColor: "{colors.ink}", typography: "{typography.code}", rounded: "{rounded.md}", padding: "16px 20px"}
  callout: {backgroundColor: "{colors.surface}", textColor: "{colors.ink}", typography: "{typography.body}", rounded: "{rounded.md}", padding: "20px 24px"}
---

# editorial-reading

## Overview

For text people read to the end. The ground is a cool paper, not cream, so the page does
not join the warm-premium cluster every generated article lands in. The ink is a deep
blue-black, never pure black. The only colour is the link.

Key characteristics:

- A serif is earned here: this is long-form reading, the one job serifs are best at.
- The measure is the design. Body caps at 68 characters.
- Space above a heading is twice the space below it.

## Colors

Links sit at 4.5:1 or better on the canvas, not the 3:1 control floor, because a link is
text first. Underline every link in running prose; colour alone is not a link cue.

## Typography

Source Serif 4 for reading, at 19px with a 1.7 line height, because a serif at a long
measure needs more leading than a sans. Public Sans for interface text only: navigation,
captions, metadata. Paragraphs are separated by space, never by space and an indent.

## Layout

One reading column, capped at 68 characters, left-aligned. Wide media may break out to
the full container. Headings carry 56px above and 24px below.

## Elevation

None. This system is flat. Separation is space and a hairline.

## Shapes

Small radii only: 3px on inline code, 6px on blocks.

## Components

Code blocks and callouts share the surface tone. A callout never uses a coloured left
border above 1px; tint the surface instead.

## Do and Do Not

- Do let the headline be plain and specific.
- Do give every image a caption that says what it shows, not a mood.
- Do not put a kicker label above the headline.
- Do not justify text on the web. Ragged right reads better.

## Responsive Behaviour

At 375 the body drops to 18px and the display to 32px. The measure holds.

## Known Gaps

No marketing components. Pair with a Persuade system for the landing page.
