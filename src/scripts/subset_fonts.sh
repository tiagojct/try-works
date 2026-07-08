#!/usr/bin/env sh
# Subset the fonts to the declared unicode-range as woff2, keeping variable axes
# and all layout features. Place source TTFs in src/fonts/ first (see src/fonts/README.md).
# Run from the repo root.
set -e
RANGE="0000-00FF,0131,0152-0153,2000-206F,20AC,2122"
OUT="src/web/public/fonts"; mkdir -p "$OUT"
for pair in "Fraunces:src/fonts/Fraunces.ttf" "Literata:src/fonts/Literata.ttf" "Archivo:src/fonts/Archivo.ttf" "JetBrainsMono:src/fonts/JetBrainsMono.ttf"; do
  name=$(echo "$pair" | cut -d: -f1); src=$(echo "$pair" | cut -d: -f2)
  [ -f "$src" ] || { echo "skip $name (missing $src)"; continue; }
  python3 -m fontTools.subset "$src" --output-file="$OUT/$name.woff2" --flavor=woff2 \
    --unicodes="$RANGE" --layout-features='*'
  echo "wrote $OUT/$name.woff2"
done
