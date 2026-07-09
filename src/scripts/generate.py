#!/usr/bin/env python3
"""Generate every Try-Works surface from src/try-works.json (the single source of truth).

Usage:
  python3 src/scripts/generate.py            write generated files into dist/
  python3 src/scripts/generate.py --check    verify files match the json; exit 1 on drift

`--check` is what CI runs: it regenerates in memory and diffs against the committed
files, so any hand-edit of a generated file fails the build.

Layout: authoring inputs live under src/; generated tokens are written under dist/
(committed). The web app embeds its generated CSS in place at src/web/src/css.
"""
import json, pathlib, sys, uuid
from generate_obsidian import build_obsidian, _mix

SRC = pathlib.Path(__file__).resolve().parent.parent   # src/ (authoring inputs)
REPO = SRC.parent                                       # repo root (holds dist/)

def load():
    return json.loads((SRC / "try-works.json").read_text())

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

def build_ghostty_cold(D):
    """True Lamp (light) Ghostty theme: bg/fg/cursor/selection from modes.cold,
    keeping the same 16-colour identity palette (Solarized-style mode swap)."""
    cold, ansi = D["modes"]["cold"], D["terminal"]["ansi"]
    g = ["# Try-Works (%s) — Ghostty theme (light). Generated from try-works.json." % cold["label"],
         "background = %s" % cold["bg"], "foreground = %s" % cold["text"],
         "cursor-color = %s" % cold["accent"], "cursor-text = %s" % cold["on-accent"],
         "selection-background = %s" % cold["sea"], "selection-foreground = %s" % cold["on-sea"]]
    g += ["palette = %d=%s" % (i, c) for i, c in enumerate(ansi)]
    return "\n".join(g) + "\n"

def _iterm_color(hexv):
    """One iTerm2 colour <dict>: sRGB components as 0-1 floats (repr is
    deterministic, so the drift gate stays stable), keys in iTerm's own
    alphabetical export order."""
    h = hexv.lstrip("#")
    r, g, b = (int(h[i:i+2], 16) / 255 for i in (0, 2, 4))
    return ("\t<dict>\n"
            "\t\t<key>Alpha Component</key>\n\t\t<real>1</real>\n"
            "\t\t<key>Blue Component</key>\n\t\t<real>%r</real>\n"
            "\t\t<key>Color Space</key>\n\t\t<string>sRGB</string>\n"
            "\t\t<key>Green Component</key>\n\t\t<real>%r</real>\n"
            "\t\t<key>Red Component</key>\n\t\t<real>%r</real>\n"
            "\t</dict>" % (b, g, r))

def _iterm_plist(pairs):
    body = "\n".join("\t<key>%s</key>\n%s" % (k, _iterm_color(v)) for k, v in pairs)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
            '<plist version="1.0">\n<dict>\n' + body + "\n</dict>\n</plist>\n")

def build_iterm(D):
    """Try-Fire (dark) iTerm2 preset: same sources as build_ghostty. Bold reuses
    the foreground and Link is ANSI 12 (bright tide) -- iTerm falls back to its
    own defaults for any key a preset omits, so both are pinned explicitly."""
    t = D["terminal"]
    pairs = [("Ansi %d Color" % i, c) for i, c in enumerate(t["ansi"])]
    pairs += [("Background Color", t["background"]), ("Bold Color", t["foreground"]),
              ("Cursor Color", t["cursor"]), ("Cursor Text Color", t["cursor-text"]),
              ("Foreground Color", t["foreground"]), ("Link Color", t["ansi"][12]),
              ("Selected Text Color", t["selection-fg"]), ("Selection Color", t["selection-bg"])]
    return _iterm_plist(pairs)

def build_iterm_cold(D):
    """True Lamp (light) iTerm2 preset: chrome from modes.cold, same 16-colour
    identity palette (mirrors build_ghostty_cold). Link uses cold sea-bright,
    not the ANSI bright blue -- it must stay readable on the light background
    (sea-bright/bg is a validate.py-locked pair)."""
    cold, ansi = D["modes"]["cold"], D["terminal"]["ansi"]
    pairs = [("Ansi %d Color" % i, c) for i, c in enumerate(ansi)]
    pairs += [("Background Color", cold["bg"]), ("Bold Color", cold["text"]),
              ("Cursor Color", cold["accent"]), ("Cursor Text Color", cold["on-accent"]),
              ("Foreground Color", cold["text"]), ("Link Color", cold["sea-bright"]),
              ("Selected Text Color", cold["on-sea"]), ("Selection Color", cold["sea"])]
    return _iterm_plist(pairs)

def _omz_theme(label, note, path, paren, branch, dirty, caret_ok, caret_err, err):
    """One oh-my-zsh .zsh-theme. Truecolor (%F{#hex}, zsh >= 5.7) so the prompt
    carries the exact brand hues in any terminal, and pairs cleanly with the
    Try-Works terminal preset. Two-line prompt: cwd + git on line one, caret on
    line two. Discipline holds -- the whole prompt is cool sea; the ember fire
    lights in exactly one place, the git-dirty mark; a failed command uses red
    (brick), a distinct signal, not the brand fire."""
    F = lambda h: "%F{" + h + "}"
    return "\n".join([
        "# Try-Works (%s) -- oh-my-zsh theme. Generated from try-works.json." % label,
        "# %s" % note,
        "# Truecolor prompt (needs zsh >= 5.7). Cool sea is the field; the ember",
        "# fire marks only uncommitted work; a red caret/code means the last command failed.",
        "",
        'ZSH_THEME_GIT_PROMPT_PREFIX=" ' + F(paren) + "(" + F(branch) + '"',
        'ZSH_THEME_GIT_PROMPT_SUFFIX="' + F(paren) + ')%f"',
        'ZSH_THEME_GIT_PROMPT_DIRTY="' + F(dirty) + '*"',
        'ZSH_THEME_GIT_PROMPT_CLEAN=""',
        "",
        "PROMPT='" + F(path) + "%~%f$(git_prompt_info)",
        "%(?." + F(caret_ok) + "." + F(caret_err) + ")❯%f '",
        "RPROMPT='%(?.." + F(err) + "%?%f)'",
        "",
    ])

def build_omz(D):
    """Try-Fire (dark) oh-my-zsh prompt: brand hues straight from the palette."""
    pal, lit = D["palette"], D["modes"]["lit"]
    return _omz_theme("Try-Fire", "Dark.",
        path=pal["sea"]["foam"], paren=lit["sea-bright"], branch=pal["extended"]["shoal"],
        dirty=pal["fire"]["ember"], caret_ok=lit["sea-bright"],
        caret_err=pal["extended"]["brick"], err=pal["extended"]["brick"])

def build_omz_cold(D):
    """True Lamp (light) oh-my-zsh prompt: cold-mode chrome plus the extended
    hues darkened toward the cold ink (t=0.45, the shared light-safe ratio) so
    branch/error read on a light terminal background."""
    cold, ex = D["modes"]["cold"], D["palette"]["extended"]
    ls = lambda h: _mix(h, cold["text"], 0.45)
    return _omz_theme("True Lamp", "Light.",
        path=cold["sea-bright"], paren=cold["text-muted"], branch=ls(ex["shoal"]),
        dirty=cold["accent"], caret_ok=cold["sea-bright"],
        caret_err=ls(ex["brick"]), err=ls(ex["brick"]))

def build_vivaldi(D, modekey):
    """Vivaldi browser theme (settings.json). Schema matches a current exported
    Vivaldi theme (engineVersion 1, verified against installed themes): five base
    colours -- Vivaldi derives the rest -- plus behaviour flags and a stable id.
    assemble.sh zips this into an importable .zip per mode. The id is derived
    deterministically (uuid5) so regeneration does not drift.

    - contrast 5, not Vivaldi's looser 2: it is the minimum-contrast floor Vivaldi
      enforces on the UI text it DERIVES from these colours (active-tab titles on
      the sea highlight, text on the fire accent). 2 under-enforces; 5 holds the
      AA-ish floor this system guarantees everywhere else. Our own colorFg is 12:1
      on colorBg, so it is never the one Vivaldi has to override.
    - radius 6 = the system's `lg` radius token (spacing.radius.lg).
    - opaque (alpha 1, blur 0): no translucency gimmick; chrome stays legible.
    - accentOnWindow false keeps the fire off the whole window -- it marks only the
      accent elements Vivaldi paints with colorAccentBg, so the fire stays rare."""
    m = D["modes"][modekey]
    up = lambda h: h.upper()
    name = "Try-Works" if modekey == "lit" else "Try-Works (True Lamp)"
    tid = str(uuid.uuid5(uuid.NAMESPACE_URL, "try-works.vivaldi." + modekey))
    theme = {
        "accentFromPage": False, "accentOnWindow": False, "accentSaturationLimit": 1,
        "alpha": 1, "backgroundImage": "", "backgroundPosition": "stretch", "backgroundSource": "",
        "blur": 0, "colorAccentBg": up(m["accent"]), "colorBg": up(m["bg"]), "colorFg": up(m["text"]),
        "colorHighlightBg": up(m["sea"]), "colorPosition": "unified", "colorWindowBg": up(m["surface"]),
        "contrast": 5, "dimBlurred": False, "engineVersion": 1, "id": tid, "name": name,
        "preferSystemAccent": False, "radius": 6, "simpleScrollbar": False,
        "transparencyTabBar": False, "transparencyTabs": False, "url": "", "version": 1,
    }
    return json.dumps(theme, indent=2) + "\n"

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
     {"scope": ["markup.inline.raw", "markup.fenced_code.block", "markup.raw.block"], "settings": {"foreground": c("type")}},
     {"scope": ["markup.quote"], "settings": {"foreground": c("comment"), "fontStyle": "italic"}},
     {"scope": ["beginning.punctuation.definition.list", "markup.list punctuation.definition.list.begin"], "settings": {"foreground": fire["ember"]}},
     {"scope": ["invalid"], "settings": {"foreground": c("decorator")}},
     # data-format keys (JSON/YAML/TOML) and CSS/SCSS properties
     {"scope": ["support.type.property-name", "support.type.property-name.json", "support.type.property-name.toml",
                "entity.name.tag.yaml", "meta.object-literal.key", "support.type.property-name.css"], "settings": {"foreground": c("function")}},
     # markup/template/JSX attribute names and tag punctuation
     {"scope": ["entity.other.attribute-name"], "settings": {"foreground": c("type")}},
     {"scope": ["punctuation.definition.tag", "punctuation.definition.tag.begin", "punctuation.definition.tag.end"], "settings": {"foreground": c("punctuation")}},
     {"scope": ["punctuation.definition.template-expression", "punctuation.section.embedded"], "settings": {"foreground": fire["ember"]}},
     # this/self/super and other language constants
     {"scope": ["variable.language", "variable.language.this", "variable.language.self", "variable.language.super"], "settings": {"foreground": c("type"), "fontStyle": "italic"}},
     {"scope": ["constant.other", "support.constant", "variable.other.constant"], "settings": {"foreground": c("number")}},
     # regex anchors and quantifiers read as operators
     {"scope": ["keyword.control.anchor.regexp", "keyword.operator.quantifier.regexp", "punctuation.definition.group.regexp"], "settings": {"foreground": c("operator")}},
     # string interpolation / format placeholders read as accents inside strings
     {"scope": ["constant.character.format.placeholder", "constant.other.placeholder", "punctuation.definition.interpolation"], "settings": {"foreground": fire["ember"]}},
     {"scope": ["meta.embedded", "source.embedded"], "settings": {"foreground": lit["text"]}},
     # builtins, primitives, namespaces
     {"scope": ["support.type.primitive", "storage.type.primitive", "support.type.builtin"], "settings": {"foreground": c("type"), "fontStyle": "italic"}},
     {"scope": ["entity.name.namespace", "entity.name.scope-resolution"], "settings": {"foreground": c("decorator")}},
     {"scope": ["storage.type.function.arrow", "storage.type.function"], "settings": {"foreground": c("keyword"), "fontStyle": "bold"}},
     # deprecated symbols get a strikethrough cue
     {"scope": ["markup.strikethrough"], "settings": {"fontStyle": "strikethrough"}},
     {"scope": ["markup.inserted"], "settings": {"foreground": ext["kelp"]}},
     {"scope": ["markup.deleted"], "settings": {"foreground": ext["brick"]}},
     {"scope": ["markup.changed"], "settings": {"foreground": fire["ember"]}},
    ]
    semantic = {"keyword": c("keyword"), "string": c("string"), "number": c("number"),
     "function": c("function"), "method": c("function"), "function.defaultLibrary": c("type"),
     "class": c("type"), "type": c("type"), "struct": c("type"), "interface": c("type"), "enum": c("type"),
     "typeParameter": {"foreground": c("type"), "fontStyle": "italic"},
     "namespace": c("decorator"), "decorator": c("decorator"), "macro": c("number"),
     "property": c("variable"), "property.readonly": c("number"), "enumMember": c("number"), "event": c("function"),
     "variable": c("variable"), "variable.defaultLibrary": c("type"), "parameter": c("parameter"),
     "variable.readonly": c("number"), "selfKeyword": {"foreground": c("type"), "fontStyle": "italic"},
     "selfParameter": {"foreground": c("type"), "fontStyle": "italic"}, "clsParameter": {"foreground": c("type"), "fontStyle": "italic"},
     "builtinConstant": c("number"), "magicFunction": c("function"), "boolean": c("number"),
     "regexp": c("string"), "escapeSequence": pal["sea"]["foam"], "formatSpecifier": c("operator"),
     "annotation": c("decorator"), "type.defaultLibrary": c("type"), "class.defaultLibrary": c("type"),
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
    # Extended workbench coverage so every surface stays on-system instead of
    # falling back to the default dark theme. All values are palette-derived.
    ember, flame, oil = fire["ember"], fire["flame"], fire["oil"]
    kelp, brick, dusk, tide, shoal = ext["kelp"], ext["brick"], ext["dusk"], ext["tide"], ext["shoal"]
    spray, foam = sea["spray"], sea["foam"]
    bg, surf, raised, text, muted, border, onacc = (lit["bg"], lit["surface"], lit["surface-raised"],
        lit["text"], lit["text-muted"], lit["border"], lit["on-accent"])
    seab, dim = lit["sea-bright"], "#606c72"
    wb.update({
     # general chrome
     "foreground": "#cdd2d3", "descriptionForeground": muted, "disabledForeground": dim,
     "errorForeground": brick, "icon.foreground": muted, "widget.border": border,
     "widget.shadow": "#0000004d", "sash.hoverBorder": ember, "selection.background": a(lit["sea"]),
     "progressBar.background": ember,
     "scrollbar.shadow": "#00000066", "scrollbarSlider.background": seab + "40",
     "scrollbarSlider.hoverBackground": seab + "66", "scrollbarSlider.activeBackground": seab + "99",
     "toolbar.hoverBackground": "#1d242b",
     # editor highlights and gutters
     "editor.selectionHighlightBackground": spray + "26", "editor.wordHighlightBackground": tide + "26",
     "editor.wordHighlightStrongBackground": kelp + "26", "editor.findMatchBackground": ember + "66",
     "editor.findRangeHighlightBackground": spray + "1a", "editor.rangeHighlightBackground": spray + "1a",
     "editor.hoverHighlightBackground": spray + "26", "editorWhitespace.foreground": "#3a4754",
     "editorIndentGuide.background1": "#222a31", "editorIndentGuide.activeBackground1": "#3a4754",
     "editorRuler.foreground": border, "editorBracketMatch.background": spray + "26",
     "editorBracketMatch.border": spray, "editorCodeLens.foreground": dim,
     "editorInlayHint.foreground": muted, "editorInlayHint.background": "#00000000",
     "editorLink.activeForeground": tide, "editorCursor.background": bg,
     "editorGutter.modifiedBackground": ember, "editorGutter.addedBackground": kelp, "editorGutter.deletedBackground": brick,
     "editorOverviewRuler.border": "#00000000", "editorOverviewRuler.modifiedForeground": ember + "cc",
     "editorOverviewRuler.addedForeground": kelp + "cc", "editorOverviewRuler.deletedForeground": brick + "cc",
     "editorOverviewRuler.errorForeground": brick, "editorOverviewRuler.warningForeground": ember, "editorOverviewRuler.infoForeground": tide,
     # widgets: hover, suggest, find
     "editorWidget.background": surf, "editorWidget.foreground": text, "editorWidget.border": border,
     "editorHoverWidget.background": surf, "editorHoverWidget.foreground": text, "editorHoverWidget.border": border,
     "editorSuggestWidget.background": surf, "editorSuggestWidget.foreground": text, "editorSuggestWidget.border": border,
     "editorSuggestWidget.selectedBackground": raised, "editorSuggestWidget.highlightForeground": ember,
     "editorSuggestWidget.focusHighlightForeground": flame,
     "editorGroup.border": border, "editorGroupHeader.tabsBorder": border, "editorGroupHeader.noTabsBackground": surf,
     # inputs, dropdowns, checkboxes, keybindings
     "input.foreground": text, "input.placeholderForeground": muted,
     "inputOption.activeBackground": ember + "33", "inputOption.activeForeground": text,
     "inputValidation.errorBackground": "#3a1d1a", "inputValidation.errorBorder": brick,
     "inputValidation.warningBackground": "#33271a", "inputValidation.warningBorder": ember,
     "inputValidation.infoBackground": "#16242c", "inputValidation.infoBorder": tide,
     "dropdown.background": surf, "dropdown.foreground": text, "dropdown.border": border, "dropdown.listBackground": surf,
     "checkbox.background": raised, "checkbox.foreground": text, "checkbox.border": border,
     "keybindingLabel.background": raised, "keybindingLabel.foreground": muted, "keybindingLabel.border": border, "keybindingLabel.bottomBorder": border,
     # lists and trees
     "list.activeSelectionForeground": text, "list.inactiveSelectionBackground": surf, "list.inactiveSelectionForeground": text,
     "list.focusBackground": raised, "list.focusForeground": text, "list.hoverForeground": text,
     "list.errorForeground": brick, "list.warningForeground": ember,
     "listFilterWidget.background": raised, "listFilterWidget.outline": ember, "listFilterWidget.noMatchesOutline": brick,
     "tree.indentGuidesStroke": "#3a4754", "tree.inactiveIndentGuidesStroke": border,
     # minimap
     "minimap.background": bg, "minimap.selectionHighlight": spray + "66", "minimap.findMatchHighlight": ember + "99",
     "minimap.errorHighlight": brick, "minimap.warningHighlight": ember,
     "minimapSlider.background": seab + "40", "minimapSlider.hoverBackground": seab + "55", "minimapSlider.activeBackground": seab + "77",
     "minimapGutter.modifiedBackground": ember, "minimapGutter.addedBackground": kelp, "minimapGutter.deletedBackground": brick,
     # breadcrumbs
     "breadcrumb.foreground": muted, "breadcrumb.focusForeground": text, "breadcrumb.activeSelectionForeground": ember,
     "breadcrumb.background": bg, "breadcrumbPicker.background": surf,
     # status bar extras
     "statusBar.noFolderBackground": surf, "statusBar.noFolderForeground": muted,
     "statusBarItem.hoverBackground": "#ffffff14", "statusBarItem.activeBackground": "#ffffff1f",
     "statusBarItem.remoteBackground": ember, "statusBarItem.remoteForeground": onacc,
     "statusBarItem.errorBackground": brick, "statusBarItem.errorForeground": text,
     "statusBarItem.warningBackground": oil, "statusBarItem.warningForeground": text,
     "statusBarItem.prominentBackground": raised,
     # title bar / tabs / panel extras
     "titleBar.inactiveBackground": bg, "titleBar.inactiveForeground": muted,
     "tab.hoverBackground": raised, "tab.unfocusedHoverBackground": raised, "tab.activeBorder": ember,
     "tab.unfocusedActiveForeground": muted, "tab.lastPinnedBorder": border, "tab.activeModifiedBorder": ember,
     "panelTitle.activeForeground": text, "panelTitle.inactiveForeground": muted, "panelInput.border": border,
     "panelSectionHeader.background": surf,
     # terminal extras
     "terminal.selectionBackground": a(lit["sea"]), "terminal.border": border, "terminalCursor.background": bg,
     # peek view
     "peekView.border": ember, "peekViewEditor.background": surf, "peekViewEditor.matchHighlightBackground": ember + "44",
     "peekViewResult.background": surf, "peekViewResult.fileForeground": text, "peekViewResult.lineForeground": muted,
     "peekViewResult.matchHighlightBackground": ember + "44", "peekViewResult.selectionBackground": raised, "peekViewResult.selectionForeground": text,
     "peekViewTitle.background": bg, "peekViewTitleLabel.foreground": text, "peekViewTitleDescription.foreground": muted,
     # diff and merge
     "diffEditor.insertedTextBackground": kelp + "22", "diffEditor.removedTextBackground": brick + "22",
     "diffEditor.insertedLineBackground": kelp + "14", "diffEditor.removedLineBackground": brick + "14", "diffEditor.diagonalFill": border,
     "merge.currentHeaderBackground": tide + "55", "merge.currentContentBackground": tide + "22",
     "merge.incomingHeaderBackground": kelp + "55", "merge.incomingContentBackground": kelp + "22",
     # notifications
     "notificationCenter.border": border, "notificationCenterHeader.background": surf, "notificationCenterHeader.foreground": text,
     "notifications.background": surf, "notifications.foreground": text, "notifications.border": border,
     "notificationsErrorIcon.foreground": brick, "notificationsWarningIcon.foreground": ember, "notificationsInfoIcon.foreground": tide,
     "notificationLink.foreground": tide,
     # quick input / command palette
     "quickInput.background": surf, "quickInput.foreground": text, "quickInputTitle.background": bg,
     "quickInputList.focusBackground": raised, "quickInputList.focusForeground": text,
     "pickerGroup.foreground": ember, "pickerGroup.border": border,
     # menus
     "menu.background": surf, "menu.foreground": text, "menu.border": border,
     "menu.selectionBackground": raised, "menu.selectionForeground": text, "menu.separatorBackground": border,
     "menubar.selectionBackground": "#ffffff14", "menubar.selectionForeground": text,
     # git decoration extras
     "gitDecoration.addedResourceForeground": kelp, "gitDecoration.renamedResourceForeground": tide,
     "gitDecoration.stageModifiedResourceForeground": flame, "gitDecoration.stageDeletedResourceForeground": brick,
     "gitDecoration.ignoredResourceForeground": dim, "gitDecoration.conflictingResourceForeground": dusk,
     "gitDecoration.submoduleResourceForeground": shoal,
     # settings UI
     "settings.headerForeground": text, "settings.modifiedItemIndicator": ember,
     "settings.dropdownBackground": surf, "settings.dropdownBorder": border,
     "settings.checkboxBackground": raised, "settings.checkboxBorder": border,
     "settings.textInputBackground": surf, "settings.textInputBorder": border,
     "settings.numberInputBackground": surf, "settings.numberInputBorder": border, "settings.focusedRowBackground": "#ffffff0a",
     # debug / testing / charts
     "debugToolBar.background": surf, "debugToolBar.border": border, "debugIcon.breakpointForeground": brick,
     "editor.stackFrameHighlightBackground": ember + "22", "editor.focusedStackFrameHighlightBackground": kelp + "22",
     "debugConsole.errorForeground": brick, "debugConsole.warningForeground": ember, "debugConsole.infoForeground": tide, "debugConsole.sourceForeground": muted,
     "testing.iconPassed": kelp, "testing.iconFailed": brick, "testing.iconQueued": ember,
     "charts.foreground": text, "charts.lines": muted, "charts.red": brick, "charts.blue": tide,
     "charts.green": kelp, "charts.orange": ember, "charts.purple": dusk, "charts.yellow": flame,
     # extension button / banner
     "extensionButton.prominentBackground": ember, "extensionButton.prominentForeground": onacc, "extensionButton.prominentHoverBackground": flame,
     "banner.background": raised, "banner.foreground": text, "banner.iconForeground": ember,
    })
    param = c("parameter")
    wb.update({
     # inline suggestions, sticky scroll, light bulb, hints
     "editorGhostText.foreground": dim, "editorGhostText.border": "#00000000",
     "editorStickyScroll.background": surf, "editorStickyScrollHover.background": "#1d242b",
     "editorStickyScroll.border": border, "editorStickyScroll.shadow": "#0000004d",
     "editorLightBulb.foreground": flame, "editorLightBulbAutoFix.foreground": tide, "editorLightBulbAi.foreground": dusk,
     "editorHint.foreground": shoal, "editorGutter.commentRangeForeground": dim, "editorGutter.foldingControlForeground": muted,
     "editorInlayHint.typeForeground": shoal, "editorInlayHint.typeBackground": "#00000000",
     "editorInlayHint.parameterForeground": muted, "editorInlayHint.parameterBackground": "#00000000",
     "editorUnnecessaryCode.opacity": "#0000007f",
     "editor.snippetTabstopHighlightBackground": tide + "22", "editor.snippetFinalTabstopHighlightBorder": ember,
     # bracket-pair colourization guides (match the six bracket colours, faint)
     "editorBracketPairGuide.background1": foam + "33", "editorBracketPairGuide.background2": ember + "33",
     "editorBracketPairGuide.background3": dusk + "33", "editorBracketPairGuide.background4": kelp + "33",
     "editorBracketPairGuide.background5": tide + "33", "editorBracketPairGuide.background6": brick + "33",
     "editorBracketPairGuide.activeBackground1": foam + "99", "editorBracketPairGuide.activeBackground2": ember + "99",
     "editorBracketPairGuide.activeBackground3": dusk + "99", "editorBracketPairGuide.activeBackground4": kelp + "99",
     "editorBracketPairGuide.activeBackground5": tide + "99", "editorBracketPairGuide.activeBackground6": brick + "99",
     # overview ruler highlight markers
     "editorOverviewRuler.findMatchForeground": ember + "99", "editorOverviewRuler.selectionHighlightForeground": spray + "66",
     "editorOverviewRuler.wordHighlightForeground": tide + "88", "editorOverviewRuler.wordHighlightStrongForeground": kelp + "88",
     "editorOverviewRuler.bracketMatchForeground": spray, "editorOverviewRuler.rangeHighlightForeground": spray + "66",
     # problems icons, command center, window border, resize handles
     "problemsErrorIcon.foreground": brick, "problemsWarningIcon.foreground": ember, "problemsInfoIcon.foreground": tide,
     "commandCenter.background": surf, "commandCenter.foreground": text, "commandCenter.border": border,
     "commandCenter.activeBackground": raised, "commandCenter.activeForeground": text, "commandCenter.activeBorder": ember,
     "commandCenter.inactiveForeground": muted, "commandCenter.inactiveBorder": border,
     "window.activeBorder": border, "window.inactiveBorder": border,
     "editorWidget.resizeBorder": ember, "editorSuggestWidgetStatus.foreground": muted, "editorHoverWidget.statusBarBackground": surf,
     # notebooks
     "notebook.editorBackground": bg, "notebook.cellEditorBackground": surf, "notebook.cellBorderColor": border,
     "notebook.focusedCellBorder": ember, "notebook.focusedEditorBorder": ember, "notebook.selectedCellBackground": raised,
     "notebook.cellHoverBackground": surf, "notebook.cellStatusBarItemHoverBackground": "#1d242b",
     "notebook.cellToolbarSeparator": border, "notebook.outputContainerBackgroundColor": surf,
     "notebookStatusSuccessIcon.foreground": kelp, "notebookStatusErrorIcon.foreground": brick, "notebookStatusRunningIcon.foreground": ember,
     # terminal extras
     "terminal.findMatchBackground": ember + "66", "terminal.findMatchHighlightBackground": flame + "33",
     "terminalCommandDecoration.defaultBackground": muted, "terminalCommandDecoration.successBackground": kelp,
     "terminalCommandDecoration.errorBackground": brick, "terminalOverviewRuler.cursorForeground": ember,
     "terminalStickyScroll.background": surf, "terminal.tab.activeBorder": ember,
     # outline / suggest symbol icons
     "symbolIcon.classForeground": shoal, "symbolIcon.interfaceForeground": shoal, "symbolIcon.structForeground": shoal,
     "symbolIcon.enumeratorForeground": dusk, "symbolIcon.enumeratorMemberForeground": dusk, "symbolIcon.constantForeground": dusk,
     "symbolIcon.functionForeground": tide, "symbolIcon.methodForeground": tide, "symbolIcon.constructorForeground": tide,
     "symbolIcon.eventForeground": flame, "symbolIcon.operatorForeground": "#aeb6b8", "symbolIcon.keywordForeground": ember,
     "symbolIcon.variableForeground": text, "symbolIcon.fieldForeground": param, "symbolIcon.propertyForeground": param,
     "symbolIcon.stringForeground": kelp, "symbolIcon.numberForeground": dusk, "symbolIcon.booleanForeground": dusk,
     "symbolIcon.moduleForeground": brick, "symbolIcon.namespaceForeground": brick, "symbolIcon.referenceForeground": tide,
     "symbolIcon.typeParameterForeground": shoal, "symbolIcon.snippetForeground": foam, "symbolIcon.colorForeground": flame,
     "symbolIcon.fileForeground": muted, "symbolIcon.folderForeground": muted, "symbolIcon.keyForeground": tide,
     "symbolIcon.nullForeground": dim, "symbolIcon.arrayForeground": text, "symbolIcon.objectForeground": text,
     "symbolIcon.textForeground": text, "symbolIcon.unitForeground": dusk, "symbolIcon.valueForeground": text,
     # debug icons, token expressions, view, exception widget
     "debugIcon.breakpointDisabledForeground": dim, "debugIcon.breakpointUnverifiedForeground": muted,
     "debugIcon.startForeground": kelp, "debugIcon.pauseForeground": tide, "debugIcon.stopForeground": brick,
     "debugIcon.disconnectForeground": brick, "debugIcon.restartForeground": kelp, "debugIcon.continueForeground": kelp,
     "debugIcon.stepOverForeground": tide, "debugIcon.stepIntoForeground": tide, "debugIcon.stepOutForeground": tide, "debugIcon.stepBackForeground": tide,
     "debugTokenExpression.name": tide, "debugTokenExpression.value": text, "debugTokenExpression.string": kelp,
     "debugTokenExpression.boolean": dusk, "debugTokenExpression.number": dusk, "debugTokenExpression.error": brick,
     "debugView.stateLabelForeground": text, "debugView.stateLabelBackground": raised, "debugView.valueChangedHighlight": ember + "55",
     "debugConsoleInputIcon.foreground": ember, "debugExceptionWidget.background": surf, "debugExceptionWidget.border": brick,
     "ports.iconRunningProcessForeground": kelp,
     # scm, welcome / walkthrough
     "scm.providerBorder": border, "welcomePage.background": bg, "welcomePage.progress.background": surf,
     "welcomePage.progress.foreground": ember, "welcomePage.tileBackground": surf, "welcomePage.tileHoverBackground": raised,
     "welcomePage.tileBorder": border, "walkThrough.embeddedEditorBackground": surf, "walkthrough.stepTitle.foreground": text,
     # inline chat / chat (Copilot and similar)
     "chat.requestBackground": surf, "chat.slashCommandBackground": ember + "22", "chat.slashCommandForeground": ember,
     "chat.avatarBackground": raised, "inlineChat.background": surf, "inlineChat.border": border,
     "inlineChatInput.background": bg, "inlineChatInput.border": border,
    })
    for i, k in enumerate(["Black","Red","Green","Yellow","Blue","Magenta","Cyan","White","BrightBlack","BrightRed","BrightGreen","BrightYellow","BrightBlue","BrightMagenta","BrightCyan","BrightWhite"]):
        wb["terminal.ansi" + k] = ansi[i]
    theme = {"name": "Try-Works", "type": "dark", "semanticHighlighting": True,
             "semanticTokenColors": semantic, "colors": wb, "tokenColors": tokenColors}
    return json.dumps(theme, indent=2) + "\n"

def _cold_remap(D):
    """Shared lit->cold colour remap for the code editors (VS Code + Zed light
    variants). One table so both light themes stay identical in philosophy and
    a colour with no mapping fails generation loudly in either. Mirrors the
    system's other light surfaces: hues darken toward the ink (t=0.45, the ratio
    the Obsidian/Quarto light builds use, verified >=4.5:1); ember->cold accent
    and flame->cold accent-deep because light-mode hovers must darken, not
    brighten; the "#ffffffNN" white overlays flip to black; pure-black alpha
    shadows pass through. Terminal ANSI is NOT remapped here (callers keep the
    identity palette, the Ghostty/iTerm precedent) -- guard terminal.ansi* keys
    before calling remap(). Returns (remap, deep)."""
    lit, cold, pal = D["modes"]["lit"], D["modes"]["cold"], D["palette"]
    fire, sea, ext = pal["fire"], pal["sea"], pal["extended"]
    ls = lambda h: _mix(h, cold["text"], 0.45)
    M6 = {
        lit["bg"]: cold["bg"], lit["surface"]: cold["surface"], lit["surface-raised"]: cold["surface-raised"],
        lit["text"]: cold["text"], lit["text-muted"]: cold["text-muted"], lit["border"]: cold["border"],
        lit["on-accent"]: cold["on-accent"], lit["sea"]: cold["sea-pale"], lit["sea-bright"]: cold["sea-bright"],
        sea["foam"]: ls(sea["foam"]),
        fire["ember"]: cold["accent"], fire["flame"]: cold["accent-deep"], fire["oil"]: cold["accent-deep"],
        # kelp gets t=0.5, not the shared 0.45: strings sit on the editor bg (cold's darkest light
        # surface, unlike Obsidian's lighter code surface) and 0.45 lands at 4.44:1 -- just under AA.
        ext["kelp"]: _mix(ext["kelp"], cold["text"], 0.5),
        ext["brick"]: ls(ext["brick"]), ext["dusk"]: ls(ext["dusk"]),
        ext["tide"]: ls(ext["tide"]), ext["shoal"]: ls(ext["shoal"]),
        # code-map roles / UI literals that are not palette tokens
        "#cdd2d3": _mix(cold["text"], cold["text-muted"], 0.35),   # parameter role + chrome fg
        "#aeb6b8": cold["text-muted"], "#8a9296": cold["text-muted"],  # operator, punctuation
        "#606c72": _mix(cold["text-muted"], cold["bg"], 0.35),     # dim
        "#1d242b": _mix(cold["surface"], cold["border"], 0.5),     # hover
        "#222a31": _mix(cold["border"], cold["bg"], 0.5),          # faint guides
        "#3a4754": _mix(cold["border"], cold["text-muted"], 0.35), # whitespace/tree strokes
        "#3a1d1a": _mix(cold["bg"], ext["brick"], 0.18),           # validation error bg
        "#33271a": _mix(cold["bg"], fire["ember"], 0.18),          # validation warning bg
        "#16242c": _mix(cold["bg"], ext["tide"], 0.18),            # validation info bg
    }
    M8 = {"#ffffff14": "#00000010", "#ffffff1f": "#0000001a", "#ffffff0a": "#0000000a"}
    KEEP = {"#00000000", "#0000004d", "#00000066", "#0000007f"}
    def remap(v):
        lv = v.lower()
        if lv in M8: return M8[lv]
        if lv in KEEP: return v
        base, alpha = lv[:7], lv[7:]
        if base in M6: return M6[base] + alpha
        raise KeyError("no light mapping for colour %r in _cold_remap" % v)
    def deep(x):
        if isinstance(x, str) and x.startswith("#"): return remap(x)
        if isinstance(x, dict): return {k: deep(v) for k, v in x.items()}
        if isinstance(x, list): return [deep(i) for i in x]
        return x
    return remap, deep

def build_vscode_cold(D):
    """True Lamp (light) VS Code theme, derived from the dark build by the shared
    _cold_remap total remap rather than a second hand-maintained builder: every
    key the dark theme sets is covered by construction, and a future dark-side
    colour with no light mapping fails generation loudly instead of shipping
    wrong."""
    cold = D["modes"]["cold"]
    remap, deep = _cold_remap(D)
    theme = json.loads(build_vscode(D))
    colors = {k: (v if k.startswith("terminal.ansi") else remap(v)) for k, v in theme["colors"].items()}
    colors.update({
        # dark pairs these with near-white text; after the remap that text is ink over a dark
        # hue, so the two status pills flip to the light-on-dark on-accent instead.
        "statusBarItem.warningForeground": cold["on-accent"],
        "statusBarItem.errorForeground": cold["on-accent"],
    })
    out = {"name": "Try-Works Cold", "type": "light", "semanticHighlighting": True,
           "semanticTokenColors": deep(theme["semanticTokenColors"]),
           "colors": colors, "tokenColors": deep(theme["tokenColors"])}
    return json.dumps(out, indent=2) + "\n"

# Try-Works Icons: monogram entries. (id, monogram, hue key, fileExtensions, fileNames, languageIds).
# Typography is the icon: a two-letter mono monogram on a faint hue chip beats pseudo-logos and stays
# single-source. Hues come from the extended tier (sanctioned on code surfaces) plus fire/neutrals;
# README carries the one rare fire mark (the file you are told to read). File/folder NAME keys are
# matched lowercased by VS Code, so tables list lowercase only.
_ICON_MONO = [
    ("py",    "Py", "tide",  ["py", "pyi"], [], ["python"]),
    ("r",     "R",  "shoal", ["r"], [], ["r"]),
    ("ipynb", "Nb", "dusk",  ["ipynb"], [], []),
    ("qmd",   "Qm", "kelp",  ["qmd"], [], ["quarto"]),
    ("rmd",   "Rm", "kelp",  ["rmd"], [], ["rmd"]),
    ("md",    "Md", "muted", ["md", "markdown"], [], ["markdown"]),
    ("js",    "JS", "flame", ["js", "mjs", "cjs"], [], ["javascript"]),
    ("ts",    "TS", "tide",  ["ts", "mts"], [], ["typescript"]),
    ("jsx",   "Jx", "shoal", ["jsx", "tsx"], [], ["javascriptreact", "typescriptreact"]),
    ("json",  "{}", "flame", ["json", "jsonc", "json5"], [], ["json", "jsonc"]),
    ("yaml",  "Ym", "dusk",  ["yaml", "yml"], [], ["yaml"]),
    ("toml",  "Tm", "dusk",  ["toml"], [], ["toml"]),
    ("csv",   "Cv", "kelp",  ["csv", "tsv"], [], []),
    ("xml",   "Xm", "muted", ["xml"], [], ["xml"]),
    ("html",  "<>", "brick", ["html", "htm"], [], ["html"]),
    ("css",   "#",  "tide",  ["css", "scss", "sass", "less"], [], ["css", "scss"]),
    ("svg",   "Sv", "dusk",  ["svg"], [], []),
    ("sh",    ">_", "kelp",  ["sh", "zsh", "bash", "fish"], [".zshrc", ".zprofile", ".bashrc", ".bash_profile"], ["shellscript"]),
    ("sql",   "Sq", "shoal", ["sql"], [], ["sql"]),
    ("tex",   "Tx", "dusk",  ["tex", "sty", "cls"], [], ["latex"]),
    ("bib",   "Bb", "dusk",  ["bib"], [], ["bibtex"]),
    ("typ",   "Ty", "tide",  ["typ"], [], ["typst"]),
    ("lua",   "Lu", "tide",  ["lua"], [], ["lua"]),
    ("rs",    "Rs", "brick", ["rs"], [], ["rust"]),
    ("go",    "Go", "shoal", ["go"], [], ["go"]),
    ("c",     "C",  "tide",  ["c", "h"], [], ["c"]),
    ("cpp",   "C+", "tide",  ["cpp", "hpp", "cc", "hh"], [], ["cpp"]),
    ("java",  "Jv", "brick", ["java"], [], ["java"]),
    ("rb",    "Rb", "brick", ["rb"], [], ["ruby"]),
    ("php",   "Ph", "dusk",  ["php"], [], ["php"]),
    ("swift", "Sw", "brick", ["swift"], [], ["swift"]),
    ("make",  "Mk", "muted", ["mk"], ["makefile", "justfile"], ["makefile"]),
    ("docker", "Dk", "tide", ["dockerfile"], ["dockerfile", ".dockerignore", "docker-compose.yml", "compose.yaml"], ["dockerfile"]),
    ("license", "Li", "muted", [], ["license", "license.md", "license.txt", "licence", "copying",
                                    "license-code", "license-design"], []),
    ("readme", "Re", "ember", [], ["readme", "readme.md", "readme.txt"], []),
    ("git",   "G",  "brick", ["gitignore"], [".gitignore", ".gitattributes", ".gitmodules"], ["git-commit", "git-rebase"]),
    ("env",   "Ev", "muted", ["env"], [".env", ".env.local", ".envrc"], []),
    ("lock",  "Lk", "muted", ["lock"], ["package-lock.json", "renv.lock", "poetry.lock", "uv.lock", "cargo.lock"], []),
    ("cff",   "Cf", "muted", ["cff"], ["citation.cff"], []),
    ("txt",   "Tt", "muted", ["txt"], [], ["plaintext"]),
    ("log",   "Lg", "muted", ["log"], [], ["log"]),
    ("font",  "Aa", "foam",  ["ttf", "otf", "woff", "woff2"], [], []),
    ("xlsx",  "Xl", "kelp",  ["xlsx", "xls", "ods"], [], []),
    ("docx",  "Dc", "tide",  ["docx", "doc", "odt"], [], []),
    ("pptx",  "Pp", "brick", ["pptx", "ppt", "odp"], [], []),
    ("db",    "Db", "shoal", ["db", "sqlite", "duckdb", "parquet", "feather"], [], []),
]

# Folder hue variants. (id suffix, hue key, folder names). Default folder is sea-bright.
_ICON_FOLDERS = [
    ("src",    "tide",  ["src", "lib"]),
    ("data",   "shoal", ["data", "datasets", "raw"]),
    ("docs",   "dusk",  ["docs", "doc", "notes", "notebooks"]),
    ("test",   "kelp",  ["tests", "test", "__tests__", "spec"]),
    ("scripts", "brick", ["scripts", "bin", "tools", ".git"]),
    ("assets", "foam",  ["assets", "static", "public", "resources", "fonts", "img", "images", "figures"]),
    ("meta",   "muted", ["config", ".config", ".github", ".vscode", "node_modules", "venv", ".venv",
                          "renv", "dist", "build", "out", "target", "__pycache__", ".cache"]),
]

def build_vscode_icons(D):
    """Try-Works Icons: a VS Code file-icon theme, generated like every other
    surface. Modeled on Material Icon Theme's JSON conventions (iconDefinitions
    + fileExtensions/fileNames/folderNames/folderNamesExpanded/languageIds,
    hidesExplorerArrows) but with a typographic design language: monogram-on-
    chip file icons and lucide-outline folders (same folder/file/image/music
    path data the Obsidian surface lifted from Obsidian's bundled icon map).
    Returns {relpath: text} for the whole dist/vscode/icons/ tree; merged into
    artifacts() with **, so the drift gate covers every SVG. Internal
    consistency is asserted here so a broken table fails generation loudly."""
    pal, lit = D["palette"], D["modes"]["lit"]
    ex, fire, sea = pal["extended"], pal["fire"], pal["sea"]
    H = {"tide": ex["tide"], "shoal": ex["shoal"], "dusk": ex["dusk"], "kelp": ex["kelp"],
         "brick": ex["brick"], "flame": fire["flame"], "ember": fire["ember"],
         "muted": lit["text-muted"], "foam": sea["foam"], "seab": lit["sea-bright"]}
    esc = lambda s: s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    def svg(body, stroke="none"):
        return ("<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%s'"
                " stroke-width='1.75' stroke-linecap='round' stroke-linejoin='round'>%s</svg>\n"
                % (stroke, body))
    def mono(mg, hue):
        fs = "12.5" if len(mg) == 1 else "10.5"
        return svg("<rect x='2.5' y='2.5' width='19' height='19' rx='4.5' fill='%s' fill-opacity='0.13'/>" % hue
                   + "<text x='12' y='12.6' text-anchor='middle' dominant-baseline='central'"
                     " font-family=\"ui-monospace,'SF Mono',Menlo,monospace\" font-weight='700'"
                     " font-size='%s' fill='%s'>%s</text>" % (fs, hue, esc(mg)))
    P = lambda d: "<path d='%s'/>" % d
    page = P("M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706"
             "l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2z")
    corner = P("M14 2v5a1 1 0 0 0 1 1h5")
    fold_closed = P("M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9"
                    "A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z")
    fold_open = P("m6 14 1.5-2.9A2 2 0 0 1 9.24 10H20a2 2 0 0 1 1.94 2.5l-1.54 6"
                  "a2 2 0 0 1-1.95 1.5H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h3.9"
                  "a2 2 0 0 1 1.69.9l.81 1.2a2 2 0 0 0 1.67.9H18a2 2 0 0 1 2 2v2")
    out, defs = {}, {}
    fe, fn, folders, folderso, li = {}, {}, {}, {}, {}
    base = "dist/vscode/icons/"
    def add(iid, svg_text):
        assert iid not in defs, "duplicate icon id %r" % iid
        defs[iid] = {"iconPath": "./tw-%s.svg" % iid}
        out[base + "tw-%s.svg" % iid] = svg_text
    # glyph icons (outline, stroke in hue)
    add("file", svg(page + corner, stroke=H["muted"]))
    add("pdf", svg(page + corner + P("M10 12H8") + P("M16 15H8") + P("M16 18H8"), stroke=H["brick"]))
    add("image", svg("<rect x='3' y='3' width='18' height='18' rx='2'/><circle cx='9' cy='9' r='2'/>"
                     + P("m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"), stroke=H["dusk"]))
    add("audio", svg(P("M9 18V5l12-2v13") + "<circle cx='6' cy='18' r='3'/><circle cx='18' cy='16' r='3'/>",
                     stroke=H["shoal"]))
    add("video", svg("<rect x='2.5' y='4.5' width='19' height='15' rx='2'/><polygon points='10 9 15.5 12 10 15'/>",
                     stroke=H["tide"]))
    add("archive", svg("<rect x='3' y='7' width='18' height='13' rx='2'/>" + P("M3 7l2-3.5h14L21 7")
                       + P("M10 11.5h4"), stroke=H["muted"]))
    for ext_list, iid in [(["png", "jpg", "jpeg", "webp", "gif", "avif", "bmp", "ico", "tiff", "heic"], "image"),
                          (["pdf"], "pdf"),
                          (["zip", "tar", "gz", "tgz", "7z", "rar"], "archive"),
                          (["mp3", "wav", "m4a", "ogg", "flac"], "audio"),
                          (["mp4", "mov", "mkv", "webm"], "video")]:
        for e in ext_list: fe[e] = iid
    # monogram icons
    for iid, mg, hue, exts, names, langs in _ICON_MONO:
        add(iid, mono(mg, H[hue]))
        for e in exts: fe[e] = iid
        for n in names: fn[n] = iid
        for l in langs: li[l] = iid
    # folders: default + hue variants, closed and open
    def add_folder(iid, hue):
        add(iid, svg(fold_closed, stroke=hue))
        add(iid + "-open", svg(fold_open, stroke=hue))
    add_folder("folder", H["seab"])
    for suffix, hue, names in _ICON_FOLDERS:
        add_folder("folder-" + suffix, H[hue])
        for n in names:
            folders[n] = "folder-" + suffix
            folderso[n] = "folder-" + suffix + "-open"
    theme = {
        "hidesExplorerArrows": False,
        "file": "file", "folder": "folder", "folderExpanded": "folder-open",
        "rootFolder": "folder", "rootFolderExpanded": "folder-open",
        "iconDefinitions": defs,
        "fileExtensions": fe, "fileNames": fn,
        "folderNames": folders, "folderNamesExpanded": folderso,
        "languageIds": li,
    }
    for m, kind in ((fe, "extension"), (fn, "name"), (folders, "folder"), (folderso, "folder-open"), (li, "language")):
        for k, v in m.items():
            assert v in defs, "unknown icon id %r for %s %r" % (v, kind, k)
    out[base + "try-works-icon-theme.json"] = json.dumps(theme, indent=2) + "\n"
    return out

def build_typst(D):
    m = D["modes"]["lit"]
    pairs = [("pitch", m["bg"]), ("hold", m["surface"]), ("sea-deep", m["sea-deep"]), ("sea", m["sea"]),
             ("sea-bright", m["sea-bright"]), ("sea-pale", m["sea-pale"]), ("ember", m["accent"]),
             ("flame", m["accent-bright"]), ("whale", m["text"]), ("gull", m["text-muted"])]
    return "// Try-Works colours. Generated from try-works.json.\n" + "".join('#let %s = rgb("%s")\n' % (n, v) for n, v in pairs)

def build_zed(D):
    """Zed theme family (schema v0.2.0). Ships both appearances in one family
    file: dark Try-Fire (built from modes.lit + the audited code map), and light
    True Lamp, derived from the dark style by the same shared _cold_remap total
    remap the VS Code light theme uses. Terminal ANSI keeps the identity palette
    in both (the Ghostty/iTerm precedent), so its keys skip the remap."""
    lit, pal, codem, t = D["modes"]["lit"], D["palette"], D["code"], D["terminal"]
    fire, sea, ext, ansi = pal["fire"], pal["sea"], pal["extended"], t["ansi"]
    c = lambda r: codem[r]["color"]
    def col(color, **extra):
        e = {"color": color}; e.update(extra); return e
    def syn(role, **extra):                         # syntax entry from a code-map role
        e = {"color": c(role)}; st = codem[role].get("style")
        if st == "italic": e["font_style"] = "italic"
        if st == "bold":   e["font_weight"] = 700
        e.update(extra); return e
    ember, flame, oil = fire["ember"], fire["flame"], fire["oil"]
    kelp, brick, dusk, tide, shoal = ext["kelp"], ext["brick"], ext["dusk"], ext["tide"], ext["shoal"]
    foam, spray = sea["foam"], sea["spray"]
    bg, surf, raised, text, muted, border, onacc = (lit["bg"], lit["surface"], lit["surface-raised"],
        lit["text"], lit["text-muted"], lit["border"], lit["on-accent"])
    seab, dim = lit["sea-bright"], "#606c72"
    style = {
     "border": border, "border.variant": "#222a31", "border.focused": ember,
     "border.selected": ember, "border.transparent": "#00000000", "border.disabled": "#222a31",
     "elevated_surface.background": raised, "surface.background": surf, "background": bg,
     "element.background": surf, "element.hover": "#1d242b", "element.active": raised,
     "element.selected": raised, "element.disabled": "#00000000", "drop_target.background": tide + "22",
     "ghost_element.background": "#00000000", "ghost_element.hover": "#ffffff0a",
     "ghost_element.active": "#ffffff14", "ghost_element.selected": raised, "ghost_element.disabled": "#00000000",
     "text": text, "text.muted": muted, "text.placeholder": dim, "text.disabled": dim, "text.accent": ember,
     "icon": text, "icon.muted": muted, "icon.disabled": dim, "icon.placeholder": muted, "icon.accent": ember,
     "status_bar.background": surf, "title_bar.background": bg, "title_bar.inactive_background": bg,
     "toolbar.background": bg, "tab_bar.background": surf,
     "tab.inactive_background": surf, "tab.active_background": bg,
     "search.match_background": ember + "55",
     "panel.background": surf, "panel.focused_border": ember, "pane.focused_border": ember, "pane_group.border": border,
     "scrollbar.thumb.background": seab + "40", "scrollbar.thumb.hover_background": seab + "66",
     "scrollbar.thumb.border": "#00000000", "scrollbar.track.background": "#00000000", "scrollbar.track.border": border,
     "editor.foreground": text, "editor.background": bg, "editor.gutter.background": bg,
     "editor.subheader.background": surf, "editor.active_line.background": surf,
     "editor.highlighted_line.background": surf, "editor.line_number": dim, "editor.active_line_number": text,
     "editor.invisible": "#3a4754", "editor.wrap_guide": "#222a31", "editor.active_wrap_guide": "#3a4754",
     "editor.indent_guide": "#222a31", "editor.indent_guide_active": "#3a4754",
     "editor.document_highlight.read_background": tide + "26", "editor.document_highlight.write_background": kelp + "26",
     "terminal.background": bg, "terminal.foreground": text, "terminal.bright_foreground": text, "terminal.dim_foreground": muted,
     "link_text.hover": flame,
     "conflict": dusk, "conflict.background": dusk + "22", "conflict.border": dusk,
     "created": kelp, "created.background": kelp + "22", "created.border": kelp,
     "deleted": brick, "deleted.background": brick + "22", "deleted.border": brick,
     "modified": ember, "modified.background": ember + "22", "modified.border": ember,
     "renamed": tide, "renamed.background": tide + "22", "renamed.border": tide,
     "error": brick, "error.background": brick + "22", "error.border": brick,
     "warning": ember, "warning.background": ember + "22", "warning.border": ember,
     "info": tide, "info.background": tide + "22", "info.border": tide,
     "hint": shoal, "hint.background": shoal + "22", "hint.border": shoal,
     "success": kelp, "success.background": kelp + "22", "success.border": kelp,
     "predictive": dim, "predictive.background": dim + "22", "predictive.border": dim,
     "unreachable": muted, "hidden": dim, "ignored": dim,
     "scrollbar.thumb.active_background": seab + "99",
     "panel.indent_guide": "#222a31", "panel.indent_guide_active": "#3a4754", "panel.indent_guide_hover": "#2c3640",
     "version_control.added": kelp, "version_control.modified": ember, "version_control.deleted": brick,
     "version_control.conflict": dusk, "version_control.renamed": tide, "version_control.ignored": dim,
    }
    for i, n in enumerate(["black", "red", "green", "yellow", "blue", "magenta", "cyan", "white"]):
        style["terminal.ansi." + n] = ansi[i]
        style["terminal.ansi.bright_" + n] = ansi[i + 8]
    style["players"] = [{"cursor": h, "background": h, "selection": h + "3d"}
                        for h in (ember, tide, kelp, dusk, shoal, brick, flame, foam)]
    style["syntax"] = {
     "attribute": col(shoal), "boolean": syn("number"), "comment": syn("comment"), "comment.doc": syn("comment"),
     "constant": syn("number"), "constructor": col(shoal, font_style="italic"), "embedded": col(text),
     "emphasis": col(text, font_style="italic"), "emphasis.strong": col(ember, font_weight=700),
     "enum": col(shoal, font_style="italic"), "function": syn("function"), "function.method": syn("function"),
     "hint": col(shoal), "keyword": syn("keyword"), "label": syn("decorator"),
     "link_text": col(tide, font_style="italic"), "link_uri": col(tide), "number": syn("number"),
     "operator": syn("operator"), "predictive": col(dim), "preproc": syn("decorator"), "primary": col(text),
     "property": col(c("parameter")), "punctuation": syn("punctuation"), "punctuation.bracket": syn("punctuation"),
     "punctuation.delimiter": syn("punctuation"), "punctuation.list_marker": col(ember), "punctuation.special": col(ember),
     "string": syn("string"), "string.escape": col(foam), "string.regex": syn("string"),
     "string.special": syn("string"), "string.special.symbol": syn("number"), "tag": syn("decorator"),
     "text.literal": col(kelp), "title": col(ember, font_weight=700), "type": syn("type"),
     "type.builtin": col(shoal, font_style="italic"), "variable": syn("variable"),
     "variable.special": col(shoal, font_style="italic"), "variant": syn("number"),
     "namespace": syn("decorator"), "module": syn("decorator"), "constant.builtin": syn("number"),
     "function.builtin": col(shoal, font_style="italic"), "function.special": col(brick),
     "variable.member": col(c("parameter")), "keyword.import": syn("keyword"), "tag.delimiter": syn("punctuation"),
    }
    remap, deep = _cold_remap(D)
    def cold_style(s):
        # top-level guard keeps terminal.ansi.* on the identity palette; syntax/players nest, so
        # they recurse through deep(); every other value is a colour string to remap.
        out = {}
        for k, v in s.items():
            if k.startswith("terminal.ansi"): out[k] = v
            elif isinstance(v, (dict, list)): out[k] = deep(v)
            else: out[k] = remap(v)
        return out
    theme = {"$schema": "https://zed.dev/schema/themes/v0.2.0.json",
             "name": "Try-Works", "author": "tiagojct",
             "themes": [{"name": "Try-Works (Try-Fire)", "appearance": "dark", "style": style},
                        {"name": "Try-Works (True Lamp)", "appearance": "light", "style": cold_style(style)}]}
    return json.dumps(theme, indent=2) + "\n"

def stamp_version(rel, D):
    obj = json.loads((SRC / rel).read_text())
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
        # standalone token surfaces under dist/
        "dist/css/try-works.css": css,
        "dist/css/typography.css": typo,
        "dist/css/p3.css": build_p3(D),
        "dist/css/a11y.css": build_a11y(D),
        "dist/css/fallbacks.css": build_fallbacks(D),
        "dist/css/motion.css": build_motion(D),
        "dist/r/tryworks.R": build_r(D),
        "dist/python/tryworks.mplstyle": build_mplstyle(D),
        "dist/python/tryworks.py": build_pyviz(D),
        "dist/print/SPEC.md": build_print_md(D),
        "dist/typst/poster.typ": build_poster_typ(D),
        "dist/typst/colors.typ": build_typst(D),
        "dist/quarto/try-works.scss": build_quarto_scss(D, "cold"),
        "dist/quarto/try-works-dark.scss": build_quarto_scss(D, "lit"),
        "dist/quarto/try-works.theme": build_quarto_theme(D),
        "dist/quarto/typst-brand.typ": build_typst_brand(D),
        "dist/tailwind/colors.generated.js": build_tailwind(D),
        "dist/themes/terminals/Try-Works.ghostty": build_ghostty(D),
        "dist/themes/terminals/Try-Works-Cold.ghostty": build_ghostty_cold(D),
        "dist/themes/terminals/Try-Works.itermcolors": build_iterm(D),
        "dist/themes/terminals/Try-Works-Cold.itermcolors": build_iterm_cold(D),
        "dist/omz/try-works.zsh-theme": build_omz(D),
        "dist/omz/try-works-cold.zsh-theme": build_omz_cold(D),
        "dist/vscode/themes/Try-Works-color-theme.json": build_vscode(D),
        "dist/vscode/themes/Try-Works-Cold-color-theme.json": build_vscode_cold(D),
        **build_vscode_icons(D),
        "dist/zed/themes/Try-Works.json": build_zed(D),
        "dist/vivaldi/lit/settings.json": build_vivaldi(D, "lit"),
        "dist/vivaldi/cold/settings.json": build_vivaldi(D, "cold"),
        "dist/obsidian/theme.css": build_obsidian(D),
        # version single-sourced from src/ manifests into dist/:
        "dist/obsidian/manifest.json": stamp_version("obsidian/manifest.json", D),
        "dist/vscode/package.json": stamp_version("vscode/package.json", D),
        "dist/tailwind/package.json": stamp_version("tailwind/package.json", D),
        # the web app embeds its generated CSS in place (the one src/ exception):
        "src/web/src/css/try-works.css": css,
        "src/web/src/css/typography.css": typo,
        "src/web/src/css/p3.css": build_p3(D),
        "src/web/src/css/a11y.css": build_a11y(D),
        "src/web/src/css/fallbacks.css": build_fallbacks(D),
        "src/web/src/css/motion.css": build_motion(D),
    }

def main(argv):
    D = load()
    arts = artifacts(D)
    if "--check" in argv:
        drift = []
        for rel, content in arts.items():
            p = REPO / rel
            if not p.exists() or p.read_text() != content:
                drift.append(rel)
        if drift:
            print("DRIFT: these files do not match src/try-works.json:")
            for d in drift: print("  " + d)
            print("Run `make generate` and commit.")
            return 1
        print("clean: %d generated files match the json" % len(arts))
        return 0
    for rel, content in arts.items():
        p = REPO / rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(content)
    print("generated %d files from src/try-works.json" % len(arts))
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
