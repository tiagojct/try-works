# Fonts

Three families, all under the SIL Open Font License: Fraunces (serif), Archivo
(sans), JetBrains Mono (mono). Fetch the variable TTFs from the Google Fonts
mirror:

```
base="https://raw.githubusercontent.com/google/fonts/main/ofl"
curl -L "$base/fraunces/Fraunces%5BSOFT%2CWONK%2Copsz%2Cwght%5D.ttf" -o Fraunces.ttf
curl -L "$base/archivo/Archivo%5Bwdth%2Cwght%5D.ttf" -o Archivo.ttf
curl -L "$base/jetbrainsmono/JetBrainsMono%5Bwght%5D.ttf" -o JetBrainsMono.ttf
```

For the web starter, convert to woff2 (needs fonttools and brotli) and place
the results in `../web/src/fonts/`:

```
pip install fonttools brotli
for f in Fraunces Archivo JetBrainsMono; do
  fonttools ttLib.woff2 compress "$f.ttf" -o "../web/src/fonts/$f.woff2"
done
```

Axis notes:
- Fraunces: opsz, wght, SOFT, WONK. Headlines use a high opsz with WONK on and a
  little SOFT; running text uses opsz around 11 with WONK off.
- Archivo: wdth, wght. The expanded cut is useful for posters.
- JetBrains Mono: wght. Used for eyebrows, labels, and data captions.

For installing on the system (so Typst can find them), use your OS font manager
or copy the TTFs into the user fonts directory.

## Body face (Literata)

Literata (OFL), a low-contrast workhorse built for sustained screen reading.
Measured stroke contrast 1.67 against Fraunces 2.60, with a larger x-height.
The body and body-lg roles render in Literata; Fraunces carries the headings.

    https://fonts.google.com/specimen/Literata   # variable opsz,wght

Subset it to the same unicode-range as the others (see i18n.unicode-range).
