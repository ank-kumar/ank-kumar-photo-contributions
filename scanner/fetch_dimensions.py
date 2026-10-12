#!/usr/bin/env python3
"""Fetch pixel dimensions for every Commons file, so the gallery can lay photographs out
at their true shape instead of cropping them all to 3:2.

Writes data/dimensions.json: {filename: [width, height]}
Cached: re-running only fetches files that are missing.
"""
import json, os, time, urllib.parse, urllib.request

DATA = "/Users/ank/projects/image-reuse-tracker/data"
OUT = f"{DATA}/dimensions.json"
UA = {"User-Agent": "ImageReuseTracker/0.8 (https://commons.wikimedia.org/wiki/User:Ank_gsx) python-urllib"}

def get(params):
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params)
    for attempt in range(4):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60))
        except Exception:
            if attempt == 3:
                raise
            time.sleep(3 * (attempt + 1))

files = json.load(open(f"{DATA}/commons_files.json", encoding="utf-8"))
dims = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}
todo = [f for f in files if f not in dims]
print(f"{len(dims):,} already known, fetching {len(todo):,}...")

for i in range(0, len(todo), 50):
    p = {"action": "query", "format": "json", "prop": "imageinfo", "iiprop": "dimensions",
         "titles": "|".join("File:" + f for f in todo[i:i + 50])}
    d = get(p)
    for pg in d.get("query", {}).get("pages", {}).values():
        ii = (pg.get("imageinfo") or [{}])[0]
        if ii.get("width") and ii.get("height"):
            dims[pg["title"].removeprefix("File:")] = [ii["width"], ii["height"]]
    if (i // 50) % 20 == 19 or i + 50 >= len(todo):
        print(f"  {min(i + 50, len(todo)):,}/{len(todo):,}")
        json.dump(dims, open(OUT, "w", encoding="utf-8"))      # checkpoint, so a crash costs nothing
    time.sleep(0.4)

json.dump(dims, open(OUT, "w", encoding="utf-8"))
land = sum(1 for w, h in dims.values() if w > h * 1.15)
port = sum(1 for w, h in dims.values() if h > w * 1.15)
print(f"\n{len(dims):,} dimensions saved to data/dimensions.json")
print(f"  landscape {land:,} | portrait {port:,} | square-ish {len(dims) - land - port:,}")
