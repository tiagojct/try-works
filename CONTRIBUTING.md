# Contributing to Try-Works

Thank you for considering a contribution. A few rules keep the system coherent.

## The single source of truth is try-works.json

Every CSS file, the Tailwind preset, the Typst themes, the R and Python helpers,
the VS Code and Obsidian themes, the print spec, and the fallbacks are generated
from try-works.json. Do not edit generated files by hand; your change would be
overwritten on the next `make generate` and the CI drift check would fail.

To change a token: edit try-works.json, then run `make generate`, then
`make test`. Commit the json and the regenerated files together.

## Checks

- `make validate` enforces structure, valid hex, lit/cold key parity, WCAG
  contrast thresholds, typography roles, and the data-viz scales.
- `make check` confirms every generated file matches the json (no drift).
- `make cvd` reports colour-vision behaviour.
- `make fonts-check` verifies Portuguese coverage and the subset range (needs
  the fonts present; skips cleanly otherwise).
- `make test` runs validate and check together. CI runs all of these.

## Adding a token or a surface

Add the data to try-works.json, then teach scripts/generate.py to emit it in a
small builder function, register it in `artifacts()`, and add a check to
scripts/validate.py if it has invariants. Keep builders pure: json in, string
out.

## Style of change

The system has a point of view: the cold sea is the field, the fire is the rare
hot mark. Proposals that would scatter the accent or break the contrast floors
will be asked to justify themselves against that.
