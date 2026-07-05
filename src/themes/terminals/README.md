# Terminal presets

Generated from `try-works.json` (the `terminal` block) by `make generate`.

## Ghostty

`Try-Works.ghostty` is a lit (dark) theme. Install it as a named theme:

```
cp Try-Works.ghostty ~/.config/ghostty/themes/Try-Works
```

Then in `~/.config/ghostty/config`:

```
theme = Try-Works
```

Or paste the file's contents straight into your config.

The ANSI red, green, and magenta are derived in the palette's low-saturation
register; the source image supplies only the blues, the amber, the whale white,
and the near-black ground.
