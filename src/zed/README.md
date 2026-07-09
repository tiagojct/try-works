# Try-Works for Zed

A Zed theme family rooted in *Moby-Dick* ch. 96: a cold sea is the field, the
fire is the one rare load-bearing mark. Ships both appearances, tuned for R and
Python (matching the VS Code themes): **Try-Works (Try-Fire)** (dark) and
**Try-Works (True Lamp)** (light). The light variant is a total remap of the
dark one -- the same hues darkened toward the ink for WCAG-safe contrast, the
same identity terminal palette -- so both stay in lockstep from one source.

`themes/Try-Works.json` is generated from `src/try-works.json`; edit the json and
run `make generate`, never the theme file.

## Install

Copy the theme into Zed's user themes directory:

    mkdir -p ~/.config/zed/themes
    cp themes/Try-Works.json ~/.config/zed/themes/

Then open Zed and pick one: `cmd-k cmd-t` (Theme Selector) and choose
**Try-Works (Try-Fire)** or **Try-Works (True Lamp)**, or set it in
`settings.json`:

    "theme": "Try-Works (Try-Fire)"

Or follow the system appearance:

    "theme": { "mode": "system",
               "light": "Try-Works (True Lamp)",
               "dark": "Try-Works (Try-Fire)" }
