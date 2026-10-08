# Ank Kumar – Open-Licence Photo Contributions

A reach and expansion map for the 12,684 photographs I have released on Wikimedia Commons under CC BY-SA 4.0: where they are used, how often they are viewed, and where else they have travelled — Wikipedia, books, journals, news sites, travel guides and my own channels.

**Version 1.0** (October 2026)

## What it does

- **Wikimedia reach** – which photos are used on which Wikimedia projects, and how often they are viewed (Wikimedia Analytics API, human traffic).
- **Web reach** – third-party pages, mirrors and my own channels that carry the photos, found by text search on photo titles plus manual additions.
- **Print** – books and journals that credit the photos, each verified against the published text.
- **Topics** – every photo tagged by region and subject from its title, caption and Commons categories.

## Parts

| Path | What it is |
|---|---|
| `scanner/` | Data collection and processing scripts (Commons inventory, reach, search scans, topic tagging, page tagging tools) |
| `app/main.py` | Local FastAPI dashboard: overview, photos, web reach, print, admin |
| `docs/` | Public static showcase page, published with GitHub Pages |

The `data/` folder is generated locally by the scanner scripts and is not included in this repository.

## Running locally

~~~
python3 -m venv .venv
.venv/bin/pip install fastapi uvicorn
.venv/bin/python -m uvicorn main:app --app-dir app --port 8010 --reload
~~~

Scripts expect their data in `data/` and currently use absolute paths for my machine.

## Data sources

Wikimedia Commons API · Wikimedia Analytics (mediarequests) API · Tavily Search API · SearXNG (self-hosted) · Google Books API · manual verification.

## Licensing

- **Photographs:** © Ank Kumar, licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). Reuse is welcome with attribution and under the same licence. They are **not** public domain.
- **Code, page text and design:** © 2026 Ank Kumar. All rights reserved.
