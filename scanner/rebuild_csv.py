#!/usr/bin/env python3
"""Rebuild the master CSV from all scanner state files.
Applies classification rules in one place and keeps permanent first/last-seen dates."""
import csv, json, os, re, urllib.parse
from collections import Counter
from datetime import date

DATA = "/Users/ank/projects/image-reuse-tracker/data"
STATES = {"tavily": os.path.join(DATA, "text_scan_state.json"),
          "searxng": os.path.join(DATA, "searxng_state.json"),
          "manual": os.path.join(DATA, "manual_state.json")}
REGISTRY = os.path.join(DATA, "seen_registry.json")
OUT = os.path.join(DATA, "text_scan_results.csv")
TODAY = date.today().isoformat()

# Ank's own accounts: (host, path prefix). Empty prefix = whole host.
OWN = [("facebook.com", "/theankkumar"),
       ("x.com", "/nomad_gsx"), ("x.com", "/ank_kumar"),
       ("twitter.com", "/nomad_gsx"), ("twitter.com", "/ank_kumar"),
       ("ankkumar.artstation.com", ""), ("artstation.com", "/artwork/wkjzbx"),
       ("vimeo.com", "/ankkumar"),
       ("youtube.com", "/channel/uccatu31eqsiumfp49crv7na"),
       ("flickr.com", "/photos/nomad_gsx"),
       ("github.com", "/ank-kumar")]
OWN_URL_MARKERS = ["xrk3pybtamc", "1hrttvseb0", "bscwfhe6l8g"]  # own YouTube video IDs
WIKIMEDIA = ["wikimedia.org", "wikipedia.org", "wikidata.org", "wikivoyage.org",
             "wiktionary.org", "wikisource.org", "wikinews.org", "wikiquote.org",
             "wikibooks.org", "wikiversity.org", "wikimediafoundation.org",
             "wmcloud.org", "toolforge.org", "wikilovesmonuments.org",
             "vikianitlariseviyor.tr"]
SEARCH_ENGINES = ("yandex.", "google.", "bing.com", "duckduckgo.com", "baidu.com", "yahoo.com")
NOTICE_HOSTS = ["picryl.com", "getarchive.net", "creazilla.com", "depic.ai"]
MIRRORS = {"wexor.tv"}

def host_path(url):
    p = urllib.parse.urlparse(url)
    host = p.netloc.lower().removeprefix("www.").removeprefix("m.")
    return host, p.path.lower(), p.query

def unwrap_archive(url):
    m = re.match(r"https?://web\.archive\.org/web/[^/]+/(https?://.+)", url, re.I)
    return (m.group(1), True) if m else (url, False)

def canon(url):
    host, path, query = host_path(url)
    q = urllib.parse.parse_qs(query)
    if "title" in q and ("diff" in q or "oldid" in q):
        return f"{host}/wiki/{q['title'][0]}"
    return host + path.rstrip("/") + ("?" + query if query else "")

def classify(url):
    target, _ = unwrap_archive(url)
    host, path, query = host_path(target)
    full = target.lower()
    on = lambda h: host == h or host.endswith("." + h)
    if any(on(h) and path.startswith(p) for h, p in OWN) or any(m in full for m in OWN_URL_MARKERS):
        return "own", ""
    if (on("500px.com") and ("n0ns3n53" in path or "-by-ank-kumar" in path)) or on("search.ch") \
       or (on("archive.org") and path.startswith("/details/") and re.search(r"(^|[/_.\-])ank([_.\-]|kumar)", path)) \
       or on("artstation.com") or on("vimeo.com") or on("pinterest.com"):
        return "own", ""
    if on("linkedin.com") and path.startswith("/in/"):
        return "own", ""
    if any(host.startswith(s) or ("." + s) in host for s in SEARCH_ENGINES):
        return None, "search engine"
    if any(on(d) for d in WIKIMEDIA):
        return None, "Wikimedia site/tool"
    if on("flickr.com") and ("/photos/tags/" in path or "/favorites" in path):
        return None, "Flickr listing"
    if any(on(h) for h in ("wiki2.org", "handwiki.org")):
        return "mirror", ""
    if any(on(h) for h in NOTICE_HOSTS):
        return "notice", ""
    if host in MIRRORS:
        return ("mirror", "") if "ank-kumar" in path else (None, "mirror sidebar match")
    if (path in ("", "/") and query) or "product-similar-image" in path:
        return "spam", ""
    return "reuse", ""

def main():
    registry = {}
    if os.path.exists(REGISTRY):
        with open(REGISTRY) as f:
            registry = json.load(f)
    pages, excluded = {}, Counter()
    for src, path in STATES.items():
        if not os.path.exists(path):
            continue
        with open(path) as f:
            state = json.load(f)
        for url, h in state.get("hits", {}).items():
            bucket, reason = classify(url)
            if not bucket:
                excluded[reason] += 1
                continue
            target, archived = unwrap_archive(url)
            key = canon(target)
            e = pages.setdefault(key, {
                "bucket": bucket,
                "domain": host_path(target)[0] + (" (archived)" if archived else ""),
                "url": url, "subjects": set(), "published": "", "sources": set()})
            e["subjects"].update(s.strip() for s in h.get("series", []) if s.strip())
            if h.get("published") and not e["published"]:
                e["published"] = str(h["published"])[:10]
            e["sources"].add(src)

    for key, e in pages.items():
        r = registry.setdefault(key, {"first_seen": TODAY})
        r.setdefault("last_seen", r["first_seen"])
        e["first_seen"], e["last_seen"] = r["first_seen"], r["last_seen"]
    with open(REGISTRY, "w") as f:
        json.dump(registry, f, indent=1)

    order = {"reuse": 0, "own": 1, "mirror": 2, "notice": 3, "spam": 4}
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["bucket", "domain", "url", "subjects", "first_seen",
                    "last_seen", "published", "source"])
        for e in sorted(pages.values(), key=lambda e: (order[e["bucket"]], e["domain"])):
            w.writerow([e["bucket"], e["domain"], e["url"],
                        " | ".join(sorted(e["subjects"])), e["first_seen"],
                        e["last_seen"], e["published"], "+".join(sorted(e["sources"]))])

    print(f"Pages kept: {len(pages)}")
    for b in ("reuse", "own", "mirror", "notice", "spam"):
        sel = [e for e in pages.values() if e["bucket"] == b]
        doms = Counter(e["domain"] for e in sel)
        subj = {s for e in sel for s in e["subjects"]}
        print(f"\n[{b.upper()}] pages: {len(sel)} | sites: {len(doms)} | subjects: {len(subj)}")
        for d, n in doms.most_common(15 if b == "reuse" else 8):
            print(f"  {n:5d}  {d}")
    print("\nExcluded (raw hits):")
    for r, n in excluded.most_common():
        print(f"  {n:5d}  {r}")
    print(f"\nCSV written: {OUT}")

if __name__ == "__main__":
    main()
