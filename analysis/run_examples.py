import json, os, sys
from pathlib import Path
# Paths (override with environment variables): the final notebook, the replay work directory and this folder.
HERE = Path(__file__).resolve().parent
NB_PATH = os.environ.get("CCL_NOTEBOOK", str(HERE.parent / "CCL_final.ipynb"))
WORK = Path(os.environ.get("CCL_REPLAY_WORK", str(HERE.parent / "_runtime" / "ccl_work")))
TEST_PKL = WORK / "outputs" / "pilot_fin" / "qwen3-8b" / "test_instances.pkl"
import json, os, sys, runpy
sys.argv = ["harness", NB_PATH, "45"]
os.environ["CCL_RUN_MODE"] = "pilot"; os.environ["CCL_OUT_TAG"] = "_fin"
src = open(HERE / "replay_harness.py").read()
src = src.split('print("TASKS"')[0]
G0 = {"__name__": "__main__"}
exec(compile(src, "harness", "exec"), G0)
G = G0["G"]
import pandas as pd
T = pd.read_pickle(TEST_PKL)
ids = ["mit_6ec9bca6b456d95182111906807e4e26c0fcd1337c218b8954443af4_tr|adjacent|orig",
       "mit_6ec9bca6b456d95182111906807e4e26c0fcd1337c218b8954443af4_tr|isolated|orig",
       "twc00519_tr|adjacent|orig", "twc00519_tr|isolated|orig"]
insts = T[T.inst_id.isin(ids)].to_dict("records")
states = G["ccl_state"](insts)
w = G["current_weights"](); tg = G["current_tau_gate"]()
out = {}
for r in insts:
    st = states[r["inst_id"]]
    decs = G["gate_decisions"](r, st, w, tg)
    eb = {e["lid"]: e for e in st["ents"]}
    act = [d for d in decs if d["decision"] in {"F", "M", "DEFER"}]
    instr = G["instructions_for"](act, eb, r["direction"], "en")
    msgs = G["p_translate"](r["lang"], "en", r["input_src"], instructions=instr, context_note=" ".join(r["memory_src"]) if r["memory_src"] else "")
    out[r["inst_id"]] = dict(input=r["input_src"], ents=[dict(lid=e["lid"], english_name=e["english_name"], description=e.get("description"),
        source_names=e["source_names"], cues=e["cues"], name_prior=e["name_prior"], prior_src=e.get("name_prior_src"),
        pF=G["entity_pF"](e, w)) for e in st["ents"]], q=str(st.get("q")), amb=str(st.get("amb_lp")), decisions=decs,
        instructions=instr, translate_prompt=msgs[1]["content"], extract_meta=st["extract_meta"])
json.dump(out, open("examples_states.json", "w"), ensure_ascii=False, indent=1, default=str)
print(json.dumps(out, ensure_ascii=False, indent=1, default=str)[:6000])
print("misses", G["ReplayBackend"].misses)
