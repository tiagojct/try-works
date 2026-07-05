# Publishing

The repository is the source of truth; each surface is published from its own
subtree. `make dist` assembles ready-to-publish copies under dist/.

## VS Code / Positron theme

The vscode/ folder is already a valid extension root.

    cd vscode && npx @vscode/vsce package

Publish the resulting .vsix to the Marketplace, or to Open VSX for Positron.
The version comes from try-works.json via `make generate`; bump it there.

## Obsidian theme

Obsidian themes are a folder with manifest.json and theme.css. The obsidian/
folder is publishable as is. For the community list, push it to a dedicated repo
whose root holds manifest.json and theme.css, and submit per Obsidian's process.
`make dist` produces dist/obsidian ready to copy into that repo.

## Tailwind preset

    cd tailwind && npm publish

## CSS

The generated stylesheets in css/ are static assets; ship them directly or via
your bundler. fallbacks.css and p3.css are progressive enhancements and degrade
on their own.
