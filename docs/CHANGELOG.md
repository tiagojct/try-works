# Changelog

## Unreleased

- Vivaldi: raised the minimum-contrast floor from 2 to 5 so Vivaldi-derived UI
  text (tab titles on the sea highlight, text on the fire accent) meets the AA-ish
  legibility the rest of the system guarantees, and added the `backgroundSource`
  field to match the current exported-theme schema. Verified against installed
  Vivaldi themes; colours and the deterministic ids are unchanged.
- Added the oh-my-zsh surface: try-works.zsh-theme (Try-Fire) and
  try-works-cold.zsh-theme (True Lamp), a truecolor two-line prompt. Cool-sea
  throughout; the ember fire marks only the git-dirty state, a failed command
  turns the caret and exit code red. Cold uses the shared light-safe hue remap.
- Zed: added Try-Works (True Lamp), a light appearance in the same theme family,
  derived from the dark style by the shared lit->cold remap now factored out of
  the VS Code light builder. Both editors' light themes stay identical in
  philosophy from one table.
- VS Code: added Try-Works Icons, a generated file-icon theme (Material-style
  JSON conventions; monogram-on-chip file icons and lucide-outline folders in
  palette hues, ~60 SVGs all drift-gated).
- VS Code: added Try-Works Cold (True Lamp), a light theme derived from the
  dark one by a total colour remap (same hues darkened toward the ink at the
  t=0.45 ratio the Obsidian/Quarto light surfaces use; identity terminal ANSI;
  hovers darken). Unmapped colours fail generation, so the two variants cannot
  drift apart silently.
- Added the iTerm2 surface: Try-Works.itermcolors (lit) and
  Try-Works-Cold.itermcolors (cold) alongside the Ghostty pair, same
  identity-palette / flipped-chrome split, generated from the json.
- Obsidian: fixed light-mode hover contrast (hovers now darken to accent-deep
  in cold; accent-bright measured 3.55:1 against the cold bg), with both hover
  pairs locked in validate.py. Added alternative task states ([/] [>] [<] [?]
  [!] [*] [-]), an opt-in focus mode, seamless transclusions (Style Settings
  toggle restores frames), image captions from pipe text, an img-grid
  cssclasses helper, quieter status bar / vault chrome, and phone-size
  Properties type. Body stays Archivo (sans), headings Fraunces (serif).

## 1.0.0

First stable release. The public surface is frozen: the CSS custom properties,
the Tailwind preset keys, the json schema, and the R and Python names. From here,
semantic versioning applies.

The system spans one source of truth (try-works.json) and 29 generated files
across CSS, Tailwind, Typst (slides and poster), 11ty, Obsidian, Ghostty, VS
Code, R (ggplot2), Python (matplotlib), Quarto (HTML and Typst), print, and the
metric-matched font fallbacks, with WCAG, CVD, typography, i18n, accessibility,
performance, and Portuguese-coverage checks enforced in CI.

## 0.19.0 — Quarto

- Added the Quarto surface, the gap the product review flagged: try-works.scss
  and try-works-dark.scss (HTML themes, Fraunces/Literata/fire), try-works.theme
  (highlight theme from the code map), and typst-brand.typ (PDF via Typst
  include-in-header). Example config and qmd included. All generated from the json.

## 0.18.1 — confirm surfaces

- Tailwind, Obsidian, and Ghostty confirmed in use; moved from the confirm tier
  to core. No surfaces pruned. Quarto theme remains the next build before 1.0.

## 0.18.0 — product focus

- Added PRODUCT.md and a product block: named the audience, tiered the surfaces
  by weekly use (core / maintained / confirm), and drew the scope line.
- Flagged the highest-value gap: a Quarto theme (SCSS for HTML, Typst for PDF),
  which sits in the weekly path and is missing. Recommended building it before
  any further surface, then pruning unconfirmed surfaces, then 1.0.

## 0.17.0 — brand

- Added BRAND.md: essence, positioning, the pequod family relationship, voice,
  and usage. Resolved the mark question type-forward: the wordmark is primary,
  with an ember emblem (assets/logo.svg, logo-cold.svg) as the square secondary.
- Added a brand block to the json and a brand sheet to the specimens.

## 0.16.0 — stewardship

- Added CONTRIBUTING, CODE_OF_CONDUCT, PUBLISHING, and CITATION.cff; documented
  licensing (MIT code, CC-BY-4.0 design, OFL fonts unbundled) and a pre-1.0
  versioning policy with a defined public surface.
- Hardened CI: actions pinned to commit SHAs, added the Portuguese coverage step,
  added Dependabot for the pinned actions.
- Added `make dist` to assemble publishable copies of each surface.

## 0.15.0 — motion

- Added motion tokens: four durations and four eases in css/motion.css and the
  Tailwind preset, with a prefers-reduced-motion reset. Motion specimen added.

## 0.14.0 — performance

- Measured and documented subsetting: woff2 to the declared range cuts the font
  payload ~50% (811K to 404K; above-fold 276K), keeping axes and diacritics.
  Added scripts/subset_fonts.sh and a `make fonts` target.
- Added css/fallbacks.css: metric-matched local() fallbacks (size-adjust,
  ascent/descent/line-gap overrides per face) to remove swap layout shift; font
  stacks updated to include the matched fallback.

## 0.13.0 — accessibility beyond contrast

- Added css/a11y.css: :focus-visible rings (3:1 in both modes), prefers-contrast
  more (muted to 7:1, borders to 3:1), forced-colors support for buttons and
  focus, and prefers-reduced-transparency.
- Audited the VS Code theme; raised line-number contrast from 2.40 to 3.36.
- Data not by colour alone: paired the categorical scale with markers
  (matplotlib) and pch shapes (ggplot2 scale_shape_tryworks_d).

## 0.12.0 — print production

- Added a print layer: print/SPEC.md (profile, ink limit, cool rich black, CMYK
  starting values) and a Typst poster preset with bleed, crop marks, and a
  safe-area guide, both generated from the json.
- Corrected the gamut framing: the amber prints well; the real CMYK casualties
  are the bright data-viz blue, green, and violet, now flagged with spot advice.
- Added an A2 poster proof showing bleed, trim, safe area, and the CMYK
  substitutions.

## 0.11.0 — data visualization

- Added categorical, sequential, and diverging scales, generated for R (ggplot2)
  and Python (matplotlib) from the json. Categorical is Okabe-Ito (CVD-safe),
  chosen over a brand-tinted set that failed the colour-blindness test (min
  OKLab separation 0.033 vs 0.075). Sequential is a perceptually even teal ramp;
  diverging is teal-amber, the built-in uniform scale deferred from colour work.
- R: scale_colour/fill_tryworks_d/_c/_div and theme_tryworks(mode).
- Python: tryworks_seq / tryworks_div colormaps, categorical cycle, use_tryworks().
- validate.py checks the scales; example spirometry plots and a CVD simulation
  added to the specimens.

## 0.10.0 — Literata for body

- Adopted Literata as the body face (body, body-lg) per preference; Fraunces
  keeps all headings (display down to subhead) for character.
- font-variation-settings are now driven by each font's declared axes, so
  Literata uses opsz and wght and does not inherit Fraunces' SOFT and WONK.
- Web loading: Literata @font-face and preload added; body base set to the
  reading face. Type specimen rebuilt to show the real Fraunces/Literata pairing.

## 0.9.0 — reading science

- Measured Fraunces against faces built for long-form screen reading. At the
  text optical size Fraunces shows stroke contrast ~2.60 and x-height/em 0.482,
  versus Literata 1.67 / 0.507 and Source Serif 4 1.82 / 0.475.
- Verdict: Fraunces stays for display, headlines, and the lede; for the long-form
  body role a lower-contrast workhorse reduces fatigue. Wired Literata as a
  first-class reading font (--tw-font-reading) with verified Portuguese coverage;
  the body role still ships on Fraunces by choice, switchable in one line.
- Added a reading-comparison specimen with the measured metrics.

## 0.8.0 — internationalisation (European Portuguese)

- Verified font and subset coverage for European Portuguese; caught the euro
  outside the declared range and added U+20AC. scripts/check_fonts.py makes the
  coverage a repeatable test (skips cleanly when fonts are not present).
- Type roles now use logical properties (max-inline-size), font-variant-numeric
  and font-variant-ligatures instead of raw feature flags, and text-wrap balance
  (display/headings) and pretty (body) for orphan control.
- Web starter set to lang="pt" with guillemet-first quotes; site.css moved to
  logical properties throughout.
- Added a Portuguese type specimen: accented uppercasing, travessão, guillemets,
  ordinals, euro, pre-AO90 spelling.

## 0.7.0 — colour science

- Audited the palette in OKLCH. Documented the colour space; the sea ramp is
  hue-consistent intent but lightness-uneven at the top (0.137/0.153/0.211).
- Evening the ramp was declined automatically because it dropped flame-on-sea to
  3.03, under the 3.05 guard. The identity sea stays; a uniform sequential scale
  is deferred to the data-viz work, built for purpose.
- Added a P3 wide-gamut fire (chroma boosted ~18% in OKLab, clamped to P3) via a
  generated p3.css behind @media (color-gamut: p3); sRGB remains the fallback.

## 0.6.0 — typography

- Replaced the bare modular scale with a typographic role system: display,
  headline, title, subhead, body-lg, body, caption, eyebrow, data, code, each
  with family, size, weight, leading, tracking, OpenType features, and measure.
- Fraunces optical size now tracks point size; WONK and SOFT are display-only;
  figures switch between oldstyle-proportional (text) and lining-tabular (data).
- Tuned fluid clamps (linear interpolation between 22rem and 80rem) replace the
  crude vw sizing on display and headline.
- Tailwind preset gained fontFamily, lineHeight, and letterSpacing.
- Web font loading rebuilt: font-display swap, preload, declared variable axes,
  Latin unicode-range.
- validate.py now checks the roles; a type specimen demonstrates the system.

## 0.5.1 — engineering pass

- Single-sourced the version: manifests are stamped from the json, fixing drift
  (vscode/tailwind were 0.1.0, obsidian 0.4.0).
- generate.py refactored into functions with a `--check` mode; drift in any
  generated file now fails the build.
- Added scripts/validate.py (structure, hex, mode parity, enforced WCAG contrast)
  which caught the cold accent sitting exactly on 4.50; darkened to clear 4.5 with
  margin (#9e5017, 4.61).
- Added GitHub Actions CI running validate, drift check, and the CVD report.
- Makefile targets: validate, check, test, all. Added .editorconfig.

## 0.5.0 — foundations

- Re-founded on a closer reading of Moby-Dick ch. 96. The signature was corrected:
  the steady light is what the system steers by; the fire is the rare, dangerous
  mark. Scarcity is now grounded as an ethic rather than a layout rule.
- Added FOUNDATIONS.md: the misreading and its correction, the sea as substance,
  the named maker's bias, the code-tier exception and its justification, Illich's
  conviviality threshold as a test for new surfaces, and the system's provisionality.
- No colour or surface changes from 0.4.0.

## 0.4.0 — a system

- Reframed as a design system. Signature stated as a principle: fire marks the
  load-bearing element, the cool field is everything else.
- Fire refined from terracotta to an oil-flame; cold reworked from a generic
  blue-grey to a sea-salt paper in the teal family.
- Modes named: Try-Fire (dark) and True Lamp (light).
- Token semantics cleaned (no more "rust" overload); core and extended tiers.
- Added a type scale and a spacing scale (CSS variables and Tailwind keys).
- Colour-vision pass added (scripts/cvd_check.py); code keywords carry the fire,
  the CVD-safe amber/blue axis, with bold and italic as secondary channels.
- Every generator brought in-repo: CSS, Tailwind, Ghostty, VS Code, Obsidian,
  and Typst colours all regenerate from try-works.json.

## 0.3.0
- Cold mode first moved to cool; Ghostty preset added.

## 0.2.0
- WCAG lock; cold accent darkened.

## 0.1.0
- First scaffold.
