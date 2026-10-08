#!/usr/bin/env python3
"""Verify claimed book credits via the Google Books API and discover new ones."""
import csv, json, os, time, urllib.parse, urllib.request

OUT = "/Users/ank/projects/image-reuse-tracker/data/books.csv"
UA = {"User-Agent": "ImageReuseTracker/0.2 (https://commons.wikimedia.org/wiki/User:Ank_gsx)"}
API = "https://www.googleapis.com/books/v1/volumes"
KEY = os.environ["GOOGLE_BOOKS_KEY"]
CLAIMED = ["A2jFEAAAQBAJ", "eLSeEAAAQBAJ", "uxqiEQAAQBAJ", "2dpOEQAAQBAJ", "UQSGEQAAQBAJ",
           "vHjZEQAAQBAJ", "Zm3VEQAAQBAJ", "1nTPEQAAQBAJ", "t3POEAAAQBAJ", "QRU4EQAAQBAJ",
           "cLg-EAAAQBAJ", "YpqcEAAAQBAJ", "YicaEQAAQBAJ", "1O-aEAAAQBAJ", "QrGmEAAAQBAJ",
           "FpJiEQAAQBAJ", "QBVGEQAAQBAJ", "ZArdEQAAQBAJ", "nqVFEQAAQBAJ", "6MYLEgAAQBAJ"]
CREDIT_HINTS = ("commons", "wikimedia", "cc by", "cc-by", "creative commons", "ank kumar")

def get(url):
    for attempt in range(4):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(url + ("&" if "?" in url else "?") + "key=" + KEY, headers=UA), timeout=30))
        except urllib.error.HTTPError as e:
            if e.code not in (429, 503):
                raise SystemExit(f"Google Books error {e.code}: {e.read().decode()[:400]}")
            time.sleep(5 * (attempt + 1))
    raise SystemExit("Google Books API kept rate-limiting; try again later.")

def info(v):
    vi = v.get("volumeInfo", {})
    return {"title": vi.get("title", "") + (": " + vi["subtitle"] if vi.get("subtitle") else ""),
            "authors": ", ".join(vi.get("authors", [])), "publisher": vi.get("publisher", ""),
            "year": vi.get("publishedDate", "")[:4], "link": vi.get("canonicalVolumeLink", "")}

# 1) Full-text search for the credit across Google Books
found = {}
for start in range(0, 200, 40):
    q = urllib.parse.urlencode({"q": '"Ank Kumar"', "startIndex": start, "maxResults": 40})
    d = get(f"{API}?{q}")
    for v in d.get("items", []):
        snip = v.get("searchInfo", {}).get("textSnippet", "")
        found[v["id"]] = (v, snip)
    print(f"full-text search: {len(found)} books so far")
    if len(d.get("items", [])) < 40:
        break
    time.sleep(1)

# 2) Check every claimed book, then add newly discovered ones
rows = []
for vid in CLAIMED:
    v = found[vid][0] if vid in found else get(f"{API}/{vid}")
    snip = found.get(vid, (None, ""))[1]
    rows.append({"id": vid, **info(v), "source": "PDF claim",
                 "credit_found": "yes" if vid in found else "not in search",
                 "snippet": snip})
    time.sleep(1)
for vid, (v, snip) in found.items():
    if vid in CLAIMED:
        continue
    hint = any(h in snip.lower() for h in CREDIT_HINTS[:-1])
    rows.append({"id": vid, **info(v), "source": "new discovery",
                 "credit_found": "yes (credit-like)" if hint else "name match only",
                 "snippet": snip})

with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader(); w.writerows(rows)

claimed = [r for r in rows if r["source"] == "PDF claim"]
print(f"\nClaimed books: {len(claimed)} | credit found in full-text search: "
      f"{sum(r['credit_found'] == 'yes' for r in claimed)}")
print(f"New books with credit-like snippet: "
      f"{sum(r['credit_found'] == 'yes (credit-like)' for r in rows)}")
for r in claimed:
    print(f"  [{r['credit_found']:>13}] {r['title'][:55]} | {r['publisher']} {r['year']}")
print(f"\nCSV written: {OUT}")
