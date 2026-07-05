# Try-Works for VS Code

A dark code theme from the Try-Works palette, tuned for R and Python. Works in
VS Code and in Positron (which reads VS Code themes and semantic tokens).

Keywords carry the fire; strings are kelp green; numbers and constants the dusk
violet; functions the sea blue; types the foam cyan; decorators, namespaces and
`pkg::` the brick red; comments the gull grey. Semantic highlighting is on, so
Pylance and the R language server refine the colours further.

## Install from source

Copy the `vscode/` folder to `~/.vscode/extensions/try-works-color-theme/`
(or build a vsix with `vsce package`). Restart, then pick **Try-Works** under
Preferences: Color Theme. In Positron the same path under its extensions folder
works.

Generated from `try-works.json`; run `make generate` to rebuild.
