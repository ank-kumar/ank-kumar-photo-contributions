#!/usr/bin/env python3
"""Wikimedia reach: where Ank's files are used on Wikimedia projects and how often they are viewed."""
import csv, hashlib, json, os, time, urllib.parse, urllib.request, urllib.error
from datetime import date

DATA = "/Users/ank/projects/image-reuse-tracker/data"
OUT = os.path.join(DATA, "wikimedia_reach.csv")
UA = {"User-Agent": "ImageReuseTracker/0.3 (https://commons.wikimedia.org/wiki/User:Ank_gsx) python-urllib"}
API = "https://commons.wikimedia.org/w/api.php"
AQS = ("https://wikimedia.org/api/rest_v1/metrics/mediarequests/per-file/"
       "all-referers/user/{path}/monthly/20150101/{end}")
END = date.today().replace(day=1).strftime("%Y%m%d")
CUTOFF = f"{int(END[:4]) - 1}{END[4:6]}01"

def get(url):
    for attempt in range(6):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60))
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            if e.code != 429:
                raise SystemExit(f"HTTP {e.code}: {e.read().decode()[:300]}")
            wait = int(e.headers.get("Retry-After", 15))
            print(f"  429, waiting {wait}s")
            time.sleep(wait)
    raise SystemExit("Still rate-limited after retries - try again later.")

def file_path(title):
    name = title.removeprefix("File:").replace(" ", "_")
    h = hashlib.md5(name.encode("utf-8")).hexdigest()
    return urllib.parse.quote(f"/wikipedia/commons/{h[0]}/{h[:2]}/{name}", safe="")

# 1) Usage on Wikimedia projects
print("Step 1/2: finding where your files are used on Wikimedia projects...")
p = {"action": "query", "generator": "allimages", "gaiuser": "Ank gsx", "gaisort": "timestamp",
     "gailimit": "50", "prop": "globalusage", "guprop": "namespace", "gufilterlocal": "1",
     "gulimit": "500", "format": "json", "maxlag": "5"}
usage = {}
while True:
    d = get(API + "?" + urllib.parse.urlencode(p))
    for pg in d.get("query", {}).get("pages", {}).values():
        for u in pg.get("globalusage", []):
            usage.setdefault(pg["title"], set()).add((u["wiki"], u["title"], str(u.get("ns"))))
    if "continue" not in d:
        break
    p.update(d["continue"])
    time.sleep(1)
print(f"  files in use: {len(usage)}")

# 2) View counts per used file
print("Step 2/2: fetching view counts (1 request/second)...")
rows = []
for i, (t, us) in enumerate(sorted(usage.items()), 1):
    d = get(AQS.format(path=file_path(t), end=END))
    items = d.get("items", []) if d else []
    total = sum(x["requests"] for x in items)
    last12 = sum(x["requests"] for x in items if x["timestamp"][:8] >= CUTOFF)
    wikis = sorted({w for w, _, _ in us})
    rows.append({"file": t.removeprefix("File:"), "views_total": total, "views_last_12m": last12,
                 "wikis": len(wikis), "article_pages": sum(1 for _, _, ns in us if ns == "0"),
                 "used_on": " | ".join(wikis)})
    if i % 50 == 0:
        print(f"  {i}/{len(usage)} files | views so far: {sum(r['views_total'] for r in rows):,}")
    time.sleep(1)

rows.sort(key=lambda r: -r["views_total"])
with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)

all_wikis = {w for us in usage.values() for w, _, _ in us}
langs = {w.split(".")[0] for w in all_wikis if w.endswith("wikipedia.org")}
print("\n=== WIKIMEDIA REACH ===")
print(f"Files used on Wikimedia projects: {len(rows)}")
print(f"Distinct wikis: {len(all_wikis)} | Wikipedia language editions: {len(langs)}")
print(f"Article pages illustrated: {sum(r['article_pages'] for r in rows):,}")
print(f"Views since Jan 2015 (people, not bots): {sum(r['views_total'] for r in rows):,}")
print(f"Views in the last 12 months: {sum(r['views_last_12m'] for r in rows):,}")
print("\nTop 10 files by views:")
for r in rows[:10]:
    print(f"  {r['views_total']:>12,}  {r['file'][:80]}")
print(f"\nCSV written: {OUT}")
