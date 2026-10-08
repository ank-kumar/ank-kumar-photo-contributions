#!/usr/bin/env python3
"""Suggest which of Ank's photos each untagged manual page shows, from the text around his credit.
Usage:
  suggest_photos.py               visit untagged pages and print numbered suggestions (changes nothing)
  suggest_photos.py apply 1a 3b   accept option a for page 1, option b for page 3
  suggest_photos.py apply all     accept every high-confidence top suggestion
"""
import html, json, math, re, subprocess, sys, time, unicodedata, urllib.request
from collections import Counter
sys.path.insert(0, "/Users/ank/projects/image-reuse-tracker/scanner")
from text_scan import subject

ROOT = "/Users/ank/projects/image-reuse-tracker"
DATA = f"{ROOT}/data"
MANUAL = f"{DATA}/manual_state.json"
SUGG = f"{DATA}/photo_suggestions.json"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh) ImageReuseTracker/0.6 (personal photo-credit check)"}
STOP = set("""the and for with from that this are was were has have its his her their our your you photo photos
image images picture credit credits courtesy source via own work license licensed licence wikimedia commons wiki
creative cc by sa nc nd ank kumar infosys limited ltd file jpg jpeg png view views page click read more http https
www com org net""".split())

def norm(s):
    s = unicodedata.normalize("NFKD", s.lower())
    return "".join(c for c in s if not unicodedata.combining(c))

def tokens(s):
    return {t for t in re.findall(r"[a-z]{3,}|\d{4}", norm(s)) if t not in STOP}

def page_evidence(raw):
    raw = re.sub(r"(?is)<(script|style|noscript)\b.*?</\1>", " ", raw)
    alts = [html.unescape(a) for a in re.findall(r'(?i)\b(?:alt|title)\s*=\s*"([^"]{3,300})"', raw)]
    m = re.search(r"(?is)<title>(.*?)</title>", raw)
    title = html.unescape(m.group(1)).strip() if m else ""
    text = re.sub(r"\s+", " ", html.unescape(re.sub(r"(?s)<[^>]+>", " ", raw)))
    low = norm(text)
    windows = [text[max(0, x.start() - 220):x.end() + 80].strip() for x in re.finditer(r"ank\s*kumar", low)]
    near = [a for a in alts if re.search(r"ank\s*kumar", norm(a))]
    if windows or near:
        return windows[:6] + near[:6], "credit"
    return [title] + alts[:20], "title"

subs = sorted({subject(f) for f in json.load(open(f"{DATA}/commons_files.json", encoding="utf-8"))})
stoks = {s: tokens(s) for s in subs}
df = Counter(t for ts in stoks.values() for t in ts)
idf = {t: math.log(len(subs) / c) + 0.1 for t, c in df.items()}

def suggest(evidence):
    c = set().union(*(tokens(e) for e in evidence)) if evidence else set()
    out = []
    for s, ts in stoks.items():
        shared = ts & c
        if not ts or not shared:
            continue
        cov = sum(idf[t] for t in shared) / sum(idf[t] for t in ts)
        if cov >= 0.45 and max(idf[t] for t in shared) > 2.0:
            out.append((round(cov, 2), sum(idf[t] for t in shared), s))
    out.sort(reverse=True)
    return out[:3]

def confidence(score, basis):
    if basis == "credit" and score >= 0.8:
        return "high"
    return "medium" if score >= 0.6 else "low"

def run_suggest():
    manual = json.load(open(MANUAL, encoding="utf-8"))
    todo = [u for u, h in manual["hits"].items() if not h.get("series")]
    print(f"Checking {len(todo)} untagged pages (about {len(todo) * 3} seconds)...")
    results = []
    for u in todo:
        try:
            raw = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=30).read().decode("utf-8", "ignore")
        except Exception as e:
            results.append({"url": u, "basis": "blocked", "evidence": str(getattr(e, "code", e)), "options": []})
            continue
        ev, basis = page_evidence(raw)
        opts = suggest(ev)
        results.append({"url": u, "basis": basis, "evidence": (ev[0] if ev else "")[:220],
                        "options": [{"subject": s, "score": sc} for sc, _, s in opts]})
        time.sleep(2)
    json.dump(results, open(SUGG, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for i, r in enumerate(results, 1):
        print(f"\n[{i}] {r['url']}")
        if r["basis"] == "blocked":
            print(f"    blocked ({r['evidence']}) - tag by hand")
            continue
        label = "caption near your credit" if r["basis"] == "credit" else "no credit text found, guessed from page title"
        print(f"    {label}: \"{r['evidence']}\"")
        if not r["options"]:
            print("    no confident match - tag by hand")
        for letter, o in zip("abc", r["options"]):
            print(f"    {letter}) {o['subject']}  [{confidence(o['score'], r['basis'])}]")
    print("\nTo accept: suggest_photos.py apply 1a 3b ...   or   suggest_photos.py apply all")

def run_apply(args):
    results = json.load(open(SUGG, encoding="utf-8"))
    manual = json.load(open(MANUAL, encoding="utf-8"))
    if args == ["all"]:
        picks = [(r, r["options"][0]) for r in results
                 if r["options"] and confidence(r["options"][0]["score"], r["basis"]) == "high"]
    else:
        picks = []
        for a in args:
            m = re.fullmatch(r"(\d+)([abc])", a.strip().lower())
            if not m:
                raise SystemExit(f"Can't read '{a}' - use forms like 1a 3b")
            r = results[int(m.group(1)) - 1]
            idx = "abc".index(m.group(2))
            if idx >= len(r["options"]):
                raise SystemExit(f"Page {m.group(1)} has no option {m.group(2)}")
            picks.append((r, r["options"][idx]))
    for r, o in picks:
        h = manual["hits"].setdefault(r["url"], {"series": []})
        h["series"] = sorted(set(h.get("series", [])) | {o["subject"]})
        print(f"  tagged {r['url'][:80]}\n      -> {o['subject']}")
    json.dump(manual, open(MANUAL, "w", encoding="utf-8"), indent=1)
    print(f"\n{len(picks)} tags applied. Rebuilding...")
    subprocess.run([sys.executable, f"{ROOT}/scanner/rebuild_csv.py"], stdout=subprocess.DEVNULL, check=True)
    subprocess.run([sys.executable, f"{ROOT}/scanner/build_thumbs.py"], check=True)

if len(sys.argv) > 1 and sys.argv[1] == "apply":
    run_apply(sys.argv[2:])
else:
    run_suggest()
