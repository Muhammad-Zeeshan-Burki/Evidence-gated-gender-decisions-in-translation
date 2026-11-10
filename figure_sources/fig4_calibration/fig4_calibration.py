"""Fig. 4: calibrated and selective commitment.

Inputs: analysis/outputs/risk_coverage_points.csv (system operating points and the CCL threshold sweep on all
analysed X->EN test instances; the sweep reproduces T11b), analysis/outputs/reliability_bins.csv (reproduces T11:
ECE 0.0656, Brier 0.2064, n 1,531) and analysis/outputs/gender_gap_ci.csv (reproduces T6 with bootstrap CIs).
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "common"))
from mplstyle import *  # noqa: E402,F401,F403
import numpy as np  # noqa: E402

rc = pd.read_csv(ANALYSIS / "risk_coverage_points.csv")
rel = pd.read_csv(ANALYSIS / "reliability_bins.csv")
gap = pd.read_csv(ANALYSIS / "gender_gap_ci.csv").set_index("system")
cal = json.loads((ANALYSIS / "paper_stats.json").read_text())["calibration"]

fig = plt.figure(figsize=(180 * MM, 60 * MM))
B, T = 0.17, 0.90


def fx(mm):
    return mm / 180.0


# ---------------- panel a: risk-coverage
ax = fig.add_axes([fx(11), B, fx(47), T - B])
sw = rc[rc.system.str.startswith("ccl_tau_")].copy()
sw["tau"] = sw.system.str.replace("ccl_tau_", "").astype(float)
sw = sw.sort_values("coverage")
ax.plot(sw.coverage * 100, sw.risk * 100, "-", color=SKY, lw=0.9, zorder=2)
ax.plot(sw.coverage * 100, sw.risk * 100, "o", ms=2.2, color=SKY, zorder=3)
tau_off = {0.5: (1.0, 2.4, "left"), 0.6: (-1.2, 3.0, "right"), 0.7: (1.0, -3.4, "left"), 0.8: (0.0, -3.4, "center"),
           0.999: (1.0, 2.4, "left")}
for _, r in sw.iterrows():
    t = "0.999" if r.tau > 0.99 else f"{r.tau:.1f}"
    dx, dy, ha = tau_off[round(r.tau, 3)]
    ax.text(r.coverage * 100 + dx, r.risk * 100 + dy, f"\u03c4 = {t}", fontsize=5.3, color="#3E8CBF", va="center", ha=ha)
handles = []
for k in ["llm_plain", "llm_cautious", "llm_cot_gender", "infer_then_tag", "ccl_gate", "oracle_goe"]:
    r = rc[rc.system == k].iloc[0]
    system_marker(ax, r.coverage * 100, r.risk * 100, k, size=4.0 if k == "ccl_gate" else 3.4, zorder=4)
    hollow = k == "oracle_goe"
    handles.append(plt.Line2D([], [], ls="", marker=MARKER[k], ms=3.2, mfc="white" if hollow else COLOR[k], mec=COLOR[k],
                              mew=0.6 if hollow else 0.3, label={"oracle_goe": "Gold-label reference"}.get(k, LABEL[k])))
r = rc[rc.system == "ccl_gate"].iloc[0]
ax.text(r.coverage * 100 + 2.2, r.risk * 100 - 2.6, "CCL-Gate", fontsize=5.8, color=BLUE, fontweight="bold", va="center")
ax.legend(handles=handles, loc="lower left", ncol=2, fontsize=5.5, columnspacing=0.8, handletextpad=0.2,
          borderaxespad=0.3, bbox_to_anchor=(0.0, 0.0))
ax.text(sw.coverage.min() * 100 - 1.0, 44.5, "CCL threshold sweep", fontsize=5.6, color="#3E8CBF")
ax.set_xlim(0, 100); ax.set_ylim(0, 55)
ax.set_xlabel("Coverage (%)"); ax.set_ylabel("Risk (%)")
ax.grid(color="#E3E6EA", lw=0.4)

# ---------------- panel b: reliability
axr = fig.add_axes([fx(72), B + 0.20, fx(38), T - B - 0.20])
axh = fig.add_axes([fx(72), B, fx(38), 0.15], sharex=axr)
axr.plot([0, 1], [0, 1], "--", color=GREY, lw=0.6)
axr.errorbar(rel.mean_pred, rel.frac_female, yerr=[rel.frac_female - rel.ci_lo, rel.ci_hi - rel.frac_female], fmt="o", ms=2.6,
             color=SKY, mfc=SKY, mec=SKY, elinewidth=0.7, capsize=0)
axr.plot(rel.mean_pred, rel.frac_female, "-", color=SKY, lw=0.7)
axr.set_xlim(0, 1); axr.set_ylim(0, 1)
axr.set_ylabel("Observed share female")
axr.tick_params(labelbottom=False)
axr.text(0.04, 0.93, f"ECE = {cal['ECE']:.3f}\nBrier = {cal['Brier']:.3f}\nn = {cal['n']:,}", fontsize=5.6, va="top", linespacing=1.15)
axr.grid(color="#E3E6EA", lw=0.4)
centres = (rel.bin_lo + rel.bin_hi) / 2
axh.bar(centres, rel.n, width=0.085, color=LIGHT, lw=0)
axh.set_ylabel("n", rotation=0, labelpad=6, va="center")
axh.set_yticks([0, 600]); axh.set_ylim(0, 700)
axh.set_xlabel("Slot posterior $P_k$(F)")
axh.set_xticks([0, 0.25, 0.5, 0.75, 1.0])

# ---------------- panel c: gender gap
order = ["llm_plain", "llm_cautious", "llm_cot_gender", "infer_then_tag", "ccl", "ccl_gate", "oracle_goe"]
ys = np.arange(len(order))[::-1]
axg = fig.add_axes([fx(145), B, fx(33), T - B])
axg.axhspan(ys[order.index("ccl_gate")] - 0.42, ys[order.index("ccl_gate")] + 0.42, color="#E7F1F9", lw=0, zorder=0)
axg.axvline(0, color=INK, lw=0.5)
for y, k in zip(ys, order):
    v, l, h = 100 * gap.loc[k, "gap_M_minus_F"], 100 * gap.loc[k, "gap_lo"], 100 * gap.loc[k, "gap_hi"]
    axg.plot([l, h], [y, y], color=COLOR[k], lw=0.9, solid_capstyle="butt")
    system_marker(axg, v, y, k, size=3.4)
axg.set_yticks(ys); axg.set_yticklabels([LABEL[k] for k in order]); axg.tick_params(axis="y", length=0)
for t, k in zip(axg.get_yticklabels(), order):
    if k == "ccl_gate":
        t.set_color(BLUE); t.set_fontweight("bold")
axg.set_xlim(-45, 55); axg.set_xticks([-40, -20, 0, 20, 40])
axg.set_ylim(-0.6, len(order) - 0.4)
axg.set_xlabel("Male minus female accuracy\n(percentage points)", linespacing=1.0)
axg.grid(axis="x", color="#E3E6EA", lw=0.4)

panel(fig, "a", 0.002, 0.985)
panel(fig, "b", fx(62), 0.985)
panel(fig, "c", fx(116), 0.985)

root = HERE.parent.parent
save(fig, "fig4_calibration", root / "overleaf" / "figures", HERE)
source_data(HERE / "fig4_source_data.xlsx", {"a_risk_coverage": rc, "b_reliability": rel.assign(ECE=cal["ECE"], Brier=cal["Brier"]),
                                            "c_gender_gap": gap.loc[order].reset_index()})
print("Fig. 4 written")
