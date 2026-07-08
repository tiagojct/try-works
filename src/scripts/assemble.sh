#!/usr/bin/env sh
# Copy hand-authored scaffolding from src/ into the generated dist/ surfaces so each
# dist/<surface> is a complete, vendorable unit. Run AFTER generate.py (which writes
# the generated tokens into dist/). Does not delete dist/ — generate.py owns those files.
set -e
REPO=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
cd "$REPO"

# tailwind preset: generated colors.generated.js + package.json already in dist/
cp src/tailwind/index.js src/tailwind/README.md dist/tailwind/

# vscode extension: generated theme + package.json already in dist/
cp src/vscode/README.md src/vscode/preview-python.svg src/vscode/preview-r.svg dist/vscode/

# zed theme: generated themes/Try-Works.json already in dist/
cp src/zed/README.md dist/zed/

# vivaldi themes: zip each generated settings.json into an importable theme
cp src/vivaldi/README.md dist/vivaldi/
rm -f dist/vivaldi/Try-Works.zip dist/vivaldi/Try-Works-Cold.zip
( cd dist/vivaldi/lit && zip -q ../Try-Works.zip settings.json )
( cd dist/vivaldi/cold && zip -q ../Try-Works-Cold.zip settings.json )

# obsidian theme: generated theme.css + manifest.json already in dist/
cp src/obsidian/README.md dist/obsidian/
cp -r src/obsidian/img dist/obsidian/img

# typst: generated colors.typ + poster.typ already in dist/
cp src/typst/try-works.typ src/typst/demo.typ src/typst/README.md dist/typst/

# quarto: generated scss/theme/typst-brand already in dist/
cp src/quarto/README.md dist/quarto/
cp -r src/quarto/example dist/quarto/example

# terminal preset: generated .ghostty already in dist/
cp src/themes/terminals/README.md src/themes/terminals/preview.svg dist/themes/terminals/

echo "assembled scaffolding into dist/ (tailwind, vscode, zed, vivaldi, obsidian, typst, quarto, themes/terminals)"
