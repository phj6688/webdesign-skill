# Pre-flight checklist

Sources: taste-skill (MIT) for the pre-flight shape, impeccable (Apache-2.0) for the
floor. Restated and merged; see `NOTICE.md`.

Run every line before hand-over. If one line cannot be ticked honestly, the page is not
done. Fix it, then run the list again.

Each line carries a tag that says how it gets checked:

- `[lint]` the linter checks it. Run `scripts/slop_lint.py`, then trust the result.
- `[shot]` a screenshot shows it. Open the PNG and look.
- `[src]` read the source.
- `[brief]` confirm it against what you declared in step 1.

## Process

- [ ] `[brief]` The design read was stated in one line before any code.
- [ ] `[brief]` The visitor mode and the three dials were declared, with reasons.
- [ ] `[brief]` The system came from the project, an official package, or a committed
      token set. Not assembled from ad hoc values.
- [ ] `[brief]` On a redesign, the mode was detected and the audit was written first.
- [ ] `[src]` One design system in the whole project.
- [ ] `[src]` Every third-party import is in `package.json`.

## Evidence

- [ ] `[lint]` `slop_lint.py` exits 0, or every remaining finding carries a written
      suppression reason.
- [ ] `[shot]` Shots exist at 375, 768 and 1280, and each one was opened and read.
- [ ] `[shot]` Shots exist for both schemes, and the dark shots are a composed theme.
      A system declared dark-only, such as amber-terminal, shoots dark only.
- [ ] `[shot]` Nothing essential disappears under `--reduced-motion`.
- [ ] `[shot]` The browser console has no errors at any width.
- [ ] `[brief]` The critique was run, scored, and every P0 and P1 is fixed.

## Type

- [ ] `[lint]` The first family in every stack is not an over-used default.
- [ ] `[lint]` No body line height below 1.3.
- [ ] `[lint]` No body text below 12px, no functional text below 11px.
- [ ] `[lint]` No tracking tighter than -0.04em, no body tracking wider than 0.05em.
- [ ] `[shot]` Body measure between 65 and 75 characters at 1280.
- [ ] `[shot]` Heading and body separate clearly at every step.
- [ ] `[src]` Every literal font size lands on the declared ramp.
- [ ] `[src]` Any serif has a stated reason tied to this brand.
- [ ] `[shot]` Italic display words with descenders are not clipped.

## Colour

- [ ] `[lint]` No pure `#000000` or `#ffffff` as a surface or text colour.
- [ ] `[lint]` No values from the over-used warm premium palette.
- [ ] `[lint]` No gradient text.
- [ ] `[shot]` One accent, the same everywhere it appears.
- [ ] `[shot]` One theme from top to bottom.
- [ ] `[src]` Body text at 4.5:1, large text and controls at 3:1, measured, in both
      themes, including text over images.
- [ ] `[src]` Every colour comes from a token.

## Layout

- [ ] `[shot]` The hero fits the first viewport at 1280: headline at most two lines,
      subtext at most 20 words, primary action visible.
- [ ] `[shot]` Hero top padding is 6rem or less.
- [ ] `[shot]` The hero holds at most four text elements.
- [ ] `[shot]` Navigation is on one line at desktop and 80px tall or less.
- [ ] `[lint]` Eyebrows are within one per three sections.
- [ ] `[lint]` No section numbering, no scroll cue, no version label in the hero.
- [ ] `[shot]` No layout family repeats, and no more than two image-and-text splits run
      in a row.
- [ ] `[shot]` Bento grids have exactly as many cells as items, and varied backgrounds.
- [ ] `[lint]` No three identical feature cards as page structure, no nested cards.
- [ ] `[shot]` No split header with a floating explainer column.
- [ ] `[shot]` Lists longer than five items use a component that is not a plain list.
- [ ] `[shot]` Every multi-column layout collapses cleanly at 375.
- [ ] `[shot]` Nothing overflows horizontally at 375.
- [ ] `[lint]` No `h-screen` or `100vh` on a full-height section.
- [ ] `[shot]` More space above each heading than below it.
- [ ] `[src]` One radius system, written down, followed everywhere.

## Actions and forms

- [ ] `[shot]` One label per intent, used everywhere that intent appears.
- [ ] `[shot]` No button label wraps at desktop.
- [ ] `[shot]` Touch targets are at least 44 by 44 pixels at 375.
- [ ] `[src]` Every input has a visible label above it. No placeholder stands in for a
      label.
- [ ] `[src]` Error text sits below its input and is announced.
- [ ] `[src]` Every interactive element has hover, focus, active and disabled states.
- [ ] `[src]` Every async surface has loading, empty and error states.

## Content

- [ ] `[lint]` Zero em dashes, and no en dash used as a separator.
- [ ] `[lint]` No filler verbs, no placeholder names, no fake-precise numbers.
- [ ] `[lint]` No runs of middle-dot separators.
- [ ] `[brief]` Every visible string was re-read in the copy audit and rewritten where it
      was broken, unclear, or cute but wrong.
- [ ] `[shot]` Quotes are three lines or fewer and attributed with a name and a role.
- [ ] `[shot]` No decorative labels: no photo credits as ornament, no pills over images,
      no locale or weather strips, no version footers.

## Images and icons

- [ ] `[shot]` Every visual slot has a real, generated, or clearly labelled image.
- [ ] `[shot]` No fake product UI built from divs.
- [ ] `[lint]` Icons come from one library, not hand-rolled paths.
- [ ] `[shot]` No emoji or Unicode glyph stands in for an icon.
- [ ] `[shot]` The logo wall is logos only, below the hero, and correct in both themes.

## Motion

- [ ] `[lint]` Every animating file has a `prefers-reduced-motion` branch.
- [ ] `[lint]` No `addEventListener('scroll')`.
- [ ] `[src]` Every animation has a one-sentence reason.
- [ ] `[src]` No layout property animates. Filter, clip-path, mask or shadow animate
      only in the one authored moment.
- [ ] `[src]` Continuous values run through motion values, never component state.
- [ ] `[src]` Every effect that animates has real cleanup.
- [ ] `[shot]` At most one marquee.
- [ ] `[brief]` Motion claimed is motion shown: MOTION above 4 means the page moves.

## Performance and accessibility

- [ ] `[src]` Space is reserved for images, fonts and embeds, so nothing shifts.
- [ ] `[src]` Fonts are self-hosted or loaded through the framework, with a swap display.
- [ ] `[src]` Anything below the fold loads lazily, including any 3D scene.
- [ ] `[src]` z-index follows a documented scale.
- [ ] `[src]` One `h1`, and no skipped heading levels.
- [ ] `[src]` Keyboard reaches everything in a sensible order, with a visible themed
      focus ring.
- [ ] `[src]` Selection, caret, scrollbar and underline offset are themed from the
      palette.

## Hand-over

- [ ] `[src]` `DESIGN.md` was written from the built result.
- [ ] `[brief]` The reply lists any image slots still needing real assets.
- [ ] `[brief]` The reply names every suppressed linter finding and its reason.
