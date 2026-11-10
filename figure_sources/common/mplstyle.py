"""Shared matplotlib style for the data figures (Nature Machine Intelligence layout).

Figures are drawn at final print size (180 mm full width), with Arial-metric sans-serif text at 5-7 pt, lowercase bold
panel letters at 8 pt, vector output with embedded TrueType fonts, and editable text in the SVG masters.
"""
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
ANALYSIS = ROOT / "analysis" / "outputs"
# Folder of the reported run (Results/pilot); set the CCL_RESULTS environment variable to point elsewhere.
RESULTS = Path(os.environ.get("CCL_RESULTS", str(ROOT / "Results" / "pilot")))
MM = 1 / 25.4

for f in ["LiberationSans-Regular.ttf", "LiberationSans-Bold.ttf", "LiberationSans-Italic.ttf", "LiberationSans-BoldItalic.ttf"]:
    if Path(f"/usr/share/fonts/truetype/liberation/{f}").exists():      # Arial is used where Liberation Sans is absent
        font_manager.fontManager.addfont(f"/usr/share/fonts/truetype/liberation/{f}")
_names = {fe.name for fe in font_manager.fontManager.ttflist}
MATHFONT = "Liberation Sans" if "Liberation Sans" in _names else "Arial"

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Liberation Sans", "Helvetica", "DejaVu Sans"],
    "font.size": 6.5, "axes.labelsize": 6.5, "axes.titlesize": 6.5, "xtick.labelsize": 6, "ytick.labelsize": 6,
    "legend.fontsize": 6, "axes.linewidth": 0.5, "xtick.major.width": 0.5, "ytick.major.width": 0.5,
    "xtick.major.size": 2.0, "ytick.major.size": 2.0, "xtick.major.pad": 1.5, "ytick.major.pad": 1.5,
    "axes.labelpad": 2.0, "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": "#3A3F45",
    "xtick.color": "#3A3F45", "ytick.color": "#3A3F45", "axes.labelcolor": "#1F2328", "text.color": "#1F2328",
    "legend.frameon": False, "legend.handlelength": 1.2, "legend.handletextpad": 0.4, "legend.borderaxespad": 0.2,
    "pdf.fonttype": 42, "svg.fonttype": "none", "savefig.dpi": 300, "lines.linewidth": 0.8,
    "errorbar.capsize": 0, "axes.axisbelow": True,
    "mathtext.fontset": "custom", "mathtext.rm": MATHFONT, "mathtext.it": f"{MATHFONT}:italic",
    "mathtext.bf": f"{MATHFONT}:bold", "mathtext.sf": MATHFONT,
})

INK, GREY, LIGHT, PALE = "#1F2328", "#6B7178", "#C9CED4", "#F1F3F5"
BLUE, SKY, SLATE, VERM = "#0072B2", "#56B4E9", "#355C7D", "#D55E00"
SYSTEMS = [  # key, label, colour, marker
    ("llm_plain", "Plain prompting", "#5F6670", "o"),
    ("llm_cautious", "Cautious prompting", "#E69F00", "s"),
    ("llm_cot_gender", "Chain-of-thought", "#009E73", "D"),
    ("infer_then_tag", "Infer-then-tag", "#CC79A7", "^"),
    ("ccl", "CCL (full conditioning)", SKY, "v"),
    ("ccl_gate", "CCL-Gate", BLUE, "o"),
    ("oracle_goe", "Gold-label reference", "#000000", "o"),
]
LABEL = {k: l for k, l, _, _ in SYSTEMS}
COLOR = {k: c for k, _, c, _ in SYSTEMS}
MARKER = {k: m for k, _, _, m in SYSTEMS}
BASELINES = ["llm_plain", "llm_cautious", "llm_cot_gender", "infer_then_tag"]
LANG = {"as": "Assamese", "az": "Azerbaijani", "bho": "Bhojpuri", "bn": "Bengali", "es": "Spanish", "et": "Estonian",
        "fa": "Persian", "fi": "Finnish", "id": "Indonesian", "lg": "Luganda", "ln": "Lingala", "mai": "Maithili",
        "om": "Oromo", "tr": "Turkish", "ar": "Arabic", "de": "German", "hi": "Hindi"}


def panel(ax_or_fig, letter, x, y, transform=None):
    """Bold lowercase panel letter at figure coordinates (x, y)."""
    fig = ax_or_fig if isinstance(ax_or_fig, plt.Figure) else ax_or_fig.figure
    fig.text(x, y, letter, fontsize=8, fontweight="bold", va="top", ha="left")


def system_marker(ax, x, y, key, size=3.2, zorder=3, **kw):
    hollow = key == "oracle_goe"
    ax.plot(x, y, MARKER[key], ms=size, mfc="white" if hollow else COLOR[key], mec=COLOR[key], mew=0.6 if hollow else 0.3,
            zorder=zorder, **kw)


def save(fig, name, pdf_dir, src_dir):
    pdf_dir, src_dir = Path(pdf_dir), Path(src_dir)
    pdf_dir.mkdir(parents=True, exist_ok=True); src_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(pdf_dir / f"{name}.pdf")
    fig.savefig(src_dir / f"{name}.svg")
    fig.savefig(src_dir / f"{name}.png", dpi=300)


def source_data(path, sheets):
    """sheets: dict sheet_name -> DataFrame."""
    with pd.ExcelWriter(path) as xw:
        for nm, df in sheets.items():
            df.to_excel(xw, sheet_name=nm[:31], index=False)
