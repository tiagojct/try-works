#!/usr/bin/env sh
# Subset the fonts to the declared unicode-range as woff2, keeping variable axes
# and all layout features. Place source TTFs in fonts/ first (see fonts/README.md).
set -e
RANGE="0000-00FF,0131,0152-0153,2000-206F,20AC,2122"
OUT="web/public/fonts"; mkdir -p "$OUT"
for pair in "Fraunces:fonts/Fraunces.ttf" "Literata:fonts/Literata.ttf" "Archivo:fonts/Archivo.ttf" "JetBrainsMono:fonts/JetBrainsMono.ttf"; do
  name=$(echo "$pair" | cut -d: -f1); src=$(echo "$pair" | cut -d: -f2)
  [ -f "$src" ] || { echo "skip $name (missing $src)"; continue; }
  python3 -m fontTools.subset "$src" --output-file="$OUT/$name.woff2" --flavor=woff2 \
    --unicodes="$RANGE" --layout-features='*'
  echo "wrote $OUT/$name.woff2"
done
