# NOTICE

This skill is a merge. It distills and restates rules from five upstream projects
into one workflow. The code in `skills/webdesign/scripts/` and the prose in
`skills/webdesign/` are original work under the MIT licence in `LICENSE`, except
where this file says otherwise.

Every upstream project below is credited as required by its licence. Rules were
restated, not copied wholesale. Numeric thresholds, banned-value lists and rule
names are kept faithful on purpose, because a paraphrased threshold is a useless
threshold.

## taste-skill

- Source: https://github.com/Leonxlnx/taste-skill
- Pinned at commit `ce26fc25c0e5e8cab638f883de62d9a86ee5e45b` (2026-09-26)
- Licence: MIT, Copyright (c) 2026 Leonxlnx. Full text: `licenses/MIT-taste-skill.txt`
- Derived here: the brief-inference step, the three dials, the AI-tell catalogue,
  the em-dash ban, the layout-discipline rules, the banned premium-consumer
  palette, the serif discipline, and the pre-flight checklist.

## impeccable

- Source: https://github.com/pbakaus/impeccable
- Read at commit `9d715cc4f5564a990ca8345abfdd5df6dc9b41c8` (2026-09-24), skill version 4.4.0
- Licence: Apache License 2.0, Copyright 2025 Paul Bakaus. Full text as shipped upstream:
  `licenses/APACHE-2.0-impeccable.txt`
- Derived here: the craft floor, the four visitor modes, the four colour
  strategies, the motion duration table, the rule names and numeric thresholds
  behind the linter, the overused-font list, the design-system document schema,
  and the Nielsen critique rubric.
- Upstream NOTICE states that its `ios.md` and `android.md` references derive
  from `ehmo/platform-design-skills` (MIT). Neither file is used here.

## awesome-design-md

- Source: https://github.com/VoltAgent/awesome-design-md
- Pinned at commit `f6961238d5cddcf8042a74a70fc400ec67181abb` (2026-09-21)
- Licence: MIT, Copyright (c) 2026 VoltAgent. Full text: `licenses/MIT-awesome-design-md.txt`
- Derived here: the `DESIGN.md` document schema in `references/systems.md`. No design
  system file is vendored. `scripts/fetch_system.sh` downloads one on request, at the
  pinned commit, into the user's project.
- Upstream disclaimer, carried here because it does not travel inside the individual
  files: the documents are extracted from public websites, the tokens represent
  publicly visible CSS values, and the maintainers claim no ownership of any site's
  visual identity. The licence covers the documents, not any brand's trademarks or
  trade dress, and not the proprietary typefaces the documents name.

## img2threejs

- Source: https://github.com/img2threejs/img2threejs
- Read at commit `6e60b5e22419464b4853e01ddb6c0e6f6659a733` (2026-09-06), version 2.0.0
- Licence: Apache License 2.0, Copyright 2026 hoainho. Full text as shipped upstream:
  `licenses/APACHE-2.0-img2threejs.txt`
- Derived here: the primitive-to-subject mapping, the camera and lighting
  conventions, the turntable rule, and the three.js version and import style, all
  in `references/three-d.md`. The full reconstruction pipeline is not reproduced.
  For a real object or character rebuild, use the upstream skill directly.

## playwright-cli

- Source: https://github.com/microsoft/playwright-cli, published as `@playwright/cli`
  (version 0.1.21 verified and pinned). Recent `playwright` releases from
  https://github.com/microsoft/playwright expose the same CLI as `playwright cli`, but
  without the emulation commands as of 1.63.0.
- Licence: Apache License 2.0. Canonical text: `licenses/APACHE-2.0.txt`
- Used as a tool, not vendored. No Playwright source is included here.
  `scripts/shoot.sh` runs the pinned CLI through `npx`.

## frontend-design (Anthropic)

- Source: https://github.com/anthropics/skills, `skills/frontend-design`
- Read at commit `33375500bcea98d610eb30ce10ac4e59b89c390d` (2026-09-24)
- Licence: Apache License 2.0. Full text as shipped upstream:
  `licenses/APACHE-2.0-frontend-design.txt`
- The upstream `impeccable` README states its own lineage starts from this skill. This
  merge keeps that lineage: the "spend your boldness in one place" and "review the plan
  against the brief" moves come from it.

## Changes made

Apache License 2.0, section 4(b), asks that modified files say so. Nothing upstream is
shipped as a copy. Every file in `skills/webdesign/references/` and `SKILL.md` restates
rules from the sources above in new words, merges them, and resolves the conflicts in
the table below. Each reference file names its sources in its first lines. The scripts
are original code.

## Where the sources disagreed

Merging five sources means choosing when two of them conflict. Each conflict below
names both positions, the rule this skill kept, and why.

| Topic | taste-skill | impeccable | Kept | Why |
|---|---|---|---|---|
| Em dash | banned outright, zero | flagged only at saturation (8 or more, about 1 per 500 characters) | taste: zero | "Use sparingly" is the phrasing that has never worked. Zero is checkable. It also matches the house writing rule. |
| Geist and Satoshi | recommended as the alternative to Inter | Geist on the over-used list | impeccable: Geist is over-used | The recommendation made it the next default. Satoshi stays allowed. |
| Display tracking | `tracking-tighter` as the display default, which is -0.05em in Tailwind | floor of -0.04em | impeccable: -0.04em floor | The default broke the floor. The linter enforces the floor. |
| Eyebrow above a heading | allowed, capped at one per three sections | banned outright, "no brief earns it back" | default against, with taste's cap as the enforced ceiling | A machine can count eyebrows, but it cannot tell a load-bearing label from decoration. The number it can check is the cap. |
| Serif display | very discouraged as a default | the reflex serifs are spent | both, combined | They agree in substance. A serif needs a reason tied to the brand. |
| Card radius | 12 to 16px for an all-soft system | 12 to 16px for cards | agreed | No conflict. |
| Emoji as icons | discouraged, with an override for playful briefs | Unicode and emoji are not an icon system | impeccable: not an icon system | A playful brief can still use a drawn icon set with a playful style. |
| Lucide icons | discouraged as the default set | not addressed | taste | No conflict, only a gap. |
| Icon source | never hand-roll SVG icons | icons are drawn, one stroke and weight, authored SVG allowed | taste: no hand-rolled paths | A model's hand-drawn paths are exactly where stroke and weight drift. One library holds them constant. |
| Animated properties | transform and opacity only | reach past them: blur, backdrop-filter, clip-path, mask, shadow | merged | Never a layout property. Transform and opacity by default. Filter, clip-path, mask and shadow for the one authored moment, because they repaint but do not reflow. |
| Reduced motion | mandatory above MOTION 3 | every animation needs a reduced-motion path | impeccable: every animation | A low dial still moves something, and vestibular triggers do not check the dial. |
