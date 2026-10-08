#!/usr/bin/env python3
"""Fetch a short caption (first sentence of the Commons description) for every photo the app displays."""
import csv, html, json, os, re, time, urllib.parse, urllib.request

DATA = "/Users/ank/projects/image-reuse-tracker/data"
OUT = os.path.join(DATA, "captions.json")
UA = {"User-Agent": "ImageReuseTracker/0.4 (https://commons.wikimedia.org/wiki/User:Ank_gsx) python-urllib"}

files = set()
with open(os.path.join(DATA, "wikimedia_reach.csv"), newline="", encoding="utf-8") as f:
    files.update(r["file"] for r in csv.DictReader(f))
sf = os.path.join(DATA, "subject_files.json")
if os.path.exists(sf):
    with open(sf, encoding="utf-8") as f:
        files.update(json.load(f).values())
files = sorted(files)

caps = {}
for i in range(0, len(files), 50):
    q = urllib.parse.urlencode({"action": "query", "format": "json", "prop": "imageinfo",
        "iiprop": "extmetadata", "iiextmetadatafilter": "ImageDescription",
        "titles": "|".join("File:" + x for x in files[i:i + 50])})
    req = urllib.request.Request("https://commons.wikimedia.org/w/api.php?" + q, headers=UA)
    d = json.load(urllib.request.urlopen(req, timeout=60))
    for pg in d.get("query", {}).get("pages", {}).values():
        meta = (pg.get("imageinfo") or [{}])[0].get("extmetadata", {})
        text = re.sub(r"<[^>]+>", " ", html.unescape(meta.get("ImageDescription", {}).get("value", "")))
        text = re.sub(r"\s+", " ", text).strip()
        text = re.sub(r"^(English|en)\s*:\s*", "", text)
        text = re.split(r"(?<=[a-z]{3}[.!?])\s+(?=[A-Z])", text)[0].strip().rstrip(".")
        text = re.sub(r"\(?\s*Ank\s*Kumar[^)]*\)?", "", text, flags=re.I)
        text = re.sub(r"\s+", " ", text).strip(" ,;-")
        prose = re.match(r"(The|This|These|A|An|It)\b", text) and re.search(r"\b(is|was|were|are|has|had)\b", text)
        if text and len(text) <= 80 and not prose:
            caps[pg["title"].removeprefix("File:")] = text
    print(f"  {min(i + 50, len(files))}/{len(files)} files")
    time.sleep(1)

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(caps, f, ensure_ascii=False, indent=1)
print(f"Captions: {len(caps)} of {len(files)} files have a Commons description -> {OUT}")
