# Critique

Sources: impeccable (Apache-2.0) for the rubric, the audit, the personas and the
working-memory rule; frontend-design (Apache-2.0) for the last subtraction pass.
Restated and merged; see `NOTICE.md`.

A critique that says "looks clean, maybe tighten the spacing" is not a critique. This
one produces a score, a severity for every issue, and a list of fixes in priority order.

## Run it with fresh eyes

Critique from the screenshots, not from the code you just wrote. The code tells you what
you meant. The screenshot tells you what you made.

When the session can spawn a subagent, give the critique to one that has not seen the
build conversation. Hand it the screenshots, the brief and this file, and nothing else.
The author's context is exactly the thing that hides the problems. When that is not
possible, say so in the first line of the critique:

> Degraded: single-context critique, the author reviewed their own build.

Run the linter separately and read its output after the visual critique, not before.
Deterministic findings still anchor judgment, and a reviewer who reads "0 errors" first
looks less hard.

## Score the heuristics

Score each of Nielsen's ten heuristics from 0 to 4.

| Score | Meaning |
|---|---|
| 0 | absent, or actively violated |
| 1 | present but broken in common use |
| 2 | works for the careful visitor |
| 3 | works for most visitors |
| 4 | works for everyone, including the edge cases |

1. Visibility of system status
2. Match between the system and the real world
3. User control and freedom
4. Consistency and standards
5. Error prevention
6. Recognition rather than recall
7. Flexibility and efficiency of use
8. Aesthetic and minimalist design
9. Help users recognise, diagnose and recover from errors
10. Help and documentation

Total out of 40.

| Total | Band |
|---|---|
| 36 to 40 | excellent |
| 28 to 35 | good |
| 20 to 27 | acceptable |
| 12 to 19 | poor |
| 0 to 11 | critical |

On a Persuade or Experience page, heuristics 7 and 10 can be not applicable. Mark them
`n/a`, renormalise to the remaining maximum, and read the band as a percentage: 90, 70,
50 and 30 percent.

Most real interfaces score 20 to 32. A self-review that lands at 38 on a first build is
a sign the review was not hard enough, not a sign the build is excellent.

## Severity for every issue

| Level | Meaning |
|---|---|
| P0 | blocks the task, or breaks for a class of visitor |
| P1 | a major problem most visitors hit |
| P2 | a minor problem, noticeable, with a workaround |
| P3 | polish |

Tie-break: would a visitor contact support about it? If yes, it is at least P1.

Fix every P0 and P1 before hand-over. List the P2 and P3 items; do not silently drop
them.

## Working memory

People hold about four things in mind at once. Use that as a hard number.

- One primary action and at most two secondary actions in a view.
- At most five top-level navigation items.
- At most four sibling choices per level in a documentation sidebar.

Four or fewer is manageable. Five to seven is pushing it. Eight or more is overload.

## Five visitors

Walk the page as each of them. Each finds different problems.

- **Alex, the impatient expert.** Wants the fastest path. Finds every extra click, every
  confirmation that was not needed, every missing keyboard shortcut.
- **Jordan, the first-timer.** Knows nothing. Finds jargon, unexplained icons, and any
  step that assumes knowledge the page never gave.
- **Sam, who uses assistive technology.** Screen reader, keyboard only, or zoomed to
  200%. Finds missing labels, broken focus order, contrast failures and content that
  only exists visually.
- **Riley, the stress tester.** Pastes a 300-character name, submits an empty form, hits
  back mid-flow, opens it in two tabs. Finds every unhandled state.
- **Casey, distracted on a phone.** One thumb, bad signal, interrupted twice. Finds tiny
  targets, lost progress and anything that needs two hands.

## The audit

Separately from the heuristic score, rate five technical dimensions from 0 to 4.

1. **Accessibility.** Contrast, keyboard, labels, focus order, reduced motion, touch
   targets of at least 44 by 44 pixels.
2. **Performance.** Largest contentful paint under 2.5s, interaction to next paint under
   200ms, cumulative layout shift under 0.1. Space is reserved for images, fonts and
   embeds. Heavy work stays off the main thread. Anything below the fold loads lazily.
3. **Theming.** Every colour comes from a token. Dark mode is composed, not inverted.
   Browser surfaces are themed: selection, caret, scrollbar, focus ring.
4. **Responsive.** It works at 375, 768 and 1280, and every multi-column layout declares
   its collapse.
5. **Implementation integrity.** No selector specificity fights. No `z-index: 50` spam;
   z-index is a documented scale. No layout maths in flexbox percentages where a grid
   would do it. Motion lives in isolated leaf components with real cleanup.

Total out of 20.

| Total | Band |
|---|---|
| 18 to 20 | excellent |
| 14 to 17 | good |
| 10 to 13 | acceptable |
| 6 to 9 | poor |
| 0 to 5 | critical |

## Write the critique like this

```
Design read: <the one line from step 1>
Heuristics: 27/40 (acceptable)   Audit: 14/20 (good)

P0  375px: the primary action is below the fold. Hero headline wraps to 4 lines.
    Fix: drop the display size one step and cut the subtext to 18 words.
P1  Dark mode: the accent fails 3:1 on the dark surface (measured 2.4:1).
    Fix: raise the accent lightness in the dark token to 70%.
P1  Three eyebrows across five sections, cap is two.
    Fix: remove the eyebrows on sections 2 and 4.
P2  ...
```

Every issue names the breakpoint or state where it appears, the evidence, and one fix.
An issue without a fix is a complaint, not a critique.

## Spend the boldness in one place

The last pass is subtraction. Let one element be the memorable thing and keep everything
around it quiet. Before hand-over, find one decorative thing that does not serve the
brief and remove it.
