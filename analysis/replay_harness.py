"""Replay harness: executes the notebook's code cells against the SQLite cache from a laptop run (no GPU, no server).
Any LLM request missing from the cache is counted and answered with an empty string.

Usage: python3 replay_harness.py <CCL_final.ipynb> <last cell index>
Set CCL_REPLAY_WORK to the run's work directory (the folder that holds cache/, data/ and outputs/, for example
v2/_runtime/ccl_work of the reported run)."""
import json, os, sys, re
# Repository root (this file lives in analysis/). When the file is exec'd by run_examples.py and friends, __file__ is
# undefined and the current directory (analysis/) is used instead.
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.path.abspath(os.getcwd()))
NB = sys.argv[1] if len(sys.argv) > 1 else os.path.join(_ROOT, "CCL_final.ipynb")
STOP = int(sys.argv[2]) if len(sys.argv) > 2 else 53
os.environ.setdefault("CCL_RUN_MODE", "smoke")
os.environ.update(CCL_WORK_DIR=os.environ.get("CCL_REPLAY_WORK", os.path.join(_ROOT, "_runtime", "ccl_work")), CCL_SKIP_INSTALL="1", CCL_LLM_BACKEND="openai",
                  CCL_TRANSLATOR="qwen3-8b", MPLBACKEND="Agg")
nb = json.load(open(NB))
G = {"__name__": "__main__"}
REPLAY = r'''
import collections as _c
TASKS = _c.Counter()
class ReplayBackend:
    supports_logprobs = True
    misses = 0
    def __init__(self, model): self.name = model
    def generate(self, batch):
        ReplayBackend.misses += len(batch)
        for r in batch:
            import re as _re
            _m = _re.search(r"TASK: *([\w_]+)", r["messages"][-1]["content"]); TASKS[(_m.group(1) if _m else "?") + ("_retry" if "Output ONLY the numbered lines" in r["messages"][-1]["content"] else "")] += r["n"]
        return [[""] * r["n"] for r in batch], [(0, 0) for _ in batch], [[{}] * r["n"] for r in batch]
_BACKENDS = {}
def get_backend(model):
    if model not in _BACKENDS:
        _BACKENDS[model] = ReplayBackend(model)
        MANIFEST["models"][model] = dict(backend="replay")
    return _BACKENDS[model]
'''
def run_cell(i, src):
    if "def git_clone_pinned" in src:
        src = src.replace("def git_clone_pinned(name):", "def git_clone_pinned(name):\n    return DATA / 'repos' / name\ndef _orig_gcp(name):")
    if "_BACKENDS = {}" in src:
        src = src[:src.index("_BACKENDS = {}")] + REPLAY + src[src.index("# unit test of the log-prob reader"):]
    if 'self.db.execute("insert or replace into cache values (?, ?)"' in src:
        src = src.replace('self.db.execute("insert or replace into cache values (?, ?)"', 'None if isinstance(self.backend, ReplayBackend) else self.db.execute("insert or replace into cache values (?, ?)"')
        assert "isinstance(self.backend, ReplayBackend)" in src
    if "PROBE = throughput_probe" in src:
        src = src.replace("PROBE = throughput_probe(LLM)", "PROBE = {}")
    exec(compile(src, f"cell{i}", "exec"), G)
for i, c in enumerate(nb["cells"]):
    if i > STOP: break
    if c["cell_type"] != "code": continue
    run_cell(i, "".join(c["source"]))
print("TASKS", dict(G["TASKS"]))
print("REPLAY cache misses:", G["ReplayBackend"].misses, "| stats", dict(G["LLM"].stats))
