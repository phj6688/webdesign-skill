# webdesign

One Claude Code skill for web design and UX/UI work. It picks design tokens
first, measures the palette, builds against a named craft floor, lints the source
for the design tells that mark generated work, then screenshots every breakpoint
in both themes and looks at the result.

## Why one skill and not five

Five good tools already cover parts of this job. Loading all five costs context,
and they disagree. One bans the em dash outright, another flags it only when it
piles up. One recommends a typeface the other lists as over-used. A model that
reads all five picks a rule at random.

This repo merges them into one rule set with one workflow. Where two sources
disagreed, one rule won, and the table at the end of `NOTICE.md` records both
positions and the reason. Numeric thresholds and banned-value lists are kept
exact, because a paraphrased threshold gates nothing.

The spine is short. Pick tokens. Measure them. Build. Run the linter. Shoot at
375, 768 and 1280 in light and dark. Look at the images. Fix what you see.

## What it merges

| Upstream project | What came from it | Licence |
| --- | --- | --- |
| [Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill) (90,359 stars) | Brief inference, the three dials, the AI-tell catalogue, layout discipline, the em dash ban | MIT |
| [pbakaus/impeccable](https://github.com/pbakaus/impeccable) (71,550 stars) | The craft floor, visitor modes, colour strategies, the motion table, the linter thresholds, the critique rubric | Apache-2.0 |
| [microsoft/playwright-cli](https://github.com/microsoft/playwright-cli) (13,595 stars) | The screenshot, scheme emulation and verify loop | Apache-2.0 |
| [VoltAgent/awesome-design-md](https://github.com/VoltAgent/awesome-design-md) (118,148 stars) | The design-system document schema and the pinned reference-system fetch | MIT |
| [img2threejs/img2threejs](https://github.com/img2threejs/img2threejs) (16,889 stars) | The 3D doctrine: primitive mapping, left and right, camera and lighting | Apache-2.0 |

## What is in the skill

| Path | What it does |
| --- | --- |
| `skills/webdesign/SKILL.md` | The loop, the hard floor and the bans |
| `skills/webdesign/references/` | Brief, tokens, tells, systems, lint, verify, critique, 3D, checklist |
| `skills/webdesign/systems/` | Four original design systems, each contrast-checked |
| `scripts/slop_lint.py` | Deterministic source linter, 26 rules, standard library only |
| `scripts/check_contrast.py` | Measures a `DESIGN.md` palette against WCAG, OKLCH aware |
| `scripts/shoot.sh` | Headless screenshots per viewport, per colour scheme |
| `scripts/fetch_system.sh` | Pulls one of 74 reference systems at a pinned commit |

The `scripts/` paths are under `skills/webdesign/`.

## Requirements

- Python 3.10 or newer, standard library only, for the linter and the contrast checker.
  PyYAML is optional; without it the checker uses its own parser.
- Bash and curl, for `fetch_system.sh`.
- Node with `npx`, for `shoot.sh`. It runs `@playwright/cli@0.1.21` and downloads a
  chromium build on first use.

## Install

1. Add the marketplace:

   ```text
   /plugin marketplace add phj6688/claude-marketplace
   ```

2. Install the plugin:

   ```text
   /plugin install webdesign@phj
   ```

3. Start a new session. Claude loads the skill when you ask for UI work.

## Usage

Ask for the work in plain words, for example "build a pricing page" or "this
dashboard looks generic, fix it". The skill also runs its tools directly:

```bash
S=skills/webdesign/scripts
python3 $S/slop_lint.py src/                 # exit 2 on any error or warning
python3 $S/check_contrast.py DESIGN.md       # exit 2 on any failing pair
$S/shoot.sh http://localhost:3000 --scheme both --console
$S/fetch_system.sh --list
```

`shoot.sh` writes one PNG per viewport and scheme. The default viewports are
375x812, 768x1024 and 1280x800. `--scheme both` shoots light and dark through
real media emulation. `--reduced-motion` emulates reduced motion. The script
exits non-zero when a PNG is missing, is not a PNG, or is under 1000 bytes. A
clean exit from a browser is not proof of a render, so open the images.

## The verify gate

`./verify.sh` runs the whole gate and exits non-zero on the first failure:

1. `py_compile` on every Python file in the skill.
2. The linter fixture suite: every rule fires on its bad fixture and stays
   quiet on its good one.
3. The contrast suite: WCAG reference values, the four archetypes, error paths.
4. Every JSON manifest parses, and `plugin.json` names a skills path that exists.
5. Every `SKILL.md` carries frontmatter with a name and a description.
6. The dash ban: no em dash and no en dash in any `.md`, `.sh` or `.py` file.
7. `ruff check .` when ruff is installed.
8. `shellcheck` on every shell script when shellcheck is installed.
9. Every relative markdown link in the skill resolves to a real file.

`./verify.sh --full` adds a real browser tier. It serves a temporary page, shoots
it at three widths, then shoots it again in both schemes and fails if the light
and dark files are identical. Run the full tier before you tag a release.

## Playwright on a headless host

These three failures were reproduced on a host with no display and no system
Chrome. `shoot.sh` handles all three.

- Pass `--browser=chromium` to `open`. Without it the CLI looks for Chrome at
  `/opt/google/chrome/chrome` and fails.
- Never pass `--headed`. There is no X server. Headless is already the default.
- Avoid `playwright-cli list`. It watches the whole browser cache, and a low
  `fs.inotify.max_user_instances` makes it fail with `ENOSPC`. Raising that
  limit needs root. `open`, `resize`, `screenshot`, `console` and `close` work
  without it.

A first run downloads the chromium build into `~/.cache/ms-playwright`. That
takes about 300 MiB and needs no root. On an unsupported distribution the CLI
prints a `BEWARE` line and uses the Ubuntu build. That line is noise.

## Licence and attribution

This repo is MIT licensed. See `LICENSE`.

`NOTICE.md` credits every upstream project, names the commit that was read,
records what was taken, and lists every conflict between sources. Upstream
licence texts live in `licenses/`. Read `NOTICE.md` before you redistribute.

The reference systems that `fetch_system.sh` downloads describe real brands'
public styling. Use them for technique. Do not ship a page a visitor could
mistake for that brand, and do not use a proprietary typeface a file names.
