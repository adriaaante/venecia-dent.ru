#!/usr/bin/env python3
"""Подготовка фото врача для сайта «Венеция».

Единый стиль карточек врачей: портрет вырезается из исходного фона и
ставится на фирменный градиент лагуны, кадр — 4:5, голова и плечи,
лицо по центру с небольшим отступом сверху. Так выглядят все врачи
(см. drobkova / kendabaeva) — новые фото обязаны совпадать.

Шаги:
  1. Удаление фона:
       * если в исходнике уже есть прозрачность (>5% пикселей с alpha<10)
         — используем как есть;
       * иначе rembg (модель birefnet-portrait, лучшая для портретов;
         fallback isnet-general-use);
       * если rembg недоступен — простой chroma-key по светлым пикселям.
  2. Композит на градиент (верх #DBEAE5 → низ #F4F9F7) в кадре 4:5,
     лицо по центру, голова у верха. Масштаб лица регулируется --zoom
     (доля ширины кадра, которую занимает силуэт; по умолчанию 1.0 —
     для фото с пышными волосами/в полный разворот ставьте больше, напр.
     1.1–1.35, чтобы лицо совпало по размеру с остальными карточками).
  3. Две PNG: 480x600 (полная, doctors/<slug>.png) и 256x320 (миниатюра
     карточки, doctors/<slug>-thumb.png).

Использование:
    python scripts/prepare-doctor-photo.py <source> <slug> [--zoom 1.0] [--top 0.05]

Примеры:
    python scripts/prepare-doctor-photo.py /tmp/kilasoniya.png kilasoniya --zoom 1.16

Выходные файлы (от корня репо):
    assets/img/doctors/<slug>.png        (480x600, полная)
    assets/img/doctors/<slug>-thumb.png  (256x320, миниатюра карточки)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = REPO_ROOT / "assets" / "img" / "doctors"

# Фирменный градиент Венеции (светлая лагуна → алебастр), как у остальных врачей.
BG_TOP = (219, 234, 229)   # #DBEAE5
BG_BOT = (244, 249, 247)   # #F4F9F7

FULL = (480, 600)          # полная (4:5)
THUMB = (256, 320)         # миниатюра карточки (4:5)
SS = 2                     # суперсэмплинг для гладких краёв


def remove_background(im: Image.Image) -> Image.Image:
    """RGBA с прозрачным фоном (birefnet-portrait → isnet → chroma-key)."""
    im = im.convert("RGBA")
    alpha = im.split()[-1]
    transparent_share = sum(1 for v in alpha.getdata() if v < 10) / (im.width * im.height)
    if transparent_share > 0.05:
        return im
    try:
        from rembg import remove, new_session  # type: ignore
        import io
        buf = io.BytesIO()
        im.save(buf, format="PNG")
        try:
            session = new_session("birefnet-portrait")
        except Exception:
            session = new_session("isnet-general-use")
        out_bytes = remove(buf.getvalue(), session=session)
        return Image.open(io.BytesIO(out_bytes)).convert("RGBA")
    except Exception as exc:
        print(f"[warn] rembg недоступен ({exc}); chroma-key fallback", file=sys.stderr)
        return _chroma_key_fallback(im)


def _chroma_key_fallback(im: Image.Image, threshold: int = 235) -> Image.Image:
    im = im.convert("RGBA")
    pixels = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            r, g, b, _ = pixels[x, y]
            if r >= threshold and g >= threshold and b >= threshold:
                pixels[x, y] = (r, g, b, 0)
    return im


def _gradient(w: int, h: int) -> Image.Image:
    g = Image.new("RGB", (w, h))
    px = g.load()
    for y in range(h):
        t = y / (h - 1)
        px_row = (
            round(BG_TOP[0] + (BG_BOT[0] - BG_TOP[0]) * t),
            round(BG_TOP[1] + (BG_BOT[1] - BG_TOP[1]) * t),
            round(BG_TOP[2] + (BG_BOT[2] - BG_TOP[2]) * t),
        )
        for x in range(w):
            px[x, y] = px_row
    return g


def compose(cut: Image.Image, zoom: float, top_frac: float) -> Image.Image:
    """Силуэт на градиент лагуны, кадр 4:5, лицо по центру у верха."""
    bbox = cut.split()[-1].getbbox()
    if bbox is None:
        raise SystemExit("после удаления фона alpha-канал пустой")
    subj = cut.crop(bbox)
    w, h = FULL[0] * SS, FULL[1] * SS
    sw, sh = subj.size
    scale = (zoom * w) / sw
    subj = subj.resize((max(1, round(sw * scale)), max(1, round(sh * scale))), Image.LANCZOS)
    canvas = _gradient(w, h).convert("RGBA")
    x = (w - subj.width) // 2
    y = round(top_frac * h)
    canvas.alpha_composite(subj, (x, y))
    return canvas.convert("RGB")


def prepare(src: Path, slug: str, zoom: float, top_frac: float) -> None:
    raw = Image.open(src)
    print(f"[1/3] open: {src} {raw.size} {raw.mode}")
    print("[2/3] удаление фона")
    cut = remove_background(raw)
    print(f"[3/3] композит (zoom={zoom}, top={top_frac}) и сохранение")
    canvas = compose(cut, zoom, top_frac)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    full_path = OUT_DIR / f"{slug}.png"
    thumb_path = OUT_DIR / f"{slug}-thumb.png"
    full = canvas.resize(FULL, Image.LANCZOS)
    thumb = canvas.resize(THUMB, Image.LANCZOS)
    full.save(full_path, optimize=True)
    thumb.save(thumb_path, optimize=True)
    # WebP — то, на что ссылаются <img> на страницах (в ~15 раз легче PNG).
    # PNG остаётся для og:image (совместимость с мессенджерами/соцсетями).
    full.convert("RGB").save(OUT_DIR / f"{slug}.webp", "WEBP", quality=82, method=6)
    thumb.convert("RGB").save(OUT_DIR / f"{slug}-thumb.webp", "WEBP", quality=85, method=6)
    print(f"        {full_path} (+ .webp)")
    print(f"        {thumb_path} (+ .webp)")


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="Фото врача → градиент лагуны 4:5")
    p.add_argument("source")
    p.add_argument("slug")
    p.add_argument("--zoom", type=float, default=1.0,
                   help="доля ширины кадра под силуэт (по умолч. 1.0; больше = крупнее лицо)")
    p.add_argument("--top", type=float, default=0.05, help="отступ макушки сверху, доля высоты")
    a = p.parse_args(argv[1:])
    prepare(Path(a.source).expanduser(), a.slug.strip().lower(), a.zoom, a.top)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
