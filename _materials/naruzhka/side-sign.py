# -*- coding: utf-8 -*-
"""
Боковая вывеска (панель-кронштейн) «Венеция» — вертикальная, двусторонняя
(обе стороны одинаковые, макет один). Размер изделия 600×800 мм,
в файле вылеты по 10 мм с каждой стороны (620×820 мм), 150 dpi 1:1 —
стандарт для изготовления вывесок/световых коробов.
Запуск: python3 side-sign.py
"""
from PIL import Image, ImageDraw, ImageFont
import os

DPI = 150
MM = DPI / 25.4
BLEED = round(10 * MM)                    # 59 px
W, H = round(620 * MM), round(820 * MM)   # 3661×4842

LAGOON_TOP = (18, 119, 111)   # #12776F — градиент логотипа
LAGOON_BOT = (10, 74, 70)     # #0A4A46
ALAB = (247, 250, 248)
TERRA = (199, 91, 57)
TINT = (217, 231, 226)

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, '..', 'buklet', 'fonts')

def prata(size):
    return ImageFont.truetype(os.path.join(FONTS, 'Prata-Regular.ttf'), size)

def onest(size, weight=400):
    f = ImageFont.truetype(os.path.join(FONTS, 'Onest[wght].ttf'), size)
    f.set_variation_by_axes([weight])
    return f

def fit_font(d, text, maker, target_w, ls=0, start=100):
    """Подбирает кегль так, чтобы строка (с трекингом) заняла target_w."""
    size = start
    while True:
        f = maker(size)
        w = sum(d.textlength(ch, font=f) for ch in text) + ls * (len(text) - 1)
        if w >= target_w:
            return maker(size - 2), size - 2
        size += 2

def ctext_ls(d, cx, y, text, font, fill, ls):
    widths = [d.textlength(ch, font=font) for ch in text]
    total = sum(widths) + ls * (len(text) - 1)
    x = cx - total / 2
    for ch, w in zip(text, widths):
        d.text((x, y), ch, font=font, fill=fill)
        x += w + ls

# ── фон: вертикальный градиент лагуны ──
grad = Image.new('RGB', (1, H))
for y in range(H):
    t = y / (H - 1)
    grad.putpixel((0, y), tuple(round(a + (b - a) * t) for a, b in zip(LAGOON_TOP, LAGOON_BOT)))
im = grad.resize((W, H))
d = ImageDraw.Draw(im)
cx = W / 2

# ── белый знак: зуб с окном-аркой + терракотовый фонарик ──
mark = Image.open(os.path.join(HERE, '..', 'vizitki', 'logo-white-mark.png')).convert('RGBA')
mh = round(H * 0.34)
mw = round(mark.width * mh / mark.height)
mark = mark.resize((mw, mh), Image.LANCZOS)
my = round(H * 0.115)
im.paste(mark, (round(cx - mw / 2), my), mark)

# ── «СТОМАТОЛОГИЯ» — категория, крупно во всю ширину ──
content_w = W - 2 * (BLEED + round(40 * MM))
ls1 = 26
f_cat, _ = fit_font(d, 'СТОМАТОЛОГИЯ', lambda s: onest(s, 640), content_w, ls=ls1, start=200)
b = d.textbbox((0, 0), 'СТОМАТОЛОГИЯ', font=f_cat)
y_cat = my + mh + round(H * 0.045)
ctext_ls(d, cx, y_cat - b[1], 'СТОМАТОЛОГИЯ', f_cat, ALAB, ls1)
cat_h = b[3] - b[1]

# ── ромб-разделитель ──
y_dia = y_cat + cat_h + round(H * 0.040)
r = round(9 * MM)
d.polygon([(cx, y_dia - r), (cx + r, y_dia), (cx, y_dia + r), (cx - r, y_dia)], fill=TERRA)

# ── «ВЕНЕЦИЯ» — бренд, Prata с разрядкой ──
ls2 = 60
f_br, _ = fit_font(d, 'ВЕНЕЦИЯ', prata, content_w, ls=ls2, start=240)
b2 = d.textbbox((0, 0), 'ВЕНЕЦИЯ', font=f_br)
y_br = y_dia + round(H * 0.035)
ctext_ls(d, cx, y_br - b2[1], 'ВЕНЕЦИЯ', f_br, ALAB, ls2)
br_h = b2[3] - b2[1]

# ── график внизу ──
f_t = onest(round(11 * MM), 500)
t = 'ежедневно 10:00–20:00'
tw = d.textlength(t, font=f_t)
d.text((cx - tw / 2, H - BLEED - round(52 * MM)), t, font=f_t, fill=TINT)

im.save(os.path.join(HERE, 'side-sign-60x80.jpg'), quality=95, dpi=(DPI, DPI))
print('built side-sign-60x80.jpg', im.size)
