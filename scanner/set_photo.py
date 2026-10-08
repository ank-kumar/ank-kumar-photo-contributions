#!/usr/bin/env python3
"""Add a page to the manual list and/or set which of Ank's photos it shows.
Usage: set_photo.py URL ["photo subject or unique part of it" ...]"""
import json, os, sys, urllib.parse
sys.path.insert(0, "/Users/ank/projects/image-reuse-tracker/scanner")
from text_scan import subject

DATA = "/Users/ank/projects/image-reuse-tracker/data"
if len(sys.argv) < 2:
    raise SystemExit(__doc__)

def clean(u):
    p = urllib.parse.urlsplit(u.strip())
    q = [(k, v) for k, v in urllib.parse.parse_qsl(p.query) if k != "srsltid"]
    return urllib.parse.urlunsplit((p.scheme, p.netloc, p.path, urllib.parse.urlencode(q), ""))

subs = {}
for f in json.load(open(f"{DATA}/commons_files.json", encoding="utf-8")):
    subs[subject(f).lower()] = subject(f)

chosen = []
for w in sys.argv[2:]:
    s = subs.get(w.lower())
    if not s:
        matches = sorted({v for k, v in subs.items() if w.lower() in k})
        if len(matches) != 1:
            print(f"'{w}' matches {len(matches)} subjects - be more specific:")
            for m in matches[:20]:
                print("  ", m)
            raise SystemExit(1)
        s = matches[0]
    chosen.append(s)

mpath = f"{DATA}/manual_state.json"
manual = json.load(open(mpath, encoding="utf-8")) if os.path.exists(mpath) else {"hits": {}}
url = clean(sys.argv[1])
hit = manual["hits"].setdefault(url, {"series": []})
hit["series"] = sorted(set(hit["series"]) | set(chosen))
json.dump(manual, open(mpath, "w", encoding="utf-8"), indent=1)
print(f"{url}\n  -> {'; '.join(hit['series']) or '(no photo set yet)'}")
