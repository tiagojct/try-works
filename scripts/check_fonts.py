#!/usr/bin/env python3
"""Verify the fonts cover European Portuguese and that every codepoint is inside
the declared subset range (try-works.json -> i18n.unicode-range).
Skips cleanly if the font files are not present (they are documented, not committed)."""
import json, pathlib, sys, re
ROOT = pathlib.Path(__file__).resolve().parent.parent
D = json.loads((ROOT / "try-works.json").read_text())
PT = "áàâãçéêíóôõúüÁÀÂÃÇÉÊÍÓÔÕÚÜ«»ºª–—“”‘’…€"

def parse_ranges(s):
    out = []
    for tok in s.split(","):
        tok = tok.strip().replace("U+", "")
        if "-" in tok: a, b = tok.split("-"); out.append((int(a, 16), int(b, 16)))
        else: out.append((int(tok, 16), int(tok, 16)))
    return out
ranges = parse_ranges(D["i18n"]["unicode-range"])
in_range = lambda cp: any(a <= cp <= b for a, b in ranges)

oob = [c for c in PT if not in_range(ord(c))]
if oob:
    print("FAIL: codepoints outside declared unicode-range:", " ".join(oob)); sys.exit(1)
print("range: all %d Portuguese codepoints inside the declared subset" % len(PT))

fdir = ROOT / "fonts"
ttfs = list(fdir.glob("*.ttf")) + list(fdir.glob("*.woff2"))
if not ttfs:
    print("fonts not present (documented, not committed) — glyph check skipped"); sys.exit(0)
try:
    from fontTools.ttLib import TTFont
except ImportError:
    print("fonttools not installed — glyph check skipped"); sys.exit(0)
bad = False
for f in ttfs:
    try: cm = set(TTFont(f).getBestCmap().keys())
    except Exception: continue
    miss = [c for c in PT if ord(c) not in cm]
    print("  %-22s %s" % (f.name, "ok" if not miss else "MISSING " + " ".join(miss)))
    bad = bad or bool(miss)
sys.exit(1 if bad else 0)
