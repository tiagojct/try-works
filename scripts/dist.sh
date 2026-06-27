#!/usr/bin/env sh
# Assemble ready-to-publish copies of each surface under dist/.
set -e
rm -rf dist && mkdir -p dist
cp -r obsidian dist/obsidian
cp -r vscode dist/vscode
mkdir -p dist/tailwind && cp tailwind/index.js tailwind/colors.generated.js tailwind/package.json tailwind/README.md dist/tailwind/ 2>/dev/null || true
mkdir -p dist/css && cp css/*.css dist/css/
( cd dist && zip -rq obsidian.zip obsidian )
echo "assembled dist/ (obsidian, vscode, tailwind, css) and dist/obsidian.zip"
