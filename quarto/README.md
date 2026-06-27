# Try-Works for Quarto

Generated from try-works.json. Two outputs, one identity.

## HTML
try-works.scss (light, True Lamp) and try-works-dark.scss (dark, Try-Fire) are
Quarto Bootstrap themes: Fraunces headings, Literata body, the fire as link and
accent. try-works.theme is a pandoc highlight theme built from the code map.

    format:
      html:
        theme: { light: try-works.scss, dark: try-works-dark.scss }
        highlight-style: try-works.theme

## PDF (Typst)
typst-brand.typ is injected into the Typst preamble; it sets Literata body,
Fraunces headings, and the fire for first-level headings and links.

    format:
      typst:
        include-in-header: typst-brand.typ

Provide the fonts (Fraunces, Literata, Archivo, JetBrains Mono) to your
environment; subset them as in fonts/README.md. See example/ for a full config.
