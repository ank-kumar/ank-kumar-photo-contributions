#!/usr/bin/env python3
"""Photo reach v3 - local web app for Ank Kumar's Wikimedia Commons photographs."""
import csv, html, json, os, random, re, sys, urllib.parse
from collections import Counter, defaultdict
from datetime import date, datetime
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

ROOT = "/Users/ank/projects/image-reuse-tracker"
DATA = f"{ROOT}/data"
sys.path.insert(0, f"{ROOT}/scanner")
from text_scan import key as subject_key, subject as subject_name  # noqa: E402

TOTAL_FILES = 12684
FILEPATH = "https://commons.wikimedia.org/wiki/Special:FilePath/"
FILEPAGE = "https://commons.wikimedia.org/wiki/File:"
BOOKS = "https://books.google.com/books?id={}&q=%22ank+kumar%22"
NAV = [("overview", "/", "Overview"), ("photos", "/photos", "Photos"), ("web", "/web", "On the web"),
       ("print", "/print", "In print"), ("admin", "/admin", "Admin")]
LANG = {"en": "English", "de": "German", "fr": "French", "es": "Spanish", "it": "Italian", "pt": "Portuguese",
        "ru": "Russian", "ja": "Japanese", "zh": "Chinese", "ar": "Arabic", "fa": "Persian", "hi": "Hindi",
        "bn": "Bengali", "ta": "Tamil", "te": "Telugu", "ml": "Malayalam", "kn": "Kannada", "mr": "Marathi",
        "ur": "Urdu", "tr": "Turkish", "nl": "Dutch", "pl": "Polish", "uk": "Ukrainian", "cs": "Czech",
        "sv": "Swedish", "no": "Norwegian", "da": "Danish", "fi": "Finnish", "hu": "Hungarian", "ro": "Romanian",
        "el": "Greek", "he": "Hebrew", "id": "Indonesian", "ms": "Malay", "vi": "Vietnamese", "th": "Thai",
        "ko": "Korean", "ca": "Catalan", "eu": "Basque", "gl": "Galician", "sr": "Serbian", "hr": "Croatian",
        "bg": "Bulgarian", "sk": "Slovak", "sl": "Slovenian", "lt": "Lithuanian", "lv": "Latvian",
        "et": "Estonian", "simple": "Simple English", "arz": "Egyptian Arabic", "azb": "South Azerbaijani",
        "uz": "Uzbek", "kk": "Kazakh", "hy": "Armenian", "ka": "Georgian", "az": "Azerbaijani", "sq": "Albanian",
        "mk": "Macedonian", "be": "Belarusian", "af": "Afrikaans", "sw": "Swahili", "tl": "Tagalog",
        "ceb": "Cebuano", "pa": "Punjabi", "gu": "Gujarati", "or": "Odia", "ne": "Nepali", "si": "Sinhala",
        "my": "Burmese", "km": "Khmer", "mn": "Mongolian", "is": "Icelandic", "ga": "Irish", "cy": "Welsh",
        "la": "Latin", "eo": "Esperanto", "als": "Alemannic", "bar": "Bavarian", "lb": "Luxembourgish",
        "rm": "Romansh", "sh": "Serbo-Croatian", "bs": "Bosnian", "nn": "Nynorsk", "ast": "Asturian"}

TOPIC_ORDER = ["Europe", "Asia", "Australia", "Switzerland", "Zurich", "Germany", "The UK", "Scotland",
               "France", "Spain", "Italy", "Vatican", "Holland", "Belgium", "Czech Republic", "Hungary",
               "Turkey", "India", "Hong Kong", "Macau", "Singapore", "Airplanes", "Military", "Automobiles",
               "Sports", "Architecture", "Museums", "Art", "Movies", "Comics", "Music", "Nature",
               "Trains & transport", "Religion"]

app = FastAPI(title="Ank Kumar – Open-Licence Photo Contributions", version="1.0",
              description="Reach of Ank Kumar's Wikimedia Commons photographs")

# ---------- helpers ----------
def esc(s):
    return html.escape(str(s or ""))

def qf(name):
    return urllib.parse.quote(name.replace(" ", "_"))

STEPS = [120, 250, 330, 500, 960, 1280, 1920]  # Wikimedia standard thumbnail widths

def thumb(name, w=500):
    w = next((x for x in STEPS if x >= w), STEPS[-1])
    return f"{FILEPATH}{qf(name)}?width={w}"

def big(n):
    n = int(n)
    if n >= 1_000_000:
        return f"{n / 1e6:.1f}M"
    if n >= 10_000:
        return f"{n / 1e3:.0f}K"
    return f"{n:,}"

def nice_title(fn):
    t = re.sub(r"\.(jpe?g|png|tiff?)$", "", fn, flags=re.I)
    t = re.sub(r"\s+\d{1,3}$", "", t)
    t = re.sub(r"\(?\s*Ank\s*Kumar[^)]*\)?", "", t, flags=re.I)
    return re.sub(r"\s+", " ", t).strip(" ,-")

def parse_date(s):
    try:
        return date.fromisoformat((s or "").strip()[:10])
    except ValueError:
        return None

def read_csv(name):
    path = f"{DATA}/{name}"
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def read_json(name):
    path = f"{DATA}/{name}"
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def split_list(s):
    return [x.strip() for x in (s or "").split("|") if x.strip()]

def keys_for(name):
    return {subject_key(name), subject_key(subject_name(name))}

# ---------- data ----------
def load():
    captions = read_json("captions.json")
    topics = read_json("topics.json")
    reach = read_csv("wikimedia_reach.csv")
    for r in reach:
        for k in ("views_total", "views_last_12m", "wikis", "article_pages"):
            r[k] = int(r.get(k) or 0)
        r["title"] = captions.get(r["file"]) or nice_title(r["file"])
        r["wiki_list"] = split_list(r.get("used_on"))
        r["topics"] = topics.get(r["file"], [])
    reach.sort(key=lambda r: -r["views_total"])
    web = read_csv("text_scan_results.csv")
    reuse = [w for w in web if w["bucket"] in ("reuse", "own", "mirror")]
    web_by_key = defaultdict(dict)
    for w in reuse:
        for s in split_list(w["subjects"]):
            for k in keys_for(s):
                web_by_key[k][w["url"]] = w
    for r in reach:
        pages = {}
        for k in keys_for(r["file"]):
            pages.update(web_by_key.get(k, {}))
        r["web"] = list(pages.values())
    srcs = [f"{DATA}/{n}" for n in ("wikimedia_reach.csv", "text_scan_results.csv", "publications.csv")]
    mt = max((os.path.getmtime(x) for x in srcs if os.path.exists(x)), default=None)
    return {"reach": reach, "web": web, "reuse": reuse, "pubs": read_csv("publications.csv"),
            "thumbs": read_json("subject_files.json"),
            "updated": datetime.fromtimestamp(mt).strftime("%d %b %Y") if mt else "no data yet"}

def summary(d):
    reach = d["reach"]
    wikis = {w for r in reach for w in r["wiki_list"]}
    langs = {w.split(".")[0] for w in wikis if w.endswith("wikipedia.org")}
    return {"photos_total": TOTAL_FILES, "photos_in_use": len(reach),
            "views_total": sum(r["views_total"] for r in reach),
            "views_last_12m": sum(r["views_last_12m"] for r in reach),
            "wikis": len(wikis), "wikipedias": len(langs),
            "articles": sum(r["article_pages"] for r in reach),
            "web_pages": len(d["reuse"]), "web_sites": len({w["domain"] for w in d["reuse"]}),
            "publications": sum(1 for p in d["pubs"] if p["status"] == "verified")}

# ---------- theme ----------
CSS = """
:root{--bg:#0B1220;--panel:#111A2C;--line:#22304A;--text:#EEF2F8;--muted:#95A3BB;--accent:#F0B25A;--link:#A9C7FF}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--text);font:14px/1.5 Aptos,"Aptos Display","Segoe UI",system-ui,-apple-system,sans-serif;-webkit-font-smoothing:antialiased}
a{color:var(--link);text-decoration:none}
a:hover{text-decoration:underline}
:focus-visible{outline:3px solid var(--accent);outline-offset:3px}
.wrap{max-width:1280px;margin:0 auto;padding:0 clamp(16px,4vw,48px)}
header{position:sticky;top:0;z-index:20;background:rgba(11,18,32,.72);backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);border-bottom:1px solid rgba(255,255,255,.06)}
header .wrap{display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap;padding-top:14px;padding-bottom:14px}
.brand{color:var(--text);font-weight:600;font-size:17px;line-height:1}
.brand span{color:var(--accent);font-weight:400}
.brand:hover{text-decoration:none}
nav{display:flex;gap:4px;flex-wrap:wrap}
nav a{color:var(--muted);padding:7px 14px;border-radius:999px;transition:color .2s,background .2s}
nav a:hover{color:var(--text);background:rgba(255,255,255,.06);text-decoration:none}
nav a.on{color:#1B1408;background:var(--accent)}
h1,h2{font-weight:600;letter-spacing:-.01em}
.hero{position:relative;min-height:min(88vh,860px);display:flex;align-items:flex-end;overflow:hidden}
.wall{position:absolute;inset:-6% -4%;display:flex;flex-direction:column;justify-content:center;gap:12px;transform:rotate(-4deg) scale(1.08)}
.row{display:flex;gap:12px;width:max-content;animation:drift 90s linear infinite}
.row:nth-child(2){animation-duration:125s;animation-direction:reverse}
.row:nth-child(3){animation-duration:105s}
.row:nth-child(4){animation-duration:140s;animation-direction:reverse}
.row:nth-child(5){animation-duration:95s}
@keyframes drift{from{transform:translateX(0)}to{transform:translateX(-50%)}}
.hero::after{content:"";position:absolute;inset:0;pointer-events:none;transition:opacity .4s;background:linear-gradient(180deg,rgba(11,18,32,.25) 0%,rgba(11,18,32,.6) 45%,var(--bg) 97%)}
.hero:has(.wall:hover)::after{opacity:.5}
.hero-in{position:relative;z-index:2;pointer-events:none;padding-top:140px;padding-bottom:56px;width:100%}
.hero .by{color:#C8D2E3;margin:0 0 12px;font-size:14px}
.hero h1{font-size:clamp(36px,6vw,84px);line-height:.98;margin:0}
.hero h1 .num{color:var(--accent);font-variant-numeric:tabular-nums}
.hero .sub{font-size:clamp(15px,1.6vw,18px);color:#C8D2E3;max-width:48ch;margin:20px 0 0}
.live{display:inline-flex;align-items:center;gap:10px;margin:28px 0 0;padding:9px 18px;border:1px solid rgba(255,255,255,.14);border-radius:999px;background:rgba(17,26,44,.65);font-size:13px;color:#C8D2E3}
.live b{color:var(--text);font-variant-numeric:tabular-nums;min-width:3ch}
.pulse{width:8px;height:8px;border-radius:50%;background:var(--accent);animation:pulse 2s infinite}
@keyframes pulse{0%{box-shadow:0 0 0 0 rgba(240,178,90,.6)}70%{box-shadow:0 0 0 10px rgba(240,178,90,0)}100%{box-shadow:0 0 0 0 rgba(240,178,90,0)}}
.stats{display:grid;grid-template-columns:repeat(4,1fr);margin:16px 0 0;border-top:1px solid var(--line)}
.stats div{padding:26px 20px 26px 0;border-bottom:1px solid var(--line)}
.stats dt{font-weight:600;font-size:clamp(24px,2.6vw,34px);line-height:1;font-variant-numeric:tabular-nums}
.stats dd{margin:6px 0 0;color:var(--muted);font-size:12px}
section{margin-top:96px}
.head{display:flex;align-items:baseline;justify-content:space-between;gap:16px;flex-wrap:wrap;margin-bottom:22px}
h2{font-size:clamp(20px,2.2vw,28px);margin:0}
.muted{color:var(--muted)}
.small{font-size:13px}
.bento{display:grid;grid-template-columns:repeat(4,1fr);grid-auto-rows:220px;gap:14px}
.bento .tile:first-child{grid-column:span 2;grid-row:span 2}
.bento .tile:first-child .t{font-size:20px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));grid-auto-rows:210px;gap:14px}
.tile{position:relative;display:block;overflow:hidden;border-radius:14px;background:var(--panel);color:var(--text)}
.tile:hover{text-decoration:none}
.tile img{width:100%;height:100%;object-fit:cover;display:block;transition:transform .7s cubic-bezier(.2,.7,.2,1)}
.tile:hover img{transform:scale(1.07)}
.tile .cap{position:absolute;left:0;right:0;bottom:0;padding:48px 16px 14px;background:linear-gradient(180deg,transparent,rgba(5,9,18,.9));display:flex;flex-direction:column;gap:3px}
.tile .t{font-weight:600;font-size:14px;line-height:1.25;color:#fff;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.tile .m{font-size:12px;color:#C8D2E3}
.cloud{display:flex;flex-wrap:wrap;gap:10px 12px;align-items:baseline}
.cloud span{padding:6px 14px;border:1px solid var(--line);border-radius:999px;color:#D7DEEA;transition:border-color .2s,color .2s}
.cloud span:hover{border-color:var(--accent);color:var(--accent)}
.cloud small{color:var(--muted);margin-left:7px;font-size:12px}
.two{display:grid;grid-template-columns:repeat(auto-fit,minmax(360px,1fr));gap:56px}
.bars{list-style:none;padding:0;margin:18px 0 0}
.bars li{display:grid;grid-template-columns:minmax(120px,40%) 1fr 56px;gap:12px;align-items:center;padding:6px 0;font-size:13px}
.bl{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.bar{background:rgba(255,255,255,.06);height:8px;border-radius:4px;overflow:hidden}
.bar i{display:block;height:100%;width:0;background:linear-gradient(90deg,var(--accent),#FFD79A);border-radius:4px;transition:width 1.2s cubic-bezier(.2,.7,.2,1)}
.in .bar i{width:var(--w)}
.bv{text-align:right;color:var(--muted);font-variant-numeric:tabular-nums}
.reveal{opacity:0;transform:translateY(20px);transition:opacity .8s ease,transform .8s ease}
.reveal.in{opacity:1;transform:none}
.pagehead{padding-top:56px}
.pagehead h1{font-size:clamp(28px,3.6vw,44px);margin:0 0 8px}
.filters{display:flex;flex-wrap:wrap;gap:12px;align-items:end;margin:24px 0 28px}
.filters label{display:flex;flex-direction:column;font-size:13px;color:var(--muted);gap:6px}
input,select{font:inherit;padding:9px 12px;border:1px solid var(--line);border-radius:10px;background:var(--panel);color:var(--text)}
button{font:inherit;font-weight:600;padding:10px 20px;border:0;border-radius:10px;background:var(--accent);color:#1B1408;cursor:pointer}
.tablewrap{overflow-x:auto}
table{width:100%;border-collapse:collapse}
th,td{text-align:left;padding:14px 10px;border-bottom:1px solid var(--line);vertical-align:top}
th{font-size:13px;color:var(--muted);font-weight:600}
td.th{width:116px}
td.th img{width:104px;height:69px;object-fit:cover;border-radius:8px;background:var(--panel);display:block}
td.ph{width:34%;font-size:13px}
td.dt{white-space:nowrap;width:120px;color:var(--muted);font-size:14px}
.url{max-width:560px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.big{margin:24px 0 0}
.big img{width:100%;max-height:76vh;object-fit:contain;border-radius:14px;background:var(--panel)}
.big h1{margin:16px 0 4px;font-size:clamp(22px,2.6vw,32px)}
.chips{list-style:none;padding:0;display:flex;flex-wrap:wrap;gap:8px}
.chips li{border:1px solid var(--line);padding:5px 12px;border-radius:999px;font-size:14px}
.links{list-style:none;padding:0}
.links li{padding:10px 0;border-bottom:1px solid var(--line)}
.pubs{list-style:none;padding:0;columns:2 400px;column-gap:56px}
.pubs li{break-inside:avoid;display:flex;flex-direction:column;gap:3px;padding:18px 0;border-bottom:1px solid var(--line)}
.pub{font-weight:600;color:var(--accent)}
cite{font-style:italic;font-size:15px}
.flag{align-self:flex-start;font-size:12px;color:#1B1408;background:var(--accent);padding:1px 9px;border-radius:999px;margin:4px 0}
.row:hover{animation-play-state:paused}
.card{position:relative;display:block;height:clamp(110px,16vh,190px);aspect-ratio:3/2;perspective:1000px;color:var(--text)}
.card:hover{text-decoration:none}
.card .front img{filter:brightness(.6);transition:filter .4s}
.card:hover .front img{filter:none}
.tile.flip{overflow:visible;background:none;perspective:1200px}
.face{position:absolute;inset:0;border-radius:14px;overflow:hidden;backface-visibility:hidden;-webkit-backface-visibility:hidden;transition:transform .7s cubic-bezier(.2,.7,.2,1),opacity .4s}
.face img{width:100%;height:100%;object-fit:cover;display:block}
.front{background:var(--panel)}
.back{transform:rotateY(180deg);background:linear-gradient(160deg,#1C2944,#0E1626);border:1px solid var(--line);padding:18px;display:flex;flex-direction:column;gap:10px}
.flip:hover .front,.flip:focus-visible .front,.card:hover .front,.card:focus-visible .front{transform:rotateY(-180deg)}
.flip:hover .back,.flip:focus-visible .back,.card:hover .back,.card:focus-visible .back{transform:rotateY(0)}
.flip:hover img{transform:none}
.back .t{font-weight:600;font-size:14px;line-height:1.25;color:#fff}
.back .facts{list-style:none;padding:0;margin:0;display:flex;flex-direction:column;gap:4px;font-size:12px;color:#C8D2E3}
.back b{color:var(--accent);font-weight:700;font-size:15px;margin-right:4px}
.back .m{font-size:13px;color:var(--muted)}
.back .go{margin-top:auto;color:var(--accent);font-size:13px;font-weight:600}
.back .src{font-size:12px;color:var(--accent);font-weight:600}
.card .back{padding:14px;gap:6px}
.card .back .t{font-size:13px;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
@media (prefers-reduced-motion:reduce){.face{transition:none}.flip .back,.card .back{transform:none;opacity:0}.flip:hover .back,.flip:focus-visible .back,.card:hover .back,.card:focus-visible .back{opacity:1}.flip:hover .front,.flip:focus-visible .front,.card:hover .front,.card:focus-visible .front{transform:none}}
.copy{float:right;margin-left:24px;color:var(--muted)}
footer{color:var(--muted);font-size:13px;padding:32px 0 56px;margin-top:96px;border-top:1px solid var(--line)}
@media (max-width:900px){.stats{grid-template-columns:repeat(2,1fr)}.bento{grid-template-columns:repeat(2,1fr)}}
@media (prefers-reduced-motion:reduce){.row,.pulse{animation:none}.reveal{opacity:1;transform:none;transition:none}.bar i,.tile img{transition:none}html{scroll-behavior:auto}}
"""

JS = """<script>
(() => {
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const fmt = (v, m) => m === 'm' ? (v / 1e6).toFixed(1) + 'M' : Math.round(v).toLocaleString('en-US');
  const count = el => {
    const end = +el.dataset.count, m = el.dataset.fmt || 'n';
    if (reduce) { el.textContent = fmt(end, m); return; }
    const t0 = performance.now(), dur = 1600;
    const step = t => {
      const p = Math.min(1, (t - t0) / dur), e = 1 - Math.pow(1 - p, 3);
      el.textContent = fmt(end * e, m);
      if (p < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  };
  const show = el => {
    el.classList.add('in');
    if (el.dataset.count) count(el);
    el.querySelectorAll('[data-count]').forEach(count);
  };
  const io = new IntersectionObserver(es => es.forEach(e => {
    if (e.isIntersecting) { show(e.target); io.unobserve(e.target); }
  }), {threshold: 0.15});
  document.querySelectorAll('.reveal, .hero [data-count]').forEach(el => reduce ? show(el) : io.observe(el));
  const wall = document.querySelector('.wall');
  if (wall && !reduce) {
    const queue = [];
    let loading = false;
    const refill = () => {
      if (loading) return;
      loading = true;
      fetch('/api/wall?n=60').then(r => r.json()).then(items => { queue.push(...items); })
        .finally(() => { loading = false; });
    };
    const fill = (c, it) => {
      c.href = it.link;
      c.querySelector('img').src = it.img;
      c.querySelector('.src').textContent = it.source;
      c.querySelector('.t').textContent = it.title;
      c.querySelector('.m').textContent = it.meta || '';
    };
    const fixBroken = () => wall.querySelectorAll('img').forEach(img => {
      if (img.complete && !img.naturalWidth && queue.length) fill(img.closest('.card'), queue.shift());
    });
    wall.addEventListener('error', e => {
      if (e.target.tagName === 'IMG' && queue.length) fill(e.target.closest('.card'), queue.shift());
    }, true);
    refill();
    setInterval(() => {
      if (queue.length < 20) refill();
      if (!queue.length) return;
      fixBroken();
      const off = [...wall.querySelectorAll('.card')].filter(c => {
        const b = c.getBoundingClientRect();
        return b.right < 0 || b.left > innerWidth;
      });
      if (!off.length) return;
      const c = off[Math.floor(Math.random() * off.length)], it = queue.shift();
      const pre = new Image();
      pre.onload = () => fill(c, it);
      pre.src = it.img;
    }, 900);
  }
  const live = document.getElementById('live');
  if (live) {
    const rate = +live.dataset.rate, t0 = Date.now();
    setInterval(() => { live.textContent = Math.floor(rate * (Date.now() - t0) / 1000).toLocaleString('en-US'); }, 250);
  }
})();
</script>"""

def layout(title, active, body, updated, hero=""):
    nav = "".join(f'<a href="{href}" class="{"on" if key == active else ""}">{label}</a>'
                  for key, href, label in NAV)
    return HTMLResponse(f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} | Ank Kumar – Open-Licence Photo Contributions</title>
<style>{CSS}</style></head><body>
<header><div class="wrap"><a class="brand" href="/">Ank Kumar <span>Open-Licence Photo Contributions</span></a><nav>{nav}</nav></div></header>
{hero}<main class="wrap">{body}</main>
<footer class="wrap">Data updated {updated}. Views come from the Wikimedia Analytics API and count human traffic, not unique visitors.
<a href="/showcase/">Public showcase</a> <a href="/docs">API</a><span class="copy">© 2026, Ank Kumar, All Rights Reserved</span></footer>{JS}</body></html>""")

def tile(r, w=600):
    langs = [LANG.get(x.split(".")[0], x.split(".")[0]) for x in r["wiki_list"] if x.endswith("wikipedia.org")]
    lang_line = ", ".join(langs[:4]) + (f" and {len(langs) - 4} more" if len(langs) > 4 else "")
    web = f"<li><b>{len(r['web'])}</b> web pages</li>" if r["web"] else ""
    return (f'<a class="tile flip" href="/photo?f={urllib.parse.quote(r["file"])}" aria-label="{esc(r["title"])}">'
            f'<span class="face front"><img src="{thumb(r["file"], w)}" loading="lazy" alt="">'
            f'<span class="cap"><span class="t">{esc(r["title"])}</span>'
            f'<span class="m">{big(r["views_total"])} views</span></span></span>'
            f'<span class="face back"><span class="t">{esc(r["title"])}</span><ul class="facts">'
            f'<li><b>{big(r["views_total"])}</b> views since 2015</li>'
            f'<li><b>{big(r["views_last_12m"])}</b> in the last 12 months</li>'
            f'<li><b>{r["wikis"]}</b> wikis, {r["article_pages"]} articles</li>{web}</ul>'
            f'<span class="m">{esc(lang_line)}</span><span class="go">See everywhere it’s used</span></span></a>')

def bars(counter, n=10, link=None):
    items = counter.most_common(n)
    if not items:
        return '<p class="muted">No data yet.</p>'
    top = items[0][1]
    rows = []
    for label, v in items:
        name = f'<a href="{link(label)}">{esc(label)}</a>' if link else esc(label)
        rows.append(f'<li><span class="bl">{name}</span><span class="bar"><i style="--w:{100 * v / top:.0f}%"></i></span>'
                    f'<span class="bv">{v:,}</span></li>')
    return '<ul class="bars">' + "".join(rows) + "</ul>"

def stat(value, label, fmt="n"):
    shown = big(value) if fmt == "m" else f"{value:,}"
    return f'<div><dt data-count="{value}" data-fmt="{fmt}">{shown}</dt><dd>{label}</dd></div>'

# ---------- pages ----------
@app.get("/", response_class=HTMLResponse)
def overview(topic: str = "random"):
    d = load()
    s = summary(d)
    reach = d["reach"]
    cards = deal(60)
    wall = "".join('<div class="row">' + "".join(card(it) for it in row + row) + "</div>"
                   for row in (cards[0::5], cards[1::5], cards[2::5], cards[3::5], cards[4::5]))
    rate = s["views_last_12m"] / (365 * 86400)
    hero = f"""
<section class="hero"><div class="wall" aria-hidden="true">{wall}</div>
<div class="hero-in wrap">
  <p class="by">Ank Kumar's photographs on Wikimedia Commons</p>
  <h1><span class="num" data-count="{s['views_total']}" data-fmt="m">{big(s['views_total'])}</span><br>views on Wikimedia</h1>
  <p class="sub">{s['views_last_12m'] / 1e6:.1f} million in the last twelve months, across {s['wikipedias']} Wikipedia language editions.</p>
  <p class="live"><span class="pulse"></span><b id="live" data-rate="{rate:.5f}">0</b> estimated views since you opened this page</p>
</div></section>"""
    pct = 100 * s["photos_in_use"] / TOTAL_FILES
    stats = "".join([
        stat(s["views_total"], "views since 2015", "m"),
        stat(s["views_last_12m"], "views in the last 12 months", "m"),
        stat(s["photos_in_use"], f"photos in use, {pct:.1f}% of {TOTAL_FILES:,}"),
        stat(s["articles"], "articles illustrated"),
        stat(s["wikipedias"], "Wikipedia language editions"),
        stat(s["wikis"], "Wikimedia wikis in total"),
        stat(s["web_pages"], f"web pages on {s['web_sites']} sites"),
        stat(s["publications"], "books and journals"),
    ])
    langs = Counter(w.split(".")[0] for r in reach for w in r["wiki_list"] if w.endswith("wikipedia.org"))
    top_l = langs.most_common(60)
    mx = top_l[0][1] if top_l else 1
    cloud = "".join(f'<span style="font-size:{13 + 15 * (c / mx) ** 0.5:.0f}px">{esc(LANG.get(code, code))}<small>{c}</small></span>'
                    for code, c in top_l)
    more = f'<span class="muted">and {len(langs) - len(top_l)} more</span>' if len(langs) > len(top_l) else ""
    topic_counts = Counter(t for r in reach for t in r["topics"])
    if topic == "top":
        picks = reach[:9]
    elif topic in topic_counts:
        picks = [r for r in reach if topic in r["topics"]][:9]
    else:
        topic = "random"
        picks = random.sample(reach, min(9, len(reach)))
    opts = ('<option value="random"' + (" selected" if topic == "random" else "") + '>Random</option>'
            + '<option value="top"' + (" selected" if topic == "top" else "") + '>Most viewed</option>'
            + "".join(f'<option value="{esc(t)}"{" selected" if t == topic else ""}>{esc(t)} ({topic_counts[t]})</option>'
                      for t in TOPIC_ORDER if topic_counts.get(t, 0) >= 4))
    wiki_c = Counter(w for r in reach for w in r["wiki_list"])
    site_c = Counter(w["domain"] for w in d["reuse"])
    body = f"""
<dl class="stats reveal">{stats}</dl>
<section class="reveal" id="gallery"><div class="head"><h2>Photos in use</h2>
<form class="filters" method="get" action="/#gallery" style="margin:0">
  <select name="topic" onchange="this.form.submit()" aria-label="Show">{opts}</select>
  <a href="/?topic=random&amp;s={random.randint(1, 10**9)}#gallery">Shuffle</a> <a href="/photos">All {len(reach)} photos in use</a>
</form></div>
<div class="bento">{"".join(tile(r, 1280 if i == 0 else 500) for i, r in enumerate(picks))}</div></section>
<section class="reveal"><div class="head"><h2>Read in {s['wikipedias']} languages</h2>
<span class="muted">Wikipedia editions using your photos, sized by number of photos</span></div>
<div class="cloud">{cloud}{more}</div></section>
<section class="two reveal">
  <div><h2>Top wikis</h2><p class="muted">How many of your photographs each wiki uses.</p>{bars(wiki_c)}</div>
  <div><h2>Top websites</h2><p class="muted">Pages found on each website, outside Wikimedia.</p>
  {bars(site_c, link=lambda dom: "/web?q=" + urllib.parse.quote(dom))}</div>
</section>"""
    return layout("Overview", "overview", body, d["updated"], hero)

@app.get("/photos", response_class=HTMLResponse)
def photos(q: str = "", sort: str = "views"):
    d = load()
    reach = d["reach"]
    if q:
        reach = [r for r in reach if q.lower() in (r["file"] + " " + r["title"]).lower()]
    sorters = {"views": lambda r: -r["views_total"], "recent": lambda r: -r["views_last_12m"],
               "wikis": lambda r: -r["wikis"], "web": lambda r: -len(r["web"])}
    reach = sorted(reach, key=sorters.get(sort, sorters["views"]))
    labels = [("views", "Most viewed"), ("recent", "Most viewed this year"),
              ("wikis", "Used on most wikis"), ("web", "Most web pages")]
    opts = "".join(f'<option value="{v}"{" selected" if v == sort else ""}>{l}</option>' for v, l in labels)
    clear = '<a href="/photos">Clear search</a>' if q else ""
    tiles = "".join(tile(r) for r in reach) or "<p>No photos match that search.</p>"
    body = f"""
<section class="pagehead" style="margin-top:0"><h1>Photos in use</h1>
<p class="muted">{len(reach)} of your photographs appear on Wikimedia projects. Select one to see everywhere it's used.</p></section>
<form class="filters" method="get">
  <label>Search<input name="q" value="{esc(q)}" placeholder="Concorde, Zurich, Colosseum"></label>
  <label>Sort<select name="sort">{opts}</select></label>
  <button type="submit">Apply</button> {clear}
</form>
<div class="grid">{tiles}</div>"""
    return layout("Photos", "photos", body, d["updated"])

@app.get("/photo", response_class=HTMLResponse)
def photo(f: str):
    d = load()
    r = next((x for x in d["reach"] if x["file"] == f), None)
    if not r:
        return layout("Not found", "photos",
                      '<p class="pagehead">That photo is not in the data. <a href="/photos">Back to photos</a></p>',
                      d["updated"])
    chips = "".join(f"<li>{esc(w)}</li>" for w in r["wiki_list"])
    web = "".join(f'<li><a href="{esc(w["url"])}">{esc(w["domain"])}</a> '
                  f'<span class="muted small">{esc(w["url"][:90])}</span></li>' for w in r["web"])
    web = web or '<li class="muted">No websites found yet.</li>'
    stats = "".join([stat(r["views_total"], "views since 2015", "m" if r["views_total"] >= 1e6 else "n"),
                     stat(r["views_last_12m"], "views in the last 12 months", "m" if r["views_last_12m"] >= 1e6 else "n"),
                     stat(r["wikis"], "wikis"), stat(len(r["web"]), "web pages")])
    body = f"""
<p class="pagehead" style="margin-top:0"><a href="/photos">All photos</a></p>
<figure class="big"><a href="{FILEPAGE}{qf(r['file'])}"><img src="{thumb(r['file'], 1600)}" alt="{esc(r['title'])}"></a>
<figcaption><h1>{esc(r['title'])}</h1><p class="muted small">{esc(r['file'])}</p></figcaption></figure>
<dl class="stats reveal">{stats}</dl>
<section class="two reveal">
  <div><h2>Used on these wikis</h2><ul class="chips">{chips}</ul></div>
  <div><h2>Used on these websites</h2><ul class="links">{web}</ul></div>
</section>
<p><a href="{FILEPAGE}{qf(r['file'])}">Open on Wikimedia Commons</a></p>"""
    return layout(r["title"], "photos", body, d["updated"])

@app.get("/web", response_class=HTMLResponse)
def web_page(q: str = "", start: str = "", end: str = "", kind: str = "all"):
    d = load()
    rows = d["reuse"]
    if kind in ("reuse", "own", "mirror"):
        rows = [w for w in rows if w["bucket"] == kind]
    if q:
        rows = [w for w in rows if q.lower() in (w["domain"] + w["url"] + w["subjects"]).lower()]
    s0, e0 = parse_date(start), parse_date(end)
    if s0 or e0:
        def in_range(w):
            dd = parse_date(w.get("first_seen"))
            return dd and (not s0 or dd >= s0) and (not e0 or dd <= e0)
        rows = [w for w in rows if in_range(w)]
    rows = sorted(rows, key=lambda w: (w.get("first_seen") or "", w["domain"]), reverse=True)
    def row(w):
        subs = split_list(w["subjects"])
        fn = next((d["thumbs"][x] for x in subs if x in d["thumbs"]), None)
        img = f'<img src="{thumb(fn, 220)}" loading="lazy" alt="">' if fn else ""
        badge = {"own": ' <span class="flag">your channel</span>', "mirror": ' <span class="flag">mirror</span>'}.get(w["bucket"], "")
        names = "; ".join(dict.fromkeys(subject_name(x) for x in subs[:3]))
        return (f'<tr><td class="th">{img}</td><td><a href="{esc(w["url"])}">{esc(w["domain"])}</a>{badge}'
                f'<div class="muted small url">{esc(w["url"])}</div></td>'
                f'<td class="ph">{esc(names)}</td><td class="dt">{esc(w.get("first_seen") or "")}</td></tr>')
    kinds = "".join(f'<option value="{v}"{" selected" if v == kind else ""}>{l}</option>' for v, l in [("all", "Everything"), ("reuse", "Used by others"), ("own", "Your channels"), ("mirror", "Mirrors")])
    trs = "".join(row(w) for w in rows) or '<tr><td colspan="4">No pages match these filters.</td></tr>'
    clear = '<a href="/web">Clear filters</a>' if (q or start or end or kind != "all") else ""
    body = f"""
<section class="pagehead" style="margin-top:0"><h1>On the web</h1>
<p class="muted">{len(rows):,} pages on {len({w['domain'] for w in rows})} websites, outside Wikimedia.</p></section>
<form class="filters" method="get">
  <label>Search<input name="q" value="{esc(q)}" placeholder="site, URL or photo"></label>
  <label>First seen from<input type="date" name="start" value="{esc(start)}"></label>
  <label>to<input type="date" name="end" value="{esc(end)}"></label>
  <label>Type<select name="kind">{kinds}</select></label>
  <button type="submit">Apply</button> {clear}
</form>
<div class="tablewrap"><table><thead><tr><th></th><th>Website</th><th>Photo</th><th>First seen</th></tr></thead>
<tbody>{trs}</tbody></table></div>"""
    return layout("On the web", "web", body, d["updated"])

@app.get("/print", response_class=HTMLResponse)
def print_page():
    d = load()
    def item(p):
        link = f'<a href="{BOOKS.format(p["google_books_id"])}">View in Google Books</a>' if p.get("google_books_id") else ""
        flag = '<span class="flag">to confirm</span>' if p["status"] != "verified" else ""
        detail = ", ".join(x for x in [p["authors"], p["year"], p["location"]] if x)
        photo_line = f'<span>{esc(p["photo"])}</span>' if p["photo"] else ""
        return (f'<li><span class="pub">{esc(p["publisher"] or "Self-published")}</span>{esc(p["title"])}'
                f'{flag}<span class="muted">{esc(detail)}</span>{photo_line}{link}</li>')
    pubs = sorted(d["pubs"], key=lambda p: p["status"] != "verified")
    verified = sum(1 for p in pubs if p["status"] == "verified")
    body = f"""
<section class="pagehead" style="margin-top:0"><h1>In print</h1>
<p class="muted">{verified} books and journals credit your photographs, each checked against the published text.</p></section>
<ul class="pubs reveal">{"".join(item(p) for p in pubs)}</ul>"""
    return layout("In print", "print", body, d["updated"])

@app.get("/admin", response_class=HTMLResponse)
def admin():
    d = load()
    rows = [w for w in d["web"] if w["bucket"] in ("notice", "spam")]
    trs = "".join(f'<tr><td>{esc(w["bucket"])}</td><td><a href="{esc(w["url"])}">{esc(w["domain"])}</a></td>'
                  f'<td>{esc("; ".join(subject_name(x) for x in split_list(w["subjects"])[:2]))}</td>'
                  f'<td class="dt">{esc(w.get("first_seen") or "")}</td></tr>'
                  for w in sorted(rows, key=lambda w: (w["bucket"], w["domain"])))
    body = f"""
<section class="pagehead" style="margin-top:0"><h1>Admin</h1>
<p class="muted">Notice targets, mirrors and spam scrapers. These never appear on the showcase.</p></section>
<div class="tablewrap"><table><thead><tr><th>Bucket</th><th>Website</th><th>Photo</th><th>First seen</th></tr></thead>
<tbody>{trs}</tbody></table></div>"""
    return layout("Admin", "admin", body, d["updated"])

# ---------- moving wall: shuffled deck of every upload ----------
_DECK = {"items": [], "i": 0}

def wall_items():
    captions = read_json("captions.json")
    views = {r["file"]: int(r.get("views_total") or 0) for r in read_csv("wikimedia_reach.csv")}
    files = read_json("commons_files.json") or list(views)
    items = []
    for f in files:
        v = views.get(f)
        items.append({"img": thumb(f, 420), "title": captions.get(f) or nice_title(f),
                      "source": "Wikimedia Commons", "link": FILEPAGE + qf(f),
                      "meta": f"{big(v)} views on Wikimedia" if v else "On Wikimedia Commons"})
    for ph in read_json("flickr_photos.json") or []:
        items.append({"img": ph["img"], "title": ph.get("title") or "Untitled", "source": "Flickr",
                      "link": ph["link"], "meta": "On Flickr"})
    return items

def deal(n):
    if _DECK["i"] + n > len(_DECK["items"]):
        items = wall_items()
        random.shuffle(items)
        _DECK["items"], _DECK["i"] = items, 0
    out = _DECK["items"][_DECK["i"]:_DECK["i"] + n]
    _DECK["i"] += n
    return out

def card(it):
    return (f'<a class="card" href="{esc(it["link"])}" target="_blank" rel="noopener">'
            f'<span class="face front"><img src="{esc(it["img"])}" alt=""></span>'
            f'<span class="face back"><span class="src">{esc(it["source"])}</span>'
            f'<span class="t">{esc(it["title"])}</span><span class="m">{esc(it["meta"])}</span></span></a>')

@app.get("/api/wall")
def api_wall(n: int = 60):
    return deal(max(1, min(n, 200)))

# ---------- API ----------
@app.get("/api/summary")
def api_summary():
    return summary(load())

@app.get("/api/photos")
def api_photos(limit: int = 50):
    return [{k: r[k] for k in ("file", "title", "views_total", "views_last_12m", "wikis", "article_pages")}
            | {"web_pages": len(r["web"])} for r in load()["reach"][:limit]]

# ---------- showcase (static page built by scanner/build_showcase.py) ----------
app.mount("/showcase", StaticFiles(directory=f"{ROOT}/docs", html=True), name="showcase")
