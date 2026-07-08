# Try-Works for Zed

A Zed theme rooted in *Moby-Dick* ch. 96: a cold sea is the field, the fire is
the one rare load-bearing mark. Ships the dark mode, **Try-Fire**, tuned for R
and Python (matching the VS Code theme). The light mode is not shipped because
the code tier is dark-tuned and CVD-audited; a light syntax map would need
colours not yet defined in the source.

`themes/Try-Works.json` is generated from `src/try-works.json`; edit the json and
run `make generate`, never the theme file.

## Install

Copy the theme into Zed's user themes directory:

    mkdir -p ~/.config/zed/themes
    cp themes/Try-Works.json ~/.config/zed/themes/

Then open Zed and pick it: `cmd-k cmd-t` (Theme Selector) and choose
**Try-Works (Try-Fire)**, or set it in `settings.json`:

    "theme": "Try-Works (Try-Fire)"
