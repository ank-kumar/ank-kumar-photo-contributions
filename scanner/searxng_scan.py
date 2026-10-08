#!/usr/bin/env python3
"""SearXNG scan: search the subjects Tavily hasn't covered, via the local SearXNG instance (free)."""
import json, os, random, sys, time, urllib.parse, urllib.request, urllib.error
sys.path.insert(0, "/Users/ank/projects/image-reuse-tracker/scanner")
from text_scan import key, subject, mentions_ank, host_of

DATA = "/Users/ank/projects/image-reuse-tracker/data"
STATE = os.path.join(DATA, "searxng_state.json")
TAVILY_STATE = os.path.join(DATA, "text_scan_state.json")
SEARX = "http://localhost:8888/search"
MAX_QUERIES = int(os.environ.get("MAX_QUERIES", "0"))  # 0 = all remaining
ENGINES = "yahoo,mojeek"

def searx(q):
    url = SEARX + "?" + urllib.parse.urlencode({"q": q, "format": "json", "engines": ENGINES})
    return json.load(urllib.request.urlopen(url, timeout=60))

def mentions(r):
    blob = " ".join(str(r.get(k, "")) for k in ("url", "title", "content")).lower()
    return mentions_ank(r) or "ankkumar" in blob.replace(" ", "").replace("_", "").replace("-", "")

try:
    searx("test")
except Exception as e:
    raise SystemExit(f"SearXNG not reachable at {SEARX} ({e}). Start it with: docker start searxng")

state = {"done_keys": [], "hits": {}}
if os.path.exists(STATE):
    state.update(json.load(open(STATE, encoding="utf-8")))
tav = json.load(open(TAVILY_STATE, encoding="utf-8")) if os.path.exists(TAVILY_STATE) else {}
done = set(state["done_keys"]) | set(tav.get("done_keys", [])) | {key(s) for s in tav.get("done", [])}

subjects = {}
for f in json.load(open(os.path.join(DATA, "commons_files.json"), encoding="utf-8")):
    subjects.setdefault(key(f), subject(f))
todo = [k for k in sorted(subjects) if k not in done]
run = todo[:MAX_QUERIES] if MAX_QUERIES else todo
print(f"{len(subjects)} subjects | already searched: {len(set(subjects) & done)} | this run: {len(run)}")
print(f"Estimated time: about {len(run) * 9 // 60} minutes. Safe to stop and rerun - progress is saved.\n")

found = 0
for i, k in enumerate(run, 1):
    s = subjects[k]
    for attempt in range(4):
        try:
            res = searx(f'{s} "Ank Kumar"')
        except (urllib.error.URLError, TimeoutError) as e:
            print(f"  SearXNG error ({e}), waiting 60s")
            time.sleep(60)
            continue
        if not res.get("results") and len(res.get("unresponsive_engines", [])) >= len(ENGINES.split(",")):
            print(f"  engines refusing {[x[0] for x in res['unresponsive_engines']]}, waiting 60s")
            time.sleep(60)
            continue
        break
    new = 0
    for r in res.get("results", []):
        if mentions(r):
            h = state["hits"].setdefault(r["url"], {"domain": host_of(r["url"]), "series": []})
            if r.get("publishedDate") and not h.get("published"):
                h["published"] = str(r["publishedDate"])[:10]
            if s not in h["series"]:
                h["series"].append(s)
                new += 1
    found += new
    state["done_keys"].append(k)
    json.dump(state, open(STATE, "w", encoding="utf-8"), indent=1)
    print(f"[{i}/{len(run)}] +{new} | {s[:80]}")
    time.sleep(8 + random.uniform(0, 2))

print(f"\nDone. New page-subject matches this run: {found} | pages in SearXNG state: {len(state['hits'])}")
