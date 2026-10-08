#!/usr/bin/env python3
"""Inventory for the moving wall: every Commons upload, plus Flickr uploads if FLICKR_API_KEY is set."""
import json, os, time, urllib.parse, urllib.request, urllib.error

DATA = "/Users/ank/projects/image-reuse-tracker/data"
UA = {"User-Agent": "ImageReuseTracker/0.5 (https://commons.wikimedia.org/wiki/User:Ank_gsx) python-urllib"}

def get(url):
    for attempt in range(5):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60))
        except urllib.error.HTTPError as e:
            if e.code not in (429, 503):
                raise SystemExit(f"HTTP {e.code}: {e.read().decode()[:200]}")
            wait = int(e.headers.get("Retry-After", 15))
            print(f"  {e.code}, waiting {wait}s")
            time.sleep(wait)
    raise SystemExit("Still rate-limited after retries - try again later.")

# --- Commons: every upload by Ank gsx ---
p = {"action": "query", "list": "allimages", "aiuser": "Ank gsx", "aisort": "timestamp",
     "ailimit": "500", "aiprop": "timestamp", "format": "json", "maxlag": "5"}
titles = []
while True:
    d = get("https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(p))
    titles += [x["title"].removeprefix("File:") for x in d["query"]["allimages"]]
    print(f"  Commons: {len(titles)} files")
    if "continue" not in d:
        break
    p.update(d["continue"])
    time.sleep(1)
with open(f"{DATA}/commons_files.json", "w", encoding="utf-8") as f:
    json.dump(titles, f, ensure_ascii=False)
print(f"Commons inventory: {len(titles)} files -> {DATA}/commons_files.json")

# --- Flickr: public photostream of nomad_gsx (needs a non-commercial API key) ---
key = os.environ.get("FLICKR_API_KEY")
if not key:
    print("FLICKR_API_KEY not set - skipping Flickr (the wall will use Commons only).")
else:
    api = "https://www.flickr.com/services/rest/?"
    base = {"api_key": key, "format": "json", "nojsoncallback": "1"}
    u = get(api + urllib.parse.urlencode({**base, "method": "flickr.urls.lookupUser",
                                          "url": "https://www.flickr.com/photos/nomad_gsx/"}))
    if u.get("stat") != "ok":
        print(f"Flickr error: {u.get('message')} - skipping Flickr.")
    else:
        nsid, photos, page = u["user"]["id"], [], 1
        while True:
            d = get(api + urllib.parse.urlencode({**base, "method": "flickr.people.getPublicPhotos",
                    "user_id": nsid, "extras": "url_z,url_m", "per_page": "500", "page": page}))
            if d.get("stat") != "ok":
                print(f"Flickr error: {d.get('message')}")
                break
            for ph in d["photos"]["photo"]:
                img = ph.get("url_z") or ph.get("url_m")
                if img:
                    photos.append({"title": ph.get("title", ""), "img": img,
                                   "link": f"https://www.flickr.com/photos/nomad_gsx/{ph['id']}"})
            print(f"  Flickr: {len(photos)} photos (page {page}/{d['photos']['pages']})")
            if page >= d["photos"]["pages"]:
                break
            page += 1
            time.sleep(1)
        with open(f"{DATA}/flickr_photos.json", "w", encoding="utf-8") as f:
            json.dump(photos, f, ensure_ascii=False)
        print(f"Flickr inventory: {len(photos)} photos -> {DATA}/flickr_photos.json")
