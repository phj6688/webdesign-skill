# Shoot and look

Original. The browser commands are those of playwright-cli (Apache-2.0), verified on a
headless host; see `NOTICE.md`.

A screenshot you did not open proves nothing. A screenshot you opened at one width proves
one width. This step exists so that somebody actually looks at every breakpoint.

## The command

```
scripts/shoot.sh <url> [--out DIR] [--viewports 375x812,768x1024,1280x800]
                 [--label NAME] [--console] [--full-page|--no-full-page]
                 [--scheme light|dark|both] [--reduced-motion]
```

It writes `<out>/<label>-<w>x<h>.png` for each viewport, defaulting to `./shots` and the
three house breakpoints: 375, 768 and 1280. With `--console` it also saves the browser
console per viewport and reports any errors. With `--scheme` or `--reduced-motion` the
scheme and a `-reduced` tag go into the file name, for example
`home-dark-reduced-375x812.png`.

It fails, with a non-zero exit, when a PNG is missing, is not a PNG, or is suspiciously
small, and when the page answers with an HTTP status of 400 or above. A blank render or
a 404 caught here is cheaper than one caught by the user. The PNG of an error page is
kept, as a record of what the browser saw.

| Exit | Meaning | What to do |
|---|---|---|
| 0 | every shot is a real PNG | open and read every one |
| 1 | a shot failed: bad URL, HTTP error, blank render | fix the page or the URL, then shoot again |
| 2 | bad command line | fix the command |
| 3 | this environment cannot take screenshots | stop, and report the page as not screenshotted |

Exit 3 means the browser tool cannot be downloaded or started here: an offline host, a
sandbox with no registry access, or a missing `npx`. Trying other browsers does not fix
that. It only spends the session. Say so once and move on.

It uses the project's own Playwright only when that copy is 1.62 or newer and its `cli`
has every command the run needs; releases before 1.62 print no HTTP status, so a 404
would pass. Otherwise it runs the pinned `@playwright/cli@0.1.21` through `npx`. It
prints which runner it picked and why.

## Then read every image

Open each PNG with the image reader. Do not summarise a screenshot you have not opened.
For each breakpoint, check:

- **375.** Does every multi-column layout collapse to one column? Does anything overflow
  horizontally? Is the primary action visible without scrolling? Are touch targets at
  least 44px? Does the navigation collapse cleanly?
- **768.** Is this a real tablet layout, or a stretched phone layout? Are line lengths
  still under 75 characters?
- **1280.** Does the hero fit the first viewport? Is the headline two lines or fewer? Is
  the navigation on one line? Does any button label wrap?

Then check the page as a whole, at the widest shot:

- Squint at it. Is there one clear focal point, or several competing ones?
- Count the eyebrows against the sections.
- Count the layout families. Does any repeat?
- Is the accent the same colour everywhere it appears?
- Is there one theme, top to bottom?
- Is there more space above each heading than below it?

A finding sends you back to the build. Re-shoot after every fix, and read the new images.
Comparing a new shot against an old one from the same build measures nothing.

## Dark mode and reduced motion

Shoot both themes. The browser emulates the media query, so the page's own
`prefers-color-scheme` rules paint, not a query-string imitation of them:

```
scripts/shoot.sh http://localhost:3000 --scheme both
```

That produces six shots, light and dark at each of the three widths. Read them in pairs.
What pops in light must pop in dark. A dark shot that looks identical to the light one
means the page has no dark theme, which is a finding, not a pass. The one exception is a
system declared dark-only in its `DESIGN.md`, such as the house `amber-terminal`: shoot it
with `--scheme dark` and treat an identical light shot as expected.

A page that switches theme with a toggle and ignores the media query will render light
in both. Check for a `data-theme` or class toggle in the source before you conclude it
has no dark mode, and drive the toggle by hand if it does.

For reduced motion, shoot once with `--reduced-motion` and confirm nothing essential
disappears: no content hidden behind an entrance that no longer runs. Then confirm in
the source that every animation has a `prefers-reduced-motion` branch. The linter flags
a file that animates without one.

## Running Playwright on a headless Linux host

These three failures were reproduced on a real headless host with no system Chrome. The
capture script already works around all three. Know them when you drive Playwright by
hand.

1. **A bare `open` looks for real Google Chrome and dies** with
   `Chromium distribution 'chrome' is not found at /opt/google/chrome/chrome`. Pass
   `--browser=chromium` every time, so the managed build is used.
2. **`--headed` dies without a display** with `Missing X server or $DISPLAY`. Headless
   is the default. Never pass `--headed` on a server.
3. **`playwright-cli list` can fail** with
   `ENOSPC: System limit for number of file watchers reached`. It watches the whole
   browser cache, and a host with a low `fs.inotify.max_user_instances` runs out. Raising
   the limit needs root. `open`, `resize`, `screenshot`, `console` and `close` are not
   affected, so avoid `list`.

On a distribution Playwright does not officially support, it prints
`BEWARE: your OS is not officially supported by Playwright` and uses an Ubuntu build.
That warning is harmless.

If no browser is installed yet, `npx --yes @playwright/cli@0.1.21 install-browser chromium`
downloads one into the user cache. It needs no root and about 300 MB.

## Driving the browser by hand

For an interaction the capture script does not cover, use the agent CLI directly. It
writes page state to disk instead of streaming it into context, which keeps it cheap.

```
npx --yes @playwright/cli@0.1.21 -s=check open http://localhost:3000 --browser=chromium
npx --yes @playwright/cli@0.1.21 -s=check resize 375 812
npx --yes @playwright/cli@0.1.21 -s=check snapshot
npx --yes @playwright/cli@0.1.21 -s=check click e12
npx --yes @playwright/cli@0.1.21 -s=check screenshot --filename=after-click.png
npx --yes @playwright/cli@0.1.21 -s=check console
npx --yes @playwright/cli@0.1.21 -s=check close
```

`snapshot` writes an accessibility tree with element references such as `e12`, which
`click`, `fill` and `hover` accept. Add `--json` to any command to get a JSON reply.
Recent `playwright` releases also expose this tool as `npx playwright cli`, but the
emulation commands `set-color-scheme` and `set-reduced-motion` are newer than 1.63.0.
Pin `@playwright/cli@0.1.21` when you need them.

For a test suite, the classic runner is the right tool. The agent CLI has no test
command.

```
PLAYWRIGHT_HTML_OPEN=never npx playwright test --reporter=json
```

`PLAYWRIGHT_HTML_OPEN=never` stops the HTML reporter from trying to open a browser tab,
which is pointless on a server.

## Accessibility pass

The screenshots cannot see these, so check them in the browser or the source:

- Keyboard: tab through the page. Every interactive element is reachable, in a sensible
  order, with a visible focus ring themed from the palette.
- Contrast: body at 4.5:1, large text and controls at 3:1. Check the real rendered
  colours, including text over images.
- Headings: one `h1`, and no skipped levels.
- Images: meaningful `alt` text, or an empty `alt` for decoration.
- Forms: a visible label above every input, never a placeholder standing in for one.
  Error text below the input, and announced.
- Motion: every animation has a reduced-motion branch.
