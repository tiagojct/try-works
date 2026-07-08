# Publishing

`src/try-works.json` is the source of truth; `make generate` builds each surface
into `dist/`, where every `dist/<surface>` is a complete, ready-to-publish unit.

## VS Code / Positron theme

`dist/vscode/` is a valid extension root.

    cd dist/vscode && npx @vscode/vsce package

Publish the resulting .vsix to the Marketplace, or to Open VSX for Positron.
The version comes from `src/try-works.json` via `make generate`; bump it there.

## Obsidian theme

Obsidian themes are a folder with manifest.json and theme.css. `dist/obsidian/`
is publishable as is. For the community list, push it to a dedicated repo whose
root holds manifest.json and theme.css, and submit per Obsidian's process.

## Tailwind preset

    cd dist/tailwind && npm publish

## CSS

The generated stylesheets in `dist/css/` are static assets; ship them directly or
via your bundler. fallbacks.css and p3.css are progressive enhancements and
degrade on their own.
