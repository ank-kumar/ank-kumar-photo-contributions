#!/usr/bin/env python3
"""Estimate where in the world Ank's photos are seen.
Method: last-12-month views of every Wikipedia article that uses one of his photos, split by each
Wikipedia edition's country mix (Wikimedia's public top-by-country data). Wikimedia does not publish
country data per article or per file, so this is an estimate, not a measurement."""
import csv, json, time, urllib.parse, urllib.request, urllib.error
from collections import defaultdict
from datetime import date, timedelta

DATA = "/Users/ank/projects/image-reuse-tracker/data"
UA = {"User-Agent": "ImageReuseTracker/0.8 (https://commons.wikimedia.org/wiki/User:Ank_gsx) python-urllib"}
AQS = "https://wikimedia.org/api/rest_v1/metrics/pageviews"

def get(url):
    for attempt in range(6):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60))
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            if e.code != 429:
                print(f"  HTTP {e.code} for {url[:100]}")
                return None
            time.sleep(int(e.headers.get("Retry-After", 15)))
        except (urllib.error.URLError, TimeoutError):
            time.sleep(10)
    return None

first_this_month = date.today().replace(day=1)
last_full_day = first_this_month - timedelta(days=1)
START = date(first_this_month.year - 1, first_this_month.month, 1).strftime("%Y%m%d")
END = last_full_day.strftime("%Y%m%d")

# 1) articles using the photos
files = [r["file"] for r in csv.DictReader(open(f"{DATA}/wikimedia_reach.csv", newline="", encoding="utf-8"))]
articles = set()
print(f"Step 1/3: finding the Wikipedia articles that use your {len(files)} photos in use...")
for i in range(0, len(files), 50):
    p = {"action": "query", "format": "json", "prop": "globalusage", "guprop": "namespace",
         "gufilterlocal": "1", "gulimit": "500", "titles": "|".join("File:" + f for f in files[i:i + 50])}
    while True:
        d = get("https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(p))
        if not d:
            break
        for pg in d.get("query", {}).get("pages", {}).values():
            for u in pg.get("globalusage", []):
                if str(u.get("ns")) == "0" and u["wiki"].endswith(("wikipedia.org", "wikivoyage.org")):
                    articles.add((u["wiki"], u["title"]))
        if "continue" not in d:
            break
        p.update(d["continue"])
        time.sleep(0.5)
    time.sleep(1)
print(f"  {len(articles)} articles")

# 2) article views per edition, last 12 full months
views_by_project = defaultdict(int)
print(f"Step 2/3: article views {START}-{END}...")
for n, (wiki, title) in enumerate(sorted(articles), 1):
    t = urllib.parse.quote(title.replace(" ", "_"), safe="")
    d = get(f"{AQS}/per-article/{wiki}/all-access/user/{t}/monthly/{START}/{END}")
    views_by_project[wiki] += sum(x["views"] for x in (d or {}).get("items", []))
    if n % 200 == 0:
        print(f"  {n}/{len(articles)}")
    time.sleep(0.12)

# 3) split each edition's views by its country mix
geo = defaultdict(float)
print(f"Step 3/3: country mix for {sum(1 for v in views_by_project.values() if v)} editions...")
for wiki, v in sorted(views_by_project.items(), key=lambda x: -x[1]):
    if not v:
        continue
    d = get(f"{AQS}/top-by-country/{wiki}/all-access/{last_full_day.year}/{last_full_day.month:02d}")
    countries = ((d or {}).get("items") or [{}])[0].get("countries", [])
    weights = {}
    for c in countries:
        w = c.get("views_ceil") or c.get("views")
        if isinstance(w, str):
            tail = w.split("-")[-1]
            w = int(tail) if tail.isdigit() else 0
        if c.get("country") and c["country"] != "--" and w:
            weights[c["country"]] = float(w)
    total_w = sum(weights.values())
    for cc, w in weights.items():
        geo[cc] += v * w / total_w
    time.sleep(0.3)

total = sum(geo.values())
out = {"method": "Estimated: article views (last 12 months) split by each Wikipedia edition's country mix",
       "period": [START, END], "articles": len(articles), "article_views": sum(views_by_project.values()),
       "countries": {cc: round(v) for cc, v in sorted(geo.items(), key=lambda x: -x[1])}}
json.dump(out, open(f"{DATA}/geo_views.json", "w", encoding="utf-8"), indent=1)

print(f"\nEstimated views by country ({len(geo)} countries, {START}-{END}):")
for cc, v in list(out["countries"].items())[:20]:
    print(f"  {cc}  {v:>12,}  {100 * v / total:5.1f}%")
print(f"\nArticles: {len(articles)} | article views in period: {out['article_views']:,} | written: {DATA}/geo_views.json")
