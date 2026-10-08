#!/usr/bin/env python3
"""Map each photo subject in the master CSV to one representative Commons file (for thumbnails)."""
import csv, json, os, sys
sys.path.insert(0, "/Users/ank/projects/image-reuse-tracker/scanner")
from text_scan import commons_titles, key, subject

DATA = "/Users/ank/projects/image-reuse-tracker/data"
CSV_PATH = os.path.join(DATA, "text_scan_results.csv")
OUT = os.path.join(DATA, "subject_files.json")

print("Fetching file list from Commons...")
by_key = {}
for t in sorted(commons_titles()):
    fn = t.removeprefix("File:")
    by_key.setdefault(key(t), fn)
    by_key.setdefault(key(subject(t)), fn)

subjects = set()
with open(CSV_PATH, newline="", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        subjects.update(s.strip() for s in r["subjects"].split("|") if s.strip())

mapping = {s: by_key[key(s)] for s in subjects if key(s) in by_key}
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(mapping, f, ensure_ascii=False, indent=1)
print(f"Subjects in CSV: {len(subjects)} | matched to a Commons file: {len(mapping)}")
print(f"Written: {OUT}")
