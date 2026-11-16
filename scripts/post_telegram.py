#!/usr/bin/env python3
"""Send every not-yet-posted item in data/posts.json to the Telegram channel.

Needs TELEGRAM_BOT_TOKEN (GitHub secret) and TELEGRAM_CHAT (e.g. @fuzionsoc).
"""
import html
import json
import os
import sys
import time
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POSTS = ROOT / "data" / "posts.json"
STATE = ROOT / "data" / "posted.json"
MAX_PER_RUN = 8


def caption(p):
    e = html.escape
    return (f"<b>{e(p['title_uk'])}</b>\n\n{e(p['summary_uk'])}\n\n"
            f"<a href=\"{e(p['link'], quote=True)}\">Читати в оригіналі — {e(p['source'])}</a>")


def send_photo(token, chat, photo, text):
    boundary = uuid.uuid4().hex
    parts = []
    for k, v in (("chat_id", chat), ("caption", text), ("parse_mode", "HTML")):
        parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode())
    parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"photo\"; filename=\"card.png\"\r\n"
                 f"Content-Type: image/png\r\n\r\n".encode() + photo.read_bytes() + b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode())
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendPhoto", data=b"".join(parts),
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())["ok"]


def main():
    token, chat = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT")
    if not token or not chat:
        print("Telegram secrets not set; skipping.")
        return
    posts = json.loads(POSTS.read_text(encoding="utf-8"))
    done = set(json.loads(STATE.read_text())) if STATE.exists() else set()
    todo = [p for p in reversed(posts) if p["id"] not in done][:MAX_PER_RUN]  # oldest first
    errors = []
    for p in todo:
        try:
            send_photo(token, chat, ROOT / "cards" / f"{p['id']}.png", caption(p))
            done.add(p["id"])
            print("posted", p["id"])
            time.sleep(3)
        except Exception as e:
            detail = ""
            if hasattr(e, "read"):  # Telegram's own error text; never contains the token
                try:
                    detail = json.loads(e.read()).get("description", "")
                except Exception:
                    pass
            errors.append(f"{p['id']}: {type(e).__name__} {getattr(e, 'code', '')} {detail}".strip())
            print("FAILED", errors[-1], file=sys.stderr)
    live = {p["id"] for p in posts}
    STATE.write_text(json.dumps(sorted(done & live)))
    (ROOT / "data" / "last_run.json").write_text(json.dumps(
        {"tried": len(todo), "errors": errors}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
