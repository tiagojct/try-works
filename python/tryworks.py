"""Generated from try-works.json - do not edit by hand.
Try-Works matplotlib colours, colormaps, and style helper."""
import os
import matplotlib as mpl
import matplotlib.pyplot as plt
from cycler import cycler
from matplotlib.colors import LinearSegmentedColormap

TRYWORKS_CATEGORICAL = ["#E69F00", "#0072B2", "#009E73", "#CC79A7", "#D55E00", "#56B4E9", "#F0E442"]
TRYWORKS_SEQUENTIAL  = ["#e4f5fb", "#b3e0ee", "#7ec4d7", "#48a0b7", "#0a7b93", "#00576c", "#003542"]
TRYWORKS_DIVERGING   = ["#00576e", "#287d93", "#72a9b4", "#bbd7d9", "#f1eee6", "#e7ccae", "#da9b6a", "#c26d32", "#984a1a"]
TRYWORKS_MARKERS     = ["o", "s", "^", "D", "v", "P", "X"]

tryworks_seq = LinearSegmentedColormap.from_list("tryworks_seq", TRYWORKS_SEQUENTIAL)
tryworks_div = LinearSegmentedColormap.from_list("tryworks_div", TRYWORKS_DIVERGING)
for _cm in (tryworks_seq, tryworks_div):
    try:
        mpl.colormaps.register(_cm)
    except (ValueError, AttributeError):
        pass

_LIGHT = dict(bg="#ffffff", panel="#ffffff", text="#18272b", grid="#dce5e1", muted="#52646a")
_DARK  = dict(bg="#12161b", panel="#12161b", text="#f1efe9", grid="#2c3640", muted="#97a0a4")

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
