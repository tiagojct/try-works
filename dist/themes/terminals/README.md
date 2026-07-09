# Terminal presets

Generated from `try-works.json` (the `terminal` block) by `make generate`.

## Ghostty

`Try-Works.ghostty` is the lit (dark) theme; `Try-Works-Cold.ghostty` is the
cold (light) one. Install as named themes:

```
cp Try-Works.ghostty ~/.config/ghostty/themes/Try-Works
cp Try-Works-Cold.ghostty ~/.config/ghostty/themes/Try-Works-Cold
```

Then in `~/.config/ghostty/config`:

```
theme = Try-Works
```

Or paste a file's contents straight into your config. Both share the same
16-colour identity palette; only the chrome (background, foreground, cursor,
selection) flips between modes.

## iTerm2

`Try-Works.itermcolors` (lit, dark) and `Try-Works-Cold.itermcolors` (cold,
light). Import via **Settings → Profiles → Colors → Color Presets… → Import…**,
then pick the preset from the same menu. Colours are sRGB; the same
identity-palette / flipped-chrome split as the Ghostty pair.

The ANSI red, green, and magenta are derived in the palette's low-saturation
register; the source image supplies only the blues, the amber, the whale white,
and the near-black ground.
