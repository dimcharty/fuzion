#!/usr/bin/env python3
"""Add the morning digest (top 3 stories of the last day) to data/posts.json.

Usage: python scripts/add_digest.py digest.json
digest.json: {"items": [{"id", "title_uk", "summary_uk"}, x3]}; ids must be in data/inbox.json.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
POSTS, INBOX = ROOT / "data" / "posts.json", ROOT / "data" / "inbox.json"
MONTHS = ["січня", "лютого", "березня", "квітня", "травня", "червня", "липня",
          "серпня", "вересня", "жовтня", "листопада", "грудня"]


def main():
    new = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))["items"]
    inbox = {i["id"]: i for i in json.loads(INBOX.read_text(encoding="utf-8"))}
    posts = json.loads(POSTS.read_text(encoding="utf-8")) if POSTS.exists() else []
    today = datetime.now(ZoneInfo("Europe/Kyiv"))
    pid = f"digest-{today:%Y-%m-%d}"
    if any(p["id"] == pid for p in posts):
        sys.exit(f"{pid} already exists; nothing to do")
    errors, items = [], []
    if len(new) != 3:
        errors.append(f"need exactly 3 items, got {len(new)}")
    for n in new:
        src = inbox.get(n.get("id"))
        title, summary = (n.get("title_uk") or "").strip(), (n.get("summary_uk") or "").strip()
        if not src:
            errors.append(f"{n.get('id')}: not in inbox")
        elif not 15 <= len(title) <= 90:
            errors.append(f"{n['id']}: title must be 15-90 characters, got {len(title)}")
        elif not 40 <= len(summary) <= 170:
            errors.append(f"{n['id']}: summary must be 40-170 characters, got {len(summary)}")
        else:
            items.append({"title_uk": title, "summary_uk": summary,
                          "source": src["source"], "link": src["link"]})
    if errors:
        sys.exit("Nothing saved:\n" + "\n".join(errors))
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    posts.insert(0, {
        "id": pid, "kind": "digest", "category": "digest",
        "title_uk": f"Ранковий дайджест: {today.day} {MONTHS[today.month - 1]}",
        "summary_uk": "Три головні події фінансового світу за минулу добу.",
        "source": "Fuzion Societe", "link": "https://t.me/fuzionsoc",
        "items": items, "published": now, "added": now})
    POSTS.write_text(json.dumps(posts[:120], ensure_ascii=False, indent=1), encoding="utf-8")
    print("added", pid)


if __name__ == "__main__":
    main()
