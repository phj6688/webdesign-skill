---
name: committed-forest
description: A committed-colour system for a brand that wants to be recognised from across a room. Deep forest green carries 30 to 60 percent of the surface, bone carries the rest, and one amber highlight lives only on the green. It is the alternative to the cream-and-brass premium default.
modes: [persuade, experience]
dials: {variance: 8, motion: 6, density: 3}
colors:
  canvas: "oklch(96.8% 0.011 128)"
  surface: "oklch(93.4% 0.016 128)"
  brand: "oklch(33% 0.075 158)"
  on-brand: "oklch(95.5% 0.016 120)"
  ink: "oklch(24% 0.035 158)"
  ink-muted: "oklch(43% 0.03 158)"
  hairline: "oklch(87% 0.018 130)"
  accent: "oklch(38% 0.08 158)"
  accent-pressed: "oklch(32% 0.075 158)"
  on-accent: "oklch(96.8% 0.011 128)"
  highlight: "oklch(80% 0.145 78)"
  on-highlight: "oklch(24% 0.035 158)"
colors-dark:
  canvas: "oklch(20% 0.035 158)"
  surface: "oklch(25% 0.045 158)"
  ink: "oklch(94% 0.014 120)"
  ink-muted: "oklch(76% 0.025 120)"
  hairline: "oklch(33% 0.04 158)"
  accent: "oklch(80% 0.145 78)"
  accent-pressed: "oklch(74% 0.145 72)"
  on-accent: "oklch(20% 0.035 158)"
contrast:
  - [ink, canvas, 4.5]
  - [ink-muted, canvas, 4.5]
  - [ink, surface, 4.5]
  - [on-brand, brand, 4.5]
  - [on-accent, accent, 4.5]
  - [accent, canvas, 3]
  - [accent-pressed, canvas, 3]
  - [highlight, brand, 3]
  - [on-highlight, highlight, 4.5]
typography:
  display-xl: {fontFamily: "Bricolage Grotesque", fontSize: 88px, fontWeight: 700, lineHeight: 0.98, letterSpacing: -0.035em}
  display: {fontFamily: "Bricolage Grotesque", fontSize: 56px, fontWeight: 700, lineHeight: 1.02, letterSpacing: -0.03em}
  heading: {fontFamily: "Bricolage Grotesque", fontSize: 32px, fontWeight: 600, lineHeight: 1.15, letterSpacing: -0.015em}
  lead: {fontFamily: "Figtree", fontSize: 20px, fontWeight: 400, lineHeight: 1.5, letterSpacing: 0}
  body: {fontFamily: "Figtree", fontSize: 17px, fontWeight: 400, lineHeight: 1.6, letterSpacing: 0}
  label: {fontFamily: "Figtree", fontSize: 15px, fontWeight: 600, lineHeight: 1.2, letterSpacing: 0}
rounded: {md: 14px, lg: 24px, pill: 999px}
spacing: {xs: 8px, sm: 16px, md: 24px, lg: 40px, xl: 64px, 2xl: 104px, 3xl: 144px}
components:
  button-primary: {backgroundColor: "{colors.accent}", textColor: "{colors.on-accent}", typography: "{typography.label}", rounded: "{rounded.pill}", padding: "14px 26px", height: 48px}
  button-on-brand: {backgroundColor: "{colors.highlight}", textColor: "{colors.on-highlight}", typography: "{typography.label}", rounded: "{rounded.pill}", padding: "14px 26px", height: 48px}
  brand-band: {backgroundColor: "{colors.brand}", textColor: "{colors.on-brand}", rounded: "{rounded.lg}", padding: "104px 64px"}
---

# committed-forest

## Overview

One colour, committed. The forest green is not an accent here, it is the ground for a
third to a half of the page, which is what makes the brand recognisable at a glance. The
rest is bone, not cream, and the only warm note is an amber highlight that is allowed on
the green and nowhere else.

Key characteristics:

- The green carries whole bands, not buttons and borders.
- Amber appears only on green. On bone it fails contrast, so it is not used there.
- Large, confident display type, with the rest held quiet.

## Colors

The contrast checker is why the highlight is confined. Amber on bone measures about
1.7:1, far under the 3:1 floor for a control, so on the light ground the action colour
is the green itself. On the green band, amber measures above 6:1, and the band's own
button uses it.

The dark theme turns the ground to green and promotes amber to the action colour,
because on a dark ground it passes everywhere.

## Typography

Bricolage Grotesque for display, set large and tight. Figtree for reading and controls.
Two families with obviously different jobs.

## Layout

Generous: 104px between sections at desktop. Brand bands run full width with large
rounded corners inside the container. No two consecutive sections share a layout family.

## Elevation

Colour blocks, not shadows. A raised element changes tone.

## Shapes

Pills for buttons, 14px for media, 24px for the brand band. Nothing sharp.

## Components

Two primary buttons exist for two grounds, and they never appear on the same ground.

## Do and Do Not

- Do give the green at least one full-width band per screen height.
- Do use real photography with green or neutral tones.
- Do not put amber on bone. The checker will fail it, correctly.
- Do not add a second saturated colour.

## Responsive Behaviour

At 375 the display drops to 44px and bands lose their side radius to run edge to edge.

## Known Gaps

No dense UI components. This is a brand and campaign system.
