"""Derived statistics for the manuscript, computed from the scored per-instance records of the reported run.

No model calls are made. Every quantity is computed from Results/pilot (tables, records) with the same estimators as the
notebook (item-cluster bootstrap, exact McNemar test, Holm correction). Usage:

    python paper_stats.py <Results/pilot dir> <dev_inspected_test_items.json> <output dir>
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.stats as st

R, SEEN_P, OUT = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
OUT.mkdir(parents=True, exist_ok=True)
ITERS = 10000
RNG = np.random.default_rng(20261006)          # seed of the reported run

sc = pd.read_csv(R / "records" / "scores_items.csv", low_memory=False)
seen = set(json.loads(SEEN_P.read_text()))
x2en = sc[(sc.direction == "x2en") & (sc.subset != "synthbio") & (sc.condition != "distant_32")]
KINDS = ["determinable", "unrecoverable", "referent_ambiguous"]
ANALYSED = x2en[x2en.gold_kind.isin(KINDS)].copy()
HELD = ANALYSED[~ANALYSED.item_id.isin(seen)].copy()
BASE = ["llm_plain", "llm_cautious", "llm_cot_gender", "infer_then_tag"]
HEAD = BASE + ["ccl", "ccl_gate", "oracle_goe"]
res = {}


def cluster_bootstrap_ci(df, value_col, cluster_col="item_id", iters=ITERS, alpha=0.05):
    d = df[[cluster_col, value_col]].dropna()
    if d.empty:
        return (np.nan, np.nan, np.nan)
    g = d.groupby(cluster_col)[value_col].agg(["sum", "count"])
    s, c = g["sum"].to_numpy(float), g["count"].to_numpy(float)
    W = RNG.multinomial(len(s), np.full(len(s), 1 / len(s)), size=iters)
    stats_ = (W @ s) / np.maximum(W @ c, 1e-9)
    return (s.sum() / c.sum(), *np.quantile(stats_, [alpha / 2, 1 - alpha / 2]))


def paired_frame(df, a, b):
    A = df[df.system == a].set_index("inst_id")
    B = df[df.system == b].set_index("inst_id")
    j = A[["item_id", "correct"]].join(B[["correct"]], rsuffix="_b", how="inner").dropna()
    j["diff"] = j["correct"].astype(float) - j["correct_b"].astype(float)
    return j


def mcnemar_exact(j):
    b = int(((j.correct == True) & (j.correct_b == False)).sum())
    c = int(((j.correct == False) & (j.correct_b == True)).sum())
    return b, c, (1.0 if b + c == 0 else float(st.binomtest(b, b + c, 0.5).pvalue))


def holm(p):
    p = np.asarray(p, float); order = np.argsort(p); m = len(p); adj = np.empty(m); run = 0.0
    for rank, i in enumerate(order):
        run = max(run, (m - rank) * p[i]); adj[i] = min(1.0, run)
    return adj


def compare(df, ref, others, label=""):
    rows = []
    for o in others:
        j = paired_frame(df, ref, o)
        if j.empty:
            continue
        est, lo, hi = cluster_bootstrap_ci(j.reset_index(), "diff")
        b, c, p = mcnemar_exact(j)
        rows.append(dict(comparison=f"{ref} - {o}", subset=label, n=len(j), diff=est, ci_low=lo, ci_high=hi, b=b, c=c, p=p))
    out = pd.DataFrame(rows)
    if len(out):
        out["p_holm"] = holm(out.p)
    return out


# 1. Held-out headline with bootstrap CIs for ACC, UCR and BAL (Table 1, Fig. 3a)
rows = []
for s_ in HEAD:
    g = HELD[HELD.system == s_].copy()
    g["acc_v"] = np.where(g.gold_kind == "determinable", g.correct.astype(float), np.nan)
    g["ucr_v"] = np.where(g.gold_kind != "determinable", g.committed_gendered.astype(float), np.nan)
    acc = cluster_bootstrap_ci(g, "acc_v"); ucr = cluster_bootstrap_ci(g, "ucr_v")
    # BAL interval: resample items, recompute both halves inside each replicate
    per = g.groupby("item_id").agg(a_s=("acc_v", "sum"), a_n=("acc_v", "count"), u_s=("ucr_v", "sum"), u_n=("ucr_v", "count"))
    M = per.to_numpy(float)
    W = RNG.multinomial(len(M), np.full(len(M), 1 / len(M)), size=ITERS)
    S = W @ M
    bal_bs = 0.5 * S[:, 0] / S[:, 1] + 0.5 * (1 - S[:, 2] / S[:, 3])
    bal = 0.5 * acc[0] + 0.5 * (1 - ucr[0])
    rows.append(dict(system=s_, ACC=acc[0], ACC_lo=acc[1], ACC_hi=acc[2], UCR=ucr[0], UCR_lo=ucr[1], UCR_hi=ucr[2],
                     BAL=bal, BAL_lo=np.quantile(bal_bs, 0.025), BAL_hi=np.quantile(bal_bs, 0.975)))
T_HEAD_CI = pd.DataFrame(rows).set_index("system")
T_HEAD_CI.round(4).to_csv(OUT / "heldout_headline_ci.csv")

# 2. Held-out per-language paired differences, CCL-Gate minus each prompt baseline (Extended Data Fig. 1)
lang_rows = []
for lang, g in HELD.groupby("lang"):
    c = compare(g, "ccl_gate", BASE, label=lang)
    lang_rows.append(c)
T_LANG = pd.concat(lang_rows, ignore_index=True)
for comp, idx in T_LANG.groupby("comparison").groups.items():           # Holm across languages, per comparison
    T_LANG.loc[idx, "p_holm_lang"] = holm(T_LANG.loc[idx, "p"])
n_lang = HELD[HELD.system == "ccl_gate"].groupby("lang").size().rename("n_inst")
T_LANG = T_LANG.merge(n_lang, left_on="subset", right_index=True)
T_LANG.round(4).to_csv(OUT / "heldout_by_language_gate_vs_baselines.csv", index=False)

# 3. Translation-level ablations: CCL-Gate minus each variant on all analysed test instances (Fig. 5a)
VARS = ["ccl", "ccl_gate_posthoc", "ccl_no_repair", "ccl_posthoc"]
T_ABL = compare(ANALYSED, "ccl_gate", VARS, label="all_analysed")
T_ABL.round(4).to_csv(OUT / "ablations_gate_vs_variants.csv", index=False)

# 4. Male-minus-female accuracy gap with item-cluster bootstrap CI (Fig. 4c)
gap_rows = []
for s_ in HEAD:
    d = ANALYSED[(ANALYSED.system == s_) & (ANALYSED.gold_kind == "determinable") & ANALYSED.gold_gender.isin(["F", "M"])].copy()
    d["c"] = d.correct.astype(float)
    per = d.assign(mF=(d.gold_gender == "F") * d.c, nF=(d.gold_gender == "F").astype(float),
                   mM=(d.gold_gender == "M") * d.c, nM=(d.gold_gender == "M").astype(float)).groupby("item_id")[["mF", "nF", "mM", "nM"]].sum()
    M = per.to_numpy(float)
    W = RNG.multinomial(len(M), np.full(len(M), 1 / len(M)), size=ITERS)
    S = W @ M
    bs = S[:, 2] / S[:, 3] - S[:, 0] / S[:, 1]
    accF, accM = M[:, 0].sum() / M[:, 1].sum(), M[:, 2].sum() / M[:, 3].sum()
    gap_rows.append(dict(system=s_, acc_F=accF, acc_M=accM, gap_M_minus_F=accM - accF,
                         gap_lo=np.quantile(bs, 0.025), gap_hi=np.quantile(bs, 0.975), n=len(d)))
T_GAP = pd.DataFrame(gap_rows).set_index("system")
T_GAP.round(4).to_csv(OUT / "gender_gap_ci.csv")

# 5. Risk-coverage: system points on all analysed X->EN test instances + CCL tau sweep (Fig. 4a)
def rc_point(g):
    det = g[g.gold_kind == "determinable"]; unr = g[g.gold_kind != "determinable"]
    cd, cu = det[det.committed_gendered], unr[unr.committed_gendered]
    cov = len(cd) / max(len(det), 1)
    risk = ((~cd.correct.astype(bool)).sum() + len(cu)) / max(len(cd) + len(cu), 1)
    return cov, risk, len(cd) + len(cu)
pts = []
for s_ in HEAD:
    cov, risk, n = rc_point(ANALYSED[ANALYSED.system == s_])
    pts.append(dict(system=s_, coverage=cov, risk=risk, n_commit=n))
sw = pd.read_csv(R / "records" / "scores_tau_sweep.csv", low_memory=False)
sw = sw[(sw.direction == "x2en") & (sw.subset != "synthbio") & (sw.condition != "distant_32") & sw.gold_kind.isin(KINDS)]
for tau, g in sw.groupby("tau"):
    cov, risk, n = rc_point(g)
    pts.append(dict(system=f"ccl_tau_{tau}", coverage=cov, risk=risk, n_commit=n))
T_RC = pd.DataFrame(pts)
T_RC.round(4).to_csv(OUT / "risk_coverage_points.csv", index=False)

# 6. Reliability of the slot posterior (Fig. 4b), same population as T11 (CCL, determinable, both directions)
sca = sc[sc.condition != "distant_32"]
cal = sca[(sca.system == "ccl") & (sca.gold_kind == "determinable") & sca.target_pF.notna() & sca.gold_gender.isin(["F", "M"])]
p = cal.target_pF.to_numpy(float); y = (cal.gold_gender == "F").to_numpy(float)
edges = np.linspace(0, 1, 11); ece = 0.0; rel = []
for a, b in zip(edges[:-1], edges[1:]):
    m = (p >= a) & ((p < b) if b < 1 else (p <= b))
    if m.any():
        ece += m.mean() * abs(p[m].mean() - y[m].mean())
        k = int(m.sum()); f = y[m].mean()
        lo, hi = st.binomtest(int(y[m].sum()), k).proportion_ci(confidence_level=0.95, method="wilson")
        rel.append(dict(bin_lo=a, bin_hi=b, mean_pred=p[m].mean(), frac_female=f, n=k, ci_lo=lo, ci_hi=hi))
T_REL = pd.DataFrame(rel)
T_REL.round(4).to_csv(OUT / "reliability_bins.csv", index=False)
res["calibration"] = dict(ECE=round(float(ece), 4), Brier=round(float(np.mean((p - y) ** 2)), 4), n=int(len(p)))

# 7. Knowing versus using with CIs (Fig. 5c), plain translator, all analysed probe instances
pr = sca[(sca.system == "probe")].set_index("inst_id")[["item_id", "correct", "condition"]]
tr = sca[(sca.system == "llm_plain")].set_index("inst_id")[["correct"]]
KU = pr.join(tr, lsuffix="_probe", rsuffix="_translate", how="inner").dropna().reset_index()
KU["kp"] = KU.correct_probe.astype(float); KU["kt"] = KU.correct_translate.astype(float)
KU["knu"] = (KU.correct_probe.astype(bool) & ~KU.correct_translate.astype(bool)).astype(float)
ku_rows = []
for cond in ["adjacent", "distant_8", "memory", "isolated"]:
    g = KU[KU.condition == cond]
    a = cluster_bootstrap_ci(g, "kp"); b = cluster_bootstrap_ci(g, "kt"); c = cluster_bootstrap_ci(g, "knu")
    ku_rows.append(dict(condition=cond, n=len(g), probe=a[0], probe_lo=a[1], probe_hi=a[2], translate=b[0], translate_lo=b[1],
                        translate_hi=b[2], know_not_use=c[0], knu_lo=c[1], knu_hi=c[2]))
T_KU = pd.DataFrame(ku_rows)
T_KU.round(4).to_csv(OUT / "knowing_vs_using_ci.csv", index=False)

# 8. Gate decision profile on held-out target slots (Extended Data). Target-line positions come from the instance table
#    written by the notebook (test_instances.pkl, optional 4th argument); without it every decision is counted.
held_ids = set(HELD.inst_id.unique())
kind_of = HELD.drop_duplicates("inst_id").set_index("inst_id")
span = {}
if len(sys.argv) > 4:
    ti = pd.read_pickle(sys.argv[4]).set_index("inst_id")
    span = {i: (int(r.target_idx) + 1, int(r.target_idx) + int(r.n_target)) for i, r in ti.iterrows()}
prof = []
with open(R / "records" / "records_items.jsonl", encoding="utf-8") as f:
    for line in f:
        r = json.loads(line)
        if r["system"] != "ccl_gate" or r["inst_id"] not in held_ids:
            continue
        lo_, hi_ = span.get(r["inst_id"], (1, 10 ** 6))
        for d in r.get("decisions") or []:
            if not (lo_ <= d["line"] <= hi_):
                continue
            prof.append(dict(inst_id=r["inst_id"], gold_kind=kind_of.loc[r["inst_id"], "gold_kind"],
                             condition=kind_of.loc[r["inst_id"], "condition"], why=d.get("why"), decision=d.get("decision")))
T_PROF = pd.DataFrame(prof)
T_PROF.groupby(["gold_kind", "why"]).size().rename("n_slots").reset_index().to_csv(OUT / "gate_decision_profile.csv", index=False)

# 9. Counterfactual pairs by type (adjacent + memory, all analysed), extends T9 to all systems
o = ANALYSED[ANALYSED.cf == "orig"].set_index(["item_id", "condition", "system"])
cf = x2en[x2en.cf != "orig"].set_index(["item_id", "condition", "system"])
J = o[["committed", "correct", "gold_gender"]].join(cf[["committed", "correct", "gold_gender", "cf_note"]], rsuffix="_cf", how="inner").reset_index()
J = J[J.condition.isin(["adjacent", "memory"])]
J["both_correct"] = J.correct.astype(bool) & J.correct_cf.astype(bool)
J["flip_expected"] = J.gold_gender != J.gold_gender_cf
J["follows"] = J.flip_expected & J.committed.isin(["F", "M"]) & J.committed_cf.isin(["F", "M"]) & (J.committed != J.committed_cf)
J["insensitive"] = J.flip_expected & (J.committed == J.committed_cf) & J.committed.isin(["F", "M"])
T_CF = J.groupby(["system", "cf_note"]).agg(n=("both_correct", "size"), both_correct=("both_correct", "mean"),
                                            insensitive=("insensitive", "mean")).reset_index()
T_CF.round(4).to_csv(OUT / "counterfactuals_by_type.csv", index=False)

# 10. Hygiene audit summary (cached extractor outputs, held-out instances; see hygiene_stats.py)
hy = pd.read_csv(Path(__file__).with_name("hygiene_heldout.csv"))
hy["d3"] = hy.d3_M + hy.d3_F; hy["d2"] = hy.d2_M + hy.d2_F
g = hy[hy.genderless]; iso = g[g.condition == "isolated"]
res["hygiene"] = dict(
    n_heldout=int(len(hy)), n_genderless=int(len(g)),
    share_genderless_with_impossible_cue=round(float((g.d3 > 0).mean()), 4),
    impossible_cues_M=int(g.d3_M.sum()), impossible_cues_F=int(g.d3_F.sum()),
    n_isolated_genderless=int(len(iso)),
    isolated_share_any_impossible=round(float((iso.d3 > 0).mean()), 4),
    isolated_share_masculine_only=round(float(((iso.d3_M > 0) & (iso.d3_F == 0)).mean()), 4),
    isolated_share_feminine_only=round(float(((iso.d3_F > 0) & (iso.d3_M == 0)).mean()), 4),
    share_with_name_only_cue=round(float((hy.d2 > 0).mean()), 4), name_only_cues=int(hy.d2.sum()),
    cues_kept=int((hy.kept_M + hy.kept_F).sum()),
    share_with_pseudo_pronoun_entity=round(float((hy.pseudo_pronoun > 0).mean()), 4))
by_cond = g.groupby("condition").apply(lambda t: pd.Series(dict(n=len(t), any_impossible=(t.d3 > 0).mean(),
                                                               M=t.d3_M.sum(), F=t.d3_F.sum()))).reset_index()
by_cond.round(4).to_csv(OUT / "hygiene_by_condition.csv", index=False)

# 11a. EN->X (MT-GenEval contextual): dataset metric with item-cluster CIs, and masculine share when context is removed
E = sc[(sc.direction == "en2x") & (sc.condition != "distant_32")]
en_rows = []
for s_ in HEAD:
    for cond in ["adjacent", "distant_8", "memory"]:
        g = E[(E.system == s_) & (E.condition == cond) & (E.gold_kind != "unrecoverable")].copy()
        g["v"] = g.correct_dataset.astype(float)
        est, lo, hi = cluster_bootstrap_ci(g, "v")
        en_rows.append(dict(system=s_, condition=cond, n=len(g), acc=est, lo=lo, hi=hi))
pd.DataFrame(en_rows).round(4).to_csv(OUT / "en2x_accuracy_ci.csv", index=False)
iso_rows = []
for s_ in HEAD:
    for lang in ["ar", "de", "hi"]:
        g = E[(E.system == s_) & (E.lang == lang) & (E.gold_kind == "unrecoverable") & E.committed.isin(["F", "M"])]
        iso_rows.append(dict(system=s_, lang=lang, n_gendered=len(g), masculine_share=(g.committed == "M").mean() if len(g) else np.nan,
                             n_isolated=int(((E.system == s_) & (E.lang == lang) & (E.gold_kind == "unrecoverable")).sum())))
pd.DataFrame(iso_rows).round(4).to_csv(OUT / "en2x_isolated_masculine_share.csv", index=False)

# 11. Sample sizes used in the text
res["n"] = dict(heldout_instances=int(HELD.inst_id.nunique()), heldout_det=int(HELD[(HELD.system == "llm_plain") & (HELD.gold_kind == "determinable")].shape[0]),
                heldout_unr=int(HELD[(HELD.system == "llm_plain") & (HELD.gold_kind != "determinable")].shape[0]),
                analysed_instances=int(ANALYSED.inst_id.nunique()), heldout_items=int(HELD.item_id.nunique()),
                analysed_items=int(ANALYSED.item_id.nunique()), heldout_languages=sorted(HELD.lang.unique().tolist()),
                n_test_instances_all=int(sc.inst_id.nunique()))
(OUT / "paper_stats.json").write_text(json.dumps(res, indent=1))
print(json.dumps(res, indent=1))
print(T_HEAD_CI.round(3).to_string()); print(T_ABL.round(4).to_string()); print(T_GAP.round(3).to_string())
print(T_RC.round(3).to_string()); print(T_REL.round(3).to_string()); print(T_KU.round(3).to_string())
print(T_PROF.groupby(["gold_kind", "why"]).size()); print(T_CF.round(3).to_string()); print(by_cond.round(3).to_string())
print(T_LANG[T_LANG.comparison.isin(["ccl_gate - llm_plain", "ccl_gate - llm_cautious"])].round(3).to_string())
