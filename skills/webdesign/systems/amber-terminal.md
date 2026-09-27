---
name: amber-terminal
description: The house system. A warm near-black ground, one amber accent, burnt-orange headings and warm-bone text, in the register of a vintage terminal that reads as a serious operator tool rather than neon. JetBrains Mono for labels, code and chrome, IBM Plex Sans for prose and tables. Dark only by design.
modes: [operate, read]
dials: {variance: 4, motion: 3, density: 7}
colors:
  canvas: "#15120b"
  surface: "#1f1a10"
  surface-elevated: "#2a2316"
  ink: "#ece0c8"
  ink-muted: "#b3a68c"
  heading: "#c9772b"
  hairline: "#3a3121"
  accent: "#f0a82a"
  accent-pressed: "#d8921c"
  on-accent: "#15120b"
  success: "#8fb35a"
  error: "#e0664a"
contrast:
  - [ink, canvas, 4.5]
  - [ink-muted, canvas, 4.5]
  - [ink, surface, 4.5]
  - [ink-muted, surface, 4.5]
  - [ink, surface-elevated, 4.5]
  - [heading, canvas, 3]
  - [on-accent, accent, 4.5]
  - [accent, canvas, 3]
  - [accent-pressed, canvas, 3]
  - [success, canvas, 3]
  - [error, canvas, 3]
typography:
  display: {fontFamily: "IBM Plex Sans", fontSize: 40px, fontWeight: 600, lineHeight: 1.1, letterSpacing: -0.02em}
  heading: {fontFamily: "IBM Plex Sans", fontSize: 24px, fontWeight: 600, lineHeight: 1.25, letterSpacing: -0.01em}
  body: {fontFamily: "IBM Plex Sans", fontSize: 16px, fontWeight: 400, lineHeight: 1.6, letterSpacing: 0}
  table: {fontFamily: "IBM Plex Sans", fontSize: 14px, fontWeight: 400, lineHeight: 1.45, letterSpacing: 0, fontFeature: tnum}
  label: {fontFamily: "JetBrains Mono", fontSize: 13px, fontWeight: 500, lineHeight: 1.3, letterSpacing: 0}
  code: {fontFamily: "JetBrains Mono", fontSize: 14px, fontWeight: 400, lineHeight: 1.6, letterSpacing: 0}
rounded: {sm: 2px, md: 4px}
spacing: {xs: 4px, sm: 8px, md: 16px, lg: 24px, xl: 40px, 2xl: 64px}
components:
  button-primary: {backgroundColor: "{colors.accent}", textColor: "{colors.on-accent}", typography: "{typography.label}", rounded: "{rounded.md}", padding: "10px 16px", height: 44px}
  button-ghost: {backgroundColor: "{colors.surface}", textColor: "{colors.ink}", typography: "{typography.label}", rounded: "{rounded.md}", padding: "10px 16px", height: 44px}
  card: {backgroundColor: "{colors.surface}", textColor: "{colors.ink}", rounded: "{rounded.md}", padding: "16px"}
  input: {backgroundColor: "{colors.canvas}", textColor: "{colors.ink}", typography: "{typography.body}", rounded: "{rounded.md}", padding: "10px 12px", height: 44px}
---

# amber-terminal

## Overview

The documented house system for this homelab's tools. It is a dark, dense operator
register: warm near-black, one amber accent, burnt-orange headings, warm-bone text. It
reads as a serious instrument, which is the point. It replaces an older matrix-green
theme.

A house system beats every rule in this skill. Where it overrides a default the skill
warns about, the override is deliberate:

- It is dark only. The skill asks for a light and a dark theme and treats identical shots
  as a finding. The house rule is dark mode always, not light only, so a dark-only tool
  is compliant: shoot it with `--scheme dark`.
- JetBrains Mono carries labels and interface chrome, not only code and data. That is a
  stated role in the house system, which is the difference between a choice and the
  monospace costume the skill warns about.

## Colors

Hex values, exactly as the house defines them. Every text pair clears 4.5:1 and every
control clears 3:1; the `contrast` list is measured by `scripts/check_contrast.py`.
Components use CSS custom properties generated from these tokens. No component carries a
hardcoded hex value.

## Typography

IBM Plex Sans for prose and tables, with tabular numerals in tables. JetBrains Mono for
labels, code and interface chrome. Body at 16px, 1.6 line height.

## Layout

Dense by design: a 4px base and tight spacing. Mobile-first, with bottom navigation on
phones and 44px touch targets everywhere.

## Elevation

Tonal steps: canvas, then surface, then surface-elevated. No drop shadows on dark.

## Shapes

Near-square: 2px and 4px only. No pills.

## Components

Cards carry `contain: layout style`, because they repeat inside live-updating views. Live
values update text content in place, never by replacing markup, and a renderer redraws at
most once per second.

## Do and Do Not

- Do reserve amber for the one thing to act on.
- Do use burnt orange for headings only, never for body text.
- Do not reintroduce the old matrix green.
- Do not add a light theme without a decision from the operator.

## Responsive Behaviour

Test at 375, 768 and 1280. Bottom navigation below 768px, side navigation above it.

## Known Gaps

No light theme, by decision. No marketing components.
