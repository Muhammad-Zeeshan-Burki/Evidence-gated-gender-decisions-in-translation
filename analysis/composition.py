"""Benchmark composition for Extended Data Table 1 and passage-level (synthbio) accuracy for Supplementary Information."""
import json, sys
from pathlib import Path
import pandas as pd
R, SEEN_P, OUT = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
sc = pd.read_csv(R / "records" / "scores_items.csv", low_memory=False)
card = pd.read_csv(R / "tables" / "data_card.csv")
seen = set(json.loads(SEEN_P.read_text()))
p = sc[sc.system == "llm_plain"].copy()
KINDS = ["determinable", "unrecoverable", "referent_ambiguous"]
p["analysed"] = (p.direction == "x2en") & (p.subset != "synthbio") & (p.condition != "distant_32") & p.gold_kind.isin(KINDS)
p["heldout"] = p.analysed & ~p.item_id.isin(seen)
rows = []
for (ds, sub), g in p.groupby(["dataset", "subset"]):
    dev = int(card[(card.dataset == ds) & (card.subset == sub) & (card.split == "dev")].n.sum())
    rows.append(dict(dataset=ds, subset=sub, direction=g.direction.iloc[0], languages=" ".join(sorted(g.lang.unique())),
                     n_lang=g.lang.nunique(), conditions=" ".join(c for c in ["adjacent", "distant_8", "distant_32", "memory", "isolated"] if c in set(g.condition)),
                     gold=" ".join(sorted(g.gold_kind.unique())), dev=dev, test=len(g), analysed=int(g.analysed.sum()), heldout=int(g.heldout.sum())))
T = pd.DataFrame(rows)
T.to_csv(OUT / "benchmark_composition.csv", index=False)
print(T.to_string())
print("totals", T[["dev", "test", "analysed", "heldout"]].sum().to_dict())
# held-out by condition and gold kind
h = p[p.heldout]
print(h.groupby(["condition", "gold_kind"]).size())
print(h.groupby("lang").size().to_dict())
# passage-level synthbio accuracy (gender of all pronouns in the passage translation)
sb = sc[(sc.subset == "synthbio") & (sc.condition == "adjacent")]
sbt = sb.groupby("system").agg(n=("correct", "size"), acc=("correct", "mean"), neutral=("committed", lambda s: (s == "N").mean()),
                              mixed=("committed", lambda s: (s == "MIXED").mean())).round(4)
sbt.to_csv(OUT / "synthbio_passage_accuracy.csv")
print(sbt)
