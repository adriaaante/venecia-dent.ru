# -*- coding: utf-8 -*-
"""
Фигурная консольная вывеска-зуб (панель-кронштейн) «Венеция».
Изделие режется по контуру зуба из логотипа. Высота зуба — 700 мм.

⚠️ Фасад клиники ЧЁРНЫЙ (владелец, 11.08.2026) — тёмные варианты зуба на
нём проваливаются, поэтому собираем несколько цветовых схем и смотрим их
на чёрной стене (см. tooth-sign-variants.py).

Для КАЖДОЙ схемы на выходе:
  - venecia-tooth-sign-<схема>-print.pdf — макет 1:1 (растр 150 dpi);
  - tooth-<схема>-cut.png — вид готового изделия (вырезано по контуру).
Контур реза ОДИН на все схемы (форма не меняется):
  - venecia-tooth-sign-cutline.pdf / .svg — вектор 1:1.

Запуск: python3 tooth-sign.py
"""
from PIL import Image, ImageDraw, ImageFont
import cairosvg, os
import numpy as np
from scipy.ndimage import distance_transform_edt

# ── геометрия ─────────────────────────────────────────────
# Контур зуба из logo.svg: bbox в юнитах viewBox: x 86..426, y 78..434
U_X0, U_Y0, U_W, U_H = 86, 78, 340, 356
SIGN_H_MM = 700.0                          # высота зуба на изделии
MMU = SIGN_H_MM / U_H                      # мм на юнит  (≈1.966)
MARGIN_MM = 10.0                           # поле листа вокруг контура
DPI = 150
PXMM = DPI / 25.4

PAGE_W_MM = U_W * MMU + 2 * MARGIN_MM      # ≈ 688 мм
PAGE_H_MM = U_H * MMU + 2 * MARGIN_MM      # = 720 мм
W, H = round(PAGE_W_MM * PXMM), round(PAGE_H_MM * PXMM)
sc = MMU * PXMM                            # px на юнит

def u2px(x, y):
    return ((x - U_X0) * MMU + MARGIN_MM) * PXMM, ((y - U_Y0) * MMU + MARGIN_MM) * PXMM

TOOTH_PATH = ("M256 96 c-33 0-51-18-86-18-54 0-84 42-84 96 0 84 41 111 55 178 "
              "8 39 19 60 40 60 31 0 28-80 75-80s44 80 75 80c21 0 32-21 40-60 "
              "14-67 55-94 55-178 0-54-30-96-84-96-35 0-53 18-86 18 z")
ARCH_PATH = ("M256 192 c-18 16-40 24-40 56 v56 a10 10 0 0 0 10 10 h60 "
             "a10 10 0 0 0 10-10 v-56 c0-32-22-40-40-56 z")
LANTERN_PATH = "M256 142 l15 20 -15 20 -15 -20 z"

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, '..', 'buklet', 'fonts')

# ── цветовые схемы (палитра BRAND.md: лагуна/терракота/алебастр) ──
# body — (верх, низ) градиента тела зуба; arch — цвет окна-арки;
# lantern — ромб-фонарик; text — «ВЕНЕЦИЯ»; border — кайма по контуру (или None)
SCHEMES = {
    'alabaster': dict(
        title='Алебастр (белый зуб)',
        body=('#FFFFFF', '#EDF4F1'), arch='#0F6E66', lantern='#C75B39',
        text=(15, 110, 102), border=None),
    'alabaster-edge': dict(
        title='Алебастр с лагуновой каймой',
        body=('#FFFFFF', '#EDF4F1'), arch='#0F6E66', lantern='#C75B39',
        text=(15, 110, 102), border=('#0F6E66', 9)),   # (цвет, ширина в юнитах)
    'lagoon': dict(
        title='Лагуна (зелёный зуб)',
        body=('#12776F', '#0A4A46'), arch='#F7FAF8', lantern='#C75B39',
        text=(247, 250, 248), border=None),
    'terracotta': dict(
        title='Терракота',
        body=('#C9603E', '#A84B2F'), arch='#F7FAF8', lantern='#0F6E66',
        text=(247, 250, 248), border=None),
}

# ── маска зуба и карта расстояний до реза (одна на все схемы) ──
def _render(svg, w=W, h=H):
    p = os.path.join(HERE, '_tmp.svg')
    open(p, 'w').write(svg)
    out = os.path.join(HERE, '_tmp.png')
    cairosvg.svg2png(url=p, write_to=out, output_width=w, output_height=h)
    img = Image.open(out).copy()
    os.remove(p); os.remove(out)
    return img

G = f'translate({MARGIN_MM * PXMM - U_X0 * sc},{MARGIN_MM * PXMM - U_Y0 * sc}) scale({sc})'
mask = _render(f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <g transform="{G}"><path d="{TOOTH_PATH}" fill="#000"/></g></svg>''').split()[3]
mask = mask.point(lambda a: 255 if a > 128 else 0)
DIST = distance_transform_edt(np.asarray(mask) > 0)
SAFE_MM = 20
SAFE_PX = round(SAFE_MM * PXMM)


def build(key):
    s = SCHEMES[key]
    border = ''
    if s['border']:
        bc, bw = s['border']
        # кайма рисуется поверх тела и обрезается маской зуба ниже
        border = f'<path d="{TOOTH_PATH}" fill="none" stroke="{bc}" stroke-width="{bw * 2}"/>'

    im = _render(f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <defs><linearGradient id="b" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="{s['body'][0]}"/><stop offset="1" stop-color="{s['body'][1]}"/>
  </linearGradient></defs>
  <rect width="{W}" height="{H}" fill="url(#b)"/>
  <g transform="{G}">
    {border}
    <path d="{ARCH_PATH}" fill="{s['arch']}"/>
    <path d="{LANTERN_PATH}" fill="{s['lantern']}"/>
  </g></svg>''').convert('RGB')
    d = ImageDraw.Draw(im)

    # «ВЕНЕЦИЯ» на коронке: кегль подбирается так, чтобы буквы не подошли
    # к линии реза ближе, чем SAFE_MM (проверка по карте расстояний)
    text = 'ВЕНЕЦИЯ'
    size_u = 30
    while size_u >= 16:
        f = ImageFont.truetype(os.path.join(FONTS, 'Prata-Regular.ttf'), round(size_u * sc))
        ls = round(size_u / 11 * sc)
        layer = Image.new('L', (W, H), 0)
        ld = ImageDraw.Draw(layer)
        widths = [ld.textlength(ch, font=f) for ch in text]
        total = sum(widths) + ls * (len(text) - 1)
        b = ld.textbbox((0, 0), text, font=f)
        cx_px, y_px = u2px(256, 108)
        x = cx_px - total / 2
        for ch, w_ in zip(text, widths):
            ld.text((x, y_px - b[1]), ch, font=f, fill=255)
            x += w_ + ls
        ink = np.asarray(layer) > 0
        min_dist = DIST[ink].min() if ink.any() else 0
        if min_dist >= SAFE_PX:
            break
        size_u -= 1
    assert min_dist >= SAFE_PX, f'{key}: «ВЕНЕЦИЯ» не влезает в контур с запасом'
    im.paste(Image.new('RGB', (W, H), s['text']), (0, 0), layer)

    im.save(os.path.join(HERE, f'venecia-tooth-sign-{key}-print.pdf'),
            resolution=DPI, title=f'Венеция — вывеска-зуб, схема «{s["title"]}», 1:1')

    # вид готового изделия: печать, вырезанная по контуру
    cut = Image.new('RGBA', im.size, (0, 0, 0, 0))
    cut.paste(im, (0, 0), mask)
    cut = cut.crop(mask.getbbox())
    cut.save(os.path.join(HERE, f'tooth-{key}-cut.png'))
    print(f'{key:16s} {s["title"]:32s} кегль {size_u}u, запас до реза {min_dist/PXMM:.0f} мм')


if __name__ == '__main__':
    for k in SCHEMES:
        build(k)

    # ── контур реза: один на все схемы ──
    svg_cut = f'''<svg xmlns="http://www.w3.org/2000/svg"
     width="{PAGE_W_MM}mm" height="{PAGE_H_MM}mm" viewBox="0 0 {PAGE_W_MM} {PAGE_H_MM}">
  <g transform="translate({MARGIN_MM - U_X0 * MMU},{MARGIN_MM - U_Y0 * MMU}) scale({MMU})">
    <path d="{TOOTH_PATH}" fill="none" stroke="#FF00FF" stroke-width="0.3"/>
  </g></svg>'''
    open(os.path.join(HERE, 'venecia-tooth-sign-cutline.svg'), 'w').write(svg_cut)
    cairosvg.svg2pdf(url=os.path.join(HERE, 'venecia-tooth-sign-cutline.svg'),
                     write_to=os.path.join(HERE, 'venecia-tooth-sign-cutline.pdf'))
    print('cutline OK (общий для всех схем)')
