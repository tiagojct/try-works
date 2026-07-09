# Try-Works for VS Code

Two code themes from the Try-Works palette, tuned for R and Python: **Try-Works**
(Try-Fire, dark) and **Try-Works Cold (True Lamp)** (light). Both work in VS Code
and in Positron (which reads VS Code themes and semantic tokens).

Keywords carry the fire; strings are kelp green; numbers and constants the dusk
violet; functions the sea blue; types the foam cyan; decorators, namespaces and
`pkg::` the brick red; comments the gull grey. Semantic highlighting is on, so
Pylance and the R language server refine the colours further. The light theme is
a total remap of the dark one: same hues darkened toward the ink for WCAG-safe
contrast, same identity terminal palette, hovers that darken instead of brighten.

## Install from source

Copy the `vscode/` folder to `~/.vscode/extensions/try-works-color-theme/`
(or build a vsix with `vsce package`). Restart, then pick **Try-Works** or
**Try-Works Cold (True Lamp)** under Preferences: Color Theme. In Positron the
same path under its extensions folder works.

## File icons

**Try-Works Icons** is a generated file-icon theme in the same palette:
monogram-on-chip file icons (Py, R, Nb, Qm, {}, ...) and hue-tinted outline
folders (src, data, docs, tests, ...). Typography is the icon. Select it under
Preferences: File Icon Theme after installing.

Generated from `try-works.json`; run `make generate` to rebuild.
