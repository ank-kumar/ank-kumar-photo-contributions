#!/usr/bin/env python3
"""For manually added pages, detect which of Ank's Commons files each page shows (by filename in its HTML)."""
import json, re, sys, time, urllib.parse, urllib.request, urllib.error
sys.path.insert(0, "/Users/ank/projects/image-reuse-tracker/scanner")
from text_scan import subject

DATA = "/Users/ank/projects/image-reuse-tracker/data"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh) ImageReuseTracker/0.5 (personal photo-credit check)"}
RX = [re.compile(r"upload\.wikimedia\.org/wikipedia/commons/(?:thumb/)?[0-9a-f]/[0-9a-f]{2}/([^/\"'?#\s<>]+)", re.I),
      re.compile(r"commons\.wikimedia\.org/wiki/File:([^\"'?#\s<>]+)", re.I)]

mine = {f.replace(" ", "_").lower(): f for f in json.load(open(f"{DATA}/commons_files.json", encoding="utf-8"))}
mpath = f"{DATA}/manual_state.json"
manual = json.load(open(mpath, encoding="utf-8"))

for url, hit in manual["hits"].items():
    if hit.get("series"):
        continue
    try:
        page = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read().decode("utf-8", "ignore")
    except Exception as e:
        print(f"  blocked   {url}  ({getattr(e, 'code', None) or type(e).__name__})")
        continue
    found = set()
    for rx in RX:
        for m in rx.findall(page):
            name = urllib.parse.unquote(m).replace(" ", "_").lower()
            if name in mine:
                found.add(mine[name])
    if found:
        hit["series"] = sorted({subject(f) for f in found})
        print(f"  matched   {url}\n            -> {'; '.join(hit['series'])}")
    else:
        print(f"  no match  {url}")
    time.sleep(2)

json.dump(manual, open(mpath, "w", encoding="utf-8"), indent=1)
print(f"\nPages with a photo identified: {sum(1 for h in manual['hits'].values() if h.get('series'))} of {len(manual['hits'])}")
