#!/usr/bin/env python3
"""Draw a branded 1200x675 card for every post in data/posts.json that lacks one."""
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
POSTS = ROOT / "data" / "posts.json"
CARDS = ROOT / "cards"
W, H, PAD = 1200, 675, 80

NAVY, NAVY_2 = (11, 31, 58), (18, 46, 84)
GOLD, IVORY, MIST = (200, 164, 90), (247, 243, 234), (154, 168, 189)

CATEGORY_UK = {
    "markets": "РИНКИ", "economy": "ЕКОНОМІКА", "banks": "БАНКИ",
    "policy": "МОНЕТАРНА ПОЛІТИКА", "companies": "КОМПАНІЇ",
    "energy": "ЕНЕРГЕТИКА", "crypto": "КРИПТО", "ukraine": "УКРАЇНА",
    "world": "СВІТ",
}


def font(name, size, weight=None):
    f = ImageFont.truetype(str(ROOT / "fonts" / name), size)
    if weight:
        try:
            axes = [a["default"] for a in f.get_variation_axes()]
            names = [a["name"] for a in f.get_variation_axes()]
            for i, n in enumerate(names):
                n = n.decode() if isinstance(n, bytes) else n
                if n.lower().startswith("weight"):
                    axes[i] = weight
            f.set_variation_by_axes(axes)
        except Exception:
            pass
    return f


def wrap(draw, text, fnt, width):
    lines, line = [], ""
    for word in text.split():
        trial = f"{line} {word}".strip()
        if draw.textlength(trial, font=fnt) <= width or not line:
            line = trial
        else:
            lines.append(line)
            line = word
    return lines + [line] if line else lines


def spaced(draw, xy, text, fnt, fill, gap=3):
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=fnt, fill=fill)
        x += draw.textlength(ch, font=fnt) + gap
    return x


def make(post, out):
    img = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(img)
    for y in range(H):  # soft vertical gradient
        t = y / H
        d.line([(0, y), (W, y)], fill=tuple(int(a + (b - a) * t) for a, b in zip(NAVY_2, NAVY)))
    # fine chart-like rule pattern, bottom right
    for i in range(9):
        x = W - PAD - i * 46
        h = 40 + (i * 37 % 150)
        d.line([(x, H - 150), (x, H - 150 - h)], fill=(28, 60, 104), width=2)
    d.rectangle([PAD, PAD, PAD + 64, PAD + 5], fill=GOLD)

    label = font("Inter.ttf", 24, 600)
    cat = CATEGORY_UK.get(post.get("category", ""), "ФІНАНСИ")
    spaced(d, (PAD, PAD + 28), cat, label, GOLD, gap=4)

    title = post["title_uk"]
    for size in (64, 56, 48, 42, 36):
        tf = font("PlayfairDisplay.ttf", size, 700)
        lines = wrap(d, title, tf, W - 2 * PAD)
        if len(lines) <= (4 if size > 42 else 5):
            break
    y = PAD + 96
    for ln in lines[:5]:
        d.text((PAD, y), ln, font=tf, fill=IVORY)
        y += int(size * 1.22)

    d.line([(PAD, H - 118), (W - PAD, H - 118)], fill=(44, 72, 112), width=1)
    small = font("Inter.ttf", 26, 500)
    d.text((PAD, H - 92), f"Джерело: {post['source']}", font=small, fill=MIST)
    brand = font("PlayfairDisplay.ttf", 34, 700)
    bw = d.textlength("ФінПульс", font=brand)
    d.text((W - PAD - bw, H - 98), "ФінПульс", font=brand, fill=GOLD)
    img.save(out, "PNG", optimize=True)


def main():
    posts = json.loads(POSTS.read_text(encoding="utf-8"))
    CARDS.mkdir(exist_ok=True)
    made = 0
    for p in posts:
        out = CARDS / f"{p['id']}.png"
        if not out.exists():
            make(p, out)
            made += 1
    keep = {f"{p['id']}.png" for p in posts}
    for f in CARDS.glob("*.png"):
        if f.name not in keep:
            f.unlink()
    print(f"{made} cards drawn")


if __name__ == "__main__":
    main()
