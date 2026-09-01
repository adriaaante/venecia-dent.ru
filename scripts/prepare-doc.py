#!/usr/bin/env python3
"""
Диплом/сертификат врача → лёгкая пара картинок + карточка на странице.

Зачем скрипт, а не «положить jpg руками»: скан с телефона весит 1–7 МБ и
часто лежит боком. Если такую картинку поставить на страницу, страдает
скорость (а это фактор ранжирования и главный источник отказов на
мобильном). Здесь скан разворачивается, обрезается, светлеет и режется на
две версии:

  • `<имя>-thumb.webp`  — ширина 420 px, ~15–25 КБ. ТОЛЬКО она стоит в
    HTML, с `loading="lazy"` и явными width/height (без скачков вёрстки);
  • `<имя>.webp`        — до 1500 px, ~120–200 КБ. Грузится ИСКЛЮЧИТЕЛЬНО
    по клику, поэтому на вес страницы и Core Web Vitals не влияет.

Оригинал складывается в `_originals/` (на хостинг не деплоится).

    python3 scripts/prepare-doc.py скан.jpg --slug drobkova \
        --name ordinatura --caption "Диплом об окончании ординатуры, 2016" \
        [--rotate 90] [--crop 2,3,2,4] [--no-enhance]

`--rotate` — на сколько градусов повернуть ПРОТИВ часовой стрелки, чтобы
текст читался нормально. `--crop l,t,r,b` — сколько процентов срезать по
краям (убрать стол, пальцы, тёмную рамку).
"""
import argparse
import html
import json
import re
import sys
from pathlib import Path

from PIL import Image, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'assets' / 'img' / 'docs'
ORIG = OUT / '_originals'
FULL_MAX = 1500
THUMB_W = 420
THUMB_H = 315   # 4:3 — единая посадка карточек в ряду


# ── Знак клиники на сканах документов (владелец, 01.09.2026) ──────────────
# Документы врачей — такой же контент клиники, как фото портфолио: без
# знака их легко утащить на чужой сайт. Но документ должен ЧИТАТЬСЯ, это
# его главная задача, поэтому знак маленький, полупрозрачный и в углу.
#
# Оригиналы в `_originals/` остаются ЧИСТЫМИ: знак накладывается уже после
# их сохранения, поэтому повторный прогон не наслаивает его второй раз.
WM_PATH = ROOT / 'assets' / 'img' / 'watermark.png'
WM_MODE = 'plate'      # знак Венеции — плотная плашка, перекрашивать нечего: ставим как есть, но мельче
WM_BRAND = (15, 110, 102)      # лагуна #0F6E66 (в режиме plate не используется)
WM_RATIO = 0.1      # сторона знака как доля короткой стороны скана
WM_MARGIN = 0.032       # отступ от края — тоже от короткой стороны
WM_OPACITY_DARK = 0.34  # тёмный знак на светлом документе
WM_OPACITY_LIGHT = 0.50 # белый знак на тёмном (бывают чёрные сертификаты)


def _busy(im: Image.Image, box) -> float:
    """Насколько «занят» угол: больше перепадов яркости — хуже для знака."""
    import numpy as np
    a = np.asarray(im.convert('L').crop(box), dtype=float)
    if a.size == 0:
        return 1e9
    gx = np.abs(np.diff(a, axis=1)).mean() if a.shape[1] > 1 else 0
    gy = np.abs(np.diff(a, axis=0)).mean() if a.shape[0] > 1 else 0
    return gx + gy + a.std() * 0.15


def stamp(im: Image.Image) -> Image.Image:
    """Знак клиники в правом углу — в тот, который свободнее.

    Угол выбирается по картинке, а не жёстко: у дипломов верх занят гербом
    и шапкой, у сертификатов низ — подписями и логотипами организаторов.
    Ставить всегда в один угол значило бы регулярно накрывать чужой
    логотип или подпись.

    Режим `tint` (Ангел, Версаль): знак перекрашивается в один фирменный
    цвет и ставится как классический водяной знак. Родной знак этих клиник
    светлый и тонкий — на белой бумаге он просто растворялся. На тёмных
    сертификатах (бывают чёрные) знак автоматически становится белым.

    Режим `plate` (Венеция): её знак — плотная плашка, у которой почти нет
    прозрачного фона, перекрашивать нечего. Ставим саму плашку, но мельче.
    """
    import numpy as np
    if not WM_PATH.is_file():
        return im
    wm = Image.open(WM_PATH).convert('RGBA')
    base = im.convert('RGBA')
    short = min(base.width, base.height)
    w = int(short * WM_RATIO)
    h = int(wm.height * w / wm.width)
    m = int(short * WM_MARGIN)
    corners = {'br': (base.width - w - m, base.height - h - m),
                'tr': (base.width - w - m, m)}
    x, y = corners[min(corners, key=lambda c: _busy(
        base, (corners[c][0], corners[c][1], corners[c][0] + w, corners[c][1] + h)))]

    scaled = wm.resize((w, h), Image.LANCZOS)
    if WM_MODE == 'plate':
        mark = scaled.copy()
        mark.putalpha(scaled.split()[3].point(lambda p: int(p * WM_OPACITY_LIGHT)))
    else:
        lum = np.asarray(base.convert('L').crop((x, y, x + w, y + h)), dtype=float).mean()
        on_light = lum > 120
        color = WM_BRAND if on_light else (255, 255, 255)
        op = WM_OPACITY_DARK if on_light else WM_OPACITY_LIGHT
        mark = Image.new('RGBA', (w, h), color + (255,))
        mark.putalpha(scaled.split()[3].point(lambda p: int(p * op)))

    out = base.copy()
    out.alpha_composite(mark, (x, y))
    return out.convert('RGB')


def build_images(src: Path, key: str, rotate: int, crop: str, enhance: bool):
    im = Image.open(src)
    im = ImageOps.exif_transpose(im).convert('RGB')
    if rotate:
        im = im.rotate(rotate, expand=True)
    if crop:
        l, t, r, b = [float(x) for x in crop.split(',')]
        w, h = im.size
        im = im.crop((int(w * l / 100), int(h * t / 100),
                      int(w * (1 - r / 100)), int(h * (1 - b / 100))))
    if enhance:
        # Сканы с телефона уходят в серый и желтизну — подтягиваем светлоту,
        # чтобы бумага читалась белой и карточки выглядели однообразно.
        im = ImageOps.autocontrast(im, cutoff=(0.5, 0.6))

    OUT.mkdir(parents=True, exist_ok=True)
    ORIG.mkdir(parents=True, exist_ok=True)
    im.save(ORIG / f'{key}.webp', 'WEBP', quality=90, method=4)   # оригинал БЕЗ знака

    im = stamp(im)
    full = im.copy()
    full.thumbnail((FULL_MAX, FULL_MAX), Image.LANCZOS)
    # Миниатюры приводим к одному кадру 4:3 на белом: документы бывают и
    # альбомные, и книжные, а в ряду карточек они должны стоять ровно.
    # Именно вписываем, а не обрезаем — документ должен читаться целиком.
    thumb = ImageOps.contain(im.copy(), (THUMB_W, THUMB_H), Image.LANCZOS)
    canvas = Image.new('RGB', (THUMB_W, THUMB_H), (255, 255, 255))
    canvas.paste(thumb, ((THUMB_W - thumb.width) // 2, (THUMB_H - thumb.height) // 2))
    thumb = canvas

    f_path, t_path = OUT / f'{key}.webp', OUT / f'{key}-thumb.webp'
    full.save(f_path, 'WEBP', quality=72, method=6)
    thumb.save(t_path, 'WEBP', quality=70, method=6)
    return (f_path, full.size), (t_path, thumb.size)


def card_html(key: str, caption: str, size) -> str:
    w, h = size
    caption = html.escape(caption, quote=True)
    return (f'<li><a class="doc" data-doc href="../assets/img/docs/{key}.webp" '
            f'target="_blank" rel="noopener" data-doc-caption="{caption}">'
            f'<span class="doc__frame"><img loading="lazy" decoding="async" '
            f'width="{w}" height="{h}" src="../assets/img/docs/{key}-thumb.webp" '
            f'alt="{caption}"></span>'
            f'<span class="doc__cap">{caption}</span></a></li>')


def put_on_page(page: Path, key: str, html: str, heading: str) -> None:
    s = page.read_text(encoding='utf-8')
    block = re.search(r'<ul class="docs" data-docs>(.*?)</ul>', s, re.S)
    if block:
        inner = block.group(1)
        inner = re.sub(rf'<li><a class="doc"[^>]*href="\.\./assets/img/docs/{key}\.webp".*?</li>',
                       '', inner, flags=re.S)
        s = s[:block.start()] + f'<ul class="docs" data-docs>{inner}{html}</ul>' + s[block.end():]
    else:
        # Ставим галерею после блоков квалификации, а если их нет (у врача
        # ещё не подтверждены данные) — перед списком услуг, чтобы сканы
        # всё равно оказались в осмысленном месте страницы.
        anchor = None
        for pat in (r'(<h2>Документы и квалификация</h2><ul>.*?</ul>)',
                    r'(<h2>Образование</h2><ul>.*?</ul>)'):
            anchor = re.search(pat, s, re.S)
            if anchor:
                pos = anchor.end()
                break
        else:
            svc = re.search(r'<h2>Услуги, которые ведёт врач</h2>', s)
            if not svc:
                sys.exit(f'{page.name}: не нашёл, куда вставить галерею документов')
            pos = svc.start()
        s = (s[:pos] + f'<h2>{heading}</h2>'
             f'<ul class="docs" data-docs>{html}</ul>' + s[pos:])
    page.write_text(s, encoding='utf-8')


def put_in_schema(page: Path, caption: str) -> None:
    """Документ врача → JSON-LD hasCredential у Person (сигнал экспертности)."""
    s = page.read_text(encoding='utf-8')
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', s, re.S):
        try:
            data = json.loads(m.group(1))
        except json.JSONDecodeError:
            continue
        if data.get('@type') != 'Person':
            continue
        creds = data.setdefault('hasCredential', [])
        if any(c.get('name') == caption for c in creds):
            return
        creds.append({'@type': 'EducationalOccupationalCredential', 'name': caption})
        new = json.dumps(data, ensure_ascii=False, indent=2)
        page.write_text(s[:m.start(1)] + '\n' + new + '\n  ' + s[m.end(1):], encoding='utf-8')
        return


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('src')
    ap.add_argument('--slug', required=True, help='врач: имя файла в doctors/ без .html')
    ap.add_argument('--name', required=True, help='короткий ключ документа, латиницей')
    ap.add_argument('--caption', required=True)
    ap.add_argument('--rotate', type=int, default=0)
    ap.add_argument('--crop', default='')
    ap.add_argument('--heading', default='Дипломы и сертификаты')
    ap.add_argument('--no-enhance', action='store_true')
    a = ap.parse_args()

    key = f'{a.slug}-{a.name}'
    (fp, fsize), (tp, tsize) = build_images(Path(a.src), key, a.rotate, a.crop, not a.no_enhance)
    page = ROOT / 'doctors' / f'{a.slug}.html'
    if not page.is_file():
        sys.exit(f'нет страницы врача: {page}')
    put_on_page(page, key, card_html(key, a.caption, tsize), a.heading)
    put_in_schema(page, a.caption)

    print(f'  ✓ {fp.name}  {fsize[0]}×{fsize[1]}, {fp.stat().st_size // 1024} КБ (по клику)')
    print(f'  ✓ {tp.name}  {tsize[0]}×{tsize[1]}, {tp.stat().st_size // 1024} КБ (на странице)')
    print(f'  ✓ карточка и JSON-LD добавлены в doctors/{a.slug}.html')
    print('  → не забудьте: python3 scripts/asset-version.py')
    return 0


if __name__ == '__main__':
    sys.exit(main())
