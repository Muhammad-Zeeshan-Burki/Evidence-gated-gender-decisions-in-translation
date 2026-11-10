import json, os, sys
from pathlib import Path
# Paths (override with environment variables): the final notebook, the replay work directory and this folder.
HERE = Path(__file__).resolve().parent
NB_PATH = os.environ.get("CCL_NOTEBOOK", str(HERE.parent / "CCL_final.ipynb"))
WORK = Path(os.environ.get("CCL_REPLAY_WORK", str(HERE.parent / "_runtime" / "ccl_work")))
TEST_PKL = WORK / "outputs" / "pilot_fin" / "qwen3-8b" / "test_instances.pkl"
import json, os, sys, collections
sys.argv = ["harness", NB_PATH, "45"]
os.environ["CCL_RUN_MODE"] = "pilot"; os.environ["CCL_OUT_TAG"] = "_fin"
src = open(HERE / "replay_harness.py").read().split('print("TASKS"')[0]
G0 = {"__name__": "__main__"}; exec(compile(src, "harness", "exec"), G0); G = G0["G"]
import pandas as pd
T = pd.read_pickle(TEST_PKL)
seen = set(json.load(open(HERE / "dev_inspected_test_items.json")))
X = T[(T.direction == "x2en") & (T.subset != "synthbio") & (T.condition != "distant_32") & ~T.item_id.isin(seen)
      & T.gold_kind.isin(["determinable", "unrecoverable", "referent_ambiguous"])]
insts = X.to_dict("records")
p_ext = G["p_extract_v3b"]; sch = G["schema_extract_v3"]; parse_ledger = G["parse_ledger"]; json_parse = G["parse_json"]
src_lang = lambda r: r["lang"]
# memory ledgers (as in ccl_state_v3)
mem_keys = list(dict.fromkeys((src_lang(r), " ".join(r["memory_src"])) for r in insts if r["memory_src"]))
res = G["EXTRACTOR"].run([dict(messages=p_ext(l, t), max_tokens=1024, schema=sch([])) for l, t in mem_keys])
mem_led = {k: parse_ledger(rr["texts"][0], k[1])[0] for k, rr in zip(mem_keys, res)}
in_keys, in_known = [], {}
for r in insts:
    mk = (src_lang(r), " ".join(r["memory_src"])) if r["memory_src"] else None
    k = (src_lang(r), " ".join(r["input_src"]), mk)
    if k not in in_known:
        in_known[k] = [(f"K{i+1}", e) for i, e in enumerate(mem_led[mk])] if mk else []; in_keys.append(k)
res = G["EXTRACTOR"].run([dict(messages=p_ext(l, t, in_known[(l, t, mk)]), max_tokens=1024, schema=sch([kid for kid, _ in in_known[(l, t, mk)]])) for l, t, mk in in_keys])
raw_cur = {k: parse_ledger(rr["texts"][0], k[1])[0] for k, rr in zip(in_keys, res)}
GL = G["GENDERLESS_SRC"]; valid = G["cue_is_valid"]; pseudo = G["is_pseudo_entity"]
rows = []
for r in insts:
    mk = (src_lang(r), " ".join(r["memory_src"])) if r["memory_src"] else None
    ents = raw_cur[(src_lang(r), " ".join(r["input_src"]), mk)]
    allents = (mem_led[mk] if mk else []) + ents
    d3 = collections.Counter(); d2 = collections.Counter(); kept = collections.Counter(); ps = collections.Counter()
    for e in allents:
        pk = pseudo(e, r["lang"])
        if pk: ps[pk] += 1
        for c in e["cues"]:
            if r["lang"] in GL and c["type"] in {"gendered_pronoun", "verb_agreement", "adjective_agreement"}:
                d3[c["gender"]] += 1
            elif not valid(c, e, r["lang"]):
                d2[c["gender"]] += 1
            else:
                kept[c["gender"]] += 1
    rows.append(dict(inst_id=r["inst_id"], lang=r["lang"], condition=r["condition"], gold_kind=r["gold_kind"], genderless=r["lang"] in GL,
                     d3_M=d3["M"], d3_F=d3["F"], d2_M=d2["M"], d2_F=d2["F"], kept_M=kept["M"], kept_F=kept["F"],
                     pseudo_pronoun=ps["pronoun"], pseudo_generic=ps["generic"], pseudo_narrator=ps["narrator"], n_ents=len(allents)))
df = pd.DataFrame(rows)
df.to_csv(HERE / "hygiene_heldout.csv", index=False)
print(len(df), "held-out X->EN instances; misses", G["ReplayBackend"].misses)
