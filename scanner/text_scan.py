#!/usr/bin/env python3
"""Text-search scan v2: third-party pages carrying Ank Kumar's Commons photo titles."""
import csv, json, os, re, time, urllib.request, urllib.parse, urllib.error
from collections import Counter

DATA = "/Users/ank/projects/image-reuse-tracker/data"
STATE = os.path.join(DATA, "text_scan_state.json")
RESULTS_CSV = os.path.join(DATA, "text_scan_results.csv")
MAX_QUERIES = int(os.environ.get("MAX_QUERIES", "200"))
TAVILY_KEY = os.environ.get("TAVILY_API_KEY", "")
UA = "ImageReuseTracker/0.2 (https://commons.wikimedia.org/wiki/User:Ank_gsx) python-urllib"

EXCLUDE_DOMAINS = ["wikimedia.org", "wikipedia.org", "wikidata.org", "wikivoyage.org",
                   "wiktionary.org", "wikisource.org", "wikinews.org", "wikiquote.org",
                   "wikibooks.org", "wikiversity.org", "wikimediafoundation.org",
                   "wikilovesmonuments.org", "vikianitlariseviyor.tr"]
SEARCH_ENGINES = ("yandex.", "google.", "bing.com", "duckduckgo.com", "baidu.com", "yahoo.com")
MIRRORS = {"wexor.tv"}

# ---------- helpers ----------
def get_json(req, retries=5):
    for attempt in range(retries):
        try:
            return json.load(urllib.request.urlopen(req, timeout=60))
        except urllib.error.HTTPError as e:
            if e.code != 429:
                raise
            wait = int(e.headers.get("Retry-After", 10))
            print(f"  429, waiting {wait}s")
            time.sleep(wait)
    raise SystemExit("Still rate-limited after retries")

def commons_titles():
    base = "https://commons.wikimedia.org/w/api.php"
    p = {"action": "query", "list": "allimages", "aiuser": "Ank gsx",
         "aisort": "timestamp", "ailimit": "500", "format": "json", "maxlag": "5"}
    titles = []
    while True:
        req = urllib.request.Request(base + "?" + urllib.parse.urlencode(p),
                                     headers={"User-Agent": UA})
        d = get_json(req)
        titles += [i["title"] for i in d["query"]["allimages"]]
        if "continue" not in d:
            return titles
        p.update(d["continue"])
        time.sleep(1)

CREDIT_RE = re.compile(
    r"\(?\s*\b(ank\s*kumar|ank\s*kunar|ank\s*lunar|ankkumar)\b"
    r"(\s*,?\s*infosys(\s*(limited|ltd))?)?\s*[)?]?", re.I)

def subject(title):
    t = title.removeprefix("File:")
    t = re.sub(r"\.(jpe?g|png|gif|tiff?|webp)$", "", t, flags=re.I)
    t = re.sub(r"\s*\d{1,3}$", "", t)
    t = CREDIT_RE.sub(" ", t)
    t = re.sub(r"\(\s*\)", " ", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip(" ,.-")

def key(s):
    return re.sub(r"\s+", " ", subject(s).lower()).strip()

def tavily(query):
    body = json.dumps({"query": query, "search_depth": "basic",
                       "max_results": 20, "exclude_domains": EXCLUDE_DOMAINS}).encode()
    req = urllib.request.Request("https://api.tavily.com/search", data=body,
        headers={"Authorization": f"Bearer {TAVILY_KEY}",
                 "Content-Type": "application/json"})
    return get_json(req)

def mentions_ank(r):
    blob = " ".join(str(r.get(k, "")) for k in ("url", "title", "content"))
    blob = blob.lower().replace("_", " ").replace("%20", " ").replace("-", " ")
    return "ank kumar" in blob

def host_of(url):
    return urllib.parse.urlparse(url).netloc.lower().removeprefix("www.")

def norm_url(url):
    p = urllib.parse.urlparse(url)
    n = host_of(url) + p.path.rstrip("/")
    return n + ("?" + p.query if p.query else "")

def classify(url):
    p = urllib.parse.urlparse(url)
    host = host_of(url)
    full = url.lower()
    if any(host.startswith(s) or ("." + s) in host for s in SEARCH_ENGINES):
        return None
    if host == "flickr.com" and ("nomad_gsx" in full or "/photos/tags/" in p.path):
        return None
    if host == "github.com" and p.path.lower().startswith("/ank-kumar"):
        return None
    if host == "web.archive.org" and ("github.com/ank-kumar" in full or "nomad_gsx" in full):
        return None
    if any(host == d or host.endswith("." + d) for d in EXCLUDE_DOMAINS):
        return None
    if host in MIRRORS:
        return "mirror" if "ank-kumar" in p.path.lower() else None
    if (p.path in ("", "/") and p.query) or "product-similar-image" in p.path:
        return "spam"
    return "reuse"

# ---------- main ----------
def main():
    os.makedirs(DATA, exist_ok=True)
    state = {"done": [], "done_keys": [], "hits": {}}
    if os.path.exists(STATE):
        with open(STATE) as f:
            state.update(json.load(f))
    done_keys = set(state.get("done_keys", [])) | {key(s) for s in state.get("done", [])}

    print("Fetching file list from Commons...")
    titles = commons_titles()
    subjects = {}
    for t in titles:
        subjects.setdefault(key(t), subject(t))
    todo = [k for k in sorted(subjects) if k not in done_keys]
    run = todo[:MAX_QUERIES]
    print(f"{len(titles)} files -> {len(subjects)} subjects | already searched: "
          f"{len(set(subjects) & done_keys)} | remaining: {len(todo)} | this run: {len(run)}")

    if run and not TAVILY_KEY:
        raise SystemExit("TAVILY_API_KEY not set (use MAX_QUERIES=0 for report-only).")

    for i, k in enumerate(run, 1):
        s = subjects[k]
        try:
            res = tavily(f"{s} Ank Kumar")
        except urllib.error.HTTPError as e:
            print(f"Tavily error {e.code}: {e.read().decode()[:200]} -- stopping, progress saved.")
            break
        new = 0
        for r in res.get("results", []):
            if mentions_ank(r):
                h = state["hits"].setdefault(r["url"], {"domain": host_of(r["url"]), "series": []})
                if s not in h["series"]:
                    h["series"].append(s)
                    new += 1
        done_keys.add(k)
        state["done_keys"] = sorted(done_keys)
        with open(STATE, "w") as f:
            json.dump(state, f, indent=1)
        print(f"[{i}/{len(run)}] +{new} | {s[:80]}")
        time.sleep(1)

    # ---------- report ----------
    pages = {}
    for url, h in state["hits"].items():
        b = classify(url)
        if not b:
            continue
        e = pages.setdefault(norm_url(url), {"bucket": b, "domain": host_of(url),
                                              "url": url, "subjects": set()})
        e["subjects"].update(subject(x) for x in h["series"])

    with open(RESULTS_CSV, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["bucket", "domain", "url", "subjects"])
        for e in sorted(pages.values(), key=lambda e: (e["bucket"], e["domain"])):
            w.writerow([e["bucket"], e["domain"], e["url"], " | ".join(sorted(e["subjects"]))])

    searched = len(set(subjects) & done_keys)
    print("\n=== RESULTS SO FAR ===")
    print(f"Subjects searched: {searched} of {len(subjects)}")
    for b in ("reuse", "mirror", "spam"):
        sel = [e for e in pages.values() if e["bucket"] == b]
        subj = {s for e in sel for s in e["subjects"]}
        doms = Counter(e["domain"] for e in sel)
        print(f"\n[{b.upper()}] pages: {len(sel)} | sites: {len(doms)} | subjects: {len(subj)}")
        for d, n in doms.most_common(25 if b == "reuse" else 10):
            print(f"  {n:5d}  {d}")
    print(f"\nCSV written: {RESULTS_CSV}")

if __name__ == "__main__":
    main()
