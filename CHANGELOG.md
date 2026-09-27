# Changelog

All notable changes to this skill are recorded here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2026-09-27

### Fixed

- CI runs on release tags, and a tag can be `v<version>` or `<name>--v<version>`.
- Step 5 in `SKILL.md` adds `--console`, which the console check in the checklist needs.
- A malformed `contrast` value makes `check_contrast.py` exit 1 with a clear message on
  both parser paths. Both paths also match numeric token names whether or not they are
  quoted, and resolve references such as `{colors.50}`.
- The em dash rule's import and `content:` exclusions now apply only inside a string
  literal, never in markup text or a copy attribute.
- The placeholder rule flags Nexus at either end of a text run and at a sentence end.
- `slop_lint.py` is now 1.1.1, because two of its rules now report more.
- `SKILL.md` now says that each `scripts/...` and `systems/...` path is relative to the
  skill directory.
- The `landing-page` eval grader accepts a `100vh` fallback only when the same property
  is redeclared with a dynamic unit.

## [0.1.0] - 2026-09-27

### Added

- One merged rule set for web design and UX/UI, distilled from taste-skill,
  impeccable, playwright-cli, awesome-design-md and img2threejs, with the last
  subtraction pass from frontend-design. `NOTICE.md` names each source, the commit
  read, its licence and what came from it, and its conflicts table records every
  point where two sources disagreed and which rule was kept.
- `scripts/slop_lint.py` 1.1.0, a deterministic source linter with 26 rules in
  three severities, inline and file-level suppression, and JSON output. Standard
  library only. It names every file it skips and exits 1 when a file you named is
  skipped.
- `scripts/check_contrast.py`, which measures the colour pairs a `DESIGN.md`
  declares against WCAG floors. It reads hex, rgb and OKLCH, composites
  translucent colours over their ground, resolves token references, checks the
  dark map with the light map as fallback, and flags OKLCH values outside the
  sRGB gamut. Both of its parser paths agree on all 74 reference systems.
- `scripts/shoot.sh`, a headless capture script on a pinned
  `@playwright/cli@0.1.21`. One PNG per viewport, `--scheme light|dark|both` and
  `--reduced-motion` through real media emulation, `file://` support, and a
  failure on any HTTP status of 400 or above. Every file is checked for the PNG
  signature and a minimum size. Exit status 3 means the environment cannot take
  screenshots at all, such as a sandbox with no npm registry, so the agent reports
  that instead of trying other browsers.
- `scripts/fetch_system.sh`, which downloads one of 74 reference design systems
  at a pinned commit, from an allowlist.
- Four original design systems under `systems/`: restrained-product,
  editorial-reading, committed-forest and amber-terminal. Every declared colour
  pair passes its floor.
- Nine references: brief, tokens, tells, systems, lint, verify, critique, 3D and
  the pre-flight checklist.
- Two behavioural eval cases under `evals/` for `claude plugin eval`, each run
  with and without the skill.
- `verify.sh`, the repo gate, with a `--full` tier that proves the capture path
  and the scheme emulation against a local server.
- GitHub Actions CI with a single required check named `CI passed`. The
  contrast suite runs twice, once with PyYAML and once on the stdlib parser.
