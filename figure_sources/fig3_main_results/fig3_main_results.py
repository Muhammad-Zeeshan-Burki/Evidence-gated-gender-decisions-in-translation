"""Fig. 3: held-out main results.

Inputs: analysis/outputs/heldout_headline_ci.csv (UCR with item-cluster bootstrap CIs), Results/pilot/tables/
T1b_wrong_gender_heldout.csv (wrong-gender rate with CIs and outcome shares) and analysis/outputs/
heldout_paired_exact_p.csv (paired differences by condition, identical to T2e).
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "common"))
from mplstyle import *  # noqa: E402,F401,F403
import numpy as np  # noqa: E402

head = pd.read_csv(ANALYSIS / "heldout_headline_ci.csv").set_index("system")
wg = pd.read_csv(RESULTS / "tables" / "T1b_wrong_gender_heldout.csv").set_index("system")
pr = pd.read_csv(ANALYSIS / "heldout_paired_exact_p.csv")

order = ["llm_plain", "llm_cautious", "llm_cot_gender", "infer_then_tag", "ccl", "ccl_gate", "oracle_goe"]
ys = np.arange(len(order))[::-1]
fig = plt.figure(figsize=(180 * MM, 64 * MM))
B, T = 0.17, 0.84                      # bottom / top of plotting area (figure fraction)


def fx(mm):
    return mm / 180.0


def band(ax, y):
    ax.axhspan(y - 0.42, y + 0.42, color="#E7F1F9", zorder=0, lw=0)


# ---------------- panel a: UCR and WGR
ax1 = fig.add_axes([fx(25), B, fx(25), T - B])
ax2 = fig.add_axes([fx(54), B, fx(17), T - B])
for ax, col, lo, hi, xmax, title in [(ax1, "UCR", "UCR_lo", "UCR_hi", 100, "Unwarranted\ncommitment (%)"),
                                     (ax2, "wrong_gender", "wrong_gender_lo", "wrong_gender_hi", 35, "Wrong\ngender (%)")]:
    src = head if col == "UCR" else wg
    band(ax, ys[order.index("ccl_gate")])
    for y, k in zip(ys, order):
        v, l, h = 100 * src.loc[k, col], 100 * src.loc[k, lo], 100 * src.loc[k, hi]
        ax.plot([l, h], [y, y], color=COLOR[k], lw=0.9, solid_capstyle="butt", zorder=2)
        system_marker(ax, v, y, k, size=3.6)
    ax.set_xlim(0, xmax); ax.set_ylim(-0.6, len(order) - 0.4)
    ax.set_xlabel(title, linespacing=1.0)
    ax.grid(axis="x", color="#E3E6EA", lw=0.4)
    ax.set_yticks(ys)
    ax.set_yticklabels([LABEL[k] for k in order] if ax is ax1 else [])
    if ax is ax1:
        for t, k in zip(ax.get_yticklabels(), order):
            if k == "ccl_gate":
                t.set_color(BLUE); t.set_fontweight("bold")
    ax.tick_params(axis="y", length=0)
ax1.set_xticks([0, 25, 50, 75, 100]); ax2.set_xticks([0, 10, 20, 30])

# ---------------- panel b: outcomes on determinable instances
ax3 = fig.add_axes([fx(76), B, fx(27), T - B])
band(ax3, ys[order.index("ccl_gate")])
for y, k in zip(ys, order):
    c, n, w = 100 * wg.loc[k, "correct"], 100 * wg.loc[k, "neutral"], 100 * wg.loc[k, "wrong_gender"]
    ax3.barh(y, c, height=0.62, color=SLATE, lw=0)
    ax3.barh(y, n, left=c, height=0.62, color=LIGHT, lw=0)
    ax3.barh(y, w, left=c + n, height=0.62, color=VERM, lw=0)
ax3.set_xlim(0, 100); ax3.set_ylim(-0.6, len(order) - 0.4)
ax3.set_yticks(ys); ax3.set_yticklabels([]); ax3.tick_params(axis="y", length=0)
ax3.set_xticks([0, 50, 100]); ax3.set_xlabel("Determinable\ninstances (%)", linespacing=1.0)
for i, (lab, colr) in enumerate([("correct", SLATE), ("neutral", LIGHT), ("wrong", VERM)]):
    xx = fx(76) + i * fx(9.6)
    fig.patches.append(plt.Rectangle((xx, 0.905), fx(1.9), 0.035, transform=fig.transFigure, color=colr, lw=0))
    fig.text(xx + fx(2.5), 0.922, lab, fontsize=5.8, va="center")

# ---------------- panel c: paired differences by condition (broken axis)
conds = [("all_conditions", "All conditions"), ("adjacent", "Adjacent"), ("memory", "Memory"), ("distant_8", "Distant"),
         ("isolated", "Isolated")]
yc = np.arange(len(conds))[::-1]
offs = dict(zip(BASELINES, [0.27, 0.09, -0.09, -0.27]))
axl = fig.add_axes([fx(130), B, fx(30), T - B])
axr = fig.add_axes([fx(163), B, fx(15.5), T - B], sharey=axl)
for ax in (axl, axr):
    for (key, _), y in zip(conds, yc):
        for b in BASELINES:
            r = pr[(pr.subset == key) & (pr.comparison == f"ccl_gate - {b}")].iloc[0]
            v, l, h = 100 * r["diff"], 100 * r.ci_low, 100 * r.ci_high
            ax.plot([l, h], [y + offs[b]] * 2, color=COLOR[b], lw=0.8, solid_capstyle="butt")
            ax.plot(v, y + offs[b], MARKER[b], ms=2.8, color=COLOR[b], mec=COLOR[b], mew=0.3)
    ax.grid(axis="x", color="#E3E6EA", lw=0.4)
    for yy in yc[:-1]:
        ax.axhline(yy - 0.5, color="#E3E6EA", lw=0.4)
axl.axvline(0, color=INK, lw=0.5)
axl.set_xlim(-34, 14); axr.set_xlim(64, 88)
axl.set_xticks([-30, -20, -10, 0, 10]); axr.set_xticks([70, 80])
axl.set_ylim(-0.6, len(conds) - 0.4)
n_of = {k: int(pr[(pr.subset == k)].n.iloc[0]) for k, _ in conds}
axl.set_yticks(yc); axl.set_yticklabels([f"{lab} ({n_of[k]:,})" for k, lab in conds]); axl.tick_params(axis="y", length=0)
axr.tick_params(axis="y", length=0, labelleft=False)
axr.spines["left"].set_visible(False)
d = 0.012
for x0 in (fx(160), fx(163)):
    fig.add_artist(plt.Line2D([x0 - d / 2, x0 + d / 2], [B - 0.02, B + 0.02], transform=fig.transFigure, color=INK, lw=0.5))
fig.text(fx(147), 0.055, "CCL-Gate minus baseline (percentage points)", ha="center", fontsize=6.5)
for i, b in enumerate(BASELINES):
    xx = fx(133) + (i % 2) * fx(21.0)
    yy = 0.945 if i < 2 else 0.885
    fig.add_artist(plt.Line2D([xx], [yy], marker=MARKER[b], ms=2.8, color=COLOR[b], mec=COLOR[b], transform=fig.transFigure))
    fig.text(xx + fx(1.6), yy, "vs " + LABEL[b].replace(" prompting", "").lower().replace("infer", "infer"), fontsize=5.8, va="center")

panel(fig, "a", 0.002, 0.985)
panel(fig, "b", fx(73.5), 0.985)
panel(fig, "c", fx(103.5), 0.985)

root = HERE.parent.parent
save(fig, "fig3_main_results", root / "overleaf" / "figures", HERE)
src_a = head.loc[order, ["UCR", "UCR_lo", "UCR_hi"]].join(wg.loc[order, ["wrong_gender", "wrong_gender_lo", "wrong_gender_hi"]]).reset_index()
src_b = wg.loc[order, ["n", "correct", "neutral", "wrong_gender", "precision_of_gendered_output", "n_gendered"]].reset_index()
src_c = pr[pr.comparison.str.startswith("ccl_gate")][["comparison", "subset", "n", "diff", "ci_low", "ci_high", "b", "c", "p_exact", "p_holm_exact"]]
source_data(HERE / "fig3_source_data.xlsx", {"a_UCR_WGR": src_a, "b_outcomes": src_b, "c_paired": src_c})
print("Fig. 3 written")
