#!/usr/bin/env python3
"""Merge edited posts into data/posts.json.

Usage: python scripts/add_posts.py new_posts.json
new_posts.json is a list of {"id", "title_uk", "summary_uk", "category"}.
The id must be an item in data/inbox.json; source, link and date come from there.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POSTS, INBOX = ROOT / "data" / "posts.json", ROOT / "data" / "inbox.json"
CATS = {"markets", "economy", "banks", "policy", "companies", "energy", "crypto", "ukraine", "world"}
KEEP = 120


def main():
    new = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    inbox = {i["id"]: i for i in json.loads(INBOX.read_text(encoding="utf-8"))}
    posts = json.loads(POSTS.read_text(encoding="utf-8")) if POSTS.exists() else []
    have = {p["id"] for p in posts}
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    errors, added = [], 0
    for n in new:
        src = inbox.get(n.get("id"))
        title, summary = (n.get("title_uk") or "").strip(), (n.get("summary_uk") or "").strip()
        if not src:
            errors.append(f"{n.get('id')}: not in inbox")
        elif n["id"] in have:
            continue
        elif not 15 <= len(title) <= 110:
            errors.append(f"{n['id']}: title must be 15-110 characters, got {len(title)}")
        elif not 80 <= len(summary) <= 420:
            errors.append(f"{n['id']}: summary must be 80-420 characters, got {len(summary)}")
        elif n.get("category") not in CATS:
            errors.append(f"{n['id']}: category must be one of {sorted(CATS)}")
        else:
            posts.insert(0, {"id": src["id"], "source": src["source"], "link": src["link"],
                             "title_uk": title, "summary_uk": summary, "category": n["category"],
                             "published": src["published"], "added": now})
            added += 1
    if errors:
        sys.exit("Nothing saved:\n" + "\n".join(errors))
    POSTS.write_text(json.dumps(posts[:KEEP], ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"added {added}")


if __name__ == "__main__":
    main()
