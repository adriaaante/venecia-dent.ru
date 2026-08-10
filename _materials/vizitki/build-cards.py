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

def front(surname, name, role, out):
    im = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(im)
    cx = W / 2

    # маленький фирменный знак вместо текстовой шапки
    mark = Image.open(os.path.join(HERE, 'logo-lagoon-mark.png')).convert('RGBA')
    mh = 96
    mw = round(mark.width * mh / mark.height)
    mark = mark.resize((mw, mh), Image.LANCZOS)
    im.paste(mark, (round(cx - mw / 2), 86), mark)

    # имя врача
    ctext(d, cx, 226, surname, prata(84), INK)
    ctext(d, cx, 336, name, prata(46), INK)

    # разделитель + должность
    d.line([cx - 56, 424, cx + 56, 424], fill=TERRA, width=3)
    ctext(d, cx, 444, role.upper(), onest(27, 550), TERRA, ls=6)

    # контакты
    ctext(d, cx, 500, '+7 (916) 838-08-88', onest(34, 650), LAGOON)
    ctext(d, cx, 544, 'Мытищи, ул. Мира, 37  ·  venecia-dent.ru', onest(24, 500), MUTED)

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
