# -*- coding: utf-8 -*-
"""
Визитки врачей «Венеции» — 90×50 мм + вылеты 2 мм, 300 dpi (1110×638 px).
Без фотографий: алебастровый лицевой слой с именем, оборот — глубокая
лагуна с белым знаком в арке. Русский текст — PIL (Prata + Onest).
Запуск: python3 build-cards.py
"""
from PIL import Image, ImageDraw, ImageFont
import os

MM = 300 / 25.4
BLEED = round(2 * MM)                 # 24 px
W, H = round(94 * MM), round(54 * MM) # 1110×638

LAGOON = (15, 110, 102)
LAGOON_DEEP = (10, 74, 70)
INK = (19, 41, 42)
TERRA = (199, 91, 57)
BG = (247, 250, 248)
TINT = (217, 231, 226)
MUTED = (84, 103, 99)

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, '..', 'buklet', 'fonts')

def prata(size):
    return ImageFont.truetype(os.path.join(FONTS, 'Prata-Regular.ttf'), size)

def onest(size, weight=400):
    f = ImageFont.truetype(os.path.join(FONTS, 'Onest[wght].ttf'), size)
    f.set_variation_by_axes([weight])
    return f

def ctext(d, cx, y, text, font, fill, ls=0):
    """Центрированный текст, опционально с трекингом (letter-spacing)."""
    if ls:
        widths = [d.textlength(ch, font=font) for ch in text]
        total = sum(widths) + ls * (len(text) - 1)
        x = cx - total / 2
        for ch, w in zip(text, widths):
            d.text((x, y), ch, font=font, fill=fill)
            x += w + ls
    else:
        w = d.textlength(text, font=font)
        d.text((cx - w / 2, y), text, font=font, fill=fill)

def diamond(d, cx, cy, r, fill):
    d.polygon([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)], fill=fill)

def front(surname, name, role, out, frame=True):
    im = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(im)
    cx = W / 2

    if frame:
        fi = BLEED + round(3.2 * MM)
        d.rectangle([fi, fi, W - fi, H - fi], outline=TINT, width=3)

    mark = Image.open(os.path.join(HERE, 'logo-lagoon-mark.png')).convert('RGBA')
    mh = 78
    mw = round(mark.width * mh / mark.height)
    mark = mark.resize((mw, mh), Image.LANCZOS)

    f_sur, f_nam, f_role = prata(76), prata(44), onest(26, 550)
    f_ph, f_ad = onest(33, 650), onest(23, 500)

    def th(text, font, ls=0):
        b = d.textbbox((0, 0), text, font=font)
        return b[1], b[3] - b[1]  # (смещение до чернил, высота чернил)

    # элементы и ЧИСТЫЕ визуальные зазоры между чернилами (px)
    seq = [
        ('mark', mh),  ('gap', 40),
        ('sur',  th(surname, f_sur)[1]),   ('gap', 26),
        ('nam',  th(name, f_nam)[1]),      ('gap', 36),
        ('line', 3),                        ('gap', 22),
        ('role', th(role.upper(), f_role)[1]), ('gap', 42),
        ('ph',   th('+7', f_ph)[1]),       ('gap', 16),
        ('ad',   th('Мытищи', f_ad)[1]),
    ]
    total = sum(hh for _, hh in seq)
    y = (H - total) / 2 - 6  # оптически чуть выше геометрического центра

    for kind, hh in seq:
        if kind == 'gap':
            y += hh; continue
        if kind == 'mark':
            im.paste(mark, (round(cx - mw / 2), round(y)), mark)
        elif kind == 'sur':
            off, _ = th(surname, f_sur)
            ctext(d, cx, y - off, surname, f_sur, INK)
        elif kind == 'nam':
            off, _ = th(name, f_nam)
            ctext(d, cx, y - off, name, f_nam, INK)
        elif kind == 'line':
            d.line([cx - 56, y + 1, cx + 56, y + 1], fill=TERRA, width=3)
        elif kind == 'role':
            off, _ = th(role.upper(), f_role)
            ctext(d, cx, y - off, role.upper(), f_role, TERRA, ls=6)
        elif kind == 'ph':
            off, _ = th('+7 (916) 838-08-88', f_ph)
            ctext(d, cx, y - off, '+7 (916) 838-08-88', f_ph, LAGOON)
        elif kind == 'ad':
            off, _ = th('Мытищи', f_ad)
            ctext(d, cx, y - off, 'Мытищи, ул. Мира, 37  ·  venecia-dent.ru', f_ad, MUTED)
        y += hh

    im.save(os.path.join(HERE, out), quality=95, dpi=(300, 300))
    print('built', out)

def back(out):
    im = Image.new('RGB', (W, H), LAGOON_DEEP)
    d = ImageDraw.Draw(im)
    cx = W / 2
    ALAB = (247, 250, 248)

    # подлинный знак клиники: белый зуб с окном-аркой + терракотовый фонарик
    mark = Image.open(os.path.join(HERE, 'logo-white-mark.png')).convert('RGBA')
    mh = 236
    mw = round(mark.width * mh / mark.height)
    mark = mark.resize((mw, mh), Image.LANCZOS)
    ay, ah = 88, 236
    im.paste(mark, (round(cx - mw / 2), ay), mark)

    ctext(d, cx, ay + ah + 42, 'ВЕНЕЦИЯ', prata(66), ALAB, ls=16)
    ctext(d, cx, ay + ah + 138, 'СЕМЕЙНАЯ СТОМАТОЛОГИЯ · МЫТИЩИ', onest(26, 500), TINT, ls=7)

    ctext(d, cx, H - BLEED - 108, 'venecia-dent.ru', onest(34, 650), ALAB)
    ctext(d, cx, H - BLEED - 62, 'ежедневно 10:00–20:00', onest(25, 450), TINT)

    im.save(os.path.join(HERE, out), quality=95, dpi=(300, 300))
    print('built', out)

if __name__ == '__main__':
    front('Дробкова', 'Кристина Олеговна', 'Стоматолог-ортодонт', 'card-drobkova-front.jpg')
    front('Киласония', 'Шорена Гиулиевна', 'Стоматолог-хирург · терапевт', 'card-kilasoniya-front.jpg')
    front('Кендабаева', 'Зухро Бурхоновна', 'Стоматолог-гигиенист', 'card-kendabaeva-front.jpg')
    back('card-back.jpg')
