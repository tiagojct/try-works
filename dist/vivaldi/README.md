# Try-Works for Vivaldi

Two Vivaldi browser themes rooted in *Moby-Dick* ch. 96: a cold sea is the field,
the fire is the one rare load-bearing mark.

- `Try-Works.zip` — **Try-Fire** (dark)
- `Try-Works-Cold.zip` — **True Lamp** (light)

A Vivaldi theme is five base colours -- Vivaldi derives the rest -- plus
behaviour flags (`colorBg`, `colorFg`, `colorAccentBg` = the fire,
`colorHighlightBg` = the sea, `colorWindowBg`). The minimum-contrast floor is set
to 5 so the text Vivaldi generates for tabs and the address field holds the same
AA-ish legibility the rest of the system guarantees; the window stays opaque and
the fire is kept off the whole chrome (`accentOnWindow` off) so it marks only the
accent elements. The `settings.json` is generated from `src/try-works.json`; edit
the json and run `make generate`, never the theme. `assemble.sh` zips each mode
into an importable `.zip`.

## Install

Vivaldi has no theme-folder drop-in; import through the UI:

1. Settings → Themes → **Import Theme** (the folder-with-arrow button at the
   bottom of the theme gallery).
2. Pick `Try-Works.zip` (or `Try-Works-Cold.zip`).
3. The theme appears in the gallery; click to apply.

Or drag the `.zip` onto the Themes settings page.
