#!/usr/bin/env python3
"""Energie-Radar: sammelt Fachquellen (RSS) + automatische Stichwortsuche
(Google-News-RSS, begrenzt auf vertrauenswürdige Domains) und erzeugt docs/index.html.

Nur Standardbibliothek, keine Installation nötig:  python3 build.py
"""
import html
import json
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

ROOT = Path(__file__).parent
CONFIG = json.loads((ROOT / "feeds.json").read_text(encoding="utf-8"))
S = CONFIG["settings"]
UA = "Mozilla/5.0 (compatible; EnergieRadar/1.0; persoenlicher RSS-Reader)"
NOW = datetime.now(timezone.utc)
CUTOFF = NOW - timedelta(days=S["days_back"])


def local(tag):
    return tag.rsplit("}", 1)[-1]


def clean(text, limit):
    text = html.unescape(re.sub(r"<[^>]+>", " ", text or ""))
    text = re.sub(r"\s+", " ", text).strip()
    return text if len(text) <= limit else text[: limit - 1].rsplit(" ", 1)[0] + "…"


def parse_date(raw):
    if not raw:
        return None
    raw = raw.strip()
    try:
        dt = parsedate_to_datetime(raw)
    except (TypeError, ValueError):
        try:
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=S["timeout_seconds"]) as r:
        return r.read()


def parse_feed(data, default_source):
    root = ET.fromstring(data)
    items = []
    for el in root.iter():
        if local(el.tag) not in ("item", "entry"):
            continue
        f = {}
        for c in el:
            name = local(c.tag)
            if name == "link":
                f.setdefault("link", c.get("href") or (c.text or "").strip())
            elif name == "source":
                f["source"] = (c.text or "").strip()
            elif name in ("title", "description", "summary", "pubDate", "published", "updated", "encoded"):
                f.setdefault(name, c.text or "")
        title = clean(f.get("title"), 300)
        link = f.get("link")
        if not title or not link:
            continue
        date = parse_date(f.get("pubDate") or f.get("published") or f.get("updated")) or NOW
        items.append({
            "title": title,
            "link": link,
            "date": date,
            "summary": clean(f.get("description") or f.get("summary") or f.get("encoded"), S["max_summary_chars"]),
            "source": f.get("source") or default_source,
        })
    return items


def search_url(search):
    sites = " OR ".join(f"site:{d}" for d in CONFIG["trusted_domains"])
    kws = " OR ".join(f'"{k}"' if " " in k else k for k in search["keywords"])
    q = f"({kws}) ({sites}) when:{S['days_back']}d"
    lang = search.get("lang", "de")
    hl, gl, ceid = ("de", "DE", "DE:de") if lang == "de" else ("en", "US", "US:en")
    return "https://news.google.com/rss/search?" + urllib.parse.urlencode(
        {"q": q, "hl": hl, "gl": gl, "ceid": ceid})


def jobs():
    for f in CONFIG["feeds"]:
        yield {"name": f["name"], "url": f["url"], "category": f["category"], "kind": "feed"}
    for s in CONFIG["searches"]:
        yield {"name": s["name"], "url": search_url(s), "category": s["category"], "kind": "suche"}


def run(job):
    try:
        items = parse_feed(fetch(job["url"]), job["name"])
        return job, items[: S["max_items_per_feed"]], None
    except Exception as e:  # ein defekter Feed soll nie alles abbrechen
        return job, [], f"{type(e).__name__}: {e}"


def main():
    with ThreadPoolExecutor(max_workers=8) as ex:
        results = list(ex.map(run, jobs()))

    seen, articles, status = set(), [], []
    for job, items, err in results:
        status.append({"name": job["name"], "kind": job["kind"], "count": len(items), "error": err})
        for it in items:
            if it["date"] < CUTOFF:
                continue
            key = re.sub(r"\W+", "", it["title"].lower())[:80]
            if key in seen:
                continue
            seen.add(key)
            articles.append({
                "title": it["title"], "link": it["link"], "summary": it["summary"],
                "source": it["source"], "category": job["category"], "kind": job["kind"],
                "date": it["date"].astimezone(timezone.utc).isoformat(),
            })
    articles.sort(key=lambda a: a["date"], reverse=True)

    out = ROOT / "docs"
    out.mkdir(exist_ok=True)
    template = (ROOT / "template.html").read_text(encoding="utf-8")
    payload = json.dumps({"articles": articles, "status": status,
                          "generated": NOW.isoformat()}, ensure_ascii=False).replace("</", "<\\/")
    (out / "index.html").write_text(template.replace("/*DATA*/null", payload), encoding="utf-8")

    ok = sum(1 for s in status if not s["error"])
    print(f"{len(articles)} Artikel aus {ok}/{len(status)} Quellen -> docs/index.html")
    for s in status:
        if s["error"]:
            print(f"  FEHLER {s['name']}: {s['error']}", file=sys.stderr)


if __name__ == "__main__":
    main()
