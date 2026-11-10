"""Fig. 5: gating rather than conditioning drives the gains.

Inputs: analysis/outputs/ablations_gate_vs_variants.csv (paired differences on all analysed X->EN test instances),
Results/pilot/tables/T8_ablations.csv (balanced accuracy per variant), Results/pilot/tables/lab/lab_real_qwen3-8b.csv
(decision-layer analysis), analysis/outputs/knowing_vs_using_ci.csv (reproduces T7 with bootstrap CIs) and
analysis/outputs/knowing_vs_using_both_ci.csv (adds the reverse disagreement, uses-not-know; revision of 24 Oct 2026).
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "common"))
from mplstyle import *  # noqa: E402,F401,F403
import numpy as np  # noqa: E402

abl = pd.read_csv(ANALYSIS / "ablations_gate_vs_variants.csv")
t8 = pd.read_csv(RESULTS / "tables" / "T8_ablations.csv").set_index("system")
lab = pd.read_csv(RESULTS / "tables" / "lab" / "lab_real_qwen3-8b.csv").set_index("variant")
ku = pd.read_csv(ANALYSIS / "knowing_vs_using_ci.csv").set_index("condition")
ku2 = pd.read_csv(ANALYSIS / "knowing_vs_using_both_ci.csv").set_index("condition")
ku = ku.join(ku2[["use_not_know", "unk_lo", "unk_hi"]])

fig = plt.figure(figsize=(180 * MM, 58 * MM))
B, T = 0.20, 0.86


def fx(mm):
    return mm / 180.0


# ---------------- panel a: translation-level comparison with other uses of the ledger
var = [("ccl", "Full conditioning"), ("ccl_no_repair", "Full conditioning, no repair"),
       ("ccl_posthoc", "Full conditioning, post hoc"), ("ccl_gate_posthoc", "Gate applied post hoc")]
ya = np.arange(len(var))[::-1]
ax = fig.add_axes([fx(33), B, fx(25), T - B])
for y, (k, lab_) in zip(ya, var):
    r = abl[abl.comparison == f"ccl_gate - {k}"].iloc[0]
    ax.plot([100 * r.ci_low, 100 * r.ci_high], [y, y], color=BLUE, lw=0.9, solid_capstyle="butt")
    ax.plot(100 * r["diff"], y, "o", ms=3.4, color=BLUE)
    ax.text(10.9, y, f"{t8.loc[k, 'BAL']:.3f}", fontsize=5.8, va="center", ha="left", color=GREY)
ax.text(10.9, len(var) - 0.35, "BAL", fontsize=5.8, va="center", ha="left", color=GREY, fontweight="bold")
ax.text(0.2, len(var) - 0.35, f"CCL-Gate BAL {t8.loc['ccl_gate', 'BAL']:.3f}", fontsize=5.6, color=BLUE, va="center")
ax.axvline(0, color=INK, lw=0.5)
ax.set_xlim(0, 10); ax.set_xticks([0, 5, 10]); ax.set_ylim(-0.6, len(var) - 0.1)
ax.set_yticks(ya); ax.set_yticklabels([l for _, l in var]); ax.tick_params(axis="y", length=0)
ax.set_xlabel("CCL-Gate minus variant\n(percentage points)", linespacing=1.0)
ax.grid(axis="x", color="#E3E6EA", lw=0.4)
ax.spines["left"].set_visible(False)

# ---------------- panel b: decision-layer components
comp = [("no_defer", "No deferral"), ("unknown_renormalised", "Unresolved mass renormalized"),
        ("tau_fixed@0.8", "Fixed threshold (0.8)"), ("no_name_prior", "No name prior"),
        ("fit_default_weights", "Expert weights, no fitting"), ("argmax_referent", "Most probable referent only"),
        ("saturating_counts", "Saturating cue counts")]
yb = np.arange(len(comp))[::-1]
axb = fig.add_axes([fx(101), B, fx(26), T - B])
XMIN = -6.0
for y, (k, lab_) in zip(yb, comp):
    r = lab.loc[k]
    v, l, h = 100 * r.dBAL, 100 * r.dBAL_lo, 100 * r.dBAL_hi
    if v < XMIN:
        axb.barh(y, XMIN - 0.2, height=0.6, color=VERM, lw=0)
        axb.text(XMIN + 0.15, y, f"{v:.1f}".replace("-", "\u2212"), fontsize=5.8, va="center", ha="left", color="white", fontweight="bold")
        axb.plot([XMIN - 0.05, XMIN + 0.1], [y + 0.36, y - 0.36], color="white", lw=1.4)
    else:
        axb.barh(y, v, height=0.6, color=VERM if h < 0 else LIGHT, lw=0)
        axb.plot([l, h], [y, y], color=INK, lw=0.6)
axb.axvline(0, color=INK, lw=0.5)
axb.set_xlim(XMIN - 0.2, 1.0); axb.set_xticks([-6, -4, -2, 0])
axb.set_ylim(-0.6, len(comp) - 0.4)
axb.set_yticks(yb); axb.set_yticklabels([l for _, l in comp]); axb.tick_params(axis="y", length=0)
axb.set_xlabel("Change in decision-level\nBAL (percentage points)", linespacing=1.0)
axb.grid(axis="x", color="#E3E6EA", lw=0.4)
axb.spines["left"].set_visible(False)

# ---------------- panel c: knowing versus using
conds = [("adjacent", "Adjacent"), ("distant_8", "Distant"), ("memory", "Memory"), ("isolated", "Isolated")]
axc = fig.add_axes([fx(141), B, fx(37), T - B])
x = np.arange(len(conds))
w = 0.205
series = [("probe", "probe_lo", "probe_hi", "#5F6670", "Asked directly (probe)", None),
          ("translate", "translate_lo", "translate_hi", "#AEB5BD", "In translation", None),
          ("know_not_use", "knu_lo", "knu_hi", VERM, "Probe right, translation wrong", None),
          ("use_not_know", "unk_lo", "unk_hi", "white", "Translation right, probe wrong", VERM)]
for j, (c, lo, hi, colr, lab_, edge) in enumerate(series):
    vals = np.array([100 * ku.loc[k, c] for k, _ in conds])
    los = np.array([100 * ku.loc[k, lo] for k, _ in conds]); his = np.array([100 * ku.loc[k, hi] for k, _ in conds])
    xx = x + (j - 1.5) * w
    axc.bar(xx, vals, width=w * 0.9, color=colr, lw=0.6 if edge else 0, edgecolor=edge if edge else colr, label=lab_)
    axc.errorbar(xx, vals, yerr=[vals - los, his - vals], fmt="none", ecolor=INK, elinewidth=0.5)
axc.set_xticks(x); axc.set_xticklabels([l for _, l in conds])
axc.set_ylim(0, 80); axc.set_yticks([0, 20, 40, 60, 80]); axc.set_ylabel("Instances (%)")
axc.grid(axis="y", color="#E3E6EA", lw=0.4)
axc.legend(loc="upper right", fontsize=5.3, ncol=1, bbox_to_anchor=(1.02, 1.08), handlelength=1.0)
axc.tick_params(axis="x", length=0)

panel(fig, "a", 0.002, 0.985)
panel(fig, "b", fx(62), 0.985)
panel(fig, "c", fx(131), 0.985)

root = HERE.parent.parent
save(fig, "fig5_mechanism", root / "overleaf" / "figures", HERE)
src_a = abl.merge(t8[["BAL", "ACC", "UCR"]].reset_index().assign(comparison=lambda d: "ccl_gate - " + d.system), on="comparison", how="left")
source_data(HERE / "fig5_source_data.xlsx", {"a_ledger_uses": src_a, "b_decision_layer": lab.reset_index(),
                                            "c_knowing_using": ku.reset_index()})
print("Fig. 5 written")
