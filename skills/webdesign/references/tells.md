# The catalogue of tells

Sources: taste-skill (MIT) and impeccable (Apache-2.0), restated and merged. See
`NOTICE.md` for attribution and for how conflicts between them were settled.

Every entry here appeared often enough in generated pages to become a signature. A
**default** is overridable when the brief asks for it in words. A **ban** is not, and no
brief earns it back. A ban can still have a boundary in its own definition: a dot that
carries real state is not a decorative dot, so the ban on decorative dots never reaches
it. What a ban never has is an exception granted by the brief.

The linter checks the mechanically checkable subset. Read
[lint.md](lint.md) for which ones those are. The rest need your eyes.

## Punctuation and micro-copy

**BAN: the em dash.** Zero instances in anything a visitor can see. Not a headline, not
an eyebrow, not a pill, not a button label, not a caption, not an image alt, not body
copy, not a quote, not an attribution. Replace it with a period, a comma, a colon, a
pair of parentheses, or two sentences. The en dash is banned as a separator too: a date
range is `2018-2026` and a number range is `40-80k`, both with a plain hyphen. The only
dash characters permitted in visible text are the hyphen in compound words and ranges,
and the minus sign in arithmetic.

Phrasing this rule as "use sparingly" has never worked, so it is binary.

**BAN: the middle dot as a general separator.** One `·` per metadata line at most.
`Design · Build · Ship · Scale` is decoration. Use line breaks, hairlines or columns.

**DEFAULT AGAINST: filler verbs.** Elevate, seamless, unleash, next-gen, revolutionize,
supercharge, empower, leverage, game-changing, cutting-edge, effortlessly, robust,
unlock the power. Use a concrete verb that names what happens.

**BAN: placeholder identities.** John Doe, Jane Doe, Acme, Nexus, SmartFlow, Cloudly,
lorem ipsum. Invent a name that could plausibly exist, or use real content.

**BAN: fake-precise numbers.** `99.99%`, `10x`, a round `50%`, `1234567`. A number is
either real, explicitly marked as sample data, or absent. Inventing engineering
precision the brand does not claim is a lie in the design.

**One copy register per page.** Do not mix technical telemetry, editorial prose and
marketing punch in one composition unless the brand voice genuinely does that.

## Labels and chrome

**DEFAULT AGAINST, WITH A HARD CEILING: the eyebrow or kicker.** The small uppercase
wide-tracked label above a heading. Its CSS signature is
`text-[11px] uppercase tracking-[0.18em]` or similar. Do not add one by default; the
headline alone is enough. The hard ceiling is one per three sections, counting the
hero's as one, and the linter enforces it. The ceiling is not an allowance to fill.

**BAN: enumerated section labels.** `01 / INDEX`, `002 · Capabilities`,
`06 - how it works`, `Stage 1 / Stage 2`, `Phase 01`, `Pass One`. This is about labelling
the sections of a page. An ordered list of real steps inside a section is content, not a
label, and an `<ol>` numbers it without any typed digits. Name each step by its verb:
Install, Configure, Ship.

**BAN: pagination labels on images and tiles** (`01 / 4`). If the visitor can count,
they do not need the count.

**BAN: the scroll cue.** `Scroll`, `Scroll to explore`, `Scroll to discover`, an
animated mouse wheel, a bouncing arrow at the fold.

**DEFAULT AGAINST: version labels in a hero.** `v0.6`, `BETA`, `ALPHA`, `EARLY ACCESS`,
`INVITE-ONLY PREVIEW`. Use one only when the brief is specifically about launch status.

**BAN: version footers on a marketing page.** `v1.4.2`, `Build 0048`,
`last sync 4s ago · main`. Those are devtool fixtures, not page content.

**BAN: the decoration text strip.** A small mono-caps line across the bottom of the
hero: `BRAND. MOTION. SPATIAL.`, `TYPE / FORM / MOTION`, `ESTD. 2018 · LISBON`. Allowed
only when the strip carries real navigation or real status.

**DEFAULT AGAINST: locale, time and weather strips.** `Lisbon 14:23 · 18°C` in a header
or footer. Use one only for a genuinely timezone-distributed studio, a travel brand, or a
physical venue. A contact address in the footer is fine; atmosphere is not.

**BAN: decorative status dots.** A coloured dot before every nav link, badge or list
row. Allowed only when the dot carries real semantic state, and then sparingly.

**BAN: micro-meta sentences under a heading.** A small explanatory sentence tucked under
a section heading, of the shape "The list will stay short on purpose." Heading plus body
is enough.

**BAN: photo credit as decoration.** `Field study no. 12`, `Plate 03 · House archive`,
`Frame XII · 35mm` under a stock image. Credit a real photographer for a real photo, or
write one functional caption, or write nothing.

**BAN: pills and tags overlaid on images.** Either the image speaks alone, or the
caption sits below it, outside the frame.

**BAN: the performative-craftsman label.** `From the field`, `Field notes`,
`Currently on the bench`, `On our desks`, `Quietly trusted by`. Use the plain label, or
drop the label.

## Layout

**BAN: the three identical feature cards.** Same icon size, same heading, same body,
three across, as page structure. Use a two-column alternation, an asymmetric grid, a
pinned section, or horizontal scroll.

**BAN: nested cards.** A card inside a card is always wrong.

**BAN: the split header.** A giant left headline with a small explainer paragraph
floating in the right column. Stack them instead, headline above body, body capped at
75 characters. Use the split only when the right column holds a real visual or control.

**Zigzag cap: two.** Alternating image-left and image-right is fine twice. The third
consecutive image-and-text split is a failure. Break it with a full-width section, a
vertical stack, a grid, or a different family entirely.

**Layout family repetition: once.** Once a section uses a layout family, that family
does not reappear. An eight-section page uses at least four different families.

**Bento cells equal content.** Three items means three cells. Five items means five
cells. An empty cell means the grid was planned wrong. Reshape it; never paste a blank
tile.

**Bento background diversity.** A multi-cell grid cannot be six white cards with text
in them. At least two or three cells need real visual variation: an image, a tint, a
pattern, a considered gradient.

**Hero fits the first viewport.** Headline at most two lines. Subtext at most 20 words
and at most four lines. The primary action visible without scrolling. A four-line hero
headline is a font-size error, never a copy-length error.

**Hero top padding caps at 6rem.** More than that and the content floats mid-viewport
and reads as a bug. If the hero needs air, increase the type scale or the asset, not the
padding.

**Hero stack caps at four text elements.** Optionally one eyebrow or brand strip, the
headline, the subtext, the actions. Everything else moves below the hero: the trust
strip, the logo wall, the pricing teaser, the feature bullets, the avatar row.

**Navigation on one line at desktop, 80px tall at most, 64 to 72px by default.** If it
does not fit at 1024px, shorten the labels, drop the secondary items, or collapse to a
menu. A two-line desktop nav is broken.

**One call to action per intent.** "Get in touch", "Contact us", "Let's talk" and
"Start a project" are one intent. Pick one label and use it in the nav, the hero and the
footer. Two labels for one intent is a failure.

**Button labels do not wrap at desktop.** Three words maximum for a primary action, one
or two is better. If it wraps, shorten the label or widen the button.

**Mobile collapse is explicit.** Every multi-column layout declares its behaviour below
768px in the same component. "Tailwind will handle it" is not a declaration.

**Long lists need a different component, not a longer list.** Above five items, reach
for a two-column split, a card grid, tabs, an accordion, scroll-snap pills, or a
carousel. A ten-row specification table with a hairline under every row is the worst
available default.

**BAN: a top and bottom border on every row.** Pick one edge and use it sparingly.

**BAN: filled progress tracks as a comparison visual.** A grey track with a partial fill
is dashboard clutter on a marketing page. Use a number, or a thin bar with no track.

## Type

**DEFAULT AGAINST these families as a first choice:** Inter, Roboto, Open Sans, Lato,
Montserrat, Arial, Helvetica, Poppins, Nunito, Geist, Mona Sans, Plus Jakarta Sans,
Space Grotesk, Fraunces, Instrument Sans, Instrument Serif, Recoleta. They are what gets
reached for, so they carry no information. A brand's own face on its own domain is
always fine.

**BAN: Impact, Arial Black, Comic Sans MS and Papyrus as a display voice.** A system
display face is not a brand voice.

**Serif needs a reason.** "It feels premium" is not a reason. Use a serif when the brief
names one, or when the work is genuinely editorial, literary, luxury or heritage and you
can say why this serif fits this brand. For a creative studio, a modern product or a
portfolio, a sans display face is the correct default, not a boring one.

**Mixed-family emphasis is amateur.** To stress one word inside a headline, use the
italic or the bold of the same family. Do not drop a serif word into a sans headline.

**Accenting one word in a headline is itself a tell.** Prefer no accent.

**All caps for labels is a tell.** Prefer sentence case.

**Italic descenders need clearance.** An italic display word containing `y g j p q`
clips at `leading-none`. Use 1.1 minimum and add bottom padding.

**Tracking floor is -0.04em.** Tighter reads as a rendering fault. -0.02 to -0.03em
usually looks better than the floor.

**DEFAULT AGAINST: monospace as a costume.** A mono face belongs to code, data and
genuinely tabular values. Setting headings or marketing copy in mono to make a page
look technical is a reflex, not a choice. A system that gives mono a stated job, such as
interface chrome in a terminal-register tool, has made the choice.

**One or two families. If two, make them obviously different.**

## Colour

**One accent, locked for the whole page.** A warm-grey page does not grow a blue button
in section seven. A rose-accented page does not grow a teal badge in the footer.

**BAN: pure `#000000` and pure `#ffffff`** as a surface or a text colour. Pure values
kill depth. Use an off-black and an off-white.

**DEFAULT AGAINST the AI purple.** Violet and blue gradient washes, glowing purple
buttons, neon on near-black. When the brand asks for violet, use it with intent: one
palette, harmonised neutrals, restrained gradients.

**DEFAULT AGAINST: the warm premium-consumer palette.** Cream or beige ground, brass or
clay or oxblood accent, espresso text. It appears on every artisan, wellness, cookware
and heritage brief, and it makes them all the same brand. The specific values that
trigger it:

```
grounds  #f5f1ea #f7f5f1 #fbf8f1 #efeae0 #ece6db #faf7f1 #e8dfcb
accents  #b08947 #b6553a #9a2436 #9c6e2a #bc7c3a #7d5621 #d97757
text     #1a1714 #1a1814 #1b1814
```

Pick another family instead, and do not repeat the one you used last time. Cold luxury
of silver, chrome and smoke. Deep forest with bone and one amber. True off-black with a
warm tan and sharp contrast. Saturated cobalt against a single neutral. Terracotta
against a cool slate. Olive, brick and paper. Monochrome with one bright pop.

**BAN: gradient text.** Also no coloured border on one side above 1px, no glass or blur
as pure decoration, no hard offset shadow outside a genuinely neobrutalist world.

**Shadows tint to the surface hue.** No pure black drop shadow on a light ground.

**Dark mode is composed, not inverted.** A mechanical inversion is not a dark theme.
Design both from the start. Keep hierarchy parity: what pops in light pops in dark.

**One theme per page.** A dark page stays dark in every section. A light page stays
light. A section tint inside the same family is fine. Flipping to a cream section in the
middle of a near-black page reads as walking into a different site. One deliberate
full-page theme switch is allowed when the brief asks for that device.

## Shape and material

**One radius system, declared.** All sharp, or all soft at 12 to 16px, or pill for
interactive controls only. A mixed system is fine when the rule is written down and
followed everywhere: pills for small controls, 12px for cards, 8px for inputs. Round
buttons in a square layout is not a mixed system, it is an accident.

**Cards only when elevation means something.** Otherwise group with space, a hairline,
or a divider. Above DENSITY 7, drop card containers entirely.

**Geometric masks are not photography.** A circle, polygon or radial-gradient cutout
approximating a photographic subject's edge reads as a shortcut, because it is one.

## Images and assets

A landing page or a portfolio is a visual product. A text-only page is not minimalism,
it is unfinished.

Priority order for every visual slot:

1. **Generate it.** If any image tool is available in the session, use it. Generate at
   the aspect ratio the slot needs.
2. **Use a real image.** A brand asset the user supplied, or a seeded placeholder at the
   right dimensions with a descriptive seed.
3. **Leave a labelled hole and say so.** `<!-- TODO: hero product photo, 1600x1200 -->`,
   then list every missing image in your reply and ask for them.

**BAN: fake product UI built from divs.** A fake dashboard, fake terminal, fake task
list or fake editor assembled from styled rectangles. This is the loudest tell in the
catalogue. Use a real screenshot, a real live component rendered small, a generated
image, or editorial photography instead.

**BAN: hand-rolled SVG icons.** One icon library, one stroke weight, standardised
globally. Emoji and Unicode glyphs are not an icon system.

**DEFAULT AGAINST hand-rolled decorative SVG.** Custom illustrations and marks drawn in
path data. Acceptable for a single simple geometric monogram.

**Even a restrained page needs images.** Two or three real ones at minimum. Generate
restrained photography rather than shipping a page of pure type.

**A logo wall is logos only.** No category label under each mark. The logo is the
credibility; the label adds nothing. Put the wall under the hero, never inside it.
Render every mark correctly in both themes.

## Motion

**Every animation needs a reason you can state in one sentence.** Valid reasons:
hierarchy, sequence that matches a narrative, feedback for an action, showing that state
changed. "It looked good" is not a reason. Reaching for a scroll library because it is
installed is not a reason.

**One marquee per page, at most.** Two reads as filler.

**No fade-and-slide-up on every section.** No hover transition on every card. A single
orchestrated moment lands; scattered effects read as generated.

**BAN: `window.addEventListener('scroll')`** and hand-rolled `scrollY` maths in
component state. Use `useScroll`, `ScrollTrigger`, `IntersectionObserver`, or CSS
`animation-timeline: view()`.

**Never drive a continuous value through component state.** Pointer position, scroll
progress and magnetic hover go through motion values, outside the render cycle. State
re-renders the tree on every frame and collapses on mobile.

**Never animate a layout property.** Not `top`, `left`, `width`, `height`, `margin` or
`padding`: each one reflows the page on every frame. Transform and opacity are the
default. Filter, clip-path, mask and shadow are allowed for the one authored moment,
because they repaint without reflowing; check the frame rate on a phone before keeping
one.

**Every animation needs a reduced-motion branch,** whatever the MOTION dial says.
Infinite loops, parallax, scroll hijacking and pointer physics collapse to static.
Feedback for an action may stay, shortened to an instant state change. A global `0.01ms` override is not an
implementation, it destroys useful feedback too.

**Pinned sections pin at the top.** A sticky stack or a horizontal pan starts at
`top top`, not `top center`. The common failure is the animation running before the
section is pinned, so the visitor sees half a slide.

**Grain and noise go on a fixed, pointer-events-none layer.** Never on a scrolling
container, because the repaint cost destroys mobile frame rate.

## The copy audit

Before you call anything done, re-read every visible string: headlines, subheads,
labels, button text, body copy, captions, alt text, footer text, error messages. Flag
any string that is grammatically broken, has an unclear referent, reads as cute but
wrong, or sounds like a machine trying to sound thoughtful. Rewrite every flagged
string. When in doubt, replace it with a plain functional sentence. Generated cute copy
is worse than boring copy.

## Copy for interface text

Words exist to make the interface easier to use. Name things the way the visitor thinks
of them, not the way the system is built. Someone manages notifications, not webhook
configuration.

Use the active voice. A button says what happens: "Save changes", not "Submit". An
action keeps its name through the whole flow, so a "Publish" button produces a
"Published" confirmation.

Treat errors and empty states as direction, not mood. An error says what happened and
how to fix it. It does not apologise and it is never vague. An empty screen is an
invitation to act.

Keep sentence case, plain verbs and no filler. Every element does exactly one job.
