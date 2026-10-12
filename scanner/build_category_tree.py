#!/usr/bin/env python3
"""Walk the Commons category tree upward from the categories on Ank's photos.

Commons contributors have spent years categorising these files; the hierarchy above each
category (Salzburg -> Cities in Austria -> Austria) is the taxonomy. This fetches that
hierarchy so topics can be derived from it instead of from guessed keywords.
Writes data/category_parents.json: {category: [parent, ...]}
"""
import json, time, urllib.parse, urllib.request

DATA = "/Users/ank/projects/image-reuse-tracker/data"
UA = {"User-Agent": "ImageReuseTracker/0.8 (https://commons.wikimedia.org/wiki/User:Ank_gsx) python-urllib"}
LEVELS = 4          # how far up the tree to climb
MAX_PER_LEVEL = 6000

def get(params):
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params)
    for attempt in range(4):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60))
        except Exception as e:
            if attempt == 3:
                raise
            time.sleep(3 * (attempt + 1))

def parents_of(names):
    """Parent categories for a batch of category names."""
    out = {}
    for i in range(0, len(names), 50):
        chunk = names[i:i + 50]
        p = {"action": "query", "format": "json", "prop": "categories", "cllimit": "max",
             "clshow": "!hidden", "titles": "|".join("Category:" + c for c in chunk)}
        while True:
            d = get(p)
            for pg in d.get("query", {}).get("pages", {}).values():
                name = pg["title"].removeprefix("Category:")
                out.setdefault(name, []).extend(
                    c["title"].removeprefix("Category:") for c in pg.get("categories", []))
            if "continue" not in d:
                break
            p.update(d["continue"])
            time.sleep(0.5)
        if (i // 50) % 20 == 19:
            print(f"    {min(i + 50, len(names))}/{len(names)}")
        time.sleep(0.5)
    return out

file_cats = json.load(open(f"{DATA}/commons_categories.json", encoding="utf-8"))
tree, frontier = {}, sorted({c for v in file_cats.values() for c in v})
print(f"Starting from {len(frontier):,} categories on your photos.")
for level in range(LEVELS):
    frontier = [c for c in frontier if c not in tree][:MAX_PER_LEVEL]
    if not frontier:
        break
    print(f"Level {level + 1}: fetching parents of {len(frontier):,} categories...")
    got = parents_of(frontier)
    for c in frontier:
        tree[c] = got.get(c, [])
    frontier = sorted({p for ps in got.values() for p in ps})

json.dump(tree, open(f"{DATA}/category_parents.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print(f"\nSaved {len(tree):,} categories with "
      f"{sum(len(v) for v in tree.values()):,} parent links to data/category_parents.json")
