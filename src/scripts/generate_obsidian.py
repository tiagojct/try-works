"""Obsidian theme builder. Generated from try-works.json.

Only build_obsidian(D) is imported by generate.py; everything else here is a
private helper local to this one surface. hsl/_mix/_rgbtriple used to live in
generate.py but are used only by this builder, so they moved here with it.
"""
import colorsys
from urllib.parse import quote


def hsl(hexv):
    h = hexv.lstrip("#"); r, g, b = [int(h[i:i+2], 16)/255 for i in (0, 2, 4)]
    hh, ll, ss = colorsys.rgb_to_hls(r, g, b); return round(hh*360), round(ss*100), round(ll*100)


def _mix(a, b, t):
    """Linear sRGB blend of two hex colours, t in [0,1]. Deterministic; endpoints
    share the system's hues so blends stay on-palette."""
    a, b = a.lstrip("#"), b.lstrip("#")
    ca = [int(a[i:i+2], 16) for i in (0, 2, 4)]; cb = [int(b[i:i+2], 16) for i in (0, 2, 4)]
    return "#%02x%02x%02x" % tuple(round(ca[i] + (cb[i] - ca[i]) * t) for i in range(3))


def _rgbtriple(h):
    h = h.lstrip("#"); return ", ".join(str(int(h[i:i+2], 16)) for i in (0, 2, 4))


def _named_hues(pal):
    """8 identity hues, mode-independent (like the terminal ANSI set) -- shared
    unchanged across both .theme-dark and .theme-light blocks."""
    fire, ext = pal["fire"], pal["extended"]
    return {"red": ext["brick"], "orange": fire["ember"], "yellow": fire["flame"],
            "green": ext["kelp"], "cyan": ext["shoal"], "blue": ext["tide"],
            "purple": ext["dusk"], "pink": _mix(ext["brick"], ext["dusk"], 0.5)}


def _ramp(m):
    bg, surf, raised, bord, txt, muted, seab = (m["bg"], m["surface"], m["surface-raised"],
        m["border"], m["text"], m["text-muted"], m["sea-bright"])
    if m["scheme"] == "dark":   # base-00 = darkest bg -> base-100 = lightest text
        return {"00": bg, "05": _mix(bg, surf, 0.5), "10": surf, "20": raised,
                "25": _mix(raised, bord, 0.5), "30": bord, "35": _mix(bord, seab, 0.35),
                "40": _mix(bord, seab, 0.6), "50": _mix(seab, muted, 0.45), "60": muted,
                "70": _mix(muted, txt, 0.4), "100": txt}
    # light: base-00 = lightest bg -> base-100 = darkest text
    return {"00": bg, "05": _mix(bg, bord, 0.25), "10": _mix(bg, bord, 0.5), "20": bord,
            "25": _mix(bord, muted, 0.2), "30": _mix(bord, muted, 0.35), "35": _mix(bord, muted, 0.5),
            "40": _mix(bord, muted, 0.65), "50": _mix(bord, muted, 0.85), "60": muted,
            "70": _mix(muted, txt, 0.4), "100": txt}


def _callout_map(n):
    """14 canonical callout-type colour variables (Editor/Callout). Warning uses
    yellow, not orange: ember is the rare load-bearing fire mark (FOUNDATIONS.md),
    reserved everywhere except a stated exception. summary/important are that
    exception's Obsidian analogue -- the two callout types whose whole job is
    "notice this" -- still only 2 of 14 so the rarity holds."""
    return {"info": n["blue"], "todo": n["blue"], "tip": n["cyan"], "success": n["green"],
            "question": n["purple"], "example": n["purple"], "error": n["red"], "fail": n["red"],
            "bug": n["pink"], "warning": n["yellow"], "summary": n["orange"], "important": n["orange"]}


def _light_safe_hue(hx, m):
    """Darken a mid-tone brand hue toward this mode's own text colour so text set
    in it clears WCAG AA against a light background. Dark mode returns the raw
    hue unchanged: mid-saturation brand colours already read fine against a
    near-black bg (verified >=4.15:1 for every colour this is used on), but the
    same raw hex against the light bg measures as low as 2.27:1 -- under half
    the 4.5:1 floor. t=0.45 clears every hue this project has tried it on with
    margin; reused wherever a named/D['code'] hue needs to double as body text
    (not just as a large icon/tint, where raw contrast matters less)."""
    return hx if m["scheme"] == "dark" else _mix(hx, m["text"], 0.45)


def _code_syntax_map(m, codem):
    """D['code']'s 11 roles -> the 11 real --code-* syntax vars (Editor/Code).

    D['code'] is tuned once, against the dark (lit) background only (e.g.
    variable == lit.text, a near-white). Reused flat in .theme-light this fails
    WCAG AA against the light code background -- measured 2.27-3.35:1 for the
    six hued roles (need >=4.5:1), and worse for the near-neutral roles. So:
    - comment/variable/parameter/operator/punctuation derive from this mode's
      own text/muted tokens instead of the flat blob (variable/comment already
      equal lit.text/lit.text-muted anyway, so lit output is unchanged).
      Mixing toward --border was tried for punctuation and rejected: border is
      deliberately near-background by design, so blending toward it tanks
      contrast in light mode (measured 2.47:1) -- punctuation stays pinned to
      text-muted instead, same as operator.
    - keyword/string/number/function/type/decorator keep D['code']'s flat hue
      in dark mode (matches today's shipped VS Code/Zed themes, already
      4.15-6.12:1 there), but in light mode are darkened toward this mode's own
      text colour (t=0.45, verified >=4.5:1 for all six) rather than reused
      raw -- same "no new colours, just mix existing ones" technique already
      used throughout this file, and thematically consistent with how cold's
      own accent is already a darkened variant of lit's ember for the same
      contrast reason."""
    c = lambda r: codem[r]["color"]
    txt, muted = m["text"], m["text-muted"]
    hue = lambda r: _light_safe_hue(c(r), m)
    return {"normal": txt, "comment": muted,
            "keyword": hue("keyword"), "string": hue("string"), "value": hue("number"),
            "function": hue("function"), "tag": hue("type"), "important": hue("decorator"),
            "property": _mix(txt, muted, 0.35), "operator": muted,
            "punctuation": muted}


_CODE_STYLE_CLASSES = {"comment": ("comment", "comment"), "keyword": ("keyword", "keyword"), "type": ("type", "tag")}


def _code_style_rules(codem):
    """Obsidian's --code-* vars are colour-only; restore the italic/bold this
    project's code-role map already carries (build_vscode/build_zed honour the
    same styles) so Obsidian isn't the one flat surface. Targets both the CM6
    edit-mode class and the reading-mode Prism-style token class defensively --
    inert on whichever engine a given Obsidian version doesn't use. Generated
    from whichever codem roles carry a style (currently comment/keyword/type),
    so a future 4th styled role picks this up automatically."""
    prop = {"italic": "font-style: italic", "bold": "font-weight: 700"}
    out = []
    for role, (cm_cls, token_cls) in _CODE_STYLE_CLASSES.items():
        style = codem[role].get("style")
        if style:
            out.append(".cm-s-obsidian .cm-%s, .markdown-rendered pre code .token.%s { %s; }"
                       % (cm_cls, token_cls, prop[style]))
    return "\n".join(out)


_TASK_GLYPHS = [(">", "fwd", "→"), ("<", "sched", "←"), ("?", "question", "?"),
                ("!", "important", "!"), ("*", "star", "★")]


def _task_rules():
    """Alternative checkbox states (- [/] [>] [<] [?] [!] [*] [-]), the Minimal/Things convention.
    data-task is set by Obsidian itself on both the reading-view <li> and the live-preview line
    (app.css 1.12 styles [data-task="x"] through exactly these selectors), so this is the most
    official hook available. Reading view uses the child combinator so nested tasks each match
    their own <li>; an editor line is its own element, so no cross-state leakage there. The
    ::after rules explicitly neutralise core's :checked checkmark (absolute position + SVG mask +
    marker background) because Obsidian marks any non-space state as checked. Colours are the
    per-mode --tw-task-* vars emitted in blk(); done [x] and the untouched [ ] keep core styling."""
    def sels(ch, after=False):
        a = "::after" if after else ""
        return ('.markdown-rendered li.task-list-item[data-task="%s"] > input.task-list-item-checkbox%s,\n'
                '.cm-s-obsidian .HyperMD-task-line[data-task="%s"] .task-list-item-checkbox%s' % (ch, a, ch, a))
    glyph_css = ('  content: "%s"; position: static; display: flex; align-items: center; justify-content: center;\n'
                 "  width: 100%%; height: 100%%; background-color: transparent; -webkit-mask-image: none;\n"
                 "  color: var(--tw-task-%s); font-family: var(--tw-font-sans);\n"
                 "  font-size: calc(var(--checkbox-size) * 0.72); font-weight: 700; line-height: 1;")
    out = []
    for ch, key, glyph in _TASK_GLYPHS:
        out.append("%s {\n  background-color: transparent; border-color: var(--tw-task-%s);\n}" % (sels(ch), key))
        out.append("%s {\n%s\n}" % (sels(ch, True), glyph_css % (glyph, key)))
    out.append("%s {\n  background-color: transparent; border-color: var(--tw-task-progress);\n}" % sels("/"))
    out.append('%s {\n  content: ""; position: static; display: block; width: 100%%; height: 100%%;\n'
               "  -webkit-mask-image: none; border-radius: inherit;\n"
               "  background: linear-gradient(90deg, var(--tw-task-progress) 50%%, transparent 50%%);\n}" % sels("/", True))
    out.append('.markdown-rendered li.task-list-item[data-task="-"],\n'
               '.cm-s-obsidian .HyperMD-task-line[data-task="-"] {\n'
               "  color: var(--text-faint); text-decoration: line-through; text-decoration-color: var(--text-faint);\n}")
    out.append("%s {\n  background-color: transparent; border-color: var(--text-faint);\n}" % sels("-"))
    out.append('%s {\n  content: "\\2013"; position: static; display: flex; align-items: center; justify-content: center;\n'
               "  width: 100%%; height: 100%%; background-color: transparent; -webkit-mask-image: none;\n"
               "  color: var(--text-faint); font-weight: 700; line-height: 1;\n}" % sels("-", True))
    return ("/* Alternative task states -- see _task_rules() docstring. */\n" + "\n".join(out) + "\n")


_FEATURES_CSS = """\
/* Focus mode (Style Settings: tw-focus). Chrome recedes until pointed at; the note stands alone.
   Restores on hover or keyboard focus within. */
body.tw-focus :is(.workspace-tab-header-container, .view-header, .workspace-ribbon, .status-bar) {
  opacity: 0.25; transition: opacity 0.2s ease;
}
body.tw-focus :is(.workspace-tab-header-container, .view-header, .workspace-ribbon, .status-bar):is(:hover, :focus-within) {
  opacity: 1;
}
/* Seamless embeds (default; Style Settings tw-embed-frames restores the framed look). Transclusions
   read as part of the note: no tint, border or title; the open-link affordance appears on hover. */
body:not(.tw-embed-frames) .markdown-rendered .markdown-embed,
body:not(.tw-embed-frames) .markdown-source-view .markdown-embed {
  background-color: transparent; border: none; padding: 0;
}
body:not(.tw-embed-frames) .markdown-embed-title { display: none; }
body:not(.tw-embed-frames) .markdown-embed-link { opacity: 0; transition: opacity 0.15s ease; }
body:not(.tw-embed-frames) .markdown-embed:hover .markdown-embed-link { opacity: 1; }
/* Images: soft corners; a pipe caption (![[img.png|caption]]) renders as a quiet figcaption. Alt
   texts that are just file names (Obsidian's fallback when no caption is given) are excluded. */
.markdown-rendered .image-embed img { border-radius: 4px; }
.markdown-rendered .image-embed[alt]:not([alt=""]):not([alt$=".png" i]):not([alt$=".jpg" i]):not([alt$=".jpeg" i]):not([alt$=".webp" i]):not([alt$=".gif" i]):not([alt$=".svg" i]):not([alt$=".bmp" i])::after {
  content: attr(alt); display: block; font-family: var(--tw-font-sans); font-size: 0.82em;
  color: var(--text-muted); text-align: center; margin-top: 0.35em;
}
/* Per-note gallery helper (Minimal's composable-cssclasses idea): add `cssclasses: img-grid` to a
   note's frontmatter and consecutive images in one paragraph tile into a grid (reading view). */
.markdown-preview-view.img-grid .markdown-preview-section p:has(> .image-embed) {
  display: flex; flex-wrap: wrap; gap: 8px;
}
.markdown-preview-view.img-grid .markdown-preview-section p > .image-embed { flex: 1 1 240px; min-width: 0; }
.markdown-preview-view.img-grid .markdown-preview-section p > .image-embed img {
  width: 100%; height: 100%; object-fit: cover;
}
/* Lists. Bullets are short accent dashes -- an explicit owner call to let the one warm mark walk
   the margin; ordered numbers stay muted so it's the dash alone that carries it. Nested dashes
   drop to the muted marker colour, so depth reads by temperature, and core's higher-specificity
   is-collapsed rule still wins in reading view -- a folded marker signals accent + halo at any
   depth. Hanging offset -0.95em (stock -0.8em) keeps air between dash and text; the editor depth
   selector is best-effort against CM6's numbered line classes, inert if a future version drops
   them. Ordered markers take muted tabular old-style figures so multi-digit lists column-align
   quietly. */
.markdown-rendered .list-bullet { margin-inline-start: -0.95em; }
.list-bullet::after {
  width: 0.55em; height: 0.12em; border-radius: 1px;
  background-color: var(--text-accent);
}
.markdown-rendered li li .list-bullet::after,
.cm-s-obsidian [class*="HyperMD-list-line-"]:not(.HyperMD-list-line-1):not(.HyperMD-list-line-nobullet) .list-bullet::after {
  background-color: var(--list-marker-color);
}
.markdown-rendered :is(ol, ul) > li::marker { color: var(--text-muted); }
.markdown-rendered ol > li::marker { font-variant-numeric: tabular-nums oldstyle-nums; }
/* Fenced code blocks get a hairline so they separate from same-tone chrome (reading view; the
   editor draws code blocks per-line, where a border would fragment). */
.markdown-rendered pre { border: 1px solid var(--background-modifier-border); }
/* Phone: the desktop-tuned 0.75em Properties type is too small under a thumb; row heights are
   already restored by core's own .is-phone metadata override. */
body.is-phone {
  --metadata-label-font-size: 0.9em; --metadata-input-font-size: 0.9em;
}
"""


def _graph_map(m, n, faint):
    return {"line": m["border"], "text": m["text-muted"], "node": m["sea-bright"],
            "node-unresolved": faint, "node-focused": m["accent-bright"],
            "node-tag": n["blue"], "node-attachment": n["cyan"]}


def _canvas_map(m, n):
    return {"background": m["bg"], "card-label-color": m["text-muted"], "dot-pattern": m["border"],
            "color-1": n["red"], "color-2": n["orange"], "color-3": n["yellow"],
            "color-4": n["green"], "color-5": n["cyan"], "color-6": n["purple"]}


def _properties_map(m):
    """Panel baseline is the note's own background (--background-primary, i.e.
    m['bg']), not a lifted "card" tone: explicit direction is that Properties
    should read as part of the note, not a distinct box. All row/cell
    backgrounds share this one baseline (still avoids the earlier two-tone
    checkerboard, since text/link/tag/date property types render through
    --metadata-input-background or --metadata-property-background even with
    nothing focused, and both are now the same value) -- only hover/active lift
    off it, so there is still a feedback cue on interaction. Font size cut well
    below body text: JetBrains Mono at the same nominal size reads larger than
    a proportional face, so matching body size looked heavier than intended.
    Rows also sit tighter than stock (gap 3px -> 1px, row min-height 1.75x ->
    1.4x --font-text-size, the base editor size -- not the 1.2x-scaled reading
    body): at the smaller mono size, stock spacing read as double-spaced. Both
    are real vars consumed by .metadata-properties / .metadata-container in
    app.css; on phones, core's own .is-phone .metadata-container override sits
    on a deeper element and wins, so mobile tap targets are untouched."""
    hover = m["surface"]
    return {"background": m["bg"], "border-color": m["border"],
            "divider-color": m["border"],
            "gap": "1px", "input-height": "calc(var(--font-text-size) * 1.4)",
            "label-text-color": m["text-muted"], "label-text-color-hover": m["text"],
            "label-font-size": "0.75em", "input-font-size": "0.75em",
            "sidebar-label-font-size": "0.75em", "sidebar-input-font-size": "0.75em",
            "input-text-color": m["text"], "input-background": m["bg"],
            "input-background-hover": hover,
            "property-background": m["bg"], "property-background-hover": hover,
            "property-background-active": "%s33" % m["sea-bright"]}


def _settings_block(lit, cold):
    """Style Settings plugin (mgmeyers/obsidian-style-settings) metadata block.
    Each setting's id is the literal CSS variable/class name the plugin writes
    to -- not just a label. Eleven settings: enough to be useful without
    re-exposing the whole token set (which would break single-source-of-truth).
    All class-toggle defaults are unchecked/absent, and the unconditional base
    CSS keeps the default look -- toggles are either opt-in modes (focus,
    framed embeds) or escape hatches back to Obsidian stock / the other
    Try-Works voice, so a fresh install (plugin absent, or present but
    untouched) always renders identically to the shipped defaults.
    Known limitation: the accent picker rewrites --text-accent and everything
    chained to it, but --accent-h/s/l stay pinned to the brand accent (CSS
    cannot decompose a hex var into HSL), so Obsidian's derived --color-accent
    tints won't track a custom accent."""
    return ('''/* @settings
name: Try-Works
id: try-works
settings:
  - id: tw-typography
    title: Typography
    type: heading
    level: 1
    collapsed: false
  - id: text-accent
    title: Accent color
    description: The one warm mark. Defaults follow Try-Fire/True Lamp.
    type: variable-themed-color
    format: hex
    default-light: "%s"
    default-dark: "%s"
  - id: tw-body-scale
    title: Body text size
    description: Multiplier on editor/reading font size (theme default 1.2x).
    type: variable-number-slider
    default: 1.2
    min: 0.9
    max: 1.4
    step: 0.02
  - id: line-height-normal
    title: Line height
    description: Paragraph line spacing (theme default 1.7).
    type: variable-number-slider
    default: 1.7
    min: 1.4
    max: 2.0
    step: 0.05
  - id: tw-headings-sans
    title: Sans headings (match body)
    description: Off (default) keeps Try-Works' serif (Fraunces) headings.
    type: class-toggle
    default: false
  - id: tw-body-serif
    title: Serif body text (Fraunces)
    description: Off (default) keeps Try-Works' sans (Archivo) note body.
    type: class-toggle
    default: false
  - id: tw-interface
    title: Interface
    type: heading
    level: 1
    collapsed: false
  - id: tw-focus
    title: Focus mode
    description: Dim tabs, ribbon, header and status bar until hovered.
    type: class-toggle
    default: false
  - id: tw-embed-frames
    title: Framed embeds (Obsidian default)
    description: Off (default) keeps Try-Works' seamless transclusions.
    type: class-toggle
    default: false
  - id: tw-nav-plain
    title: Plain file list (no icons)
    description: Off (default) keeps folder and file icons in the explorer.
    type: class-toggle
    default: false
  - id: tw-explorer-truncate
    title: Truncate file names (Obsidian default)
    description: Off (default) keeps Try-Works' wrapped file-explorer labels.
    type: class-toggle
    default: false
*/
''' % (cold["accent"], lit["accent"]))


def build_obsidian(D):
    """Obsidian theme. Every variable here is a real Obsidian CSS variable
    (verified against docs.obsidian.md). The grayscale --color-base-* ramp and
    named --color-* primitives let Obsidian derive on-system defaults; the rest
    are pinned to brand tokens per mode."""
    lit, cold, pal = D["modes"]["lit"], D["modes"]["cold"], D["palette"]
    fire, ext, codem = pal["fire"], pal["extended"], D["code"]
    named = _named_hues(pal)

    def blk(m, sel):
        ah = hsl(m["accent"]); r = _ramp(m)
        faint = _mix(m["text-muted"], m["bg"], 0.4)
        # Hover accent: brighter in dark mode, DEEPER in light mode. Light hovers must darken to hold
        # WCAG AA -- accent-bright on the cold bg measures 3.55:1, under the 4.5 floor, while
        # accent-deep clears it with margin. validate.py locks both pairs (lit accent-bright/bg,
        # cold accent-deep/bg) so a palette edit can't silently reintroduce the failure.
        hov = m["accent-bright"] if m["scheme"] == "dark" else m["accent-deep"]
        callout, graph, canvas, meta, code = (_callout_map(named), _graph_map(m, named, faint),
            _canvas_map(m, named), _properties_map(m), _code_syntax_map(m, codem))
        L = ["." + sel + " {",
             "  --accent-h: %d; --accent-s: %d%%; --accent-l: %d%%;" % (ah[0], ah[1], ah[2])]
        L += ["  --color-base-%s: %s;" % (k, v) for k, v in r.items()]
        for n, hx in named.items():
            L += ["  --color-%s: %s;" % (n, hx), "  --color-%s-rgb: %s;" % (n, _rgbtriple(hx))]
        L += [
         "  --background-primary: %s;" % m["bg"], "  --background-primary-alt: %s;" % m["surface"],
         # Secondary (sidebar, margin/footnote panels) matches primary (the note itself) rather than the
         # lifted "surface" tone -- same seam the Properties-panel and .footnote fixes already addressed;
         # this is the general form of that same complaint (any secondary panel vs. the note itself).
         "  --background-secondary: %s;" % m["bg"], "  --background-secondary-alt: %s;" % m["surface-raised"],
         "  --background-modifier-border: %s;" % m["border"],
         "  --background-modifier-border-hover: %s;" % _mix(m["border"], m["text-muted"], 0.3),
         "  --background-modifier-border-focus: %s;" % m["accent"],
         # Hover/selected feedback tint. ~70 app.css rules read this (menu items, suggestion lists, tab
         # headers, clickable icons, the copy-code button); an earlier round pinned it to the note bg to
         # keep the footnotes panel flat, which silently erased that feedback across all of them. The
         # panel's grey actually comes from dedicated variables (the --footnote-input-background(-active)
         # chain plus --embed-background, read by the .footnotes-view rules in app.css 1.12), which are
         # set explicitly below -- so this var is free to do its real job again. Same sea-bright family as
         # --nav-item-background-hover (0x1f), one step under --background-modifier-active-hover's 0x33.
         "  --background-modifier-hover: %s1f;" % m["sea-bright"],
         # Footnotes panel rows keep the note's own background, editing included (the edit state still
         # reads via Obsidian's own focus ring on .is-editing). Without these two, the -active default
         # chains to --background-modifier-hover and the tint above would reintroduce the grey. Real
         # variables from app.css's footnotes view (Obsidian 1.12); not yet on docs.obsidian.md.
         "  --footnote-input-background: %s;" % m["bg"],
         "  --footnote-input-background-active: %s;" % m["bg"],
         # Obsidian's own blockquote background hook (default transparent), read by both
         # .markdown-rendered blockquote and live preview's .HyperMD-quote -- replaces the earlier
         # private --tw-blockquote-bg plus a hand-rolled background on those same selectors.
         "  --blockquote-background-color: %s1f;" % m["sea-bright"],
         "  --background-modifier-active-hover: %s33;" % m["sea-bright"],
         "  --background-modifier-form-field: %s;" % m["surface"],
         "  --background-modifier-success: rgba(%s, 0.15);" % _rgbtriple(ext["kelp"]),
         "  --text-normal: %s;" % m["text"], "  --text-muted: %s;" % m["text-muted"], "  --text-faint: %s;" % faint,
         # Reading weight, per mode: bright text on the near-black lit bg optically thins (halation), so
         # the dark body reads at a hair over regular to hold its colour; the light bg has no halation,
         # so cold stays at the true 400. Consumed as font-weight (not font-variation-settings) on the
         # reading/edit surfaces below, so bold and headings still win by cascade. Archivo is a real
         # variable font (wght 100-900), so 430 is interpolated, not faux-bold.
         "  --tw-body-weight: %d;" % (430 if m["scheme"] == "dark" else 400),
         "  --text-on-accent: %s;" % m["on-accent"], "  --text-on-accent-inverted: %s;" % m["text"],
         "  --text-accent: %s;" % m["accent"], "  --text-accent-hover: %s;" % hov,
         "  --text-error: %s;" % ext["brick"],
         "  --text-selection: %s44;" % m["sea-bright"],
         "  --text-highlight-bg: rgba(%s, 0.4);" % _rgbtriple(fire["flame"]),
         "  --text-highlight-bg-active: rgba(%s, 0.6);" % _rgbtriple(fire["ember"]),
         "  --interactive-normal: %s;" % m["surface"], "  --interactive-hover: %s;" % m["surface-raised"],
         "  --interactive-accent: var(--text-accent);", "  --interactive-accent-hover: %s;" % hov,
         "  --link-color: var(--text-accent);", "  --link-color-hover: %s;" % hov,
         "  --link-decoration: underline;", "  --link-decoration-hover: underline;",
         "  --link-decoration-thickness: 0.07em;",
         "  --link-unresolved-color: %s;" % m["text-muted"], "  --link-unresolved-opacity: 0.7;",
         "  --link-unresolved-decoration-style: dashed;", "  --link-unresolved-decoration-color: %s;" % m["text-muted"],
         "  --link-external-color: var(--text-accent);", "  --link-external-color-hover: %s;" % hov,
         "  --link-external-decoration: underline;",
         "  --code-background: %s;" % m["surface"], "  --code-white-space: pre-wrap;",
        ]
        L += ["  --code-%s: %s;" % (k, v) for k, v in code.items()]
        L += [
         "  --blockquote-border-color: var(--text-accent);", "  --blockquote-color: %s;" % m["text-muted"],
         "  --hr-color: %s;" % m["border"], "  --divider-color: %s;" % m["border"],
         # Explicit call: tags are one of the places the fire mark is allowed to show, alongside
         # links/checkboxes/focus. Accent/bg contrast already verified by validate.py (>=4.61:1 both
         # modes), so no separate light-mode darkening needed the way the cool tide hue required.
         "  --tag-color: var(--text-accent);", "  --tag-color-hover: %s;" % hov,
         "  --tag-background: %s1f;" % m["accent"],
         "  --tag-background-hover: %s33;" % m["accent"], "  --tag-border-color: transparent;",
         "  --tag-border-color-hover: %s55;" % m["accent"],
         "  --checkbox-color: var(--text-accent);", "  --checkbox-color-hover: %s;" % hov,
         "  --checkbox-marker-color: %s;" % m["on-accent"],
         "  --checkbox-border-color: %s;" % m["border"], "  --checkbox-border-color-hover: var(--text-accent);",
         "  --checklist-done-color: %s;" % m["text-muted"],
         # Alternative task states (- [/] [>] [<] [?] [!] [*], Minimal/Things convention), rendered by
         # the shared _task_rules() CSS at the bottom of this file. Hues follow the callout logic (cool
         # named hues, light-safe in cold); star is ember -- checkboxes are already a sanctioned fire
         # location (--checkbox-color above).
         "  --tw-task-progress: %s;" % m["sea-bright"],
         "  --tw-task-fwd: %s;" % _light_safe_hue(named["blue"], m),
         "  --tw-task-sched: %s;" % _light_safe_hue(named["cyan"], m),
         "  --tw-task-question: %s;" % _light_safe_hue(named["purple"], m),
         "  --tw-task-important: %s;" % _light_safe_hue(named["yellow"], m),
         "  --tw-task-star: %s;" % m["accent"],
         "  --pill-color: %s;" % m["text"], "  --pill-color-hover: %s;" % m["text"],
         "  --pill-color-remove: %s;" % m["text-muted"], "  --pill-color-remove-hover: %s;" % ext["brick"],
         # Property pills (author, aliases, ...) sit flat on the note like the rest of the Properties
         # panel -- the boxed surface-raised chip read as a second UI inside it. Hover keeps the tint
         # and accent outline, so a pill still announces itself as removable on interaction. Tag-type
         # pills are unaffected: they read --tag-background, the deliberate accent tint.
         "  --pill-background: transparent;", "  --pill-background-hover: %s33;" % m["sea-bright"],
         "  --pill-border-color: transparent;", "  --pill-border-color-hover: var(--text-accent);",
         "  --list-marker-color: %s;" % m["text-muted"], "  --list-marker-color-hover: var(--text-accent);",
         # Collapsed marker goes accent, restoring core's own affordance (this theme used to mute it):
         # a closed bullet hides content, which is worth the one warm mark -- same sanctioned family as
         # links/checkboxes/tags. Core pairs it with a halo via --background-modifier-active-hover.
         "  --list-marker-color-collapsed: var(--text-accent);",
         "  --nav-item-color: %s;" % m["text-muted"], "  --nav-item-color-hover: %s;" % m["text"],
         "  --nav-item-color-active: %s;" % m["text"], "  --nav-item-background-hover: %s1f;" % m["sea-bright"],
         # A flat surface-raised swap reads fine in dark mode (lighter than a near-black bg) but washes
         # out in light mode (surface-raised is literally lighter than the page bg there, i.e. invisible);
         # a sea-bright tint is visible in both, and stronger than --nav-item-background-hover's tint
         # so the persistently-selected note reads as more prominent than a transient hover.
         "  --nav-item-background-active: %s33;" % m["sea-bright"],
         "  --tab-background-active: %s;" % m["bg"], "  --tab-text-color: %s;" % m["text-muted"],
         "  --tab-text-color-active: %s;" % m["text"], "  --tab-text-color-focused-active-current: %s;" % m["text"],
         "  --tab-container-background: %s;" % m["surface"], "  --tab-divider-color: %s;" % m["border"],
         # Width set alongside the colour: relying on Obsidian's default (0.5-1px, varies by context)
         # made the accent outline near-invisible on some displays.
         "  --tab-outline-color: var(--text-accent);", "  --tab-outline-width: 2px;",
         "  --titlebar-background: %s;" % m["bg"], "  --titlebar-background-focused: %s;" % m["surface"],
         "  --titlebar-text-color: %s;" % m["text-muted"], "  --titlebar-text-color-focused: %s;" % m["text"],
         "  --scrollbar-bg: transparent;", "  --scrollbar-thumb-bg: %s40;" % m["sea-bright"],
         "  --scrollbar-active-thumb-bg: %s66;" % m["sea-bright"],
         "  --table-background: %s;" % m["surface"],
         # Alt rows deliberately equal --table-background: flat tables, no zebra. Row hover (below) is
         # the location cue; a stripe read as noise against the calm sea surfaces.
         "  --table-border-color: %s;" % m["border"], "  --table-row-alt-background: %s;" % m["surface"],
         "  --table-row-background-hover: %s14;" % m["sea-bright"], "  --table-selection: %s22;" % m["accent"],
         "  --table-selection-border-color: var(--text-accent);",
         "  --table-header-background: %s;" % m["surface-raised"], "  --table-header-background-hover: %s33;" % m["sea-bright"],
         "  --table-header-border-color: %s;" % m["border"], "  --table-header-color: %s;" % m["text"],
         "  --table-header-weight: 600;",
         "  --table-text-color: %s;" % m["text"],
         "  --table-drag-handle-background: %s;" % m["surface-raised"], "  --table-drag-handle-background-active: var(--text-accent);",
         "  --table-drag-handle-color: %s;" % m["text-muted"], "  --table-drag-handle-color-active: %s;" % m["on-accent"],
         "  --ribbon-background: %s;" % m["bg"], "  --ribbon-background-collapsed: %s;" % m["bg"],
         # Quieter chrome: status bar drops to the smallest UI size, vault name recedes to muted
         # weight-400 small type (all official vars) -- the note, not the workspace, is the subject.
         "  --status-bar-background: %s;" % m["surface"], "  --status-bar-border-color: %s;" % m["border"],
         "  --status-bar-text-color: %s;" % m["text-muted"], "  --status-bar-font-size: var(--font-smallest);",
         "  --vault-profile-color: %s;" % m["text-muted"], "  --vault-profile-color-hover: %s;" % m["text"],
         "  --vault-profile-font-weight: 400;", "  --vault-profile-font-size: var(--font-ui-smaller);",
         "  --modal-background: %s;" % m["surface"], "  --modal-border-color: %s;" % m["border"],
         "  --icon-color: %s;" % m["text-muted"], "  --icon-color-hover: %s;" % m["text"],
         "  --icon-color-active: var(--text-accent);", "  --icon-color-focused: var(--text-accent);",
         "  --search-clear-button-color: %s;" % m["text-muted"], "  --search-icon-color: %s;" % m["text-muted"],
         "  --search-result-background: %s;" % m["surface"],
         "  --embed-background: %s;" % m["surface"], "  --embed-border-start: 4px solid var(--text-accent);",
         "  --embed-block-shadow-hover: 0 2px 10px rgba(%s, 0.25);" % _rgbtriple(m["sea-bright"]),
         "  --inline-title-color: %s;" % m["text"], "  --inline-title-font: var(--tw-font-serif);",
         "  --divider-color-hover: var(--text-accent);", "  --divider-width-hover: 2px;",
        ]
        L += ["  --callout-%s: %s;" % (k, v) for k, v in callout.items()]
        L += ["  --callout-quote: var(--text-muted);", "  --callout-default: var(--text-muted);"]
        L += ["  --graph-%s: %s;" % (k, v) for k, v in graph.items()]
        L += ["  --canvas-%s: %s;" % (k, v) for k, v in canvas.items()]
        L += ["  --metadata-%s: %s;" % (k, v) for k, v in meta.items()]
        L += ["}"]
        return "\n".join(L)

    # External-link glyph: lucide "arrow-up-right". Percent-encoded so the data URI
    # needs no CSS quoting; drawn via mask so currentColor tints it to the link colour.
    arrow = ("<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' "
             "stroke='black' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'>"
             "<path d='M7 7h10v10'/><path d='M7 17 17 7'/></svg>")
    arrow_uri = "data:image/svg+xml," + quote(arrow)

    # File-explorer icons: lucide outlines with element data lifted verbatim from Obsidian's own
    # bundled icon map (app.js 1.12) so they match every icon the app draws natively. Same mask +
    # currentColor technique as the arrow above, so each row's icon follows its nav colour (muted
    # at rest, text on hover/active). Typed set stays deliberately small (pdf / image / canvas /
    # audio, drawn from file-text / image / layout-dashboard / music); past this scale the Iconize
    # plugin is the right tool, not more data URIs.
    def icon_uri(*els):
        svg = ("<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black'"
               " stroke-width='2' stroke-linecap='round' stroke-linejoin='round'>%s</svg>" % "".join(els))
        return "data:image/svg+xml," + quote(svg)
    pth = lambda d: "<path d='%s'/>" % d
    ico_folder = icon_uri(pth("M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9"
                              "A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"))
    ico_folder_open = icon_uri(pth("m6 14 1.5-2.9A2 2 0 0 1 9.24 10H20a2 2 0 0 1 1.94 2.5l-1.54 6"
                                   "a2 2 0 0 1-1.95 1.5H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h3.9"
                                   "a2 2 0 0 1 1.69.9l.81 1.2a2 2 0 0 0 1.67.9H18a2 2 0 0 1 2 2v2"))
    _page = pth("M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706"
                "l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2z")
    _corner = pth("M14 2v5a1 1 0 0 0 1 1h5")
    ico_file = icon_uri(_page, _corner)
    ico_pdf = icon_uri(_page, _corner, pth("M10 9H8"), pth("M16 13H8"), pth("M16 17H8"))
    ico_image = icon_uri("<rect x='3' y='3' width='18' height='18' rx='2'/>",
                         "<circle cx='9' cy='9' r='2'/>",
                         pth("m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"))
    ico_canvas = icon_uri("<rect x='3' y='3' width='7' height='9' rx='1'/>",
                          "<rect x='14' y='3' width='7' height='5' rx='1'/>",
                          "<rect x='14' y='12' width='7' height='9' rx='1'/>",
                          "<rect x='3' y='16' width='7' height='5' rx='1'/>")
    ico_audio = icon_uri(pth("M9 18V5l12-2v13"),
                         "<circle cx='6' cy='18' r='3'/>", "<circle cx='18' cy='16' r='3'/>")
    fx = 'body:not(.tw-nav-plain) .workspace-leaf-content[data-type="file-explorer"]'

    def nav_type(uri, *exts):
        sel = ", ".join('[data-path$="%s" i]' % e for e in exts)
        return (fx + " .nav-file-title:is(%s) .nav-file-title-content::before {\n"
                "  -webkit-mask-image: url(%s);\n  mask-image: url(%s);\n}\n" % (sel, uri, uri))
    nav_icons = (
        "/* File-explorer icons (Style Settings: tw-nav-plain removes them). Folders swap closed/open\n"
        "   with their collapse state; the vault-root row is excluded; a small typed set covers pdf,\n"
        "   images, canvas and audio via data-path. See icon_uri() note: artwork is Obsidian's own\n"
        "   lucide set. */\n"
        + fx + " :is(.nav-folder-title-content, .nav-file-title-content)::before {\n"
        '  content: ""; display: inline-block; width: 0.95em; height: 0.95em; margin-inline-end: 0.4em;\n'
        "  vertical-align: -0.12em; background-color: currentColor; opacity: 0.8;\n"
        "  -webkit-mask: url(%s) center / contain no-repeat;\n"
        "  mask: url(%s) center / contain no-repeat;\n}\n" % (ico_file, ico_file)
        + fx + " .nav-folder-title-content::before {\n"
        "  -webkit-mask-image: url(%s);\n  mask-image: url(%s);\n}\n" % (ico_folder, ico_folder)
        + fx + " .nav-folder:not(.is-collapsed) > .nav-folder-title .nav-folder-title-content::before {\n"
        "  -webkit-mask-image: url(%s);\n  mask-image: url(%s);\n}\n" % (ico_folder_open, ico_folder_open)
        + fx + " .nav-folder.mod-root > .nav-folder-title .nav-folder-title-content::before { display: none; }\n"
        + nav_type(ico_pdf, ".pdf")
        + nav_type(ico_image, ".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".avif", ".bmp")
        + nav_type(ico_canvas, ".canvas")
        + nav_type(ico_audio, ".mp3", ".m4a", ".wav", ".ogg", ".flac"))
    extra = (
        "/* Link underline offset: no official Obsidian variable for this, --link-decoration*\n"
        "   (colour, style, thickness) above covers the rest. */\n"
        ".markdown-rendered a, .cm-s-obsidian .cm-link, .cm-s-obsidian .cm-url, .cm-s-obsidian .cm-hmd-internal-link {\n"
        "  text-underline-offset: 0.16em;\n}\n"
        ".markdown-rendered a:hover { text-decoration-thickness: 0.1em; }\n"
        "/* External-link glyph: a clean up-right arrow that inherits the link colour. */\n"
        ".external-link { background-image: none; padding-right: 0; }\n"
        ".external-link::after {\n"
        '  content: ""; display: inline-block; width: 0.62em; height: 0.62em; margin-left: 0.12em; vertical-align: -0.05em;\n'
        "  background-color: currentColor;\n"
        "  -webkit-mask: url(%s) center / contain no-repeat;\n"
        "  mask: url(%s) center / contain no-repeat;\n}\n" % (arrow_uri, arrow_uri)
    )
    code_style = _code_style_rules(codem)
    return (_settings_block(lit, cold) +
            "/* Try-Works for Obsidian. Generated from try-works.json. */\n"
            "/* Popover (Components/Popover): Obsidian exposes no colour variables here (verified docs.obsidian.md); nothing to set. */\n"
            "body {\n"
            '  --tw-font-serif: "Fraunces", Georgia, serif;\n'
            '  --tw-font-sans: "Archivo", system-ui, sans-serif;\n'
            '  --tw-font-mono: "JetBrains Mono", ui-monospace, monospace;\n'
            "  /* Literal stacks here, not var(--tw-font-*): these three are Obsidian's own theme-level\n"
            "     font hooks, unlike every other font-family reference below which is an ordinary CSS\n"
            "     property on a selector we wrote. Keeping them literal matches the one arrangement\n"
            "     already proven to work this session (the original Georgia-fallback diagnosis). */\n"
            '  --font-text-theme: "Archivo", system-ui, sans-serif;\n'
            '  --font-interface-theme: "Archivo", system-ui, sans-serif;\n'
            '  --font-monospace-theme: "JetBrains Mono", ui-monospace, monospace;\n'
            "  --nav-item-white-space: normal;\n"
            "  --line-height-normal: 1.7;\n  --p-spacing: 1.35em;\n"
            "  /* Air after a heading in live preview: --p-spacing-empty is core's one hook for the first\n"
            "     line that follows a heading line (verified single consumer in app.css 1.12; 0 by\n"
            "     default). Reading view gets its match from the margin-block-end rule further down.\n"
            "     List items breathe a touch more than stock (0.075em). */\n"
            "  --p-spacing-empty: 0.6em;\n  --list-spacing: 0.1em;\n"
            "  /* Tighter than stock (0.5625em x 4 = 2.25em): lists sit closer to the text margin. Room\n"
            "     still clears the hanging dash (offset -0.95em, drawn in the list rules below). */\n"
            "  --list-indent: 1.5em;\n"
            "  /* Pull the dash left, clear of the text: the ::after mark anchors at the bullet span's\n"
            "     static position, so a mark wider than stock's dot otherwise grows toward the text.\n"
            "     Official knob; applies in reading view and editor alike. */\n"
            "  --list-bullet-transform: translateX(-0.3em);\n"
            "  /* JetBrains Mono's tall x-height reads a step larger than Archivo at equal em (same\n"
            "     reasoning as the Properties panel's 0.75em); one notch under stock font-smaller. */\n"
            "  --code-size: 0.85em;\n"
            "  /* Interface icons one stroke-step lighter than stock (m/l 1.75 -> 1.5px, s/xs 2 ->\n"
            "     1.75px): hairline icons sit with the type instead of against it. Official\n"
            "     Foundations/Icons vars; xl already ships at 1.25px and stays. */\n"
            "  --icon-m-stroke-width: 1.5px;\n  --icon-l-stroke-width: 1.5px;\n"
            "  --icon-s-stroke-width: 1.75px;\n  --icon-xs-stroke-width: 1.75px;\n}\n\n"
            + blk(lit, "theme-dark") + "\n\n" + blk(cold, "theme-light") + "\n\n"
            "/* Note body in Archivo (sans) -- the working voice; headings answer in Fraunces (serif), same\n"
            "   pairing as every other Try-Works surface. A touch larger (relative em, so the font-size\n"
            "   slider still works), at the per-mode reading weight (halation-compensated in dark), with\n"
            "   the reading OpenType features already used on the web surface (old-style, proportional\n"
            "   figures; common ligatures). text-wrap: pretty improves rag and kills orphans; headings keep\n"
            "   balance below. font-weight lands on the container, so bold/headings still win by cascade. */\n"
            ".markdown-preview-view, .markdown-source-view.mod-cm6 .cm-content {\n"
            "  font-size: calc(1em * var(--tw-body-scale, 1.2));\n"
            "  font-weight: var(--tw-body-weight, 400);\n"
            "  text-wrap: pretty;\n"
            "  font-variant-numeric: oldstyle-nums proportional-nums; font-variant-ligatures: common-ligatures;\n}\n"
            "/* Headings set in Fraunces (serif), matching every other Try-Works surface; body text and UI\n"
            "   chrome stay Archivo (sans) so the two read as distinct voices. Weights stay from Obsidian's\n"
            "   --h*-weight. The note title itself is --inline-title-font above, not this selector. */\n"
            ".markdown-rendered :is(h1, h2, h3, h4, h5, h6),\n"
            ".markdown-source-view.mod-cm6 :is(.HyperMD-header, .cm-header) {\n"
            "  font-family: var(--tw-font-serif); font-variation-settings: normal; letter-spacing: -0.01em; text-wrap: balance;\n"
            "  font-variant-ligatures: common-ligatures discretionary-ligatures;\n}\n"
            "/* Breathing room after headings (reading view): 1.4x the paragraph rhythm, in the heading's\n"
            "   own em so larger headings carry proportionally more air. Core keeps 2.5x above (via\n"
            "   --heading-spacing), so the hierarchy still reads top-heavy, as it should. Live preview's\n"
            "   equivalent is --p-spacing-empty in the body block above. Headings inside list items are\n"
            "   untouched -- core's `li h*` margin-zero rule is more specific. */\n"
            ".markdown-rendered :is(h1, h2, h3, h4, h5, h6) { margin-block-end: calc(var(--p-spacing) * 1.4); }\n"
            "/* Blockquotes read as a quoted voice, distinct from body: serif, like headings, over the sea\n"
            "   tint (--blockquote-background-color, per mode above) and the accent border. */\n"
            ".markdown-rendered blockquote, .cm-s-obsidian .HyperMD-quote {\n"
            "  border-radius: 0 4px 4px 0; font-family: var(--tw-font-serif);\n}\n"
            "/* Explicit belt-and-suspenders: emphasis/italic text should read as sans body text like\n"
            "   everything else around it, not switch typeface. Written directly (not relying on\n"
            "   --font-text-theme alone) in case Obsidian has its own internal default for em/i independent\n"
            "   of the theme's text-font hook. Blockquotes are the one deliberate exception (serif, above),\n"
            "   so they're excluded here. */\n"
            ".markdown-rendered em:not(blockquote *), .markdown-rendered i:not(blockquote *),\n"
            ".cm-s-obsidian .cm-em {\n"
            "  font-family: var(--tw-font-sans);\n}\n"
            '.markdown-rendered pre code, .cm-s-obsidian { font-feature-settings: "liga" 1, "calt" 1; }\n'
            "/* Properties panel in mono, for the key: value read. Obsidian's CSS-variable API has no documented\n"
            "   font-family hook for Properties (only sizes/colours), so this targets the panel's actual DOM classes\n"
            "   directly -- best-effort/unofficial, inert if a future Obsidian version renames them; verify visually. */\n"
            ".metadata-property-key, .metadata-property-value { font-family: var(--tw-font-mono); }\n"
            "/* Footnotes panel: one background, the note's own. Root cause of the old two-tone seam,\n"
            "   found by reading app.css 1.12 directly: each footnote's content renders as a\n"
            "   .markdown-embed, whose background reads --embed-background -- the lifted surface tone set\n"
            "   above for real embeds -- while the row around it reads --footnote-input-background (the\n"
            "   note bg, set above). Row and content disagreeing is exactly the seam. The embed is\n"
            "   detinted here only inside the panel; hover-popover footnote previews keep the embed look.\n"
            "   The !important catch-all survives from earlier selector fights as a backstop against\n"
            "   internal rules this app.css no longer has -- redundant today, harmless, and it also keeps\n"
            "   the .is-editing row flat (the focus ring, not a background swap, signals editing). */\n"
            ".footnotes-view .markdown-embed { background-color: transparent; }\n"
            ".footnote, .footnote-list-item, .footnote-list {\n"
            "  background: var(--background-primary) !important;\n}\n"
            "/* Footnotes stay in the sans voice, upright: they're apparatus, not reading text. Clipped\n"
            "   sources love arriving as wall-to-wall italics, so emphasis inside a footnote flattens to\n"
            "   upright rather than rendering italic. Covers the footnotes panel, the reading-view footnote\n"
            "   section, and live preview's footnote definition lines. */\n"
            ".footnotes-view .footnote-content, .markdown-rendered .footnotes,\n"
            ".cm-s-obsidian .cm-line.HyperMD-footnote {\n"
            "  font-family: var(--tw-font-sans); font-style: normal;\n}\n"
            ".footnotes-view .footnote-content :is(em, i), .markdown-rendered .footnotes :is(em, i),\n"
            ".cm-s-obsidian .cm-line.HyperMD-footnote .cm-em {\n"
            "  font-style: normal;\n}\n\n"
            + code_style + "\n\n" + extra + "\n" + nav_icons + "\n" + _task_rules() + "\n" + _FEATURES_CSS + "\n"
            "/* File explorer: slightly smaller labels that wrap to a second/third line instead of truncating. */\n"
            '.workspace-leaf-content[data-type="file-explorer"] .tree-item-self { height: auto; }\n'
            '.workspace-leaf-content[data-type="file-explorer"] .tree-item-inner {\n'
            "  font-size: 0.88em; line-height: 1.25; white-space: normal; overflow: visible; text-overflow: clip; word-break: break-word;\n}\n\n"
            "/* Style Settings escape hatches: class present reverts that one piece (to Obsidian stock, or\n"
            "   to the other Try-Works voice). Font stack literal in tw-body-serif for the same reason the\n"
            "   three theme font hooks above are literal. */\n"
            "body.tw-headings-sans { --inline-title-font: var(--tw-font-sans); }\n"
            "body.tw-headings-sans .markdown-rendered :is(h1, h2, h3, h4, h5, h6),\n"
            "body.tw-headings-sans .markdown-source-view.mod-cm6 :is(.HyperMD-header, .cm-header) {\n"
            "  font-family: var(--tw-font-sans); letter-spacing: -0.015em;\n"
            "  font-variant-ligatures: common-ligatures;\n}\n"
            'body.tw-body-serif { --font-text-theme: "Fraunces", Georgia, serif; }\n'
            "body.tw-body-serif .markdown-preview-view, body.tw-body-serif .markdown-source-view.mod-cm6 .cm-content {\n"
            "  font-optical-sizing: auto;\n}\n"
            'body.tw-explorer-truncate .workspace-leaf-content[data-type="file-explorer"] .tree-item-inner {\n'
            "  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;\n}\n")
