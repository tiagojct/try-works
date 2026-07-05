#!/usr/bin/env python3
"""Generate every Try-Works surface from try-works.json (the single source of truth).

Usage:
  python3 scripts/generate.py            write all generated files
  python3 scripts/generate.py --check    verify files match the json; exit 1 on drift

`--check` is what CI runs: it regenerates in memory and diffs against the committed
files, so any hand-edit of a generated file fails the build.
"""
import json, pathlib, colorsys, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

def load():
    return json.loads((ROOT / "try-works.json").read_text())

def hsl(hexv):
    h = hexv.lstrip("#"); r, g, b = [int(h[i:i+2], 16)/255 for i in (0, 2, 4)]
    hh, ll, ss = colorsys.rgb_to_hls(r, g, b); return round(hh*360), round(ss*100), round(ll*100)

SKIP = {"label", "scheme"}

def fluid(min_rem, max_rem, min_vw, max_vw):
    """A tuned clamp: linear interpolation between min_vw and max_vw (rem units)."""
    slope = (max_rem - min_rem) / (max_vw - min_vw)
    inter = min_rem - slope * min_vw
    return "clamp(%grem, %.4frem + %.4fvw, %grem)" % (min_rem, inter, slope * 100, max_rem)

def build_typography(D):
    t = D["typography"]; feats = t["features"]; meas = t["measure"]; fl = t["fluid"]; roles = t["roles"]
    fv = {"serif": "--tw-font-serif", "sans": "--tw-font-sans", "mono": "--tw-font-mono", "reading": "--tw-font-reading"}
    def features_decl(preset):
        # Prefer high-level font-variant-* (robust, does not clobber kerning/locl).
        if preset == "text":    return ["font-variant-numeric: oldstyle-nums proportional-nums;", "font-variant-ligatures: common-ligatures;"]
        if preset == "tabular": return ["font-variant-numeric: lining-nums tabular-nums;"]
        if preset == "display": return ["font-variant-ligatures: common-ligatures discretionary-ligatures;"]
        if preset == "code":    return ['font-feature-settings: "liga" 1, "calt" 1;']
        return ["font-feature-settings: %s;" % feats.get(preset, preset)]
    out = ["/* Generated typographic roles from try-works.json. Use as .tw-<role>. */", ":root {"]
    out += ["  --tw-measure-%s: %s;" % (k, v) for k, v in meas.items()]
    out.append("}")
    for name, r in roles.items():
        d = ["  font-family: var(%s);" % fv[r["font"]]]
        d.append("  font-size: %s;" % (fluid(r["fluid"][0], r["fluid"][1], fl["min-vw"], fl["max-vw"]) if "fluid" in r else r["size"]))
        d.append("  font-weight: %d;" % r.get("weight", 400))
        d.append("  line-height: %s;" % r["leading"])
        if r.get("tracking") and r["tracking"] != "0": d.append("  letter-spacing: %s;" % r["tracking"])
        if r.get("transform"): d.append("  text-transform: %s;" % r["transform"])
        axes = t["fonts"][r["font"]].get("axes", {})
        parts = []
        if "opsz" in axes and "opsz" in r: parts.append('"opsz" %d' % r["opsz"])
        if "wght" in axes: parts.append('"wght" %d' % r.get("weight", 400))
        if "SOFT" in axes and "soft" in r: parts.append('"SOFT" %d' % r["soft"])
        if "WONK" in axes and "wonk" in r: parts.append('"WONK" %d' % r["wonk"])
        if parts: d.append("  font-variation-settings: %s;" % ", ".join(parts))
        if r.get("features"): d += ["  " + x for x in features_decl(r["features"])]
        if r.get("wrap"): d.append("  text-wrap: %s;" % r["wrap"])
        if r.get("measure"): d.append("  max-inline-size: var(--tw-measure-%s);" % r["measure"])
        out.append(".tw-%s {" % name); out += d; out.append("}")
    return "\n".join(out) + "\n"

# ---------------- builders (each returns file text) ----------------
def build_css(D):
    typ, sp = D["type"], D["spacing"]; lit, cold = D["modes"]["lit"], D["modes"]["cold"]
    rd = typ.get if False else None
    def fam2(D):
        r = D["typography"]["fonts"].get("reading")
        return ('"%s", "%s fallback", Georgia, serif' % (r["family"], r["family"])) if r else 'var(--tw-font-serif)'
    fam = lambda r: '"%s", "%s fallback", %s' % (typ[r]["family"], typ[r]["family"], {"serif":"Georgia, serif","sans":"system-ui, sans-serif","mono":"ui-monospace, monospace"}[r])
    out = ["/* Generated from try-works.json. Edit the json, then `make generate`. */", ":root {",
           "  --tw-font-serif: %s;" % fam("serif"), "  --tw-font-sans: %s;" % fam("sans"), "  --tw-font-mono: %s;" % fam("mono"), "  --tw-font-reading: %s;" % fam2(D)]
    for k, v in typ["scale"]["steps"].items():   out.append("  --tw-text-%s: %s;" % (k, v))
    for k, v in typ["scale"]["leading"].items(): out.append("  --tw-leading-%s: %s;" % (k, v))
    for k, v in typ["scale"]["weight"].items():  out.append("  --tw-weight-%s: %s;" % (k, v))
    for k, v in sp["scale"].items():             out.append("  --tw-space-%s: %s;" % (k, v))
    for k, v in sp["radius"].items():            out.append("  --tw-radius-%s: %s;" % (k, v))
    out += ["  --tw-border: %s;" % sp["border"], "}", "",
            '/* %s is dark; %s is light. */' % (lit["label"], cold["label"]),
            ':root,\n[data-mode="lit"] {'] + ["  --tw-%s: %s;" % (k, v) for k, v in lit.items() if k not in SKIP] + ["}", "",
            '[data-mode="cold"] {'] + ["  --tw-%s: %s;" % (k, v) for k, v in cold.items() if k not in SKIP] + ["}"]
    return "\n".join(out) + "\n"

def _js(o, ind="  "):
    if isinstance(o, dict):
        body = ",\n".join('%s  %s: %s' % (ind, ('"%s"' % k if k == "DEFAULT" else k), _js(v, ind+"  ")) for k, v in o.items())
        return "{\n" + body + "\n" + ind + "}"
    if isinstance(o, list):
        return "[" + ", ".join(_js(x, ind) for x in o) + "]"
    return '"%s"' % o

def build_tailwind(D):
    pal, typ, sp, tg = D["palette"], D["type"], D["spacing"], D["typography"]
    sea, fire, gr, wh, ext = pal["sea"], pal["fire"], pal["ground"], pal["whale"], pal["extended"]
    colors = {
        "sea": {"DEFAULT": sea["swell"], "deep": sea["trough"], "bright": sea["spray"], "pale": sea["foam"]},
        "fire": {"DEFAULT": fire["ember"], "ember": fire["ember"], "flame": fire["flame"], "oil": fire["oil"]},
        "whale": wh["whale"], "bone": wh["bone"], "gull": wh["gull"],
        "pitch": gr["pitch"], "hold": gr["hold"], "deck": gr["deck"], "iron": gr["iron"],
        "kelp": ext["kelp"], "brick": ext["brick"], "dusk": ext["dusk"], "tide": ext["tide"], "shoal": ext["shoal"],
    }
    fontFamily = {"serif": [tg["fonts"]["serif"]["family"], "Georgia", "serif"],
                  "sans": [tg["fonts"]["sans"]["family"], "system-ui", "sans-serif"],
                  "mono": [tg["fonts"]["mono"]["family"], "ui-monospace", "monospace"]}
    lineHeight = typ["scale"]["leading"]
    letterSpacing = {"tight": "-0.02em", "snug": "-0.01em", "normal": "0", "wide": "0.05em", "eyebrow": "0.18em"}
    md = D["motion"]
    transitionDuration = dict(md["durations"])
    transitionTimingFunction = dict(md["easings"])
    return ("// Generated from try-works.json. Edit the json, then `make generate`.\n"
            "module.exports = {\n  colors: %s,\n  fontFamily: %s,\n  fontSize: %s,\n"
            "  lineHeight: %s,\n  letterSpacing: %s,\n  spacing: %s,\n  borderRadius: %s,\n"
            "  transitionDuration: %s,\n  transitionTimingFunction: %s,\n};\n"
            % (_js(colors), _js(fontFamily), _js(typ["scale"]["steps"]),
               _js(lineHeight), _js(letterSpacing), _js(sp["scale"]), _js(sp["radius"]),
               _js(transitionDuration), _js(transitionTimingFunction)))

def build_ghostty(D):
    t, lit = D["terminal"], D["modes"]["lit"]
    g = ["# Try-Works (%s) — Ghostty theme. Generated from try-works.json." % lit["label"],
         "background = %s" % t["background"], "foreground = %s" % t["foreground"],
         "cursor-color = %s" % t["cursor"], "cursor-text = %s" % t["cursor-text"],
         "selection-background = %s" % t["selection-bg"], "selection-foreground = %s" % t["selection-fg"]]
    g += ["palette = %d=%s" % (i, c) for i, c in enumerate(t["ansi"])]
    return "\n".join(g) + "\n"

def build_vscode(D):
    lit, pal, codem, t = D["modes"]["lit"], D["palette"], D["code"], D["terminal"]
    fire, sea, ext = pal["fire"], pal["sea"], pal["extended"]; ansi = t["ansi"]
    c = lambda r: codem[r]["color"]; stl = lambda r: codem[r].get("style")
    SC = {
     "comment": ["comment", "punctuation.definition.comment"],
     "keyword": ["keyword", "keyword.control", "storage.type", "storage.modifier", "keyword.other", "keyword.operator.arrow.r", "keyword.operator.assignment.r"],
     "string": ["string", "string.quoted", "punctuation.definition.string", "constant.character.escape", "string.regexp"],
     "number": ["constant.numeric", "constant.language", "constant.language.boolean", "constant.language.python"],
     "function": ["entity.name.function", "meta.function-call", "support.function", "entity.name.function.r"],
     "type": ["entity.name.type", "entity.name.class", "support.type", "support.class", "storage.type.class.python", "entity.name.type.class.python", "support.function.builtin"],
     "decorator": ["meta.decorator", "punctuation.definition.decorator", "entity.name.function.decorator.python", "entity.name.tag", "keyword.other.namespace", "support.other.namespace"],
     "variable": ["variable", "variable.other", "meta.definition.variable", "variable.other.r"],
     "parameter": ["variable.parameter", "variable.parameter.python"],
     "operator": ["keyword.operator", "keyword.operator.r"],
     "punctuation": ["punctuation", "meta.brace", "punctuation.separator", "punctuation.terminator"],
    }
    tokenColors = []
    for role, scopes in SC.items():
        s = {"foreground": c(role)}
        if stl(role): s["fontStyle"] = stl(role)
        tokenColors.append({"scope": scopes, "settings": s})
    tokenColors += [
     {"scope": ["markup.heading", "entity.name.section"], "settings": {"foreground": fire["ember"], "fontStyle": "bold"}},
     {"scope": ["markup.bold"], "settings": {"foreground": lit["text"], "fontStyle": "bold"}},
     {"scope": ["markup.italic"], "settings": {"foreground": lit["text"], "fontStyle": "italic"}},
     {"scope": ["markup.underline.link", "string.other.link"], "settings": {"foreground": c("function"), "fontStyle": "underline"}},
     {"scope": ["markup.inline.raw"], "settings": {"foreground": c("type")}},
     {"scope": ["invalid"], "settings": {"foreground": c("decorator")}},
    ]
    semantic = {"keyword": c("keyword"), "string": c("string"), "number": c("number"),
     "function": c("function"), "method": c("function"), "function.defaultLibrary": c("type"),
     "class": c("type"), "type": c("type"), "struct": c("type"), "interface": c("type"), "enum": c("type"),
     "namespace": c("decorator"), "decorator": c("decorator"), "macro": c("number"),
     "variable": c("variable"), "parameter": c("parameter"), "variable.readonly": c("number"),
     "operator": c("operator"), "comment": {"foreground": c("comment"), "fontStyle": "italic"}}
    a = lambda x: x + "66"
    wb = {
     "editor.background": lit["bg"], "editor.foreground": lit["text"],
     "editorLineNumber.foreground": "#606c72", "editorLineNumber.activeForeground": lit["text-muted"],
     "editorCursor.foreground": fire["ember"], "editor.selectionBackground": a(lit["sea"]),
     "editor.lineHighlightBackground": lit["surface"], "editor.findMatchHighlightBackground": fire["flame"] + "33",
     "editorBracketHighlight.foreground1": sea["foam"], "editorBracketHighlight.foreground2": fire["ember"],
     "editorBracketHighlight.foreground3": ext["dusk"], "editorBracketHighlight.foreground4": ext["kelp"],
     "editorBracketHighlight.foreground5": ext["tide"], "editorBracketHighlight.foreground6": ext["brick"],
     "editorError.foreground": ext["brick"], "editorWarning.foreground": fire["ember"], "editorInfo.foreground": ext["tide"],
     "focusBorder": fire["ember"], "button.background": fire["ember"], "button.foreground": lit["on-accent"],
     "button.hoverBackground": fire["flame"], "badge.background": fire["ember"], "badge.foreground": lit["on-accent"],
     "input.background": lit["surface"], "input.border": lit["border"], "inputOption.activeBorder": fire["ember"],
     "list.activeSelectionBackground": lit["surface-raised"], "list.highlightForeground": fire["ember"], "list.hoverBackground": "#1d242b",
     "sideBar.background": lit["surface"], "sideBar.foreground": "#cdd2d3", "sideBar.border": lit["border"],
     "sideBarTitle.foreground": lit["text-muted"], "sideBarSectionHeader.background": lit["bg"],
     "activityBar.background": lit["bg"], "activityBar.foreground": lit["text"],
     "activityBarBadge.background": fire["ember"], "activityBarBadge.foreground": lit["on-accent"],
     "statusBar.background": lit["surface"], "statusBar.foreground": lit["text-muted"], "statusBar.border": lit["border"],
     "statusBar.debuggingBackground": fire["ember"], "statusBar.debuggingForeground": lit["on-accent"],
     "titleBar.activeBackground": lit["bg"], "titleBar.activeForeground": lit["text"], "titleBar.border": lit["border"],
     "tab.activeBackground": lit["bg"], "tab.inactiveBackground": lit["surface"], "tab.activeForeground": lit["text"],
     "tab.inactiveForeground": lit["text-muted"], "tab.activeBorderTop": fire["ember"], "tab.border": lit["border"],
     "editorGroupHeader.tabsBackground": lit["surface"], "panel.background": lit["bg"], "panel.border": lit["border"],
     "panelTitle.activeBorder": fire["ember"],
     "terminal.background": lit["bg"], "terminal.foreground": lit["text"], "terminalCursor.foreground": fire["ember"],
     "gitDecoration.modifiedResourceForeground": fire["ember"], "gitDecoration.untrackedResourceForeground": ext["kelp"],
     "gitDecoration.deletedResourceForeground": ext["brick"],
     "textLink.foreground": ext["tide"], "textLink.activeForeground": fire["flame"],
    }
    for i, k in enumerate(["Black","Red","Green","Yellow","Blue","Magenta","Cyan","White","BrightBlack","BrightRed","BrightGreen","BrightYellow","BrightBlue","BrightMagenta","BrightCyan","BrightWhite"]):
        wb["terminal.ansi" + k] = ansi[i]
    theme = {"name": "Try-Works", "type": "dark", "semanticHighlighting": True,
             "semanticTokenColors": semantic, "colors": wb, "tokenColors": tokenColors}
    return json.dumps(theme, indent=2) + "\n"

def build_obsidian(D):
    lit, cold = D["modes"]["lit"], D["modes"]["cold"]
    def blk(m, sel, ah):
        return (f".{sel} {{\n  --accent-h: {ah[0]}; --accent-s: {ah[1]}%; --accent-l: {ah[2]}%;\n"
                f"  --background-primary: {m['bg']};\n  --background-secondary: {m['surface']};\n"
                f"  --background-secondary-alt: {m['surface-raised']};\n  --background-modifier-border: {m['border']};\n"
                f"  --background-modifier-hover: {m['sea-bright']}1f;\n  --text-normal: {m['text']};\n"
                f"  --text-muted: {m['text-muted']};\n  --text-accent: {m['accent']};\n  --text-accent-hover: {m['accent-bright']};\n"
                f"  --text-on-accent: {m['on-accent']};\n  --interactive-accent: {m['accent']};\n"
                f"  --interactive-accent-hover: {m['accent-bright']};\n  --link-color: {m['accent']};\n"
                f"  --hr-color: {m['border']};\n  --blockquote-border-color: {m['accent']};\n"
                f"  --code-background: {m['surface']};\n  --tag-color: {m['accent']};\n  --tag-background: {m['accent']}1f;\n}}")
    return ("/* Try-Works for Obsidian. Generated from try-works.json. */\nbody {\n"
            '  --font-text-theme: "Fraunces", Georgia, serif;\n'
            '  --font-interface-theme: "Archivo", system-ui, sans-serif;\n'
            '  --font-monospace-theme: "JetBrains Mono", ui-monospace, monospace;\n}\n\n'
            + blk(lit, "theme-dark", hsl(lit["accent"])) + "\n\n" + blk(cold, "theme-light", hsl(cold["accent"])) + "\n\n"
            '.markdown-rendered h1, .inline-title { font-family: var(--font-text); font-variation-settings: "opsz" 96, "wght" 600, "WONK" 1; }\n'
            '.markdown-rendered h2 { font-family: var(--font-text); font-variation-settings: "opsz" 60, "wght" 600, "WONK" 1; }\n'
            '.markdown-rendered blockquote { background: var(--background-modifier-hover); border-radius: 0 4px 4px 0; }\n')

def build_typst(D):
    m = D["modes"]["lit"]
    pairs = [("pitch", m["bg"]), ("hold", m["surface"]), ("sea-deep", m["sea-deep"]), ("sea", m["sea"]),
             ("sea-bright", m["sea-bright"]), ("sea-pale", m["sea-pale"]), ("ember", m["accent"]),
             ("flame", m["accent-bright"]), ("whale", m["text"]), ("gull", m["text-muted"])]
    return "// Try-Works colours. Generated from try-works.json.\n" + "".join('#let %s = rgb("%s")\n' % (n, v) for n, v in pairs)

def stamp_version(rel, D):
    obj = json.loads((ROOT / rel).read_text())
    obj["version"] = D["version"]
    return json.dumps(obj, indent=2) + "\n"

def build_p3(D):
    g = D.get("gamut", {}).get("p3")
    if not g:
        return "/* no p3 block in json */\n"
    lit, cold = g["lit"], g["cold"]
    return ("/* Wide-gamut fire. Generated. Outside P3 the sRGB hexes in try-works.css apply. */\n"
            "@media (color-gamut: p3) {\n"
            '  :root,\n  [data-mode="lit"] { --tw-accent: %s; --tw-accent-bright: %s; }\n'
            '  [data-mode="cold"] { --tw-accent: %s; --tw-accent-bright: %s; }\n}\n'
            % (lit["accent"], lit["accent-bright"], cold["accent"], cold["accent-bright"]))

def artifacts(D):
    css = build_css(D)
    typo = build_typography(D)
    return {
        "css/try-works.css": css,
        "css/typography.css": typo,
        "css/p3.css": build_p3(D),
        "css/a11y.css": build_a11y(D),
        "css/fallbacks.css": build_fallbacks(D),
        "css/motion.css": build_motion(D),
        "web/src/css/a11y.css": build_a11y(D),
        "web/src/css/fallbacks.css": build_fallbacks(D),
        "web/src/css/motion.css": build_motion(D),
        "r/tryworks.R": build_r(D),
        "python/tryworks.mplstyle": build_mplstyle(D),
        "python/tryworks.py": build_pyviz(D),
        "print/SPEC.md": build_print_md(D),
        "typst/poster.typ": build_poster_typ(D),
        "quarto/try-works.scss": build_quarto_scss(D, "cold"),
        "quarto/try-works-dark.scss": build_quarto_scss(D, "lit"),
        "quarto/try-works.theme": build_quarto_theme(D),
        "quarto/typst-brand.typ": build_typst_brand(D),
        "web/src/css/try-works.css": css,
        "web/src/css/typography.css": typo,
        "web/src/css/p3.css": build_p3(D),
        "tailwind/colors.generated.js": build_tailwind(D),
        "themes/terminals/Try-Works.ghostty": build_ghostty(D),
        "vscode/themes/Try-Works-color-theme.json": build_vscode(D),
        "obsidian/theme.css": build_obsidian(D),
        "typst/colors.typ": build_typst(D),
        # version single-sourced into the manifests:
        "obsidian/manifest.json": stamp_version("obsidian/manifest.json", D),
        "vscode/package.json": stamp_version("vscode/package.json", D),
        "tailwind/package.json": stamp_version("tailwind/package.json", D),
    }

def main(argv):
    D = load()
    arts = artifacts(D)
    if "--check" in argv:
        drift = []
        for rel, content in arts.items():
            p = ROOT / rel
            if not p.exists() or p.read_text() != content:
                drift.append(rel)
        if drift:
            print("DRIFT: these files do not match try-works.json:")
            for d in drift: print("  " + d)
            print("Run `make generate` and commit.")
            return 1
        print("clean: %d generated files match the json" % len(arts))
        return 0
    for rel, content in arts.items():
        p = ROOT / rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(content)
    print("generated %d files from try-works.json" % len(arts))
    return 0



def build_r(D):
    dv = D["dataviz"]; pl = dv["plot"]; f = dv["fonts"]
    rv = lambda xs: "c(" + ", ".join('"%s"' % x for x in xs) + ")"
    L, K = pl["light"], pl["dark"]
    t = R_TEMPLATE
    repl = {"@@CAT@@": rv(dv["categorical"]["colors"]), "@@SEQ@@": rv(dv["sequential"]["colors"]),
            "@@DIV@@": rv(dv["diverging"]["colors"]), "@@PCH@@": "c(" + ", ".join(str(x) for x in dv["shapes"]["ggplot_pch"]) + ")", "@@BASE@@": f["base"], "@@TITLE@@": f["title"],
            "@@LBG@@": L["bg"], "@@LPANEL@@": L["panel"], "@@LTEXT@@": L["text"], "@@LGRID@@": L["grid"], "@@LMUTED@@": L["muted"],
            "@@DBG@@": K["bg"], "@@DPANEL@@": K["panel"], "@@DTEXT@@": K["text"], "@@DGRID@@": K["grid"], "@@DMUTED@@": K["muted"]}
    for k, v in repl.items(): t = t.replace(k, v)
    return t


def build_mplstyle(D):
    f = D["dataviz"]["fonts"]
    return ("# Generated from try-works.json. Try-Works matplotlib base (non-colour keys only).\n"
            "# Colours are applied by tryworks.use_tryworks(); hex values are not parsed here\n"
            "# because the style-file parser treats '#' as a comment.\n"
            "font.family: sans-serif\n"
            "font.sans-serif: %s, DejaVu Sans\n"
            "axes.grid: True\ngrid.linewidth: 0.6\n"
            "axes.spines.top: False\naxes.spines.right: False\n"
            "axes.titlelocation: left\n" % f["base"])


def build_pyviz(D):
    dv = D["dataviz"]; L = dv["plot"]["light"]; K = dv["plot"]["dark"]
    pl = lambda xs: "[" + ", ".join('"%s"' % x for x in xs) + "]"
    t = PY_TEMPLATE
    for k, v in {"@@CAT@@": pl(dv["categorical"]["colors"]), "@@SEQ@@": pl(dv["sequential"]["colors"]),
                 "@@DIV@@": pl(dv["diverging"]["colors"]), "@@MARK@@": pl(dv["shapes"]["matplotlib"]),
                 "@@LBG@@": L["bg"], "@@LPANEL@@": L["panel"], "@@LTEXT@@": L["text"], "@@LGRID@@": L["grid"], "@@LMUTED@@": L["muted"],
                 "@@DBG@@": K["bg"], "@@DPANEL@@": K["panel"], "@@DTEXT@@": K["text"], "@@DGRID@@": K["grid"], "@@DMUTED@@": K["muted"]}.items():
        t = t.replace(k, v)
    return t


R_TEMPLATE = r'''# Generated from try-works.json - do not edit by hand.
# Try-Works: ggplot2 scales and theme. Source the file, then add the scales/theme to a plot.

tryworks_categorical <- @@CAT@@
tryworks_sequential  <- @@SEQ@@
tryworks_diverging   <- @@DIV@@
tryworks_shapes      <- @@PCH@@

.tryworks_plot <- list(
  light = list(bg="@@LBG@@", panel="@@LPANEL@@", text="@@LTEXT@@", grid="@@LGRID@@", muted="@@LMUTED@@"),
  dark  = list(bg="@@DBG@@", panel="@@DPANEL@@", text="@@DTEXT@@", grid="@@DGRID@@", muted="@@DMUTED@@")
)

tryworks_pal_d <- function(n) {
  if (n > length(tryworks_categorical))
    warning("Try-Works categorical has ", length(tryworks_categorical), " colours; ", n, " requested.")
  unname(tryworks_categorical[seq_len(n)])
}

scale_colour_tryworks_d   <- function(...) ggplot2::discrete_scale("colour", "tryworks", tryworks_pal_d, ...)
scale_fill_tryworks_d     <- function(...) ggplot2::discrete_scale("fill", "tryworks", tryworks_pal_d, ...)
scale_colour_tryworks_c   <- function(...) ggplot2::scale_colour_gradientn(colours = tryworks_sequential, ...)
scale_fill_tryworks_c     <- function(...) ggplot2::scale_fill_gradientn(colours = tryworks_sequential, ...)
scale_colour_tryworks_div <- function(...) ggplot2::scale_colour_gradientn(colours = tryworks_diverging, ...)
scale_fill_tryworks_div   <- function(...) ggplot2::scale_fill_gradientn(colours = tryworks_diverging, ...)
scale_color_tryworks_d    <- scale_colour_tryworks_d
scale_color_tryworks_c    <- scale_colour_tryworks_c
scale_color_tryworks_div  <- scale_colour_tryworks_div
scale_shape_tryworks_d    <- function(...) ggplot2::scale_shape_manual(values = tryworks_shapes, ...)

theme_tryworks <- function(base_size = 12, base_family = "@@BASE@@", mode = c("light", "dark")) {
  mode <- match.arg(mode); p <- .tryworks_plot[[mode]]
  ggplot2::theme_minimal(base_size = base_size, base_family = base_family) +
    ggplot2::theme(
      plot.background  = ggplot2::element_rect(fill = p$bg, colour = NA),
      panel.background = ggplot2::element_rect(fill = p$panel, colour = NA),
      panel.grid.major = ggplot2::element_line(colour = p$grid, linewidth = 0.3),
      panel.grid.minor = ggplot2::element_blank(),
      axis.text   = ggplot2::element_text(colour = p$muted),
      axis.title  = ggplot2::element_text(colour = p$text),
      plot.title  = ggplot2::element_text(colour = p$text, family = "@@TITLE@@"),
      plot.subtitle = ggplot2::element_text(colour = p$muted),
      legend.text  = ggplot2::element_text(colour = p$text),
      legend.title = ggplot2::element_text(colour = p$text)
    )
}
'''

PY_TEMPLATE = r'''"""Generated from try-works.json - do not edit by hand.
Try-Works matplotlib colours, colormaps, and style helper."""
import os
import matplotlib as mpl
import matplotlib.pyplot as plt
from cycler import cycler
from matplotlib.colors import LinearSegmentedColormap

TRYWORKS_CATEGORICAL = @@CAT@@
TRYWORKS_SEQUENTIAL  = @@SEQ@@
TRYWORKS_DIVERGING   = @@DIV@@
TRYWORKS_MARKERS     = @@MARK@@

tryworks_seq = LinearSegmentedColormap.from_list("tryworks_seq", TRYWORKS_SEQUENTIAL)
tryworks_div = LinearSegmentedColormap.from_list("tryworks_div", TRYWORKS_DIVERGING)
for _cm in (tryworks_seq, tryworks_div):
    try:
        mpl.colormaps.register(_cm)
    except (ValueError, AttributeError):
        pass

_LIGHT = dict(bg="@@LBG@@", panel="@@LPANEL@@", text="@@LTEXT@@", grid="@@LGRID@@", muted="@@LMUTED@@")
_DARK  = dict(bg="@@DBG@@", panel="@@DPANEL@@", text="@@DTEXT@@", grid="@@DGRID@@", muted="@@DMUTED@@")

def _apply(p):
    mpl.rcParams.update({
        "axes.prop_cycle": (cycler(color=TRYWORKS_CATEGORICAL) + cycler(marker=TRYWORKS_MARKERS)),
        "figure.facecolor": p["bg"], "axes.facecolor": p["panel"],
        "text.color": p["text"], "axes.labelcolor": p["text"], "axes.titlecolor": p["text"],
        "axes.edgecolor": p["muted"], "xtick.color": p["muted"], "ytick.color": p["muted"],
        "grid.color": p["grid"],
    })

def use_tryworks(mode="light"):
    """Apply the Try-Works style. mode='light' (default) or 'dark'."""
    plt.style.use(os.path.join(os.path.dirname(__file__), "tryworks.mplstyle"))
    _apply(_DARK if mode == "dark" else _LIGHT)
'''

def build_print_md(D):
    p = D["print"]
    rows = "\n".join("| %s | %s |" % (k, v) for k, v in p["cmyk"].items())
    sizes = "\n".join("- %s: %s mm (trim)" % (k, v) for k, v in p["sizes_mm"].items())
    return ("# Try-Works - print specification\n\n"
            "Generated from try-works.json. %s\n\n"
            "## Colour management\nProfile: %s\nInk limit: %s\n\n"
            "## Rich black\n%s. %s\n\n"
            "## CMYK starting values\n| token | CMYK |\n| --- | --- |\n%s\n\n"
            "## Gamut risks\nThese desaturate in process; proof them or run as spot: %s.\n\n%s\n\n"
            "## Geometry\nBleed: %d mm. Safe margin: %d mm from trim.\n\n%s\n"
            % (p["note"], p["profile"], p["ink_limit"], p["rich_black"]["recipe"], p["rich_black"]["note"],
               rows, ", ".join(p["gamut_risk"]), p["spot"], p["bleed_mm"], p["safe_mm"], sizes))


def build_poster_typ(D):
    L = D["modes"]["lit"]; C = D["modes"]["cold"]
    t = POSTER_TEMPLATE
    for k, v in {"@@PITCH@@": L["bg"], "@@WHALE@@": L["text"], "@@EMBER@@": L["accent"], "@@FLAME@@": L["accent-bright"],
                 "@@SEADEEP@@": L["sea-deep"], "@@SEA@@": L["sea"], "@@PAPER@@": C["bg"], "@@INK@@": C["text"]}.items():
        t = t.replace(k, v)
    return t


POSTER_TEMPLATE = r'''// Generated from try-works.json. Try-Works poster preset (Typst).
// Colours below are screen sRGB; substitute the CMYK in print/SPEC.md at output.

#let tw = (
  pitch: rgb("@@PITCH@@"), whale: rgb("@@WHALE@@"),
  ember: rgb("@@EMBER@@"), flame: rgb("@@FLAME@@"),
  seadeep: rgb("@@SEADEEP@@"), sea: rgb("@@SEA@@"),
  paper: rgb("@@PAPER@@"), ink: rgb("@@INK@@"),
)

// poster(trim, bleed, safe, fill, body): page = trim + 2*bleed, with crop marks
// (top-left and bottom-right shown) and a non-printing safe-area guide.
#let poster(trim: (420mm, 594mm), bleed: 3mm, safe: 5mm, fill: tw.seadeep, body) = {
  set page(width: trim.at(0) + 2*bleed, height: trim.at(1) + 2*bleed, margin: 0pt, fill: fill)
  let m = 4mm
  place(top + left, dx: bleed, dy: 0mm, line(end: (0mm, m), stroke: 0.25pt + tw.whale))
  place(top + left, dx: 0mm, dy: bleed, line(end: (m, 0mm), stroke: 0.25pt + tw.whale))
  place(bottom + right, dx: -bleed, dy: 0mm, line(end: (0mm, -m), stroke: 0.25pt + tw.whale))
  place(bottom + right, dx: 0mm, dy: -bleed, line(end: (-m, 0mm), stroke: 0.25pt + tw.whale))
  place(top + left, dx: bleed + safe, dy: bleed + safe,
    rect(width: trim.at(0) - 2*safe, height: trim.at(1) - 2*safe,
      stroke: (paint: tw.ember, thickness: 0.25pt, dash: "dotted")))
  place(top + left, dx: bleed, dy: bleed,
    block(width: trim.at(0), height: trim.at(1), inset: safe + 10mm, body))
}

// Demo: the fire as the one hot mark on a cold field.
#poster(fill: tw.seadeep)[
  #set text(fill: tw.whale, font: "Fraunces")
  #text(size: 13pt, fill: tw.flame, font: "JetBrains Mono", tracking: 3pt)[A MOBY-DICK DESIGN SYSTEM]
  #v(1fr)
  #text(size: 110pt, weight: 600)[Try-Works]
  #v(6mm)
  #text(size: 22pt)[Look not too long in the face of the fire.]
]
'''


def build_a11y(D):
    a = D["a11y"]; f = a["focus"]; cm = a["contrast_more"]
    return ("/* Generated accessibility layer: focus, forced-colors, higher-contrast, reduced-transparency. */\n"
            ':root,\n[data-mode="lit"] { --tw-focus: %s; }\n[data-mode="cold"] { --tw-focus: %s; }\n\n'
            ":where(a, button, input, select, textarea, [tabindex]):focus-visible {\n"
            "  outline: %s solid var(--tw-focus);\n  outline-offset: %s;\n}\n"
            ":where(a, button, input, select, textarea, [tabindex]):focus:not(:focus-visible) { outline: none; }\n\n"
            "@media (prefers-contrast: more) {\n"
            '  :root,\n  [data-mode="lit"] { --tw-text-muted: %s; --tw-border: %s; }\n'
            '  [data-mode="cold"] { --tw-text-muted: %s; --tw-border: %s; }\n}\n\n'
            "@media (forced-colors: active) {\n"
            '  :where(button, .btn, [role="button"]) { border: 1px solid ButtonText; }\n'
            "  :where(a, button, input, select, textarea, [tabindex]):focus-visible { outline: 2px solid Highlight; outline-offset: 2px; }\n}\n\n"
            "@media (prefers-reduced-transparency: reduce) {\n  .hero::after { display: none; }\n}\n"
            % (f["lit"], f["cold"], f["width"], f["offset"],
               cm["lit"]["text-muted"], cm["lit"]["border"], cm["cold"]["text-muted"], cm["cold"]["border"]))


def build_fallbacks(D):
    fb = D["performance"]["fallbacks"]
    out = ["/* Generated metric-matched fallbacks. local() fallback with overrides so the swap does not shift text. */"]
    for name, m in fb.items():
        out += ['@font-face {',
                '  font-family: "%s fallback";' % name,
                '  src: local("%s");' % m["fallback"],
                '  size-adjust: %s%%;' % m["size_adjust"],
                '  ascent-override: %s%%;' % m["ascent"],
                '  descent-override: %s%%;' % m["descent"],
                '  line-gap-override: %s%%;' % m["line_gap"],
                '}']
    return "\n".join(out) + "\n"


def build_motion(D):
    m = D["motion"]
    out = ["/* Generated motion tokens. Restrained by intent; reduced-motion respected. */", ":root {"]
    out += ["  --tw-duration-%s: %s;" % (k, v) for k, v in m["durations"].items()]
    out += ["  --tw-ease-%s: %s;" % (k, v) for k, v in m["easings"].items()]
    out += ["}", "",
            "@media (prefers-reduced-motion: reduce) {",
            "  *, *::before, *::after {",
            "    animation-duration: 0.01ms !important;",
            "    animation-iteration-count: 1 !important;",
            "    transition-duration: 0.01ms !important;",
            "    scroll-behavior: auto !important;",
            "  }", "}"]
    return "\n".join(out) + "\n"


def build_quarto_scss(D, modekey):
    m = D["modes"][modekey]; fonts = D["typography"]["fonts"]
    serif = fonts["serif"]["family"]; mono = fonts["mono"]["family"]; reading = fonts["reading"]["family"]
    h1 = m["accent"]
    return ("/*-- scss:defaults --*/\n"
            "$body-bg: %s;\n$body-color: %s;\n$link-color: %s;\n$border-color: %s;\n"
            '$font-family-base: "%s", Georgia, serif;\n'
            '$headings-font-family: "%s", Georgia, serif;\n'
            '$font-family-monospace: "%s", ui-monospace, monospace;\n'
            "$code-color: %s;\n$code-bg: %s;\n$blockquote-border-color: %s;\n\n"
            "/*-- scss:rules --*/\n"
            "body { font-variant-numeric: oldstyle-nums proportional-nums; line-height: 1.62; }\n"
            'h1, h2, h3, h4 { font-variation-settings: "opsz" 60, "wght" 600, "WONK" 1; letter-spacing: -0.01em; text-wrap: balance; }\n'
            "h1 { color: %s; }\n"
            "a { text-underline-offset: 0.15em; }\n"
            ".callout { border-inline-start-color: %s; }\n"
            'pre, code { font-feature-settings: "liga" 1, "calt" 1; }\n'
            % (m["bg"], m["text"], m["accent"], m["border"], reading, serif, mono,
               m["accent-deep"], m["surface"], m["accent"], h1, m["accent"]))


def build_quarto_theme(D):
    c = D["code"]; lit = D["modes"]["lit"]
    def st(role):
        r = c[role]; sty = r.get("style", "")
        return {"text-color": r["color"], "background-color": None,
                "bold": sty == "bold", "italic": sty == "italic", "underline": False}
    role = {"Keyword": "keyword", "ControlFlow": "keyword", "Import": "keyword",
            "DataType": "type", "BuiltIn": "type",
            "DecVal": "number", "BaseN": "number", "Float": "number", "Constant": "number",
            "Char": "string", "String": "string", "VerbatimString": "string", "SpecialString": "string",
            "Comment": "comment", "CommentVar": "comment", "Documentation": "comment",
            "Function": "function", "Operator": "operator", "Variable": "variable",
            "Attribute": "decorator", "Annotation": "decorator", "Preprocessor": "decorator",
            "Other": "variable", "Normal": "variable"}
    theme = {"text-color": c["variable"]["color"], "background-color": lit["surface"],
             "line-number-color": lit["text-muted"], "line-number-background-color": None,
             "text-styles": {k: st(v) for k, v in role.items()}}
    return json.dumps(theme, indent=2) + "\n"


def build_typst_brand(D):
    c = D["modes"]["cold"]; fonts = D["typography"]["fonts"]
    return ("// Try-Works brand for Quarto Typst output. Generated.\n"
            "// _quarto.yml:  format: typst: { include-in-header: typst-brand.typ }\n"
            '#set text(font: "%s", size: 11pt, fill: rgb("%s"))\n'
            '#show heading: set text(font: "%s", fill: rgb("%s"))\n'
            '#show heading.where(level: 1): set text(fill: rgb("%s"))\n'
            '#show link: set text(fill: rgb("%s"))\n'
            '#show raw: set text(font: "%s")\n'
            % (fonts["reading"]["family"], c["text"], fonts["serif"]["family"], c["text"],
               c["accent"], c["accent"], fonts["mono"]["family"]))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
