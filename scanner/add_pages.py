#!/usr/bin/env python3
"""Add pages found by hand to the manual list. Usage: add_pages.py URL [URL ...]"""
import csv, json, os, sys, urllib.parse

DATA = "/Users/ank/projects/image-reuse-tracker/data"

def clean(u):
    p = urllib.parse.urlsplit(u.strip())
    q = [(k, v) for k, v in urllib.parse.parse_qsl(p.query) if k != "srsltid"]
    return urllib.parse.urlunsplit((p.scheme, p.netloc, p.path, urllib.parse.urlencode(q), ""))

def norm(u):
    p = urllib.parse.urlsplit(clean(u))
    return p.netloc.lower().removeprefix("www.") + p.path.rstrip("/").lower() + ("?" + p.query if p.query else "")

with open(f"{DATA}/text_scan_results.csv", newline="", encoding="utf-8") as f:
    known = {norm(r["url"]) for r in csv.DictReader(f)}
mpath = f"{DATA}/manual_state.json"
manual = json.load(open(mpath, encoding="utf-8")) if os.path.exists(mpath) else {"hits": {}}
in_manual = {norm(u) for u in manual["hits"]}

added = 0
for u in dict.fromkeys(clean(x) for x in sys.argv[1:]):
    if norm(u) in known:
        print(f"  already covered: {u}")
    elif norm(u) in in_manual:
        print(f"  already in manual list: {u}")
    else:
        manual["hits"][u] = {"series": []}
        in_manual.add(norm(u))
        added += 1
        print(f"  ADDED: {u}")
json.dump(manual, open(mpath, "w", encoding="utf-8"), indent=1)
print(f"\nManual list: {added} added, {len(manual['hits'])} total")
