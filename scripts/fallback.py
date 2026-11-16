#!/usr/bin/env python3
"""If no edited posts arrived for STALE_HOURS, publish the top inbox headlines
as they are (original language) so the channel does not go quiet."""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POSTS, INBOX = ROOT / "data" / "posts.json", ROOT / "data" / "inbox.json"
STALE_HOURS, TAKE, KEEP = 9, 3, 120


def main():
    posts = json.loads(POSTS.read_text(encoding="utf-8")) if POSTS.exists() else []
    inbox = json.loads(INBOX.read_text(encoding="utf-8")) if INBOX.exists() else []
    now = datetime.now(timezone.utc)
    newest = max((p.get("added", "") for p in posts), default="")
    # Nothing published yet (first run) or recent edited posts exist: do nothing.
    if not newest or now - datetime.fromisoformat(newest) < timedelta(hours=STALE_HOURS):
        return
    have = {p["id"] for p in posts}
    fresh = [i for i in inbox if i["id"] not in have
             and now - datetime.fromisoformat(i["published"]) < timedelta(hours=24)]
    fresh.sort(key=lambda i: (i["weight"], i["published"]), reverse=True)
    picked, used = [], set()
    for i in fresh:  # at most one per source
        if i["source"] not in used:
            picked.append(i)
            used.add(i["source"])
        if len(picked) == TAKE:
            break
    for i in picked:
        posts.insert(0, {
            "id": i["id"], "source": i["source"], "link": i["link"],
            "title_uk": i["title"], "summary_uk": i["teaser"] or "Деталі — за посиланням.",
            "category": "world", "published": i["published"],
            "added": now.isoformat(timespec="seconds"), "fallback": True,
        })
    POSTS.write_text(json.dumps(posts[:KEEP], ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"fallback added {len(picked)}")


if __name__ == "__main__":
    main()
