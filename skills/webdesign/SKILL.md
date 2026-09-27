---
name: webdesign
description: Use when designing or building any web interface, landing page, portfolio, marketing site, app shell, or component, when the user asks for a redesign, a design system, or a UX and UI review, or when a page looks generic and nobody can say why. Picks tokens before code, refuses the known AI design tells, lints the source for them, and screenshots every breakpoint before calling the work done.
---

# webdesign: pages that survive being looked at

A generated page usually fails in ways the author cannot see. The code compiles, the
layout is valid, the colours pass a glance, and the result still reads as machine
output. The reason is always the same: the model picked a default instead of making a
choice, then never looked at what it built.

So this skill has two spines, and both are mechanical.

**Tokens before code.** Decide the type, the colour, the spacing and the radius as
named values first. A page assembled from ad hoc values cannot be corrected later,
because there is nothing to correct it against.

**Evidence before "done".** Three gates stand between a build and a hand-over. A
contrast check measures the palette before anything is built on it. A deterministic
linter reads the source for the known tells. A screenshot run captures every breakpoint
in both themes, so somebody, model or human, actually looks. None of the three can be
satisfied by an opinion.

**The one unbreakable rule: never hand over a page you have not screenshotted and
looked at.** A passing build is not a look. A green linter is not a look. Run
`${CLAUDE_SKILL_DIR}/scripts/shoot.sh` and read the images.

One environment cannot satisfy it: a sandbox or an offline host where no browser can run.
`shoot.sh` says so with exit status 3. When it does, stop there. Do not try another
browser or a workaround. Put `Not screenshotted: <the reason shoot.sh gave>` in the first
line of the hand-over, list what the shots would have checked, and never write that the
page was looked at.

## The loop

The scripts live in `${CLAUDE_SKILL_DIR}/scripts/`. Every `scripts/...` path in the
reference files is relative to that directory, not to the project you are working in.

Run these in order. Do not skip step 1, and do not reorder 4 and 5 before 3.

1. **Read the brief.** State the design read in one line before any code. See
   [references/brief.md](references/brief.md).
2. **Pick the system.** Either an official package, a project design system already on
   disk, or a token set you commit to now, as the frontmatter of `DESIGN.md`. Four
   starting points live in `systems/`, and
   `${CLAUDE_SKILL_DIR}/scripts/fetch_system.sh` pulls a reference system modelled on a
   real site. Measure the palette with
   `python3 ${CLAUDE_SKILL_DIR}/scripts/check_contrast.py DESIGN.md` before building on
   it. See [references/systems.md](references/systems.md) and
   [references/tokens.md](references/tokens.md).
3. **Build.** Hold to the floor below and the catalogue in
   [references/tells.md](references/tells.md).
4. **Lint.** `python3 ${CLAUDE_SKILL_DIR}/scripts/slop_lint.py <src>`. Fix every error
   and warning, or suppress one with a written reason. See
   [references/lint.md](references/lint.md).
5. **Shoot and look.** `${CLAUDE_SKILL_DIR}/scripts/shoot.sh <url> --scheme both` at
   375, 768 and 1280, in light and dark. Open and read every PNG. See
   [references/verify.md](references/verify.md).
6. **Critique.** Score the result against the rubric in
   [references/critique.md](references/critique.md). Fix every P0 and P1.
7. **Document.** Finish `DESIGN.md` from the built result: correct any token the build
   changed, then write the prose sections. When the user asked for a single file, the
   tokens ship as custom properties on `:root` in that file; remove the working
   `DESIGN.md` from step 2 unless the user wants it kept. See
   [references/systems.md](references/systems.md).

Steps 4, 5 and 6 are a loop, not a line. A finding sends you back to 3.

## Step 1 is not optional

Most bad output comes from skipping straight to an aesthetic. Before any code, say:

> Reading this as a `<page kind>` for `<audience>`, in a `<vibe>` language, built on
> `<system or token set>`.

Then pick the visitor mode, because it governs every later decision:

| Mode | The visitor is there to | Typical surface |
|---|---|---|
| Persuade | decide and act | landing, pricing, campaign |
| Operate | complete a task | app UI, dashboard, editor, settings |
| Read | understand something | docs, article, changelog |
| Experience | be inside the work | portfolio, gallery, showcase |

Pick the mode from the surface, not from the product. A developer tool's landing page
is still Persuade. A fashion house's documentation is still Read.

If the read genuinely forks, ask exactly one question. Never ask a list. If you can
infer it, do not ask at all.

## The hard floor

These are measured on the built result, not on intentions. Every one of them is
checkable, and most of them the linter checks for you.

**Type.** Body text at 16px by default. Prose measure 65 to 75 characters. Line height
1.5 to 1.7 for body, never below 1.3. Letter spacing never tighter than -0.04em.
Body never below 12px, and functional text (links, buttons, labels, table cells) never
below 11px. Display type tops out around 6rem.

**Colour.** Body text at 4.5:1 contrast or better. Large text and every control, icon
and focus ring at 3:1 or better. One accent, used on the whole page. No pure `#000000`
and no pure `#ffffff` as a surface or a text colour. Declare new palettes in OKLCH,
because lightness and chroma then move predictably.

**Space.** A 4px base gives the middle steps an 8px-only scale misses. More space above
a heading than below it. Tight inside a group, generous between groups. At least 16px
of horizontal padding on body text, and 24 to 32px is better.

**Depth.** A shadow carries an offset and a blur. A zero-offset coloured halo is
decoration, not depth. Pick a border or a shadow for an edge, not both.

**Motion.** One authored moment per page. 100 to 150ms for feedback, 150 to 300ms for a
state change, 300 to 500ms for a layout or overlay change, 500 to 800ms for one
deliberate entrance. Exit faster than you enter. `cubic-bezier(0.16, 1, 0.3, 1)` is the
confident arrival curve. Every animation needs a `prefers-reduced-motion` path with a
real alternative, and a global `0.01ms` kill is not an alternative.

**States.** Hover, focus, active, disabled, loading, empty and error, on every
interactive thing. A page that only has its successful state is half built.

**Browser surfaces.** Theme the text selection, the caret, the focus ring, the
scrollbar and the underline offset from the palette. This is the set models skip most
reliably, and skipping it is why a page feels unfinished at the edges.

**Content.** Every visible string is design content. Re-read all of them before you
ship. See the copy audit in [references/tells.md](references/tells.md).

## The bans

A default is overridable by an explicit brief. A ban is not. The full catalogue lives
in [references/tells.md](references/tells.md); these are the ones worth repeating here.

- **No em dash, anywhere visible.** Not in a headline, a label, a button, a caption, a
  quote or body copy. Use a period, a comma, a colon or parentheses. The en dash is
  banned as a separator too. Ranges take a plain hyphen. This is the single most
  reliable tell, and "use sparingly" has never worked, so the rule is zero.
- **No eyebrow above a heading by default.** The small uppercase label over a section
  title is a template reflex; the headline alone is enough. The linter fails a page
  with more than one per three sections. That number is a ceiling, not an allowance.
- **No enumerated section labels** (`01 / 02 / 03`, `Stage 1`, `Phase 02`). An ordered
  list of real steps inside a section is content, not a label; let an `<ol>` number it.
- **No scroll cue.** The visitor is looking at the hero. They know what scrolling is.
- **No drawn illustration in place of a photograph.** A hand-built SVG of the product,
  a dial or a map reads as a placeholder, because it is one. Generate the image, use a
  real one, or leave a labelled slot such as `<!-- TODO: hero photo, 1600x1200 -->` and
  list every open slot in the reply. A simple geometric brand mark is fine.
- **No fake product UI.** A dashboard, terminal or task list assembled from styled
  `div`s is the loudest tell there is. Use a real screenshot, a real component, or a
  generated image.
- **No gradient text.** No glass or blur as pure decoration. No neon glow by default.
- **No hand-rolled SVG icons.** Icons come from one library, at one stroke weight.
  Emoji is not an icon system.
- **No identical card grid as page structure.** Nested cards are always wrong.
- **No `h-screen` on a hero.** Use `min-h-[100dvh]`, because the mobile address bar
  moves and `100vh` jumps.
- **No `addEventListener('scroll')`.** Use `useScroll`, `ScrollTrigger`,
  `IntersectionObserver` or `animation-timeline`.

## When the project already has a system

A house design system beats everything in this skill. If the repo carries a
`DESIGN.md`, a token file, a theme config or a documented palette, read it first and
build inside it. Report a conflict with the floor above; do not silently resolve it
your way.

The same holds for an official package. If the brief reads as Material, Fluent, Carbon,
Polaris, Primer, GOV.UK or USWDS, install the real package and use it. Do not hand-roll
its CSS, and do not import its tokens and then override most of them. One system per
project.

## What this skill does not cover

It covers interfaces. It does not cover data tables (use TanStack Table or AG Grid),
code editors (use Monaco or CodeMirror with their own theming), native mobile (use the
Apple or Material guidelines directly), or realtime collaboration surfaces. When the
brief is one of those, say so, name the right tool, and apply only the parts of this
skill that reach the surrounding pages.

For a 3D hero built from a reference image, see
[references/three-d.md](references/three-d.md). For a full object or character
reconstruction, that reference points at the upstream tool instead, because the job is
a pipeline and not a page.

## Before you say it is done

Run the checklist in [references/checklist.md](references/checklist.md). It is
mechanical on purpose. If one line cannot be ticked honestly, the page is not done.

The repo gate is `./verify.sh` at the root of this skill's repository. It runs the
linter fixtures, the manifest checks and the dash ban, and it exits non-zero on the
first failure.
