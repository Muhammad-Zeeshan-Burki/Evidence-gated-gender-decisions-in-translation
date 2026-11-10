"""Removes failed model calls from the pilot cache so that a resumed run requests them again.
Failed = empty reply (server rejected the request) or reply cut off at the 4,096-token slot limit.
A full backup of the cache is written first (cache\llm_cache_pilot.backup_<time>.sqlite)."""
import sqlite3, json, shutil, sys, time, os
p = sys.argv[1]
bak = p.replace(".sqlite", time.strftime(".backup_%Y%m%d_%H%M%S.sqlite"))
shutil.copy2(p, bak)
db = sqlite3.connect(p)
bad = []
for k, v in db.execute("select key, value from cache"):
    j = json.loads(v)
    if not any(j["texts"]) or (j.get("pt", 0) + j.get("ct", 0)) >= 4090:
        bad.append(k)
db.executemany("delete from cache where key = ?", [(k,) for k in bad]); db.commit()
n = db.execute("select count(*) from cache").fetchone()[0]
print(f"backup: {bak}\nremoved {len(bad)} failed calls; {n} good calls kept")
