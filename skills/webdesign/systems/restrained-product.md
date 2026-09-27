---
name: restrained-product
description: A quiet, cool-neutral system for software products and their marketing pages. One cobalt accent does all the pointing. Type carries the hierarchy, so nothing else has to shout. It refuses gradients, glow and card grids as structure.
modes: [persuade, operate]
dials: {variance: 6, motion: 4, density: 5}
colors:
  canvas: "oklch(98.5% 0.004 255)"
  surface: "oklch(96.2% 0.007 255)"
  ink: "oklch(23% 0.028 262)"
  ink-muted: "oklch(45% 0.022 262)"
  hairline: "oklch(90.5% 0.009 255)"
  accent: "oklch(51% 0.2 263)"
  accent-pressed: "oklch(44% 0.19 263)"
  on-accent: "oklch(98.5% 0.004 255)"
  success: "oklch(52% 0.13 150)"
  warning: "oklch(62% 0.15 70)"
  error: "oklch(53% 0.19 27)"
colors-dark:
  canvas: "oklch(17% 0.012 262)"
  surface: "oklch(21.5% 0.014 262)"
  ink: "oklch(94% 0.008 255)"
  ink-muted: "oklch(74% 0.015 258)"
  hairline: "oklch(30% 0.014 262)"
  accent: "oklch(70% 0.15 258)"
  accent-pressed: "oklch(64% 0.15 258)"
  on-accent: "oklch(17% 0.012 262)"
contrast:
  - [ink, canvas, 4.5]
  - [ink-muted, canvas, 4.5]
  - [ink, surface, 4.5]
  - [ink-muted, surface, 4.5]
  - [on-accent, accent, 4.5]
  - [accent, canvas, 3]
  - [accent-pressed, canvas, 3]
typography:
  display-lg: {fontFamily: "Schibsted Grotesk", fontSize: 56px, fontWeight: 600, lineHeight: 1.05, letterSpacing: -0.03em}
  display-md: {fontFamily: "Schibsted Grotesk", fontSize: 40px, fontWeight: 600, lineHeight: 1.1, letterSpacing: -0.025em}
  heading: {fontFamily: "Schibsted Grotesk", fontSize: 24px, fontWeight: 600, lineHeight: 1.25, letterSpacing: -0.015em}
  lead: {fontFamily: "Schibsted Grotesk", fontSize: 20px, fontWeight: 400, lineHeight: 1.5, letterSpacing: -0.005em}
  body: {fontFamily: "Schibsted Grotesk", fontSize: 16px, fontWeight: 400, lineHeight: 1.6, letterSpacing: 0}
  body-sm: {fontFamily: "Schibsted Grotesk", fontSize: 14px, fontWeight: 400, lineHeight: 1.55, letterSpacing: 0}
  label: {fontFamily: "Schibsted Grotesk", fontSize: 14px, fontWeight: 500, lineHeight: 1.2, letterSpacing: 0}
  code: {fontFamily: "JetBrains Mono", fontSize: 14px, fontWeight: 400, lineHeight: 1.6, letterSpacing: 0}
rounded: {sm: 4px, md: 8px, lg: 12px, pill: 999px}
spacing: {2xs: 4px, xs: 8px, sm: 12px, md: 16px, lg: 24px, xl: 32px, 2xl: 48px, 3xl: 80px, 4xl: 112px}
components:
  button-primary: {backgroundColor: "{colors.accent}", textColor: "{colors.on-accent}", typography: "{typography.label}", rounded: "{rounded.md}", padding: "10px 18px", height: 40px}
  button-secondary: {backgroundColor: "{colors.surface}", textColor: "{colors.ink}", typography: "{typography.label}", rounded: "{rounded.md}", padding: "10px 18px", height: 40px}
  input: {backgroundColor: "{colors.canvas}", textColor: "{colors.ink}", typography: "{typography.body}", rounded: "{rounded.md}", padding: "10px 12px", height: 40px}
  panel: {backgroundColor: "{colors.surface}", textColor: "{colors.ink}", rounded: "{rounded.lg}", padding: "32px"}
---

# restrained-product

## Overview

Built for a product that wants to be trusted before it wants to be noticed. The palette
is a cool neutral with a faint blue cast, so the single cobalt accent reads as the only
live colour on the page. Hierarchy comes from type weight and size, not from colour, so
the page survives a greyscale print and a colour-blind reader.

Key characteristics:

- One accent. It marks actions and the current location, and nothing else.
- Panels are defined by a tonal step, not by a border and a shadow together.
- The type ramp does the work. No eyebrows, no accented words in headlines.

## Colors

Declared in OKLCH so the light and dark themes move along the same hue axis. The dark
theme is composed, not inverted: the canvas stays blue-cast, and the accent rises in
lightness so it still passes on a dark ground.

Every pair in the `contrast` list is measured by `scripts/check_contrast.py`.

## Typography

Schibsted Grotesk, an open-licence grotesque with more character than the usual
product sans, for everything but code. JetBrains Mono for code only, never as a costume
for "technical".

Display tracking stops at -0.03em. Body sits at 16px and 1.6 line height, capped at 70
characters.

## Layout

A 4px base. Sections sit 80px apart at desktop, 48px at mobile. Content caps at 1200px.
Proximity groups first; a panel only appears when a group needs to read as one object.

## Elevation

Flat by default. A raised element steps up one surface tone. When a floating layer needs
a shadow (a menu, a dialog), use `0 8px 24px -6px` with the ink colour at 12% alpha, and
drop the border.

## Shapes

8px on controls, 12px on panels, pill only on small tags. Written down, so it stays
consistent.

## Components

Buttons are 40px tall with a 44px hit area on touch. The primary button is the only
filled accent element in a view. Inputs carry a visible label above them and a 2px
accent focus ring offset by 2px.

## Do and Do Not

- Do let one headline and one image carry the hero.
- Do use the tonal surface step to group, before reaching for a panel.
- Do not add a second accent colour for "variety".
- Do not put an icon, a heading and a sentence in three identical cards across.

## Responsive Behaviour

Test at 375, 768 and 1280. The display size steps down one ramp level per breakpoint.
Every multi-column block collapses to one column below 768px.

## Known Gaps

No data-visualisation palette. Build one with distinct lightness steps before charting.
