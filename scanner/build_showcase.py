#!/usr/bin/env python3
"""Build the public showcase page (static HTML). v3: whole collection, Random default, grouped topic filter."""
import csv, html, json, os, re, urllib.parse
from collections import Counter, OrderedDict
from datetime import date

ROOT = "/Users/ank/projects/image-reuse-tracker"
DATA = f"{ROOT}/data"
OUT = f"{ROOT}/docs/index.html"
COMMONS_USER = "https://commons.wikimedia.org/wiki/User:Ank_gsx"
FLICKR = "https://www.flickr.com/photos/nomad_gsx"
HERO_IMG = "hero.jpg"
HERO_LINK = "https://www.flickr.com/photos/nomad_gsx/51846955840"
HERO_TITLE = "Alpine golden hour from the Schilthorn, Bernese Oberland, Switzerland, 2015"
COPY = "© 2026, Ank Kumar, All Rights Reserved"
FONT = 'Aptos,"Aptos Display","Segoe UI",system-ui,-apple-system,sans-serif'
REGIONS = ["Europe", "Asia", "Australia", "Switzerland", "Zurich", "Germany", "The UK", "Scotland", "France", "Spain",
           "Italy", "Vatican", "Holland", "Belgium", "Czech Republic", "Hungary", "Turkey", "India", "Hong Kong",
           "Macau", "Singapore"]
SUBJECTS = ["Airplanes", "Military", "Automobiles", "Sports", "Architecture", "Museums", "Art", "Movies", "Comics",
            "Music", "Nature", "Trains & transport", "Religion"]
TOPIC_ORDER = REGIONS + SUBJECTS
FEATURED = OrderedDict([
    ("smithsonianmag.com", "Smithsonian Magazine"), ("rollingstone.co.uk", "Rolling Stone UK"),
    ("sfexaminer.com", "San Francisco Examiner"), ("ethz.ch", "ETH Zurich"), ("dezeen.com", "Dezeen"),
    ("domusweb.it", "Domus"), ("archinect.com", "Archinect"), ("simpleflying.com", "Simple Flying"),
    ("migflug.com", "MiGFlug"), ("samford.edu", "Samford University"), ("americamagazine.org", "America Magazine"),
    ("ewtnnews.com", "EWTN News"), ("ncronline.org", "National Catholic Reporter"), ("risk.net", "Risk.net"),
    ("economicsobservatory.com", "Economics Observatory"), ("allafrica.com", "AllAfrica"),
    ("tripadvisor.com", "Tripadvisor"), ("getyourguide.com", "GetYourGuide"), ("klook.com", "Klook"),
    ("celebritycruises.com", "Celebrity Cruises"), ("travelandleisureasia.com", "Travel + Leisure Asia"),
    ("kids.kiddle.co", "Kiddle encyclopedia"), ("structurae.net", "Structurae"),
    ("brusselstimes.com", "The Brussels Times"), ("medium.com", "Medium"),
])

def esc(s):
    return html.escape(s or "")

def file_url(name, width=500):
    return ("https://commons.wikimedia.org/wiki/Special:FilePath/"
            + urllib.parse.quote(name.replace(" ", "_")) + f"?width={width}")

def file_page(name):
    return "https://commons.wikimedia.org/wiki/File:" + urllib.parse.quote(name.replace(" ", "_"))

def nice_title(fn):
    t = re.sub(r"\.(jpe?g|png|tiff?)$", "", fn, flags=re.I)
    t = re.sub(r"\s+\d{1,3}$", "", t)
    t = re.sub(r"\(?\s*Ank\s*Kumar[^)]*\)?", "", t, flags=re.I)
    return re.sub(r"\s+", " ", t).strip(" ,-")

def read_csv(name):
    with open(f"{DATA}/{name}", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def read_json(name, default):
    p = f"{DATA}/{name}"
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else default

def millions(n):
    return f"{n / 1e6:.1f} million"

# ---------- data ----------
captions, topics = read_json("captions.json", {}), read_json("topics.json", {})
reach = read_csv("wikimedia_reach.csv")
for r in reach:
    r["views_total"], r["views_last_12m"] = int(r["views_total"]), int(r["views_last_12m"])
reach_by = {r["file"]: r for r in reach}
files = list(dict.fromkeys(read_json("commons_files.json", []) + list(reach_by)))
TOTAL_FILES = len(files)
total_views = sum(r["views_total"] for r in reach)
last12 = sum(r["views_last_12m"] for r in reach)
wikis = {w for r in reach for w in r["used_on"].split(" | ") if w}
langs = {w.split(".")[0] for w in wikis if w.endswith("wikipedia.org")}
articles = sum(int(r["article_pages"]) for r in reach)

tidx = {t: i for i, t in enumerate(TOPIC_ORDER)}
photos = []
for f in sorted(files, key=lambda f: -reach_by[f]["views_total"] if f in reach_by else 0):
    e = {"f": f, "g": [tidx[t] for t in topics.get(f, []) if t in tidx]}
    if f in reach_by:
        e["v"], e["w"] = reach_by[f]["views_total"], int(reach_by[f]["wikis"])
    if captions.get(f):
        e["t"] = captions[f]
    photos.append(e)
counts = Counter(TOPIC_ORDER[i] for p in photos for i in p["g"])

def group(label, names):
    opts = "".join(f'<option value="{esc(t)}">{esc(t)} ({counts[t]:,})</option>' for t in names if counts.get(t, 0) >= 4)
    return f'<optgroup label="{label}">{opts}</optgroup>' if opts else ""

options = (f'<option value="random" selected>Random, all {TOTAL_FILES:,}</option>'
           f'<option value="top">Most viewed, {len(reach)} in use</option>'
           + group("Regions", REGIONS) + group("Subjects", SUBJECTS))

def title(e):
    return e.get("t") or nice_title(e["f"])

def card(e):
    meta = f'{e["v"]:,} views, used on {e["w"]} wiki{"s" if e["w"] != 1 else ""}' if e.get("v") else "On Wikimedia Commons"
    return (f'<figure class="shot"><a href="{file_page(e["f"])}"><img src="{file_url(e["f"])}" alt="{esc(title(e))}" loading="lazy"></a>'
            f'<figcaption><span class="title">{esc(title(e))}</span><span class="meta">{meta}</span>'
            f'<span class="credit">Photo: Ank Kumar, CC BY-SA 4.0</span></figcaption></figure>')

seen, sampler = set(), []
for t in TOPIC_ORDER:
    pick = next((p for p in photos if tidx[t] in p["g"] and p["f"] not in seen), None)
    if pick:
        sampler.append(pick)
        seen.add(pick["f"])
    if len(sampler) == 12:
        break

pubs = [p for p in read_csv("publications.csv") if p["status"] == "verified"]
web = [w for w in read_csv("text_scan_results.csv") if w["bucket"] == "reuse"]
web_sites = {w["domain"] for w in web}
featured = []
for dom, label in FEATURED.items():
    hit = next((w for w in web if w["domain"] == dom), None)
    if hit:
        featured.append((label, hit["url"]))
as_of = date.today().strftime("%B %Y")

pub_items = "\n".join(f"""
    <li><span class="publisher">{esc(p['publisher'] or 'Self-published')}</span>
      {esc(p['title'])}
      <span class="detail">{esc(', '.join(x for x in [p['authors'], p['year'], p['location']] if x))}</span>
      {f'<span class="photo">{esc(p["photo"])}</span>' if p['photo'] else ''}</li>""" for p in pubs)
site_items = "\n".join(f'<li><a href="{esc(u)}">{esc(l)}</a></li>' for l, u in featured)

CSS = """
:root{--ink:#14213D;--paper:#FFFFFF;--mist:#EEF1F5;--rule:#D3D9E2;--blue:#2E5FB8;--muted:#5A6577}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font:15px/1.55 FONTSTACK}
a{color:var(--blue)} a:focus-visible,select:focus-visible,button:focus-visible{outline:3px solid var(--blue);outline-offset:2px}
.hero{position:relative;margin:0}
.hero img{display:block;width:100%;height:min(78vh,760px);object-fit:cover}
.hero .label{position:absolute;left:clamp(16px,5vw,64px);bottom:clamp(16px,5vw,56px);max-width:600px;background:var(--ink);color:var(--paper);padding:24px 28px}
.hero h1{font-weight:600;font-size:clamp(22px,2.8vw,32px);line-height:1.2;margin:0 0 10px}
.hero p{margin:0;color:#C9D2E3}
.hero figcaption{position:absolute;right:16px;bottom:10px;font-size:12px;color:#fff;text-shadow:0 1px 3px rgba(0,0,0,.7)}
main{max-width:1180px;margin:0 auto;padding:0 clamp(16px,4vw,40px) 64px}
section{padding-top:64px}
h2{font-weight:600;font-size:22px;line-height:1.25;margin:0 0 6px}
.lede{max-width:72ch;color:var(--muted);margin:0 0 18px}
.facts{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:24px 40px;margin:44px 0 0;padding:26px 0 0;border-top:1px solid var(--rule)}
.facts div{margin:0} .facts dt{font-weight:600;font-size:26px;line-height:1.1} .facts dd{margin:4px 0 0;color:var(--muted);font-size:13px}
.controls{display:flex;flex-wrap:wrap;gap:12px;align-items:center;margin:0 0 26px}
.controls label{font-size:13px;color:var(--muted)}
select{font:inherit;padding:8px 12px;border:1px solid var(--rule);border-radius:8px;background:#fff;color:var(--ink);min-width:240px}
button{font:inherit;padding:8px 18px;border:1px solid var(--ink);border-radius:8px;background:#fff;color:var(--ink);cursor:pointer}
button:hover{background:var(--ink);color:#fff}
.gallery{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:32px 24px}
.shot{margin:0} .shot img{width:100%;aspect-ratio:3/2;object-fit:cover;display:block;background:var(--mist)}
.shot figcaption{display:flex;flex-direction:column;padding-top:8px}
.shot .title{font-weight:600;font-size:14px;line-height:1.3}
.shot .meta{color:var(--muted);font-size:13px} .shot .credit{font-size:12px;color:var(--muted);font-style:italic}
.morewrap{text-align:center;margin-top:32px}
.pubs{list-style:none;padding:0;margin:0;columns:2 360px;column-gap:56px}
.pubs li{break-inside:avoid;padding:12px 0;border-bottom:1px solid var(--rule);display:flex;flex-direction:column}
.pubs .publisher{font-weight:600} .pubs cite{font-style:italic;font-size:15px}
.pubs .detail,.pubs .photo{color:var(--muted);font-size:13px}
.sites{list-style:none;padding:0;margin:0;display:flex;flex-wrap:wrap;gap:8px 24px}
footer{max-width:1180px;margin:0 auto;padding:36px clamp(16px,4vw,40px) 56px;color:var(--muted);font-size:13px;border-top:1px solid var(--rule)}
footer p{max-width:72ch}
.copy{float:right;margin-left:24px}
@media (max-width:700px){.hero .label{position:static;max-width:none}.hero img{height:52vh}.copy{float:none;display:block;margin:0 0 12px}}
""".replace("FONTSTACK", FONT)

JS = """<script>
(() => {
  const data = JSON.parse(document.getElementById('photos').textContent);
  const TOPICS = JSON.parse(document.getElementById('topics').textContent);
  const FP = 'https://commons.wikimedia.org/wiki/Special:FilePath/', PG = 'https://commons.wikimedia.org/wiki/File:';
  const enc = f => encodeURIComponent(f.replace(/ /g, '_'));
  const nice = f => f.replace(/\\.(jpe?g|png|tiff?)$/i, '').replace(/\\s+\\d{1,3}$/, '')
    .replace(/\\(?\\s*Ank\\s*Kumar[^)]*\\)?/ig, '').replace(/\\s+/g, ' ').replace(/^[ ,\\-]+|[ ,\\-]+$/g, '');
  const esc = s => s.replace(/[&<>"]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]));
  const card = p => {
    const t = esc(p.t || nice(p.f));
    const meta = p.v ? p.v.toLocaleString('en-US') + ' views, used on ' + p.w + (p.w === 1 ? ' wiki' : ' wikis') : 'On Wikimedia Commons';
    return '<figure class="shot"><a href="' + PG + enc(p.f) + '"><img src="' + FP + enc(p.f) + '?width=500" alt="' + t +
      '" loading="lazy"></a><figcaption><span class="title">' + t + '</span><span class="meta">' + meta +
      '</span><span class="credit">Photo: Ank Kumar, CC BY-SA 4.0</span></figcaption></figure>';
  };
  const shuffle = a => { for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; };
  const grid = document.getElementById('gallery'), sel = document.getElementById('topic');
  const more = document.getElementById('more'), shuf = document.getElementById('shuffle');
  let list = [], shown = 0;
  const show = n => {
    grid.insertAdjacentHTML('beforeend', list.slice(shown, shown + n).map(card).join(''));
    shown += n;
    more.hidden = shown >= list.length;
  };
  const pick = () => {
    const v = sel.value;
    if (v === 'top') list = data.filter(p => p.v);
    else if (v === 'random') list = shuffle(data.slice());
    else { const k = TOPICS.indexOf(v); list = shuffle(data.filter(p => p.g.includes(k))); }
    shuf.hidden = v === 'top';
    grid.innerHTML = '';
    shown = 0;
    show(12);
  };
  sel.addEventListener('change', pick);
  shuf.addEventListener('click', pick);
  more.addEventListener('click', () => show(12));
  sel.disabled = false;
  pick();
})();
</script>"""

page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Ank Kumar – Open-Licence Photo Contributions</title>
<meta name="description" content="{TOTAL_FILES:,} openly licensed photographs by Ank Kumar, viewed {millions(total_views)} times on Wikipedia.">
<style>{CSS}</style></head>
<body>
<figure class="hero">
  <a href="{HERO_LINK}"><img src="{HERO_IMG}" alt="{esc(HERO_TITLE)}"></a>
  <div class="label">
    <h1>My photographs have been viewed {millions(total_views)} times on Wikipedia.</h1>
    <p>{millions(last12)} of those views came in the past year, across {len(langs)} language editions. All {TOTAL_FILES:,} of my photographs on Wikimedia Commons are free to use under CC BY-SA 4.0.</p>
  </div>
  <figcaption>{esc(HERO_TITLE)}. Photo: Ank Kumar, on Flickr</figcaption>
</figure>
<main>
  <dl class="facts">
    <div><dt>{TOTAL_FILES:,}</dt><dd>photographs released on Wikimedia Commons</dd></div>
    <div><dt>{len(reach):,}</dt><dd>of them illustrating {articles:,} articles</dd></div>
    <div><dt>{len(wikis)}</dt><dd>Wikimedia sites, including {len(langs)} Wikipedias</dd></div>
    <div><dt>{len(pubs)}</dt><dd>books and journals that credit my work</dd></div>
  </dl>
  <section>
    <h2>The collection</h2>
    <p class="lede">A random mix from all {TOTAL_FILES:,} photographs, {len(reach)} of them used on Wikipedia. Pick a region or subject, switch to most viewed, or shuffle again.</p>
    <div class="controls">
      <label for="topic">Show</label>
      <select id="topic" disabled>{options}</select>
      <button id="shuffle" type="button">Shuffle</button>
    </div>
    <div class="gallery" id="gallery">{"".join(card(p) for p in sampler)}</div>
    <div class="morewrap"><button id="more" type="button">Show more</button></div>
  </section>
  <section>
    <h2>In print</h2>
    <p class="lede">Books and journals that reproduce my photographs with credit, each checked against the published text.</p>
    <ul class="pubs">{pub_items}
    </ul>
  </section>
  <section>
    <h2>On the web</h2>
    <p class="lede">{len(web):,} pages on {len(web_sites)} websites use my photographs, including:</p>
    <ul class="sites">{site_items}</ul>
  </section>
</main>
<footer>
  <span class="copy">{COPY}</span>
  <p>View counts come from the Wikimedia Analytics API and count each time a page showing the photograph was viewed by a reader; they are views, not unique visitors. Web and print uses were found by searching for the credit line &ldquo;Ank Kumar&rdquo; and checked individually. Updated {as_of}.</p>
  <p><a href="{COMMONS_USER}">All photographs on Wikimedia Commons</a> &nbsp; <a href="{FLICKR}">Flickr</a></p>
</footer>
<script type="application/json" id="photos">{json.dumps(photos, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")}</script>
<script type="application/json" id="topics">{json.dumps(TOPIC_ORDER)}</script>
{JS}
</body></html>"""

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(page)
print(f"Built {OUT} ({os.path.getsize(OUT) / 1e6:.1f} MB)")
print(f"  {TOTAL_FILES:,} photos | {millions(total_views)} views | {len(pubs)} publications | {len(web)} web pages")
print("  Regions: " + ", ".join(f"{t} ({counts[t]:,})" for t in REGIONS if counts.get(t, 0) >= 4))
print("  Subjects: " + ", ".join(f"{t} ({counts[t]:,})" for t in SUBJECTS if counts.get(t, 0) >= 4))
