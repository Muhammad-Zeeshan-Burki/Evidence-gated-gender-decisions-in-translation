import json, os, sys
from pathlib import Path
# Paths (override with environment variables): the final notebook, the replay work directory and this folder.
HERE = Path(__file__).resolve().parent
NB_PATH = os.environ.get("CCL_NOTEBOOK", str(HERE.parent / "CCL_final.ipynb"))
WORK = Path(os.environ.get("CCL_REPLAY_WORK", str(HERE.parent / "_runtime" / "ccl_work")))
TEST_PKL = WORK / "outputs" / "pilot_fin" / "qwen3-8b" / "test_instances.pkl"
import json, os, sys
sys.argv = ["harness", NB_PATH, "45"]
os.environ["CCL_RUN_MODE"] = "pilot"; os.environ["CCL_OUT_TAG"] = "_fin"
src = open(HERE / "replay_harness.py").read().split('print("TASKS"')[0]
G0 = {"__name__": "__main__"}; exec(compile(src, "harness", "exec"), G0); G = G0["G"]
import pandas as pd
T = pd.read_pickle(TEST_PKL)
res = {}
for iid in ["twc00519_tr|adjacent|orig", "twc00519_tr|isolated|orig", "mit_6ec9bca6b456d95182111906807e4e26c0fcd1337c218b8954443af4_tr|isolated|orig", "mit_6ec9bca6b456d95182111906807e4e26c0fcd1337c218b8954443af4_tr|adjacent|orig"]:
    r = T[T.inst_id == iid].iloc[0].to_dict()
    msgs = G["p_extract_v3b"](r["lang"], " ".join(r["input_src"]), ())
    o = G["EXTRACTOR"].run([dict(messages=msgs, max_tokens=1024, schema=G["schema_extract_v3"]([]))])[0]
    st = G["ccl_state"]([r])[r["inst_id"]]
    ents = st["ents"]
    lv = [G["LETTERS"][i] for i in range(min(len(ents), len(G["LETTERS"])))] + ["unknown", "ambiguous"]
    rmsg = G["p_resolve_lp_v3b"](r["lang"], r["direction"], "en", ents, r["input_src"], r["target_idx"] + 1)
    ro = G["EXTRACTOR"].run([dict(messages=rmsg, n=1, temperature=0.0, max_tokens=512, logprobs=True, schema=G["schema_resolve"](lv))])[0]
    res[iid] = dict(extract_raw=o["texts"][0], extract_tokens=[o["pt"], o["ct"]], resolve_raw=ro["texts"][0], resolve_extras=ro.get("extras"), resolve_prompt=rmsg[1]["content"], extract_prompt=msgs[1]["content"])
json.dump(res, open("examples_raw.json", "w"), ensure_ascii=False, indent=1, default=str)
for k, v in res.items():
    print("=====", k); print("EXTRACT:", v["extract_raw"]); print("RESOLVE:", v["resolve_raw"]); print("EXTRAS:", str(v["resolve_extras"])[:800])
print("misses", G["ReplayBackend"].misses)
