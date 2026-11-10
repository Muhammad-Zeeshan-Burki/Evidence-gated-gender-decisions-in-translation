"""Additional statistics added in the revision (24 Oct 2026). No model calls; reads the reported run only.

Usage:  python extra_stats.py <Results/pilot dir> <dev_inspected_test_items.json> <output dir>

Writes to <output dir>:
  overall_correctness_ci.csv     held-out per-instance correctness per system with item-cluster bootstrap CIs, plus the
                                 always-neutral reference (ACC 0, UCR 0, BAL 0.50)
  knowing_vs_using_both_ci.csv   knows-not-use and uses-not-know shares with CIs (same population as Fig. 5c)
  counterfactual_both.csv        counterfactual pairs: same gendered pronoun after a flip, and both members correct
  posterior_informativeness.json share of determinable instances with a near-uninformative slot posterior, and AUC
The bootstrap uses its own generator (seed 20261006) so that the outputs of paper_stats.py are unchanged.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

R, SEEN_P, OUT = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
OUT.mkdir(parents=True, exist_ok=True)
RNG = np.random.default_rng(20261006)
ITERS = 10000
sc = pd.read_csv(R / "records" / "scores_items.csv", low_memory=False)
seen = set(json.loads(SEEN_P.read_text()))
KINDS = ["determinable", "unrecoverable", "referent_ambiguous"]
x2en = sc[(sc.direction == "x2en") & (sc.subset != "synthbio") & (sc.condition != "distant_32")]
AN = x2en[x2en.gold_kind.isin(KINDS)].copy()
HELD = AN[~AN.item_id.isin(seen)].copy()


def ok(r):
    return (r.committed == r.gold_gender) if r.gold_kind == "determinable" else (r.committed == "N")


def boot(df, col):
    g = df.groupby("item_id")[col].agg(["sum", "count"])
    s, c = g["sum"].to_numpy(float), g["count"].to_numpy(float)
    W = RNG.multinomial(len(s), np.full(len(s), 1 / len(s)), size=ITERS)
    st = (W @ s) / np.maximum(W @ c, 1e-9)
    return s.sum() / c.sum(), *np.quantile(st, [0.025, 0.975])


# 1. Overall per-instance correctness (held-out)
rows = []
for s in ["llm_plain", "llm_cautious", "llm_cot_gender", "infer_then_tag", "ccl", "ccl_gate", "oracle_goe"]:
    x = HELD[HELD.system == s].copy()
    x["ok"] = x.apply(ok, axis=1).astype(float)
    e, lo, hi = boot(x, "ok")
    rows.append(dict(system=s, n=len(x), correct=e, lo=lo, hi=hi))
ref = HELD[HELD.system == "llm_plain"]
n_u = int((ref.gold_kind != "determinable").sum())
rows.append(dict(system="always_neutral_reference", n=len(ref), correct=n_u / len(ref), lo=np.nan, hi=np.nan))
pd.DataFrame(rows).round(4).to_csv(OUT / "overall_correctness_ci.csv", index=False)

# 2. Knowing versus using in both directions (same population as paper_stats.py section 7)
sca = sc[sc.condition != "distant_32"]
pr = sca[sca.system == "probe"].set_index("inst_id")[["item_id", "correct", "condition"]]
tr = sca[sca.system == "llm_plain"].set_index("inst_id")[["correct"]]
KU = pr.join(tr, lsuffix="_probe", rsuffix="_translate", how="inner").dropna().reset_index()
cp = KU.correct_probe.map(lambda v: str(v) == "True")
ct = KU.correct_translate.map(lambda v: str(v) == "True")
KU["knu"] = (cp & ~ct).astype(float)
KU["unk"] = (~cp & ct).astype(float)
ku = []
for cond in ["adjacent", "distant_8", "memory", "isolated"]:
    g = KU[KU.condition == cond]
    a = boot(g, "knu"); b = boot(g, "unk")
    ku.append(dict(condition=cond, n=len(g), know_not_use=a[0], knu_lo=a[1], knu_hi=a[2],
                   use_not_know=b[0], unk_lo=b[1], unk_hi=b[2]))
pd.DataFrame(ku).round(4).to_csv(OUT / "knowing_vs_using_both_ci.csv", index=False)

# 3. Counterfactual pairs (copied from counterfactuals_by_type.csv when present, for the systems in the text)
cf = pd.read_csv(OUT / "counterfactuals_by_type.csv") if (OUT / "counterfactuals_by_type.csv").exists() else None
if cf is not None:
    keep = ["llm_plain", "llm_cautious", "llm_cot_gender", "infer_then_tag", "ccl", "ccl_gate", "oracle_goe"]
    cf[cf.system.isin(keep) & cf.cf_note.isin(["name_flip", "name_only_flip"])].to_csv(OUT / "counterfactual_both.csv", index=False)

# 4. Informativeness of the slot posterior (same population as the reliability diagram)
cal = sca[(sca.system == "ccl") & (sca.gold_kind == "determinable") & sca.target_pF.notna() & sca.gold_gender.isin(["F", "M"])]
p = cal.target_pF.to_numpy(float); y = (cal.gold_gender == "F").to_numpy(int)
order = np.argsort(p); ranks = np.empty(len(p)); ranks[order] = np.arange(1, len(p) + 1)
# AUC by the rank-sum formula with average ranks for ties
ranks = pd.Series(p).rank().to_numpy()
n1, n0 = y.sum(), (1 - y).sum()
auc = (ranks[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)
info = dict(n=int(len(p)), share_posterior_045_055=float(((p >= 0.45) & (p <= 0.55)).mean()),
            share_conf_below_060=float((np.maximum(p, 1 - p) < 0.60).mean()), auc=float(auc))
(OUT / "posterior_informativeness.json").write_text(json.dumps(info, indent=1))
print(pd.DataFrame(rows).round(4).to_string()); print(pd.DataFrame(ku).round(4).to_string()); print(info)
