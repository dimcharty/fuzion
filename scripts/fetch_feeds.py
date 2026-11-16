#!/usr/bin/env python3
"""Read the public RSS/Atom feeds in sources.json into data/inbox.json.

Only what the publisher puts in its own feed is kept: headline, a short
teaser (trimmed), link and date. Article pages are never opened.
"""
import hashlib
import html
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INBOX = ROOT / "data" / "inbox.json"
KEEP = 300          # newest items kept in the inbox
TEASER_MAX = 280    # characters of the publisher's teaser we keep
UA = "FuzionSocieteBot/1.0 (+https://t.me/fuzionsoc; RSS reader)"


def strip(text):
    text = re.sub(r"<[^>]+>", " ", text or "")
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def local(tag):
    return tag.rsplit("}", 1)[-1].lower()


def child(node, *names):
    for c in node:
        if local(c.tag) in names:
            return c
    return None


def parse_date(raw):
    if not raw:
        return None
    raw = raw.strip()
    try:
        d = parsedate_to_datetime(raw)
    except Exception:
        try:
            d = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except Exception:
            return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d.astimezone(timezone.utc).isoformat(timespec="seconds")


def parse_feed(xml_bytes, source):
    root = ET.fromstring(xml_bytes)
    items = []
    for node in root.iter():
        if local(node.tag) not in ("item", "entry"):
            continue
        title = child(node, "title")
        link = child(node, "link")
        desc = child(node, "description", "summary")
        date = child(node, "pubdate", "published", "updated", "date")
        href = ""
        if link is not None:
            href = (link.text or "").strip() or link.attrib.get("href", "")
        if title is None or not href:
            continue
        teaser = strip(desc.text if desc is not None else "")
        if len(teaser) > TEASER_MAX:
            teaser = teaser[:TEASER_MAX].rsplit(" ", 1)[0] + "…"
        items.append({
            "id": hashlib.sha1(href.encode()).hexdigest()[:12],
            "source": source["name"],
            "lang": source.get("lang", "en"),
            "weight": source.get("weight", 5),
            "title": strip(title.text),
            "teaser": teaser,
            "link": href,
            "published": parse_date(date.text if date is not None else None),
        })
    return items


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read()


def main():
    sources = json.loads((ROOT / "sources.json").read_text(encoding="utf-8"))
    old = json.loads(INBOX.read_text(encoding="utf-8")) if INBOX.exists() else []
    known = {i["id"]: i for i in old}
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    added = 0
    for s in sources:
        try:
            items = parse_feed(fetch(s["url"]), s)
        except Exception as e:  # one broken feed must not stop the rest
            print(f"SKIP {s['name']}: {e}", file=sys.stderr)
            continue
        new = [i for i in items if i["id"] not in known]
        for i in new:
            i["published"] = i["published"] or now
            i["seen"] = now
            known[i["id"]] = i
        added += len(new)
        print(f"OK   {s['name']}: {len(items)} items, {len(new)} new")
    merged = sorted(known.values(), key=lambda i: i["published"], reverse=True)[:KEEP]
    INBOX.parent.mkdir(exist_ok=True)
    INBOX.write_text(json.dumps(merged, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{added} new, {len(merged)} in inbox")


if __name__ == "__main__":
    main()
