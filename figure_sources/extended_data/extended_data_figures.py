"""Extended Data Figs 1-5. Every plotted value is read from Results/pilot tables or analysis/outputs (see each block)."""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "common"))
from mplstyle import *  # noqa: E402,F401,F403
import numpy as np  # noqa: E402

ROOTP = HERE.parent.parent
PDF_DIR = ROOTP / "overleaf" / "extended_data"


def fx(mm, total=180.0):
    return mm / total


ORDER7 = ["llm_plain", "llm_cautious", "llm_cot_gender", "infer_then_tag", "ccl", "ccl_gate", "oracle_goe"]

# =====================================================================================================================
# Extended Data Fig. 1: per-language held-out comparisons (analysis/outputs/heldout_by_language_gate_vs_baselines.csv)
lang = pd.read_csv(ANALYSIS / "heldout_by_language_gate_vs_baselines.csv")
plain = lang[lang.comparison == "ccl_gate - llm_plain"].sort_values("diff")
langs = plain.subset.tolist()                       # ascending: bottom = smallest
fig = plt.figure(figsize=(180 * MM, 78 * MM))
B, T = 0.12, 0.90
y = np.arange(len(langs))
for j, b in enumerate(BASELINES):
    ax = fig.add_axes([fx(30 + j * 37.5), B, fx(34), T - B])
    g = lang[lang.comparison == f"ccl_gate - {b}"].set_index("subset").loc[langs]
    ax.axvline(0, color=INK, lw=0.5)
    for yy, (lg, r) in zip(y, g.iterrows()):
        sig = r.p_holm_lang < 0.05
        ax.plot([100 * r.ci_low, 100 * r.ci_high], [yy, yy], color=COLOR[b], lw=0.8, solid_capstyle="butt")
        ax.plot(100 * r["diff"], yy, MARKER[b], ms=3.0, mfc=COLOR[b] if sig else "white", mec=COLOR[b], mew=0.6)
    ax.set_xlim(-60, 38); ax.set_xticks([-50, -25, 0, 25])
    ax.set_ylim(-0.7, len(langs) - 0.3)
    ax.set_yticks(y)
    ax.set_yticklabels([f"{LANG[l]} ({int(g.loc[l, 'n_inst'])})" for l in langs] if j == 0 else [])
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="x", color="#E3E6EA", lw=0.4)
    ax.set_title("vs " + LABEL[b].replace(" prompting", "").lower(), fontsize=6.5, color=COLOR[b], pad=3)
fig.text(fx(30 + 2 * 37.5 - 2), 0.025, "CCL-Gate minus baseline, per-instance correctness (percentage points)", ha="center", fontsize=6.5)
save(fig, "edfig1_languages", PDF_DIR, HERE)
source_data(HERE / "edfig1_source_data.xlsx", {"per_language": lang})
plt.close(fig)

# =====================================================================================================================
# Extended Data Fig. 2: results by condition (Results/pilot/tables/T2_main_x2en_by_condition.csv)
t2 = pd.read_csv(RESULTS / "tables" / "T2_main_x2en_by_condition.csv")
fig = plt.figure(figsize=(180 * MM, 62 * MM))
B, T = 0.20, 0.86
axa = fig.add_axes([fx(12), B, fx(100), T - B])
axb = fig.add_axes([fx(126), B, fx(52), T - B])
off = np.linspace(-0.33, 0.33, len(ORDER7))
for gi, cond in enumerate(["adjacent", "distant_8", "memory"]):
    for k, o in zip(ORDER7, off):
        r = t2[(t2.system == k) & (t2.condition == cond)].iloc[0]
        axa.plot([gi + o, gi + o], [100 * r.ACC_lo, 100 * r.ACC_hi], color=COLOR[k], lw=0.8)
        system_marker(axa, gi + o, 100 * r.ACC, k, size=3.0)
for gi, cond in enumerate(["adjacent", "isolated"]):
    for k, o in zip(ORDER7, off):
        r = t2[(t2.system == k) & (t2.condition == cond)].iloc[0]
        axb.plot([gi + o, gi + o], [100 * r.UCR_lo, 100 * r.UCR_hi], color=COLOR[k], lw=0.8)
        system_marker(axb, gi + o, 100 * r.UCR, k, size=3.0)
axa.set_xticks([0, 1, 2]); axa.set_xticklabels(["Adjacent (685)", "Distant (292)", "Memory (525)"])
axb.set_xticks([0, 1]); axb.set_xticklabels(["Adjacent,\nreferent-ambiguous (240)", "Isolated,\nunrecoverable (152)"], linespacing=1.0)
axa.set_ylabel("Exact-gender accuracy (%)"); axb.set_ylabel("Unwarranted commitment (%)")
for ax in (axa, axb):
    ax.set_ylim(0, 102); ax.grid(axis="y", color="#E3E6EA", lw=0.4); ax.tick_params(axis="x", length=0)
    ax.set_yticks([0, 20, 40, 60, 80, 100])
axa.set_xlim(-0.55, 2.55); axb.set_xlim(-0.55, 1.55)
handles = [plt.Line2D([], [], ls="", marker=MARKER[k], ms=3.2, mfc="white" if k == "oracle_goe" else COLOR[k], mec=COLOR[k],
                      mew=0.6 if k == "oracle_goe" else 0.3, label=LABEL[k]) for k in ORDER7]
fig.legend(handles=handles, loc="upper center", ncol=7, fontsize=5.8, bbox_to_anchor=(0.5, 1.0), columnspacing=1.0)
panel(fig, "a", 0.002, 0.90); panel(fig, "b", fx(117), 0.90)
save(fig, "edfig2_conditions", PDF_DIR, HERE)
source_data(HERE / "edfig2_source_data.xlsx", {"by_condition": t2[t2.system.isin(ORDER7)]})
plt.close(fig)

# =====================================================================================================================
# Extended Data Fig. 3: calibration on development data and transfer (tau_selection, tau_gate_selection, T12)
ts = pd.read_csv(RESULTS / "tables" / "tau_selection__qwen3-8b.csv")
tg = pd.read_csv(RESULTS / "tables" / "tau_gate_selection__qwen3-8b.csv")
lolo = pd.read_csv(RESULTS / "tables" / "T12_lolo_transfer.csv")
fig = plt.figure(figsize=(180 * MM, 58 * MM))
B, T = 0.19, 0.84
ax1 = fig.add_axes([fx(11), B, fx(44), T - B])
ax2 = fig.add_axes([fx(71), B, fx(44), T - B])
ax3 = fig.add_axes([fx(132), B, fx(46), T - B])
curves = [("acc_determinable", "Accuracy, determinable", SLATE, "-"), ("abstain_unrecoverable", "Deferral, unrecoverable or ambiguous", GREY, "--"),
          ("balanced", "Balanced mean", BLUE, "-")]
for ax, df, col, sel, xl in [(ax1, ts, "tau", 0.70, "Full-conditioning threshold $\\tau$"),
                             (ax2, tg, "tau_gate", 0.60, "Gate threshold $\\tau_{\\mathrm{gate}}$")]:
    for c, lab_, colr, ls in curves:
        ax.plot(df[col], 100 * df[c], ls, color=colr, lw=1.0, marker="o", ms=2.0, label=lab_)
    ax.axvline(sel, color=VERM, lw=0.6, ls=":")
    ax.text(sel + 0.01, 3, f"selected {sel:.2f}", color=VERM, fontsize=5.6)
    ax.set_ylim(0, 100); ax.set_xlabel(xl); ax.grid(color="#E3E6EA", lw=0.4)
ax1.set_ylabel("Development instances (%)")
ax2.set_xticks([0.6, 0.7, 0.8, 0.9, 1.01]); ax2.set_xticklabels(["0.60", "0.70", "0.80", "0.90", "1.01"])
fig.legend(*ax1.get_legend_handles_labels(), loc="upper center", ncol=3, fontsize=5.8, bbox_to_anchor=(0.36, 0.94))
ax3.plot([0, 0.6], [0, 0.6], "--", color=GREY, lw=0.6)
ax3.plot(100 * 0 + lolo.decision_acc_pooled, lolo.decision_acc_lolo, "o", ms=2.8, color=SLATE)
for _, r in lolo.iterrows():
    if abs(r.decision_acc_lolo - r.decision_acc_pooled) > 1e-9:
        tx, ty = (0.47, 0.575) if r.lang == "et" else (0.44, 0.47)
        ax3.annotate(f"{LANG[r.lang]}: {100 * r.decision_acc_pooled:.1f} \u2192 {100 * r.decision_acc_lolo:.1f}%",
                     (r.decision_acc_pooled, r.decision_acc_lolo), (tx, ty), fontsize=5.3, color=GREY, ha="right", va="center",
                     arrowprops=dict(arrowstyle="-", color=GREY, lw=0.4, shrinkA=1, shrinkB=2))
n_same = int((abs(lolo.decision_acc_lolo - lolo.decision_acc_pooled) < 1e-9).sum())
ax3.text(0.585, 0.03, f"Identical for {n_same} of {len(lolo)} languages", fontsize=5.6, color=INK, ha="right")
ax3.set_xlim(0, 0.6); ax3.set_ylim(0, 0.6)
ax3.set_xlabel("Decision accuracy, pooled calibration"); ax3.set_ylabel("Decision accuracy,\nleave-one-language-out", linespacing=1.0)
ax3.grid(color="#E3E6EA", lw=0.4)
panel(fig, "a", 0.002, 0.985); panel(fig, "b", fx(60), 0.985); panel(fig, "c", fx(119), 0.985)
save(fig, "edfig3_calibration_dev", PDF_DIR, HERE)
source_data(HERE / "edfig3_source_data.xlsx", {"a_tau": ts, "b_tau_gate": tg, "c_lolo": lolo})
plt.close(fig)

# =====================================================================================================================
# Extended Data Fig. 4: EN->X (analysis/outputs/en2x_accuracy_ci.csv, en2x_isolated_masculine_share.csv)
ea = pd.read_csv(ANALYSIS / "en2x_accuracy_ci.csv")
em = pd.read_csv(ANALYSIS / "en2x_isolated_masculine_share.csv")
fig = plt.figure(figsize=(180 * MM, 58 * MM))
B, T = 0.18, 0.84
axa = fig.add_axes([fx(12), B, fx(96), T - B]); axb = fig.add_axes([fx(124), B, fx(54), T - B])
for gi, cond in enumerate(["adjacent", "distant_8", "memory"]):
    for k, o in zip(ORDER7, off):
        r = ea[(ea.system == k) & (ea.condition == cond)].iloc[0]
        axa.plot([gi + o, gi + o], [100 * r.lo, 100 * r.hi], color=COLOR[k], lw=0.8)
        system_marker(axa, gi + o, 100 * r.acc, k, size=3.0)
for gi, lg in enumerate(["ar", "de", "hi"]):
    for k, o in zip(ORDER7, off):
        r = em[(em.system == k) & (em.lang == lg)].iloc[0]
        system_marker(axb, gi + o, 100 * r.masculine_share, k, size=3.0)
nn = ea.groupby("condition").n.first()
axa.set_xticks([0, 1, 2]); axa.set_xticklabels([f"Adjacent ({nn['adjacent']})", f"Distant ({nn['distant_8']})", f"Memory ({nn['memory']})"])
axb.set_xticks([0, 1, 2]); axb.set_xticklabels(["Arabic", "German", "Hindi"])
axa.set_ylabel("MT-GenEval accuracy (%)"); axb.set_ylabel("Masculine share of gendered\nrenderings, context removed (%)", linespacing=1.0)
axa.set_ylim(50, 100); axb.set_ylim(50, 102)
for ax in (axa, axb):
    ax.grid(axis="y", color="#E3E6EA", lw=0.4); ax.tick_params(axis="x", length=0)
axa.set_xlim(-0.55, 2.55); axb.set_xlim(-0.55, 2.55)
fig.legend(handles=handles, loc="upper center", ncol=7, fontsize=5.8, bbox_to_anchor=(0.5, 1.0), columnspacing=1.0)
panel(fig, "a", 0.002, 0.88); panel(fig, "b", fx(113), 0.88)
save(fig, "edfig4_en2x", PDF_DIR, HERE)
source_data(HERE / "edfig4_source_data.xlsx", {"a_accuracy": ea, "b_masculine_share": em})
plt.close(fig)

# =====================================================================================================================
# Extended Data Fig. 5: mechanism (hygiene_by_condition.csv, gate_decision_profile.csv, counterfactuals_by_type.csv)
hy = pd.read_csv(ANALYSIS / "hygiene_by_condition.csv").set_index("condition")
prof = pd.read_csv(ANALYSIS / "gate_decision_profile.csv")
cf = pd.read_csv(ANALYSIS / "counterfactuals_by_type.csv")
fig = plt.figure(figsize=(180 * MM, 60 * MM))
B, T = 0.20, 0.86
axa = fig.add_axes([fx(11), B, fx(42), T - B])
conds = [("adjacent", "Adjacent"), ("distant_8", "Distant"), ("memory", "Memory"), ("isolated", "Isolated")]
vals = [100 * hy.loc[c, "any_impossible"] for c, _ in conds]
axa.bar(range(4), vals, width=0.62, color=SLATE, lw=0)
for i, (c, _) in enumerate(conds):
    axa.text(i, vals[i] - 2.0, f"{int(hy.loc[c, 'M'])} M\n{int(hy.loc[c, 'F'])} F", ha="center", va="top", fontsize=5.4,
             color="white", linespacing=1.1)
axa.set_xticks(range(4)); axa.set_xticklabels([f"{l}\n({int(hy.loc[c, 'n'])})" for c, l in conds], linespacing=1.0)
axa.set_ylim(0, 100); axa.set_ylabel("Instances with an impossible cue (%)")
axa.grid(axis="y", color="#E3E6EA", lw=0.4); axa.tick_params(axis="x", length=0)
# panel b: decision profile
axb = fig.add_axes([fx(79), B, fx(40), T - B])
kinds = [("determinable", "Determinable"), ("referent_ambiguous", "Referent-\nambiguous"), ("unrecoverable", "Unrecoverable")]
cats = [("confident", "Commit", BLUE), ("keep", "Keep", LIGHT), ("unobservable", "Defer, unobservable", SLATE), ("ambiguous", "Defer, ambiguous", "#7A9CBB")]
prof["why2"] = prof.why.replace({"unobservable_noslot": "unobservable"})
yk = np.arange(len(kinds))[::-1]
for yy, (k, lab_) in zip(yk, kinds):
    g = prof[prof.gold_kind == k].groupby("why2").n_slots.sum()
    tot = g.sum(); left = 0.0
    for c, cl, colr in cats:
        v = 100 * g.get(c, 0) / tot
        axb.barh(yy, v, left=left, height=0.6, color=colr, lw=0)
        if v >= 9:
            axb.text(left + v / 2, yy, f"{v:.0f}", ha="center", va="center", fontsize=5.4, color="white" if colr != LIGHT else INK)
        left += v
    axb.text(101.5, yy, f"{tot}", va="center", fontsize=5.4, color=GREY)
axb.set_yticks(yk); axb.set_yticklabels([l for _, l in kinds], linespacing=1.0); axb.tick_params(axis="y", length=0)
axb.set_xlim(0, 100); axb.set_xlabel("Held-out target slots (%)")
for i, (c, cl, colr) in enumerate(cats):
    xx = fx(79) + (i % 2) * fx(23)
    yy = 0.95 if i < 2 else 0.90
    fig.patches.append(plt.Rectangle((xx, yy - 0.017), fx(1.9), 0.034, transform=fig.transFigure, color=colr, lw=0))
    fig.text(xx + fx(2.5), yy, cl, fontsize=5.6, va="center")
# panel c: counterfactual insensitivity
axc = fig.add_axes([fx(132), B, fx(46), T - B])
sysc = ["llm_plain", "llm_cautious", "llm_cot_gender", "infer_then_tag", "ccl_gate"]
types = [("name_flip", "Name swap (134)"), ("name_only_flip", "Name-only cue (46)")]
w = 0.15
for j, k in enumerate(sysc):
    v = [100 * cf[(cf.system == k) & (cf.cf_note == t)].insensitive.iloc[0] for t, _ in types]
    axc.bar(np.arange(2) + (j - 2) * w, v, width=w * 0.92, color=COLOR[k], lw=0, label=LABEL[k])
axc.set_xticks([0, 1]); axc.set_xticklabels([l for _, l in types]); axc.tick_params(axis="x", length=0)
axc.set_ylim(0, 80); axc.set_ylabel("Same gender after a flip (%)")
axc.grid(axis="y", color="#E3E6EA", lw=0.4)
axc.legend(fontsize=5.3, loc="upper right", ncol=1, handlelength=0.9)
panel(fig, "a", 0.002, 0.985); panel(fig, "b", fx(58), 0.985); panel(fig, "c", fx(123), 0.985)
save(fig, "edfig5_mechanism", PDF_DIR, HERE)
source_data(HERE / "edfig5_source_data.xlsx", {"a_hygiene": hy.reset_index(), "b_decisions": prof, "c_counterfactuals": cf})
plt.close(fig)
print("Extended Data figures written")
