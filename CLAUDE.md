# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Try-Works is a single-source design system (palette, type, spacing, motion, data-viz, print) that compiles to many platform surfaces: CSS, Tailwind, Typst slides/posters, an 11ty starter, Obsidian, a Ghostty terminal preset, a VS Code theme, Quarto themes, and R/Python plot styles. Rooted in *Moby-Dick* ch. 96: a cold sea is the field, the fire is the one rare load-bearing mark.

## Repository layout

```
src/                 authoring inputs — the only files you edit
  try-works.json     the single source of truth
  scripts/           generator + checks (generate, validate, cvd, check_fonts, assemble, subset_fonts)
  web/               the 11ty app (its generated CSS is embedded at src/web/src/css)
  tailwind/ vscode/ zed/ vivaldi/ obsidian/ typst/ quarto/ themes/   hand-authored scaffolding per surface
  assets/ fonts/ specimen/                              brand assets, font docs, demo HTML
docs/                README's siblings: FOUNDATIONS, PRODUCT, BRAND, PUBLISHING, RELEASING, CONTRIBUTING, CHANGELOG, CODE_OF_CONDUCT
dist/                generated, committed, vendorable surfaces — the build output
README.md  CLAUDE.md  Makefile  LICENSE-*  CITATION.cff   (stay at root)
```

## The one rule that governs everything

`src/try-works.json` is the **only** file you edit. `make generate` rebuilds everything under `dist/` from it (and re-emits the web app's CSS in place at `src/web/src/css`). Hand-editing a generated file is wrong and CI rejects it: `generate.py --check` regenerates in memory and diffs against the committed files, failing on any drift.

Two-step generation, both run by `make generate`:
1. `src/scripts/generate.py` writes the **generated** files (the `artifacts()` map): everything under `dist/css/`, `dist/r/`, `dist/python/`, `dist/print/`, `dist/typst/{colors,poster}.typ`, `dist/quarto/*`, `dist/tailwind/colors.generated.js`, `dist/themes/terminals/Try-Works{,-Cold}.ghostty`, `dist/vscode/themes/*.json`, `dist/zed/themes/Try-Works.json`, `dist/vivaldi/{lit,cold}/settings.json`, `dist/obsidian/theme.css`, the version-stamped `dist/{obsidian/manifest.json,vscode/package.json,tailwind/package.json}`, and the web app's CSS at `src/web/src/css/*`. Only these are drift-gated.
2. `src/scripts/assemble.sh` copies the hand-authored scaffolding (`index.js`, READMEs, previews, `demo.typ`, `quarto/example`, etc.) from `src/<surface>` into `dist/<surface>` so each `dist/<surface>` is a complete, vendorable unit. These copies are NOT drift-gated, so after editing scaffolding in `src/`, re-run `make generate`.

## Commands

```
make generate   # generate.py (tokens into dist/) + assemble.sh (scaffolding into dist/)
make validate   # structure, hex, mode parity, WCAG contrast (src/scripts/validate.py)
make check      # drift gate: fail if any generated file differs from the json
make test       # validate + check (what CI gates on)
make cvd        # Machado-2009 colour-vision report (src/scripts/cvd_check.py)
make fonts-check # Portuguese coverage + subset range (needs fonts in src/fonts/)
make fonts      # subset fonts to woff2 (needs source TTFs in src/fonts/ + brotli)
make demo       # compile src/typst/demo.typ (needs typst + the three fonts)
```

CI ([.github/workflows/ci.yml](.github/workflows/ci.yml)) runs `validate.py`, `generate.py --check`, `cvd_check.py`, and `check_fonts.py` on every push. There is no single-test runner; the checks are whole-file Python scripts. To verify a change: `make generate && make test`.

The npm subprojects only consume generated output. `src/web/` is the 11ty app (`npm run serve` / `npm run build`, run from `src/web`); `src/tailwind/index.js` re-exports `colors.generated.js`.

## Architecture

- **`src/try-works.json`** — the source of truth. Holds modes, palette tiers, code-token map, terminal ANSI, typography roles, spacing, a11y, motion, dataviz scales, print/CMYK, gamut (P3), i18n range, and product/brand metadata.
- **`src/scripts/generate.py`** — one `build_*` function per surface, each returning file text; `artifacts(D)` maps output paths (relative to repo root) to builder results; `main()` either writes them (`REPO / rel`) or (`--check`) diffs them. Path constants: `SRC` = `src/`, `REPO` = repo root. CSS roles are emitted from `typography.roles` as `.tw-<role>` classes. Templates (`R_TEMPLATE`, `PY_TEMPLATE`, `POSTER_TEMPLATE`) use `@@TOKEN@@` placeholders filled from the json.
- **`src/scripts/validate.py`** — makes the accessibility guarantee a test: required keys, lit/cold key parity, valid hex everywhere, typography-role sanity (opsz within Fraunces range, measure defined), dataviz hex, and WCAG ratios for the locked body/UI pairs.
- **`src/scripts/cvd_check.py`** — simulates the code hues under protan/deutan/tritan (Machado-2009) and reports worst-case deltaE; close pairs are reinforced with weight/italics, not colour alone.
- **`src/scripts/assemble.sh`** — copies scaffolding into `dist/`; **`subset_fonts.sh`** — woff2 subsetting; **`check_fonts.py`** — coverage check. validate.py / cvd_check.py / check_fonts.py read `src/try-works.json` via `parent.parent`, so they need no path constants.

## Key model concepts

- **Two modes**: `lit` (Try-Fire, dark, `scheme: dark`) and `cold` (True Lamp, light, `scheme: light`). They must keep identical token keys — `validate.py` enforces parity. CSS emits `lit` as `:root` / `[data-mode="lit"]`, `cold` as `[data-mode="cold"]`.
- **Tiers**: `core` hues (ground, sea, fire, whale) are the identity and appear everywhere; `extended` hues (kelp, brick, dusk, tide, shoal) exist **only** for code/terminal and must not appear on posters, slides, or web.
- **The deliberate exception**: the system keeps fire rare everywhere except the code tier, where colour-blind safety puts fire on keywords. See [docs/FOUNDATIONS.md](docs/FOUNDATIONS.md).

## Versioning (public surface is frozen at 1.0)

Semver applies to the public surface: CSS custom properties, Tailwind preset keys, the json schema, and the R/Python names. Renaming/removing any is breaking; adding a token is additive; changing a value that alters output is at least minor. To release: bump `version` in `src/try-works.json`, run `make generate` and `make test`, update `docs/CHANGELOG.md`, tag. See `docs/RELEASING.md` / `docs/PUBLISHING.md`.

## Licensing split

Code (generators, configs, CI, scripts) is MIT; the design (palette, token values, docs) is CC-BY-4.0. Fonts are OFL and are not bundled.
