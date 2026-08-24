#!/usr/bin/env python3
"""Табличка с QR-кодом на отзывы — «Венеция», стойка регистрации.

Собирает из одного источника (URL карточки Яндекса) четыре файла в out/:
    venecia-qr-otzyv-A6.pdf   — печать 105×148 мм (стойка ресепшена)
    venecia-qr-otzyv-A5.pdf   — печать 148×210 мм (на стену / в кабинет)
    venecia-qr-otzyv.jpg      — превью карточки для чата и согласования
    venecia-qr-plain.png      — чистый QR 1200×1200 без оформления
                                (для соцсетей, визиток, чека)

Оформление — фирменное для Венеции (BRAND.md): алебастровый фон, рамка
лагуны, заголовок Prata, текст Onest, терракотовый ромб и арочная ниша
под QR. Знак клиники впечатан в центр кода — код собирается с уровнем
коррекции H, поэтому читается даже с закрытым центром (после сборки
скрипт сам проверяет читаемость, в том числе на уменьшенной копии).

    python3 _materials/qr/build-qr.py            # собрать всё
    python3 _materials/qr/build-qr.py --check    # только проверить QR
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

import qrcode
from qrcode.constants import ERROR_CORRECT_H
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.lib.utils import ImageReader

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
OUT = HERE / "out"
FONTS = REPO / "_materials" / "buklet" / "fonts"

# Куда ведёт код: отзывы в карточке Яндекс.Бизнеса (id организации — CLAUDE.md).
REVIEW_URL = "https://yandex.ru/profile/104110939502/reviews"

# Фирменные цвета (BRAND.md).
LAGOON = (15, 110, 102)
LAGOON_DEEP = (10, 74, 70)
INK = (19, 41, 42)
TERRA = (199, 91, 57)
BG = (247, 250, 248)
TINT = (217, 231, 226)
MUTED = (84, 103, 99)

DPI = 300
MM = DPI / 25.4          # пикселей в миллиметре
SS = 2                   # суперсэмплинг: рисуем крупнее, потом уменьшаем


def px(mm_value: float) -> int:
    return round(mm_value * MM * SS)


def font(name: str, size_mm: float, weight: int | None = None) -> ImageFont.FreeTypeFont:
    path = FONTS / name
    f = ImageFont.truetype(str(path), px(size_mm))
    if weight is not None:
        try:
            f.set_variation_by_axes([weight])
        except Exception:
            pass
    return f


def measure(f: ImageFont.FreeTypeFont, s: str, tracking: int = 0) -> tuple[int, int]:
    """Ширина и высота строки ровно по её краске (без пустых полей шрифта)."""
    x0, y0, x1, y1 = f.getbbox(s)
    w = x1 - x0 + tracking * max(0, len(s) - 1)
    return round(w), round(y1 - y0)


def text_center(d: ImageDraw.ImageDraw, cx: int, top: int, s: str,
                f: ImageFont.FreeTypeFont, fill, tracking: int = 0) -> int:
    """Строка по центру, верх краски ровно на `top`. Возвращает её высоту.

    Разрядка рисуется посимвольно, но от ОДНОЙ базовой линии (anchor «la»
    у всех букв общий): по отдельным bbox-ам дефис и точка уехали бы вверх.
    """
    x0, y0, x1, y1 = f.getbbox(s)
    base = top - y0
    w, h = measure(f, s, tracking)
    if tracking:
        x = cx - w / 2 - x0
        for ch in s:
            d.text((x, base), ch, font=f, fill=fill, anchor="la")
            x += d.textlength(ch, font=f) + tracking
    else:
        d.text((cx, base), s, font=f, fill=fill, anchor="ma")
    return h


def make_qr(size_px: int, logo: Image.Image | None) -> Image.Image:
    """QR с уровнем коррекции H и знаком клиники в центре."""
    qr = qrcode.QRCode(error_correction=ERROR_CORRECT_H, border=2, box_size=10)
    qr.add_data(REVIEW_URL)
    qr.make(fit=True)
    img = qr.make_image(fill_color=INK, back_color="white").convert("RGB")
    img = img.resize((size_px, size_px), Image.NEAREST)
    if logo is not None:
        # Знак 16% стороны: при коррекции H (30%) читаемость не страдает.
        side = round(size_px * 0.16)
        pad = round(side * 0.16)
        mark = logo.resize((side, side), Image.LANCZOS)
        plate = Image.new("RGB", (side + pad * 2, side + pad * 2), "white")
        plate.paste(mark, (pad, pad), mark)
        img.paste(plate, ((size_px - plate.width) // 2, (size_px - plate.height) // 2))
    return img


def arch(d: ImageDraw.ImageDraw, box, fill) -> None:
    """Арка: прямоугольник с полукруглым верхом — фирменный мотив Венеции."""
    x0, y0, x1, y1 = box
    r = (x1 - x0) / 2
    d.pieslice([x0, y0, x1, y0 + 2 * r], 180, 360, fill=fill)
    d.rectangle([x0, y0 + r, x1, y1], fill=fill)


def diamond(d: ImageDraw.ImageDraw, cx: int, cy: int, r: int, fill) -> None:
    d.polygon([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)], fill=fill)


def build_card(w_mm: float, h_mm: float) -> Image.Image:
    """Табличка целиком.

    Блоки сначала обмеряются, потом свободная высота раздаётся между ними
    по весам — поэтому A6 и A5 совпадают по композиции, а не растягиваются,
    и текст не наезжает на код, какой бы длины ни была строка.
    """
    k = h_mm / 148.0                      # масштаб относительно A6
    W, H = px(w_mm), px(h_mm)
    card = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(card)
    cx = W // 2

    # Рамка: линия лагуны + тонкий внутренний волосок.
    m = px(7 * k)
    d.rectangle([m, m, W - m, H - m], outline=LAGOON, width=px(0.7 * k))
    m2 = m + px(1.8 * k)
    d.rectangle([m2, m2, W - m2, H - m2], outline=TINT, width=px(0.25 * k))

    logo = Image.open(REPO / "assets" / "img" / "logo.png").convert("RGBA")
    f_name = font("Onest[wght].ttf", 5.0 * k, 700)
    f_sub = font("Onest[wght].ttf", 3.4 * k, 400)
    f_title = font("Prata-Regular.ttf", 8.2 * k)
    f_cta = font("Onest[wght].ttf", 4.2 * k, 600)
    f_note = font("Onest[wght].ttf", 3.1 * k, 400)
    f_dom = font("Onest[wght].ttf", 3.0 * k, 600)

    tile = px(15 * k)
    tr_name = px(0.9 * k)
    tr_dom = px(0.25 * k)
    qr_side = px(39 * k)
    niche_pad_top = px(9 * k)
    niche_pad_bottom = px(7 * k)
    niche_h = niche_pad_top + qr_side + niche_pad_bottom

    # (высота блока, вес зазора после него)
    blocks = [
        ("logo", tile, 1.0),
        ("name", measure(f_name, "ВЕНЕЦИЯ", tr_name)[1], 0.75),
        ("sub", measure(f_sub, "Семейная стоматология · Мытищи")[1], 1.35),
        ("rule", px(0.4 * k), 1.35),
        ("t1", measure(f_title, "Оцените нас")[1], 0.5),
        ("t2", measure(f_title, "на Яндексе")[1], 1.15),
        ("niche", niche_h, 1.2),
        ("cta", measure(f_cta, "Наведите камеру телефона")[1], 0.7),
        ("note", measure(f_note, "Ваш отзыв помогает нам становиться лучше")[1], 1.3),
        ("dom", measure(f_dom, "venecia-dent.ru", tr_dom)[1], 0.0),
    ]
    inner_top = m2 + px(5 * k)
    inner_bottom = H - m2 - px(5 * k)
    free = (inner_bottom - inner_top) - sum(b[1] for b in blocks)
    weights = sum(b[2] for b in blocks)
    if free < 0:
        raise SystemExit("блоки не помещаются в формат — уменьшите кегли")
    unit = free / weights

    y = float(inner_top)
    for kind, h, gap in blocks:
        y_i = round(y)
        if kind == "logo":
            card.paste(logo.resize((tile, tile), Image.LANCZOS),
                       (cx - tile // 2, y_i), logo.resize((tile, tile), Image.LANCZOS))
        elif kind == "name":
            text_center(d, cx, y_i, "ВЕНЕЦИЯ", f_name, INK, tracking=tr_name)
        elif kind == "sub":
            text_center(d, cx, y_i, "Семейная стоматология · Мытищи", f_sub, MUTED)
        elif kind == "rule":
            line_w = px(24 * k)
            d.line([(cx - line_w, y_i), (cx - px(4 * k), y_i)], fill=TINT, width=px(0.35 * k))
            d.line([(cx + px(4 * k), y_i), (cx + line_w, y_i)], fill=TINT, width=px(0.35 * k))
            diamond(d, cx, y_i, px(1.4 * k), TERRA)
        elif kind == "t1":
            text_center(d, cx, y_i, "Оцените нас", f_title, INK)
        elif kind == "t2":
            text_center(d, cx, y_i, "на Яндексе", f_title, INK)
        elif kind == "niche":
            niche_w = qr_side + px(20 * k)
            arch(d, [cx - niche_w // 2, y_i, cx + niche_w // 2, y_i + niche_h], (222, 236, 231))
            qr_y = y_i + niche_pad_top
            pad = px(3.2 * k)
            d.rectangle([cx - qr_side // 2 - pad, qr_y - pad,
                         cx + qr_side // 2 + pad, qr_y + qr_side + pad],
                        fill="white", outline=TINT, width=px(0.3 * k))
            card.paste(make_qr(qr_side, logo), (cx - qr_side // 2, qr_y))
        elif kind == "cta":
            text_center(d, cx, y_i, "Наведите камеру телефона", f_cta, TERRA)
        elif kind == "note":
            text_center(d, cx, y_i, "Ваш отзыв помогает нам становиться лучше", f_note, MUTED)
        elif kind == "dom":
            text_center(d, cx, y_i, "venecia-dent.ru", f_dom, LAGOON, tracking=tr_dom)
        y += h + gap * unit

    return card.resize((W // SS, H // SS), Image.LANCZOS)


def decodes(img: Image.Image) -> str:
    """Читаемость кода: то же, что делает камера телефона."""
    import numpy as np
    import cv2
    from PIL import ImageOps
    grey = ImageOps.expand(img.convert("L"), border=60, fill=255)
    ok, texts, _, _ = cv2.QRCodeDetector().detectAndDecodeMulti(np.array(grey))
    return texts[0] if ok and texts else ""


def save_pdf(card: Image.Image, path: Path, w_mm: float, h_mm: float) -> None:
    buf = io.BytesIO()
    card.save(buf, "PNG")
    buf.seek(0)
    c = pdfcanvas.Canvas(str(path), pagesize=(w_mm * mm, h_mm * mm))
    c.drawImage(ImageReader(buf), 0, 0, width=w_mm * mm, height=h_mm * mm)
    c.showPage()
    c.save()


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Табличка с QR на отзывы — Венеция")
    ap.add_argument("--check", action="store_true",
                    help="только проверить, что код читается")
    a = ap.parse_args(argv[1:])

    logo = Image.open(REPO / "assets" / "img" / "logo.png").convert("RGBA")
    plain = make_qr(1200, logo)
    got = decodes(plain)
    if got != REVIEW_URL:
        print(f"QR не читается или ведёт не туда: {got!r}", file=sys.stderr)
        return 1
    print(f"[✓] код читается: {got}")

    if a.check:
        for f in sorted(OUT.glob("*")):
            img = Image.open(f) if f.suffix in {".jpg", ".png"} else None
            if img and decodes(img) != REVIEW_URL:
                print(f"[!] {f.name}: код не читается", file=sys.stderr)
                return 1
        print("[✓] готовые файлы читаются")
        return 0

    OUT.mkdir(exist_ok=True)
    plain.save(OUT / "venecia-qr-plain.png", optimize=True)

    a6 = build_card(105, 148)
    a5 = build_card(148, 210)
    # Проверяем читаемость уже на свёрстанной табличке — и в размере
    # «камера издалека» (карточка ужата вчетверо).
    for name, img in (("A6", a6), ("A5", a5)):
        # 900 px по высоте ≈ табличка в кадре телефона с полуметра.
        scale = 900 / img.height
        small = img.resize((round(img.width * scale), 900), Image.LANCZOS)
        if decodes(img) != REVIEW_URL or decodes(small) != REVIEW_URL:
            print(f"[!] {name}: код на табличке не читается", file=sys.stderr)
            return 1
        print(f"[✓] {name}: код читается и в печати, и в кадре телефона")

    a6.save(OUT / "venecia-qr-otzyv.jpg", quality=92, subsampling=0)
    save_pdf(a6, OUT / "venecia-qr-otzyv-A6.pdf", 105, 148)
    save_pdf(a5, OUT / "venecia-qr-otzyv-A5.pdf", 148, 210)
    for f in sorted(OUT.iterdir()):
        print(f"        {f.relative_to(REPO)}  {f.stat().st_size // 1024} КБ")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
