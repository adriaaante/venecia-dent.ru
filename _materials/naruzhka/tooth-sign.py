# -*- coding: utf-8 -*-
"""
Фигурная боковая вывеска-зуб (панель-кронштейн) «Венеция».
Изделие режется по контуру зуба из логотипа. Высота зуба — 700 мм.

На выходе:
  - venecia-tooth-sign-print.pdf   — полноцветный макет 1:1 (растр 150 dpi,
    заливка на всю плиту: фигурный рез сам задаст форму, вылет не нужен);
  - venecia-tooth-sign-cutline.pdf — ВЕКТОРНЫЙ контур реза 1:1 (та же
    система координат, что у печатного файла);
  - tooth-sign-preview.png — превью (печать + контур реза красным).

Запуск: python3 tooth-sign.py
"""
from PIL import Image, ImageDraw, ImageFont
import cairosvg, os

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

def u2mm(x, y):
    return (x - U_X0) * MMU + MARGIN_MM, (y - U_Y0) * MMU + MARGIN_MM

def u2px(x, y):
    mx, my = u2mm(x, y)
    return mx * PXMM, my * PXMM

TOOTH_PATH = ("M256 96 c-33 0-51-18-86-18-54 0-84 42-84 96 0 84 41 111 55 178 "
              "8 39 19 60 40 60 31 0 28-80 75-80s44 80 75 80c21 0 32-21 40-60 "
              "14-67 55-94 55-178 0-54-30-96-84-96-35 0-53 18-86 18 z")
ARCH_PATH = ("M256 192 c-18 16-40 24-40 56 v56 a10 10 0 0 0 10 10 h60 "
             "a10 10 0 0 0 10-10 v-56 c0-32-22-40-40-56 z")

LAGOON = (15, 110, 102)
ALAB = '#F7FAF8'
HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, '..', 'buklet', 'fonts')

sc = MMU * PXMM  # px на юнит

# ── печатный макет: алебастровая плита + окно-арка + фонарик + имя ──
svg_print = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}"
     viewBox="0 0 {W} {H}">
  <rect width="{W}" height="{H}" fill="{ALAB}"/>
  <g transform="translate({u2px(0,0)[0] - 0*sc},{u2px(0,0)[1] - 0*sc}) scale({sc}) translate({-0},{-0})">
  </g>
  <g transform="translate({(MARGIN_MM)*PXMM - U_X0*sc},{(MARGIN_MM)*PXMM - U_Y0*sc}) scale({sc})">
    <defs>
      <linearGradient id="lag" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stop-color="#12776F"/>
        <stop offset="1" stop-color="#0A4A46"/>
      </linearGradient>
    </defs>
    <path d="{ARCH_PATH}" fill="url(#lag)"/>
    <path d="M256 136 l15 20 -15 20 -15 -20 z" fill="#C75B39"/>
  </g>
</svg>'''
open(os.path.join(HERE, '_print.svg'), 'w').write(svg_print)
cairosvg.svg2png(url=os.path.join(HERE, '_print.svg'),
                 write_to=os.path.join(HERE, '_print.png'),
                 output_width=W, output_height=H)

im = Image.open(os.path.join(HERE, '_print.png')).convert('RGB')
d = ImageDraw.Draw(im)

# «ВЕНЕЦИЯ» на теле зуба под аркой (Prata, лагуна, с разрядкой)
f = ImageFont.truetype(os.path.join(FONTS, 'Prata-Regular.ttf'), round(34 * sc))
text, ls = 'ВЕНЕЦИЯ', round(3 * sc)
widths = [d.textlength(ch, font=f) for ch in text]
total = sum(widths) + ls * (len(text) - 1)
cx_px, y_px = u2px(256, 326)
b = d.textbbox((0, 0), text, font=f)
x = cx_px - total / 2
for ch, w in zip(text, widths):
    d.text((x, y_px - b[1]), ch, font=f, fill=LAGOON)
    x += w + ls

im.save(os.path.join(HERE, 'venecia-tooth-sign-print.pdf'),
        resolution=DPI, title='Венеция — фигурная вывеска-зуб, печать 1:1')
im.save(os.path.join(HERE, '_print_flat.png'))
print('print OK', im.size, f'{PAGE_W_MM:.0f}x{PAGE_H_MM:.0f} mm')

# ── векторный контур реза (той же системы координат) ──
svg_cut = f'''<svg xmlns="http://www.w3.org/2000/svg"
     width="{PAGE_W_MM}mm" height="{PAGE_H_MM}mm"
     viewBox="0 0 {PAGE_W_MM} {PAGE_H_MM}">
  <g transform="translate({MARGIN_MM - U_X0 * MMU},{MARGIN_MM - U_Y0 * MMU}) scale({MMU})">
    <path d="{TOOTH_PATH}" fill="none" stroke="#FF00FF" stroke-width="0.3"/>
  </g>
</svg>'''
open(os.path.join(HERE, 'venecia-tooth-sign-cutline.svg'), 'w').write(svg_cut)
cairosvg.svg2pdf(url=os.path.join(HERE, 'venecia-tooth-sign-cutline.svg'),
                 write_to=os.path.join(HERE, 'venecia-tooth-sign-cutline.pdf'))
print('cutline OK')

# ── превью: печать + контур реза ──
cairosvg.svg2png(url=os.path.join(HERE, 'venecia-tooth-sign-cutline.svg'),
                 write_to=os.path.join(HERE, '_cut.png'),
                 output_width=W, output_height=H)
cut = Image.open(os.path.join(HERE, '_cut.png'))
prev = im.copy()
prev.paste(cut, (0, 0), cut)
prev.thumbnail((700, 800))
prev.save(os.path.join(HERE, 'tooth-sign-preview.png'))
for t in ('_print.svg', '_print.png', '_cut.png'):
    os.remove(os.path.join(HERE, t))
print('preview OK')
