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
from generate_obsidian import build_obsidian

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

def build_vivaldi(D, modekey):
    """Vivaldi browser theme (settings.json). Schema matches an exported Vivaldi
    theme (engineVersion 1): five colours plus behaviour flags and a stable id.
    assemble.sh zips this into an importable .zip per mode. The id is derived
    deterministically (uuid5) so regeneration does not drift."""
    m = D["modes"][modekey]
    up = lambda h: h.upper()
    name = "Try-Works" if modekey == "lit" else "Try-Works (True Lamp)"
    tid = str(uuid.uuid5(uuid.NAMESPACE_URL, "try-works.vivaldi." + modekey))
    theme = {
        "accentFromPage": False, "accentOnWindow": False, "accentSaturationLimit": 1,
        "alpha": 1, "backgroundImage": "", "backgroundPosition": "stretch", "blur": 0,
        "colorAccentBg": up(m["accent"]), "colorBg": up(m["bg"]), "colorFg": up(m["text"]),
        "colorHighlightBg": up(m["sea"]), "colorPosition": "unified", "colorWindowBg": up(m["surface"]),
        "contrast": 2, "dimBlurred": False, "engineVersion": 1, "id": tid, "name": name,
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

def build_typst(D):
    m = D["modes"]["lit"]
    pairs = [("pitch", m["bg"]), ("hold", m["surface"]), ("sea-deep", m["sea-deep"]), ("sea", m["sea"]),
             ("sea-bright", m["sea-bright"]), ("sea-pale", m["sea-pale"]), ("ember", m["accent"]),
             ("flame", m["accent-bright"]), ("whale", m["text"]), ("gull", m["text-muted"])]
    return "// Try-Works colours. Generated from try-works.json.\n" + "".join('#let %s = rgb("%s")\n' % (n, v) for n, v in pairs)

def build_zed(D):
    """Zed theme family (schema v0.2.0). Dark (Try-Fire) only: UI from modes.lit,
    syntax from the audited code map, terminal ANSI from the terminal block."""
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
    theme = {"$schema": "https://zed.dev/schema/themes/v0.2.0.json",
             "name": "Try-Works", "author": "tiagojct",
             "themes": [{"name": "Try-Works (Try-Fire)", "appearance": "dark", "style": style}]}
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
        "dist/vscode/themes/Try-Works-color-theme.json": build_vscode(D),
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
