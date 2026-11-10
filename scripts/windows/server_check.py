"""Pre-flight check of llama-server against what the CCL notebook sends.
Writes <repository>/_runtime/logs/server_check.json. Usage: python server_check.py [base_url] [model]"""
import json, sys, time, re, os
from concurrent.futures import ThreadPoolExecutor
import requests

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080/v1").rstrip("/")
MODEL = sys.argv[2] if len(sys.argv) > 2 else "qwen3-8b"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "_runtime", "logs", "server_check.json")
res = {"base": BASE, "model": MODEL, "checks": {}}

def call(extra, msg, max_tokens=200, temperature=0.0):
    p = dict(model=MODEL, messages=[{"role": "user", "content": msg}], temperature=temperature, max_tokens=max_tokens,
             seed=20261006, chat_template_kwargs={"enable_thinking": False}, reasoning_effort="none")
    p.update(extra)
    t0 = time.time(); r = requests.post(BASE + "/chat/completions", json=p, timeout=300)
    return r, time.time() - t0

def check(name, fn):
    try:
        res["checks"][name] = fn()
    except Exception as e:
        res["checks"][name] = {"ok": False, "error": f"{type(e).__name__}: {e}"}
    print(name, json.dumps(res["checks"][name], ensure_ascii=False)[:400])

def plain():
    r, dt = call({}, "Translate into English: 'O dün akşam eve geç geldi.' Output only the translation.")
    j = r.json(); txt = j["choices"][0]["message"].get("content") or ""
    return {"ok": r.status_code == 200 and "<think>" not in txt and len(txt.strip()) > 0, "status": r.status_code,
            "text": txt, "has_reasoning_field": bool(j["choices"][0]["message"].get("reasoning_content")),
            "usage": j.get("usage"), "sec": round(dt, 2)}

SCHEMA = {"type": "object", "properties": {"slots": {"type": "array", "items": {"type": "object",
          "properties": {"sentence": {"type": "integer"}, "slot": {"type": "integer"},
                         "referent": {"type": "string", "enum": ["A", "B", "unknown", "ambiguous"]}},
          "required": ["sentence", "slot", "referent"]}}}, "required": ["slots"]}
MSG = ("TASK: resolve_slots\nPEOPLE:\n A = Ayşe (woman)\n B = Mehmet (man)\nTEXT:\n[1] Ayşe aradı.\n[2] O çok yorgundu.\n"
       "For each third-person pronoun slot in line 2, which person does it refer to? Answer in JSON.")
def schema():
    r, dt = call({"response_format": {"type": "json_schema", "json_schema": {"name": "out", "schema": SCHEMA}, "schema": SCHEMA}}, MSG)
    txt = r.json()["choices"][0]["message"].get("content") or "" if r.status_code == 200 else r.text[:300]
    try:
        obj = json.loads(txt); ok = isinstance(obj.get("slots"), list)
    except Exception:
        obj, ok = None, False
    return {"ok": r.status_code == 200 and ok, "status": r.status_code, "text": txt, "sec": round(dt, 2)}

def logprobs():
    r, dt = call({"response_format": {"type": "json_schema", "json_schema": {"name": "out", "schema": SCHEMA}, "schema": SCHEMA},
                  "logprobs": True, "top_logprobs": 10}, MSG)
    j = r.json(); ch = j["choices"][0]
    lp = (ch.get("logprobs") or {}).get("content") or []
    sample = [{"token": t.get("token"), "top": [(a.get("token"), round(a.get("logprob", -99), 3)) for a in (t.get("top_logprobs") or [])[:4]]}
              for t in lp if re.search(r'[A-Za-z]', t.get("token", ""))][:12]
    return {"ok": r.status_code == 200 and len(lp) > 0 and all("top_logprobs" in t for t in lp[:3]), "status": r.status_code,
            "n_tokens": len(lp), "top_k_first": len((lp[0].get("top_logprobs") or [])) if lp else 0, "sample": sample,
            "text": ch["message"].get("content"), "sec": round(dt, 2)}

def throughput():
    msgs = [f"Write a 100-word description of a quiet village morning (variant {i})." for i in range(8)]
    t0 = time.time()
    with ThreadPoolExecutor(4) as ex:
        outs = list(ex.map(lambda m: call({}, m, max_tokens=128, temperature=0.7)[0].json(), msgs))
    dt = time.time() - t0; ct = sum(o.get("usage", {}).get("completion_tokens", 0) for o in outs)
    return {"ok": ct > 0, "wall_s": round(dt, 1), "completion_tokens": ct, "agg_tok_per_s": round(ct / dt, 1)}

check("plain_no_thinking", plain)
check("json_schema", schema)
check("logprobs", logprobs)
check("throughput_4way", throughput)
res["all_ok"] = all(c.get("ok") for c in res["checks"].values())
json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("ALL OK" if res["all_ok"] else "SOME CHECKS FAILED", "->", os.path.abspath(OUT))
