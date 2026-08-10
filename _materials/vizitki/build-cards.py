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

    # тонкая рамка-паспарту (внутри реза на 4 мм)
    fi = BLEED + round(4 * MM)
    d.rectangle([fi, fi, W - fi, H - fi], outline=TINT, width=3)

    # шапка: ромбик + имя клиники
    diamond(d, cx, fi + 34, 9, TERRA)
    ctext(d, cx, fi + 56, 'СТОМАТОЛОГИЯ ВЕНЕЦИЯ', onest(28, 600), LAGOON, ls=10)

    # имя врача
    ctext(d, cx, 196, surname, prata(86), INK)
    ctext(d, cx, 306, name, prata(50), INK)

    # разделитель + должность
    d.line([cx - 70, 396, cx + 70, 396], fill=TERRA, width=3)
    ctext(d, cx, 414, role.upper(), onest(28, 550), TERRA, ls=6)

    # контакты
    ctext(d, cx, 464, '+7 (916) 838-08-88', onest(36, 700), LAGOON)
    ctext(d, cx, 508, 'Мытищи, ул. Мира, 37  ·  venecia-dent.ru', onest(25, 500), MUTED)

    im.save(os.path.join(HERE, out), quality=95, dpi=(300, 300))
    print('built', out)

def back(out):
    im = Image.new('RGB', (W, H), LAGOON_DEEP)
    d = ImageDraw.Draw(im)
    cx = W / 2
    ALAB = (247, 250, 248)

    # тонкая арка-медальон с ромбом внутри
    aw, ah = 190, 232
    ax, ay = cx - aw / 2, 92
    d.arc([ax, ay, ax + aw, ay + aw], 180, 360, fill=TINT, width=3)
    d.line([ax, ay + aw / 2, ax, ay + ah], fill=TINT, width=3)
    d.line([ax + aw, ay + aw / 2, ax + aw, ay + ah], fill=TINT, width=3)
    d.line([ax, ay + ah, ax + aw, ay + ah], fill=TINT, width=3)
    diamond(d, cx, ay + ah / 2 + 14, 26, TERRA)

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
