#!/usr/bin/env python3
"""Build the public showcase page (static HTML). v3: whole collection, Random default, grouped topic filter."""
import csv, html, json, os, re, urllib.parse
from collections import Counter, OrderedDict
from datetime import date
import pycountry

ROOT = "/Users/ank/projects/image-reuse-tracker"
DATA = f"{ROOT}/data"
OUT = f"{ROOT}/docs/index.html"
COMMONS_USER = "https://commons.wikimedia.org/wiki/User:Ank_gsx"
FLICKR = "https://www.flickr.com/photos/nomad_gsx"
HERO_IMG = "hero.jpg"
HERO_LINK = "https://www.flickr.com/photos/nomad_gsx/51846955840"
HERO_TITLE = "Alpine golden hour from the Schilthorn, Bernese Oberland, Switzerland, 2015"
COPY = "© 2026, Ank Kumar, All Rights Reserved"
SITE = "https://ank-kumar.github.io/ank-kumar-photo-contributions/"
GITHUB = "https://github.com/ank-kumar/ank-kumar-photo-contributions"
SEO_TITLE = "Ank Kumar – Open-Licence Photo Contributions"
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
geo_raw = read_json("geo_views.json", {})
geo = {}
for a2, v in geo_raw.get("countries", {}).items():
    c = pycountry.countries.get(alpha_2=a2)
    if c and v:
        geo[int(c.numeric)] = {"n": getattr(c, "common_name", None) or c.name, "v": int(v)}
geo_total = sum(x["v"] for x in geo.values()) or 1
rivers_json = json.dumps(read_json("rivers.json", []), separators=(",", ":"))
geo_rows = "".join(f'<li><span>{esc(x["n"])}</span><span class="pct">{100 * x["v"] / geo_total:.1f}%</span></li>'
                   for x in sorted(geo.values(), key=lambda x: -x["v"])[:10])
seo_desc = (f"{TOTAL_FILES:,} photographs by Ank Kumar on Wikimedia Commons under CC BY-SA 4.0, "
            f"viewed {millions(total_views)} times on Wikipedia across {len(langs)} languages, "
            f"and published in {len(pubs)} books and journals.")
ld = {"@context": "https://schema.org", "@type": "CollectionPage", "name": SEO_TITLE, "url": SITE,
      "description": seo_desc, "inLanguage": "en", "image": SITE + "hero.jpg",
      "author": {"@type": "Person", "name": "Ank Kumar", "url": "https://ank-kumar.github.io/",
                 "sameAs": ["https://www.linkedin.com/in/ankkumar/", "https://github.com/ank-kumar",
                            "https://huggingface.co/Ank-77", COMMONS_USER, FLICKR, GITHUB]},
      "mainEntity": {"@type": "ImageGallery", "name": "Photographs by Ank Kumar on Wikimedia Commons",
                     "url": COMMONS_USER, "numberOfItems": TOTAL_FILES,
                     "license": "https://creativecommons.org/licenses/by-sa/4.0/"}}
ld_json = json.dumps(ld, ensure_ascii=False).replace("</", "<\\/")

pub_items = "\n".join(f"""
    <li><span class="publisher">{esc(p['publisher'] or 'Self-published')}</span>
      {esc(p['title'])}
      <span class="detail">{esc(', '.join(x for x in [p['authors'], p['year'], p['location']] if x))}</span>
      {f'<span class="photo">{esc(p["photo"])}</span>' if p['photo'] else ''}</li>""" for p in pubs)
site_items = "\n".join(f'<li><a href="{esc(u)}">{esc(l)}</a></li>' for l, u in featured)
page_thumbs = read_json("page_thumbs.json", {})
def page_li(w):
    t = page_thumbs.get(w["url"])
    icon = (f'<img class="ph" src="{esc(t)}" width="60" height="40" alt="" loading="lazy">' if t else
            f'<img class="fav" src="https://www.google.com/s2/favicons?domain={esc(w["domain"])}&sz=64" width="32" height="32" alt="" loading="lazy">')
    return f'<li><a href="{esc(w["url"])}">{icon}<span>{esc(w["domain"])}</span></a></li>'
all_items = "\n".join(page_li(w) for w in sorted(web, key=lambda w: (w["url"] not in page_thumbs, w["domain"])))

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
.allsites{margin-top:18px} .allsites summary{cursor:pointer;color:var(--blue);font-weight:600}
.weblist{list-style:none;padding:0;margin:14px 0 0;display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:10px 18px;font-size:13px}
.weblist a{display:flex;gap:10px;align-items:center;text-decoration:none}
.weblist img.ph{width:60px;height:40px;object-fit:cover;border-radius:4px;flex:none;background:var(--mist)}
.weblist img.fav{width:32px;height:32px;margin:4px 14px;flex:none}
.weblist span{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.globe{display:grid;grid-template-columns:minmax(0,1.3fr) minmax(0,1fr);gap:28px;align-items:center;background:radial-gradient(120% 140% at 15% 20%, #3B1D6E 0%, #1E2A6B 48%, #0B1030 100%);color:#fff;border-radius:16px;padding:28px}
.globe-stage{position:relative}
#globe{width:100%;aspect-ratio:1/1;display:block;cursor:grab}
#globe:active{cursor:grabbing}
.tip{position:absolute;pointer-events:none;background:#fff;color:var(--ink);font-size:12px;padding:4px 8px;border-radius:6px;white-space:nowrap;box-shadow:0 2px 8px rgba(0,0,0,.3)}
.globe-side h3{margin:0 0 10px;font-size:15px;color:#7EE8D6}
.toplist{margin:0;padding-left:20px;font-size:14px}
.toplist li{padding:3px 0}
.toplist li span:first-child{display:inline-block;min-width:150px}
.toplist .pct{color:#AEB9CF;font-variant-numeric:tabular-nums}
.note{color:#AEB9CF;font-size:12px;margin:14px 0 0}
.globe.nogeo .globe-stage{display:none}
@media (max-width:760px){.globe{grid-template-columns:1fr}}
footer{max-width:1180px;margin:0 auto;padding:36px clamp(16px,4vw,40px) 56px;color:var(--muted);font-size:13px;border-top:1px solid var(--rule)}
footer p{max-width:72ch}
.copy{float:right;margin-left:24px}
@media (max-width:700px){.hero .label{position:static;max-width:none}.hero img{height:52vh}.copy{float:none;display:block;margin:0 0 12px}}
""".replace("FONTSTACK", FONT)

GLOBE_JS = """<script>
(async () => {
  const el = document.getElementById('globe');
  if (!el || !window.Globe || !window.d3 || !window.topojson) return;
  const geo = JSON.parse(document.getElementById('geo').textContent);
  let world;
  try { world = await (await fetch('https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json')).json(); }
  catch (e) { el.closest('.globe').classList.add('nogeo'); return; }
  const countries = topojson.feature(world, world.objects.countries).features;
  const vals = Object.values(geo).map(d => d.v);
  const lo = Math.log10(Math.max(1000, d3.min(vals))), hi = Math.log10(d3.max(vals));
  const t = v => Math.max(0, Math.min(1, (Math.log10(Math.max(v, 1)) - lo) / (hi - lo)));
  const heat = d3.interpolateRgbBasis(['#16425B', '#1F7A8C', '#3FC1C9', '#B8F3E9']);
  const capFor = (f, hov) => {
    const gg = geo[+f.id];
    if (!gg) return hov ? '#2A3F57' : '#1B2B3F';
    const c = d3.color(heat(t(gg.v)));
    return hov ? c.brighter(0.6).formatRgb() : c.formatRgb();
  };
  const fmt = n => n >= 1e6 ? (n / 1e6).toFixed(1) + 'M' : n >= 1e3 ? Math.round(n / 1e3) + 'K' : String(n);
  const centre = f => {
    if (f.geometry.type !== 'MultiPolygon') return d3.geoCentroid(f);
    let best = null, area = -1;
    for (const coords of f.geometry.coordinates) {
      const poly = {type: 'Polygon', coordinates: coords}, a = d3.geoArea(poly);
      if (a > area) { area = a; best = poly; }
    }
    return d3.geoCentroid(best);
  };
  const bars = countries.filter(f => geo[+f.id]).map(f => {
    const g = geo[+f.id], c = centre(f);
    return {lng: c[0], lat: c[1], name: g.n, v: g.v, t: t(g.v)};
  });
  const label = (name, v) => '<div style="font:13px/1.35 Aptos,Segoe UI,sans-serif;background:rgba(8,18,28,.88);color:#fff;padding:6px 10px;border-radius:8px">'
    + '<b>' + name + '</b><br>' + (v ? 'about ' + fmt(v) + ' views' : 'no readers recorded') + '</div>';
  const IMG = 'https://cdn.jsdelivr.net/npm/three-globe/example/img/';
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  let ctl = null;
  const hover = on => { if (ctl) ctl.autoRotate = !reduce && !on; };
  let g;
  try { g = new Globe(el); } catch (e) { g = Globe()(el); }
  g.width(el.clientWidth).height(el.clientWidth)
    .backgroundColor('rgba(0,0,0,0)')
    .showAtmosphere(true).atmosphereColor('#5EEAD4').atmosphereAltitude(0.16)
    .polygonsData(countries)
    .polygonAltitude(0.008)
    .polygonCapColor(f => capFor(f, false))
    .polygonSideColor(() => 'rgba(10,22,38,0.9)')
    .polygonStrokeColor(() => 'rgba(8,20,34,0.9)')
    .polygonLabel(f => label(geo[+f.id] ? geo[+f.id].n : (f.properties.name || ''), geo[+f.id] ? geo[+f.id].v : 0))
    .onPolygonHover(f => { g.polygonCapColor(d => capFor(d, d === f)).polygonAltitude(d => d === f ? 0.03 : 0.008); hover(!!f); })
    .pointOfView({lat: 32, lng: 20, altitude: 1.85});
  const mat = g.globeMaterial();
  mat.color.set('#0B1E33');
  mat.shininess = 8;
  ctl = g.controls();
  ctl.enableZoom = false;
  ctl.autoRotate = !reduce;
  ctl.autoRotateSpeed = 0.35;
  new ResizeObserver(() => g.width(el.clientWidth).height(el.clientWidth)).observe(el);
})();
</script>"""

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
<meta name="google-site-verification" content="6vdaUTOa-y8qc5O59yglXf5UBSVu7NfmA9-W5IPGy5A">
<meta name="description" content="{esc(seo_desc)}">
<link rel="canonical" href="{SITE}">
<meta property="og:type" content="website">
<meta property="og:title" content="{esc(SEO_TITLE)}">
<meta property="og:description" content="{esc(seo_desc)}">
<meta property="og:url" content="{SITE}">
<meta property="og:image" content="{SITE}hero.jpg">
<meta property="og:image:alt" content="{esc(HERO_TITLE)}">
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">{ld_json}</script>
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
    <h2>Where my photographs are seen</h2>
    <p class="lede">Estimated readers of Wikipedia articles that use my photographs, by country, over the last 12 months. Countries are shaded by readers, from deep blue to bright mint. Drag to spin; hover for figures.</p>
    <div class="globe">
      <div class="globe-stage"><div id="globe" role="img" aria-label="Interactive 3D globe shaded by estimated readers per country"></div></div>
      <div class="globe-side"><h3>Top countries</h3><ol class="toplist">{geo_rows}</ol>
      <p class="note">{len(geo)} countries in total. Estimate: each article's views are split by its Wikipedia edition's reader mix by country (Wikimedia Analytics). Wikimedia does not publish country data per article or per file.</p></div>
    </div>
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
    <details class="allsites"><summary>All {len(web):,} pages on {len(web_sites)} websites</summary><ul class="weblist">{all_items}</ul></details>
  </section>
</main>
<footer>
  <span class="copy">{COPY}</span>
  <p>View counts come from the Wikimedia Analytics API and count each time a page showing the photograph was viewed by a reader; they are views, not unique visitors. Web and print uses were found by searching for the credit line &ldquo;Ank Kumar&rdquo; and checked individually. Updated {as_of}.</p>
  <p><a href="{COMMONS_USER}">All photographs on Wikimedia Commons</a> &nbsp; <a href="{FLICKR}">Flickr</a></p>
</footer>
<script type="application/json" id="photos">{json.dumps(photos, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")}</script>
<script type="application/json" id="topics">{json.dumps(TOPIC_ORDER)}</script>
<script type="application/json" id="geo">{json.dumps(geo)}</script>
<script src="https://cdn.jsdelivr.net/npm/d3@7"></script>
<script src="https://cdn.jsdelivr.net/npm/topojson-client@3"></script>
<script src="https://cdn.jsdelivr.net/npm/globe.gl@2"></script>
{GLOBE_JS}
{JS}
</body></html>"""

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(page)
with open(os.path.join(os.path.dirname(OUT), "sitemap.xml"), "w", encoding="utf-8") as f:
    f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            f"  <url><loc>{SITE}</loc><lastmod>{date.today().isoformat()}</lastmod></url>\n</urlset>\n")
print(f"Built {OUT} ({os.path.getsize(OUT) / 1e6:.1f} MB) + sitemap.xml")
print(f"  {TOTAL_FILES:,} photos | {millions(total_views)} views | {len(pubs)} publications | {len(web)} web pages")
print("  Regions: " + ", ".join(f"{t} ({counts[t]:,})" for t in REGIONS if counts.get(t, 0) >= 4))
print("  Subjects: " + ", ".join(f"{t} ({counts[t]:,})" for t in SUBJECTS if counts.get(t, 0) >= 4))
