"""Held-out paired comparisons of CCL-Gate with the four prompting strategies (Fig. 3c, Extended Data Table 2).

Usage:
    python3 paired_exact.py <Results/pilot> <outputs dir>

Reads tables/T2e_heldout_key_comparisons.csv from the reported run, keeps the CCL-Gate rows, recomputes the two-sided exact
McNemar test from the discordant counts b and c, and applies the Holm adjustment across the four baselines within each
condition. Writes outputs/heldout_paired_exact_p.csv.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import binomtest

R, OUT = Path(sys.argv[1]), Path(sys.argv[2])
BASE = ["llm_cautious", "llm_cot_gender", "infer_then_tag", "llm_plain"]
t = pd.read_csv(R / "tables" / "T2e_heldout_key_comparisons.csv", index_col=0)
t = t[t.comparison.isin([f"ccl_gate - {b}" for b in BASE])].copy()


def holm(p):
    p = np.asarray(p, float)
    order = np.argsort(p)
    adj = np.empty_like(p)
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (len(p) - rank) * p[i]))
        adj[i] = running
    return adj


t["p_exact"] = [binomtest(int(min(b, c)), int(b + c), 0.5).pvalue if b + c > 0 else 1.0 for b, c in zip(t.b, t.c)]
t["p_holm_exact"] = t.groupby("subset").p_exact.transform(holm)
assert t.groupby("subset").size().eq(len(BASE)).all()
t.to_csv(OUT / "heldout_paired_exact_p.csv", index=False)
print(t.to_string())
