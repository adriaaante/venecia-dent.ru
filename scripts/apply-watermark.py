#!/usr/bin/env python3
"""Apply Venecia-Dent watermark to portfolio before/after images.

Source images live in `assets/img/portfolio/_originals/` (un-watermarked).
Watermarked output is written to `assets/img/portfolio/<same-name>`.

This split keeps re-runs idempotent — the script always reads from
_originals/, so it never stacks watermarks on top of already-watermarked
images. To add a new portfolio photo: drop it into _originals/, run this
script, commit both copies.

Usage:
  python3 scripts/apply-watermark.py                 # process all
  python3 scripts/apply-watermark.py NAME.webp ...   # process specific files
"""

import sys
from pathlib import Path

from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "assets" / "img" / "portfolio" / "_originals"
OUT_DIR = ROOT / "assets" / "img" / "portfolio"
WM_PATH = ROOT / "assets" / "img" / "watermark.png"

# Знак Венеции — плотная плашка-логотип (в отличие от лёгкой линейной
# графики Angel/Versal), поэтому он меньше и прозрачнее: при 32%/78%
# перетягивал внимание с клинического фото. Ниже 20%/45% зуб перестаёт
# читаться и знак превращается в мутный квадрат — не опускать.
WM_WIDTH_RATIO = 0.24  # watermark width as fraction of image width
WM_MARGIN_RATIO = 0.03
WM_OPACITY = 0.62
# Под знаком мягкий тёмный halo, чтобы он оставался читаемым
# и на белом, и на тёмном фоне.
SHADOW_OPACITY = 0.38
SHADOW_BLUR_RATIO = 0.014  # радиус блюра как доля от ширины знака


def watermark_image(src: Path, out: Path, wm: Image.Image) -> None:
    img = Image.open(src).convert("RGBA")

    target_w = int(img.width * WM_WIDTH_RATIO)
    scale = target_w / wm.width
    target_h = int(wm.height * scale)
    wm_scaled = wm.resize((target_w, target_h), Image.LANCZOS)

    alpha = wm_scaled.split()[3].point(lambda p: int(p * WM_OPACITY))
    wm_scaled.putalpha(alpha)

    margin = int(img.width * WM_MARGIN_RATIO)
    pos = (img.width - target_w - margin, img.height - target_h - margin)

    blur_radius = max(2, int(target_w * SHADOW_BLUR_RATIO))
    pad = blur_radius * 4
    shadow_alpha = wm_scaled.split()[3].point(lambda p: int(p * SHADOW_OPACITY))
    shadow = Image.new("RGBA", (target_w + pad * 2, target_h + pad * 2), (0, 0, 0, 0))
    shadow.paste(Image.new("RGBA", wm_scaled.size, (0, 0, 0, 255)), (pad, pad), shadow_alpha)
    shadow = shadow.filter(ImageFilter.GaussianBlur(blur_radius))

    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    layer.paste(shadow, (pos[0] - pad, pos[1] - pad), shadow)
    layer.paste(wm_scaled, pos, wm_scaled)
    composed = Image.alpha_composite(img, layer).convert("RGB")

    ext = out.suffix.lower()
    if ext == ".webp":
        composed.save(out, "WEBP", quality=85, method=6)
    elif ext in (".jpg", ".jpeg"):
        composed.save(out, "JPEG", quality=90, optimize=True)
    else:
        composed.save(out)


def main() -> int:
    if not WM_PATH.exists():
        print(f"error: watermark not found at {WM_PATH}", file=sys.stderr)
        return 1
    if not SRC_DIR.is_dir():
        print(f"error: originals dir not found: {SRC_DIR}", file=sys.stderr)
        return 1

    wm = Image.open(WM_PATH).convert("RGBA")

    names = sys.argv[1:] or sorted(p.name for p in SRC_DIR.iterdir() if p.is_file())
    for name in names:
        src = SRC_DIR / name
        if not src.exists():
            print(f"skip (no source): {name}")
            continue
        out = OUT_DIR / name
        watermark_image(src, out, wm)
        print(f"  ✓ {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
