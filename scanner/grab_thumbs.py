#!/usr/bin/env python3
"""For every web page in the reach list, save a thumbnail of the image that carries the 'Ank Kumar' credit.
Order of evidence on each page:
  1. hand-checked image in data/page_thumbs_manual.tsv
  2. an <img> whose filename, alt or title contains 'Ank Kumar'
  3. the <img> closest before the 'Ank Kumar' caption/credit text
  4. YouTube: the video's own thumbnail
  5. the page's share image (og:image) whose filename contains 'Ank Kumar'
Pages that can't be read keep the site logo and are listed in data/page_thumbs_todo.txt."""
import csv, hashlib, html as H, io, json, os, re, sys, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageOps

ROOT = "/Users/ank/projects/image-reuse-tracker"
DATA, OUT = f"{ROOT}/data", f"{ROOT}/docs/thumbs"
MAP, MANUAL, TODO = f"{DATA}/page_thumbs.json", f"{DATA}/page_thumbs_manual.tsv", f"{DATA}/page_thumbs_todo.txt"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"
CREDIT = re.compile(r"ank[\s_%20.+,-]*kumar", re.I)
SKIP = ("logo", "icon", "avatar", "sprite", "pixel", "gravatar", "emoji", "badge", "flag", "favicon")

def get(url, referer=None):
    h = {"User-Agent": UA, "Accept-Language": "en"}
    if referer:
        h["Referer"] = referer
    return urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=25).read()

def src_of(tag):
    for a in ("data-src", "data-lazy-src", "data-original", "src"):
        m = re.search(r'\s' + a + r'\s*=\s*["\']([^"\']+)', tag, re.I)
        if m and not m.group(1).startswith("data:"):
            return H.unescape(m.group(1))
    m = re.search(r'srcset\s*=\s*["\']([^"\'\s,]+)', tag, re.I)
    return H.unescape(m.group(1)) if m else None

def pick(html, page):
    imgs = []
    for m in re.finditer(r"<img\b[^>]*>", html, re.I):
        s = src_of(m.group(0))
        if s and not s.lower().split("?")[0].endswith(".svg") and not any(k in s.lower() for k in SKIP):
            imgs.append((m.start(), s, m.group(0)))
    for pos, s, tag in imgs:                                  # 2. credit in the image itself
        if CREDIT.search(urllib.parse.unquote(s)) or CREDIT.search(tag):
            return s, "image named/captioned Ank Kumar"
    text_credits = [m.start() for m in CREDIT.finditer(html)]
    best, dist = None, 10 ** 9
    for c in text_credits:                                    # 3. image just before the caption
        for pos, s, tag in imgs:
            if pos <= c and c - pos < dist and c - pos < 5000:
                best, dist = s, c - pos
    if best:
        return best, "image above the Ank Kumar caption"
    m = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)', html, re.I) or \
        re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']', html, re.I)
    if m and CREDIT.search(urllib.parse.unquote(m.group(1))):  # 5.
        return H.unescape(m.group(1)), "share image named Ank Kumar"
    return None, "no image found next to the credit"

def youtube_id(url):
    m = re.search(r"(?:v=|/shorts/|youtu\.be/)([A-Za-z0-9_-]{11})", url)
    return m.group(1) if m else None

def save(page, img_url):
    im = Image.open(io.BytesIO(get(img_url, referer=page))).convert("RGB")
    if im.width < 120 or im.height < 80:
        raise ValueError("image too small")
    name = hashlib.sha1(page.encode()).hexdigest()[:14] + ".jpg"
    ImageOps.fit(im, (240, 160)).save(f"{OUT}/{name}", "JPEG", quality=82)
    return f"thumbs/{name}"

def work(job):
    page, manual = job
    try:
        if manual:
            img, why = manual, "checked by hand"
        elif youtube_id(page):
            img, why = f"https://i.ytimg.com/vi/{youtube_id(page)}/hqdefault.jpg", "YouTube thumbnail"
        else:
            img, why = pick(get(page).decode("utf-8", "ignore"), page)
            if not img:
                return page, None, why
            img = urllib.parse.urljoin(page, img)
        return page, save(page, img), why
    except Exception as e:
        return page, None, f"could not read ({str(e)[:60]})"

os.makedirs(OUT, exist_ok=True)
done = json.load(open(MAP)) if os.path.exists(MAP) else {}
manual = {}
if os.path.exists(MANUAL):
    for line in open(MANUAL, encoding="utf-8"):
        if line.strip() and not line.startswith("#") and "\t" in line:
            p, i = line.rstrip("\n").split("\t", 1)
            manual[p.strip()] = i.strip()
pages = [r["url"] for r in csv.DictReader(open(f"{DATA}/text_scan_results.csv", encoding="utf-8")) if r["bucket"] == "reuse"]
redo = "--all" in sys.argv
jobs = [(p, manual.get(p)) for p in pages if redo or p not in done or p in manual]
print(f"Checking {len(jobs)} pages for the image beside your credit...")
todo = []
with ThreadPoolExecutor(max_workers=8) as ex:
    for page, path, why in ex.map(work, jobs):
        if path:
            done[page] = path
            print(f"  ok    {why:<34} {page[:90]}")
        else:
            todo.append(f"{page}\t{why}")
            print(f"  --    {why:<34} {page[:90]}")
json.dump(done, open(MAP, "w"), indent=1)
open(TODO, "w").write("\n".join(todo) + "\n")
print(f"\n{sum(1 for p in pages if p in done)} of {len(pages)} pages have their image. "
      f"{len(todo)} still need one: listed in data/page_thumbs_todo.txt")
