#!/usr/bin/env python3
"""Сторож ориентации сканов документов врачей.

Появился 24.08.2026: сертификат Twicare у Дробковой уехал на прод лежащим
на боку — я проверял партию сканов «пачкой» на контактном листе и не
разглядел. Глазами такое пропускается легко, машиной — нет.

Что делает:

1. **Ловит повороты на 90° и 270°** — считает, вдоль какой оси в документе
   идут строки текста (у строк резкие перепады яркости по горизонтали).
   Проверено на 20 сканах Дробковой: 20 из 20 намеренно повёрнутых
   поймано, ложных срабатываний нет. Поля 15% срезаются — рамки и цветные
   плашки сканов иначе перебивают сигнал.

2. **Собирает контактный лист** всех сканов врача в один PNG. Это нужно
   потому, что переворот на 180° (текст вверх ногами) машина по этой
   метрике НЕ отличает — там строки идут так же горизонтально. Такой
   случай ловится только глазами, но зато одним взглядом на лист.

    python3 scripts/docs-orientation-check.py            # все врачи
    python3 scripts/docs-orientation-check.py drobkova   # один врач
    python3 scripts/docs-orientation-check.py --no-sheet # без картинки

Код возврата 1 — если что-то лежит боком.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / 'assets' / 'img' / 'docs'
SHEET = DOCS / '_originals' / '_orientation-sheet.png'


def text_axis_score(im: Image.Image) -> float:
    """Во сколько раз «строчность» по горизонтали сильнее, чем по вертикали."""
    w, h = im.size
    im = im.crop((int(w * .15), int(h * .15), int(w * .85), int(h * .85)))
    g = np.asarray(im.convert('L').resize((480, 480)), dtype=float)
    horiz = np.abs(np.diff(g, axis=1)).sum(axis=1).var()
    vert = np.abs(np.diff(g, axis=0)).sum(axis=0).var()
    return horiz / max(vert, 1e-6)


def build_sheet(items: list[tuple[str, Path]]) -> None:
    """Контактный лист: посмотреть глазами, нет ли перевёрнутых на 180°."""
    thumbs = []
    for name, path in items:
        im = Image.open(path).convert('RGB')
        im.thumbnail((260, 260), Image.LANCZOS)
        thumbs.append((name, im))
    if not thumbs:
        return
    cols = min(5, len(thumbs))
    cw = 265
    ch = max(i.height for _, i in thumbs) + 24
    rows = (len(thumbs) + cols - 1) // cols
    sheet = Image.new('RGB', (cols * cw, rows * ch), 'white')
    d = ImageDraw.Draw(sheet)
    for n, (name, im) in enumerate(thumbs):
        x, y = (n % cols) * cw, (n // cols) * ch + 18
        sheet.paste(im, (x, y))
        d.text((x + 2, y - 14), name[:36], fill=(200, 0, 0))
    SHEET.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(SHEET)
    print(f'  контактный лист: {SHEET.relative_to(ROOT)} — посмотрите глазами,'
          f' машина не отличает переворот на 180°')


def main(argv: list[str]) -> int:
    slug = next((a for a in argv[1:] if not a.startswith('-')), None)
    make_sheet = '--no-sheet' not in argv

    originals = DOCS / '_originals'
    if not originals.exists():
        print('сканов нет'); return 0
    files = sorted(originals.glob(f'{slug}-*.webp' if slug else '*.webp'))
    files = [f for f in files if not f.name.startswith('_')]
    if not files:
        print('сканов нет'); return 0

    sideways = []
    items = []
    for f in files:
        im = Image.open(f)
        now = text_axis_score(im)
        turned = text_axis_score(im.rotate(90, expand=True))
        items.append((f.stem, f))
        if turned > now:
            sideways.append((f.stem, now, turned))

    print(f'проверено сканов: {len(files)}')
    for name, now, turned in sideways:
        print(f'  ✗ ЛЕЖИТ БОКОМ: {name}  (текущая {now:.2f} < повёрнутой {turned:.2f})')
    if not sideways:
        print('  ✓ все сканы стоят вертикально')

    if make_sheet:
        build_sheet(items)
    return 1 if sideways else 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
