#!/usr/bin/env python3
"""For every web page in the reach list, save a thumbnail of the image Ank's photo appears as.
Order of evidence on each page:
  1. hand-checked image in data/page_thumbs_manual.tsv
  2. an <img> whose filename matches one of Ank's Commons files
  3. an <img> whose filename, alt or title carries the credit (Ank Kumar / Infosys Limited)
  4. the <img> closest before the credit text
  5. YouTube: the video's own thumbnail
  6. PDF pages: the largest JPEG embedded in the document
  7. no credit anywhere: the page's main image anyway (the photo is Ank's either way)
Side lists written next to the map:
  data/page_no_credit.txt    - page uses an image but carries no credit for Ank (to chase later)
  data/page_credit_pages.txt - page IS a credits/attribution list; the photo sits on another page
  data/page_thumbs_todo.txt  - page could not be read at all
"""
import csv, hashlib, html as H, io, json, os, re, sys, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageOps

ROOT = "/Users/ank/projects/image-reuse-tracker"
DATA, OUT = f"{ROOT}/data", f"{ROOT}/docs/thumbs"
MAP, MANUAL, TODO = f"{DATA}/page_thumbs.json", f"{DATA}/page_thumbs_manual.tsv", f"{DATA}/page_thumbs_todo.txt"
NOCREDIT, CREDITPAGES = f"{DATA}/page_no_credit.txt", f"{DATA}/page_credit_pages.txt"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"

SEP = r"[\s_%20+.,\-]*"
NAME = rf"ank{SEP}kumar"
BYLINE = rf"(?:{NAME}|infosys{SEP}limited|infosys{SEP}ltd|nomad[_\s-]?gsx)"
CREDIT = re.compile(NAME, re.I)            # the name itself
CREDIT_ANY = re.compile(BYLINE, re.I)      # name or the Infosys byline he shot under
SKIP = ("logo", "icon", "avatar", "sprite", "pixel", "gravatar", "emoji", "badge", "flag", "favicon")
# Pages that are themselves a list of picture credits: the photo lives on some other page of the site.
CREDIT_PAGE = re.compile(r"(bildnachweis|fotoverantwoording|bildkreditt|attribution|/credits?\b|"
                         r"impressum|legal-notice|acknowledg|photo-credit)", re.I)

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

def norm(name):
    name = urllib.parse.unquote(name.split("?")[0].rsplit("/", 1)[-1])
    name = re.sub(r"^\d+px-", "", name).replace("_", " ")
    return re.sub(r"\.(jpe?g|png|webp)(\.(jpe?g|png|webp))?$", "", name, flags=re.I).strip().lower()

MINE = {norm(f) for f in json.load(open(f"{DATA}/commons_files.json", encoding="utf-8"))}

def wm_fix(u):
    m = re.match(r"(https?://upload\.wikimedia\.org/.+/thumb/.+?/)(\d+)px-([^/?]+)", u)
    return f"{m.group(1)}500px-{m.group(3)}" if m else u

def all_imgs(html, page):
    imgs = []
    for m in re.finditer(r"<img\b[^>]*>", html, re.I):
        s = src_of(m.group(0))
        if s and not s.lower().split("?")[0].endswith(".svg") and not any(k in s.lower() for k in SKIP):
            imgs.append((m.start(), urllib.parse.urljoin(page, s), m.group(0)))
    for m in re.finditer(r'(?:href|content)\s*=\s*["\']([^"\']*upload\.wikimedia\.org[^"\']+)', html, re.I):
        imgs.append((m.start(), H.unescape(m.group(1)), ""))
    return imgs

def og_image(html, page):
    m = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)', html, re.I) or \
        re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']', html, re.I)
    return urllib.parse.urljoin(page, H.unescape(m.group(1))) if m else None

def candidates(html, page):
    """Images backed by evidence that the photo is Ank's."""
    imgs = all_imgs(html, page)
    out = []
    for pos, s, tag in imgs:                                   # exact: one of Ank's Commons files
        if norm(s) in MINE:
            out.append((wm_fix(s), "your Commons file"))
    for pos, s, tag in imgs:                                   # named or captioned with the credit
        if CREDIT_ANY.search(urllib.parse.unquote(s)) or CREDIT_ANY.search(tag):
            out.append((wm_fix(s), "image named/captioned with your credit"))
    credits = [m.start() for m in CREDIT_ANY.finditer(html)]
    near = sorted(((c - pos, s) for c in credits for pos, s, tag in imgs if 0 <= c - pos < 5000))
    out += [(wm_fix(s), "image above your credit") for d, s in near[:4]]
    og = og_image(html, page)
    if og and (CREDIT_ANY.search(urllib.parse.unquote(og)) or norm(og) in MINE):
        out.append((og, "share image is your photo"))
    seen, uniq = set(), []
    for u, why in out:
        if u not in seen:
            seen.add(u); uniq.append((u, why))
    return uniq

def fallback(html, page):
    """No credit on the page. The photo is still Ank's, so take the page's main image."""
    out = []
    og = og_image(html, page)
    if og and not any(k in og.lower() for k in SKIP):
        out.append((og, "no credit: share image"))
    for pos, s, tag in all_imgs(html, page):
        out.append((s, "no credit: main image"))
    seen, uniq = set(), []
    for u, why in out:
        if u not in seen:
            seen.add(u); uniq.append((u, why))
    return uniq[:6]

def pdf_jpegs(data):
    """Pull embedded JPEG (DCTDecode) images out of a PDF with no external library, biggest first."""
    out = []
    for m in re.finditer(rb"/Subtype\s*/Image\b", data):
        seg = data[m.start():m.start() + 4000]
        if b"/DCTDecode" not in seg:
            continue                                   # Flate/JPX images need a codec; skip
        s = data.find(b"stream", m.start())
        if s < 0:
            continue
        s += 6
        while s < len(data) and data[s] in (13, 10):
            s += 1
        e = data.find(b"endstream", s)
        if e > s:
            out.append(data[s:e])
    return sorted(out, key=len, reverse=True)[:5]

def youtube_id(url):
    m = re.search(r"(?:v=|/shorts/|youtu\.be/)([A-Za-z0-9_-]{11})", url)
    return m.group(1) if m else None

def store(page, raw):
    im = Image.open(io.BytesIO(raw)).convert("RGB")
    if im.width < 120 or im.height < 80:
        raise ValueError("image too small")
    name = hashlib.sha1(page.encode()).hexdigest()[:14] + ".jpg"
    ImageOps.fit(im, (240, 160)).save(f"{OUT}/{name}", "JPEG", quality=82)
    return f"thumbs/{name}"

def save(page, img_url):
    return store(page, get(img_url, referer=page))

def work(job):
    page, manual = job
    try:
        if manual:
            return page, save(page, manual), "checked by hand", None
        if youtube_id(page):
            return page, save(page, f"https://i.ytimg.com/vi/{youtube_id(page)}/hqdefault.jpg"), "YouTube thumbnail", None

        raw = get(page)
        if raw[:4] == b"%PDF" or page.lower().split("?")[0].endswith(".pdf"):
            jpegs = pdf_jpegs(raw)
            if not jpegs:
                return page, None, "PDF: no extractable JPEG inside", None
            last = ""
            for j in jpegs:
                try:
                    return page, store(page, j), "largest image in the PDF", None
                except Exception as e:
                    last = str(e)[:50]
            return page, None, f"PDF images found but none usable ({last})", None

        html = raw.decode("utf-8", "ignore")
        cands, flag = candidates(html, page), None
        if not cands:
            flag = "creditpage" if CREDIT_PAGE.search(page) else "nocredit"
            cands = fallback(html, page)
        if not cands:
            return page, None, "no image on the page at all", flag
        last = ""
        for img, why in cands:
            try:
                return page, store(page, get(img, referer=page)), why, flag
            except Exception as e:
                last = str(e)[:50]
        return page, None, f"images found but none loaded ({last})", flag
    except Exception as e:
        return page, None, f"could not read ({str(e)[:60]})", None

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
print(f"Checking {len(jobs)} pages for your image...")
todo, nocredit, creditpages = [], [], []
with ThreadPoolExecutor(max_workers=8) as ex:
    for page, path, why, flag in ex.map(work, jobs):
        if flag == "nocredit":
            nocredit.append(page)
        elif flag == "creditpage":
            creditpages.append(page)
        if path:
            done[page] = path
            print(f"  ok    {why:<36} {page[:88]}")
        else:
            todo.append(f"{page}\t{why}")
            print(f"  --    {why:<36} {page[:88]}")
json.dump(done, open(MAP, "w"), indent=1)
open(TODO, "w").write("\n".join(todo) + "\n")
if not redo:   # keep earlier findings when only new pages were checked
    for f, lst in ((NOCREDIT, nocredit), (CREDITPAGES, creditpages)):
        old = [l.strip() for l in open(f, encoding="utf-8")] if os.path.exists(f) else []
        lst[:] = sorted(set(x for x in old if x and not x.startswith("#")) | set(lst))
open(NOCREDIT, "w").write("# Pages using your photo with no credit to you anywhere on the page.\n"
                          + "\n".join(sorted(set(nocredit))) + "\n")
open(CREDITPAGES, "w").write("# Pages that are themselves a picture-credit list; your photo sits on another page.\n"
                             + "\n".join(sorted(set(creditpages))) + "\n")
print(f"\n{sum(1 for p in pages if p in done)} of {len(pages)} pages have their image. "
      f"{len(todo)} still need one: listed in data/page_thumbs_todo.txt")
print(f"{len(set(nocredit))} pages carry no credit to you: data/page_no_credit.txt")
print(f"{len(set(creditpages))} pages are credit lists: data/page_credit_pages.txt")
