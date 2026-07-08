# Try-Works

A design system rooted in *Moby-Dick*, chapter 96: the brick furnace on the
Pequod's deck. A cold sea is the field; the fire is the load-bearing mark.
Sibling to [pequod](https://github.com/tiagojct/pequod).

Two modes: **Try-Fire** (dark, the furnace at night) and **True Lamp** (light,
the natural sun on cold water).

## The signature

Steer by the steady light, not the fire. The cool field carries the substance,
the sea and the whale white and the True Lamp daylight; the fire is the rare
mark, kept rare because in chapter 96 to fix on it is to lose your bearings. The
one place the system breaks this on purpose is the code tier, where a duty to
colour-blind readers puts the fire on keywords. The reasoning is in
[FOUNDATIONS.md](docs/FOUNDATIONS.md).

## Tiers

Core hues are the identity: ground, sea, fire, whale. They define the brand and
appear everywhere. Extended hues are added only for code, a derived green, red,
and violet plus a blue and cyan drawn from the sea; they never appear on
posters, slides, or the web.

## Layout

```
src/                 authoring inputs (the only files you edit)
  try-works.json     the single source of truth
  scripts/           generator + checks (generate, validate, cvd, fonts)
  web/               the 11ty app (its generated CSS is embedded in src/web/src/css)
  tailwind/ vscode/ zed/ vivaldi/ obsidian/ typst/ quarto/ themes/   hand-authored scaffolding
  assets/ fonts/ specimen/                              brand assets, fonts, demos
docs/                README's siblings (FOUNDATIONS, PRODUCT, BRAND, ...)
dist/                generated, committed, vendorable surfaces (the build output)
```

## Surfaces

Each is built into `dist/` from `src/try-works.json`:

```
dist/css/               custom properties (colours, type scale, spacing), both modes
dist/tailwind/          preset: colours, fontSize, spacing, borderRadius
dist/typst/             slide theme + generated colours + poster preset
dist/obsidian/          theme.css + manifest (Try-Fire / True Lamp)
dist/themes/terminals/  Ghostty presets (Try-Fire dark + True Lamp light)
dist/vscode/            dark code theme, tuned for R and Python
dist/zed/               Zed theme (Try-Fire dark), tuned for R and Python
dist/vivaldi/           Vivaldi browser themes (dark + light), zipped for import
dist/r/ dist/python/    ggplot2 / matplotlib scales and themes
dist/quarto/ dist/print/   Quarto themes; print CMYK spec
src/web/                minimal 11ty starter (built in place)
```

Run `make generate` and all of them rebuild (generate the tokens, then assemble the
scaffolding alongside). `make cvd` runs the colour-vision check.

## Data visualization

Three scales, generated for R (ggplot2) and Python (matplotlib) from the same
json. The categorical scale is Okabe-Ito, the colour-blind-safe field standard,
led by its brand-adjacent amber and blue; it keeps far more separation under
deuteranopia than a brand-tinted set would (measured min OKLab distance 0.075
versus 0.033). The sequential scale is a perceptually even teal ramp; the
diverging scale runs teal to amber through a pale centre, which is also the
colour-blind-safe axis.

R: source dist/r/tryworks.R for scale_colour_tryworks_d, _c, _div, their fill
equivalents, and theme_tryworks(mode = "light" or "dark").

Python: import dist/python/tryworks.py and call use_tryworks(); it registers the
tryworks_seq and tryworks_div colormaps and sets the categorical cycle. The
.mplstyle carries fonts and grid only, since the style parser treats the hash
in a hex colour as a comment.

## Print

Posters leave sRGB, so the print layer carries a spec rather than CSS.
dist/print/SPEC.md is generated from the json: a recommended profile (PSO Coated v3 /
FOGRA51), a 300% ink limit, a cool rich-black recipe, and CMYK starting values
for the core tokens. These are uncalibrated starting points; the printer's RIP
and a physical proof are authoritative.

A correction to an easy assumption: the amber is a clean magenta-yellow orange
and reproduces well in process. The colours that desaturate are the bright
data-viz blue, green, and violet; run them as spot if fidelity matters.

dist/typst/poster.typ is a poster preset with a page sized to trim plus 3 mm bleed,
crop marks, and a 5 mm safe-area guide, defaulting to the fire-as-one-mark
layout. A poster proof showing the geometry is in src/specimen/poster-proof.svg.

## Accessibility

Body contrast is locked at build time; this layer covers the rest, in
dist/css/a11y.css. Interactive elements get a visible :focus-visible ring in the
accent (cleared at 3:1 against each mode). prefers-contrast: more raises muted
text to 7:1 and borders to 3:1. forced-colors (Windows high contrast) keeps
buttons and focus visible with system colours. prefers-reduced-transparency
drops the hero wash.

The VS Code theme was contrast-audited; line numbers were lifted above 3:1.

Data is not encoded by colour alone: the categorical scale is paired with a
marker set (matplotlib) and pch shapes (ggplot2, via scale_shape_tryworks_d), so
series stay distinct in greyscale and for colour-blind readers.

## Performance

Subsetting the fonts to the declared range (Latin plus Portuguese plus euro) as
woff2 halves the payload: 404K total against 811K full, and the above-the-fold
pair (Fraunces and Literata) is 276K. The subsets keep the variable axes and the
diacritics. Run it with `make fonts` (needs the source TTFs in fonts/ and
brotli); output lands in web/public/fonts.

dist/css/fallbacks.css declares a local() fallback per face with size-adjust and
ascent, descent, and line-gap overrides computed from each face's own metrics,
so when the web font swaps in the text does not move. The font stacks place the
matched fallback between the web font and the generic. The starter preloads only
the two above-the-fold faces.

## Motion

Motion is restrained by intent: it marks a change, it does not decorate.
dist/css/motion.css carries four durations (fast 120ms to slower 480ms) and four
eases (standard, out, in, emphasized) as variables, mirrored in the Tailwind
preset. prefers-reduced-motion collapses every animation and transition. See
src/specimen/motion.html for the curves.

## Brand

The identity is type-forward: the Try-Works wordmark in Fraunces is the
primary mark, with an ember emblem (src/assets/logo.svg) as a square secondary for
favicons. The spine is one rule, the fire is the single hot mark on a cold
field. See [BRAND.md](docs/BRAND.md).

## Licensing

Code (the generators, configs, CI, scripts) is MIT, see LICENSE-MIT. The design
itself, the palette, the token values, and the documentation, is CC-BY-4.0, see
LICENSE-CC-BY-4.0; attribute Try-Works. The fonts (Fraunces, Literata, Archivo,
JetBrains Mono) are not bundled: they are SIL Open Font License and are fetched
separately (src/fonts/README.md). If you redistribute subsetted fonts, ship the OFL
text alongside them and keep the reserved font names.

## Versioning

As of 1.0 the public surface is frozen and semantic versioning applies: a
breaking change bumps major, additive tokens bump minor, value changes that
alter output bump at least minor. The public surface is the
CSS custom properties, the Tailwind preset keys, the json schema, and the R and
Python names. Renaming or removing any of those is breaking; adding a token is
additive; changing a value that alters output is at least a minor. To release:
bump version in try-works.json, run make generate and make test, update the
changelog, tag. docs/CONTRIBUTING.md and docs/PUBLISHING.md cover the rest.

## Quarto

Documents and the site run through Quarto, so it gets first-class support, both
outputs from the one json. For HTML, try-works.scss (light) and
try-works-dark.scss (dark) are Bootstrap themes with Fraunces headings, Literata
body, and the fire as link and accent; try-works.theme is a pandoc highlight
theme built from the code map. For PDF, typst-brand.typ is injected into the
Typst preamble so headings, body, links, and code stay on system. See
src/quarto/README.md and src/quarto/example (built to dist/quarto).

## Typography

The type layer is a set of roles, not a bare size scale. Each role in
`try-works.json` carries family, size (fluid where it should be), weight,
leading, tracking, OpenType features, measure, and for Fraunces the optical
size plus the WONK and SOFT axes. `make generate` emits them as `.tw-<role>`
classes in `dist/css/typography.css`: display, headline, title, subhead, body-lg,
body, caption, eyebrow, data, code.

Three things the roles enforce that a scale cannot. Optical size tracks point
size, so Fraunces is set at opsz 144 in display and opsz 10 in body rather than
scaled blindly. WONK and SOFT are confined to display and headlines, off for
reading. Figures switch by context: oldstyle proportional in running text,
lining tabular in data. Body roles carry a measure (68ch) so lines do not run
long.

The web starter loads fonts with `font-display: swap`, preloads the display
face, and declares the variable axes per family; subset to Latin for
production. `src/specimen/type-specimen.html` shows the ladder, the optical-size
axis, WONK, figures, italic, and measure.

A spacing scale on a 0.25rem unit and radius tokens round out the system, also
exposed as CSS variables and Tailwind keys. Fonts: Fraunces, Archivo, JetBrains
Mono, all OFL; see `src/fonts/README.md`.


## Accessibility

Every body pair clears WCAG-AA in both modes, and a Machado-2009 colour-vision
pass (`src/scripts/cvd_check.py`) covers the code hues. The identity hues separate
cleanly; in the code tier the blue and amber axis is the CVD-safe spine, and the
close residual pairs are reinforced with weight and italics rather than colour
alone. Run `make cvd` for the table.

## Development

`src/try-works.json` is the only file you edit. Everything under `dist/` is
generated and committed; `make generate` rebuilds it. (The web app embeds its
generated CSS at `src/web/src/css` — the one generated path inside `src/`.)

```
make generate   # rebuild all surfaces from the json into dist/
make validate   # check tokens, hex, mode parity, and WCAG contrast
make check      # fail if any generated file drifts from the json
make test       # validate + check (what CI runs)
make cvd        # colour-vision-deficiency report
```

CI runs `validate`, `check`, and `cvd` on every push, so a hand-edited generated
file or a contrast regression fails the build.

## Licence

Tokens and docs CC BY 4.0; code (generator, CSS, Tailwind, Typst, web, Obsidian,
VS Code) MIT.

## Credits

[pequod](https://github.com/tiagojct/pequod) and
[Flexoki](https://stephango.com/flexoki) for the published-tokens philosophy.
Fraunces by Undercase Type, Archivo by Omnibus-Type, JetBrains Mono by
JetBrains. Herman Melville, *Moby-Dick* (1851), chapter 96.
