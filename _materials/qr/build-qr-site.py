#!/usr/bin/env python3
"""Чистый QR-код на сайт «Венеции» — без оформления и надписей.

В отличие от build-qr.py (табличка на отзывы для стойки) это просто код:
его кладут на визитку, буклет, чек, наклейку, в презентацию — туда, где
оформление уже своё.

    python3 _materials/qr/build-qr-site.py           # собрать
    python3 _materials/qr/build-qr-site.py --check   # только проверить

Что появляется в out/:
    venecia-qr-site.png       2000×2000, чёрный код на белом — базовый
    venecia-qr-site.svg       вектор: печатать любым размером без пикселей
    venecia-qr-site-logo.png  2000×2000 со знаком клиники в центре

⚠️ Код собирается с уровнем коррекции H (30%) — только поэтому знак в
центре не мешает чтению. Уровень не понижать. После сборки скрипт сам
проверяет, что код распознаётся — и в печатном разрешении, и на копии
высотой 900 px (примерно то, что видит камера телефона с полуметра); если
нет — падает, а не отдаёт нечитаемый файл.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import qrcode
import qrcode.image.svg
from qrcode.constants import ERROR_CORRECT_H
from PIL import Image, ImageOps

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
OUT = HERE / "out"

SITE_URL = "https://venecia-dent.ru/"

INK = (19, 41, 42)      # чернила BRAND.md — почти чёрный, контраст в норме
SIZE = 2000
QUIET = 4               # поля вокруг кода в модулях (стандарт — не меньше 4)


def qr_object() -> qrcode.QRCode:
    qr = qrcode.QRCode(error_correction=ERROR_CORRECT_H, border=QUIET, box_size=10)
    qr.add_data(SITE_URL)
    qr.make(fit=True)
    return qr


def make_png(size_px: int, logo: Image.Image | None) -> Image.Image:
    img = qr_object().make_image(fill_color=INK, back_color="white").convert("RGB")
    img = img.resize((size_px, size_px), Image.NEAREST)
    if logo is not None:
        side = round(size_px * 0.16)
        pad = round(side * 0.16)
        mark = logo.resize((side, side), Image.LANCZOS)
        plate = Image.new("RGB", (side + pad * 2, side + pad * 2), "white")
        plate.paste(mark, (pad, pad), mark)
        img.paste(plate, ((size_px - plate.width) // 2, (size_px - plate.height) // 2))
    return img


def decodes(img: Image.Image) -> str:
    """Читаемость кода: то же, что делает камера телефона."""
    import numpy as np
    import cv2
    grey = ImageOps.expand(img.convert("L"), border=60, fill=255)
    ok, texts, _, _ = cv2.QRCodeDetector().detectAndDecodeMulti(np.array(grey))
    return texts[0] if ok and texts else ""


def check(img: Image.Image, label: str) -> bool:
    small = img.resize((900, 900), Image.LANCZOS)
    for name, test in (("печать", img), ("камера с полуметра", small)):
        got = decodes(test)
        if got != SITE_URL:
            print(f"  ✗ {label}, {name}: код не читается (получено {got!r})")
            return False
    print(f"  ✓ {label}: читается, ведёт на {SITE_URL}")
    return True


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Чистый QR на сайт Венеции")
    ap.add_argument("--check", action="store_true", help="только проверить код")
    a = ap.parse_args(argv[1:])

    logo = Image.open(REPO / "assets" / "img" / "logo.png").convert("RGBA")
    plain = make_png(SIZE, None)
    withlogo = make_png(SIZE, logo)

    print(f"QR на {SITE_URL}")
    ok = check(plain, "без знака") & check(withlogo, "со знаком клиники")
    if not ok:
        return 1
    if a.check:
        return 0

    OUT.mkdir(exist_ok=True)
    plain.save(OUT / "venecia-qr-site.png", optimize=True)
    withlogo.save(OUT / "venecia-qr-site-logo.png", optimize=True)
    qr_object().make_image(image_factory=qrcode.image.svg.SvgPathImage) \
        .save(str(OUT / "venecia-qr-site.svg"))

    for f in ("venecia-qr-site.png", "venecia-qr-site.svg", "venecia-qr-site-logo.png"):
        p = OUT / f
        print(f"  · {p.relative_to(REPO)}  {p.stat().st_size // 1024} КБ")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
