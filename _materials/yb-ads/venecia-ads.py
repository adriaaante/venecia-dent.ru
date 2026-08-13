# -*- coding: utf-8 -*-
"""
Картинки для раздела «Свои объявления» Яндекс.Бизнеса — «Венеция».

Правила общие с Версалем (`Versal-Dent-site/_materials/yb-ads/`):
кадры только с лицами, текст объявления пишется в полях кабинета и на
картинку не кладётся, водяного знака нет. Впечатана лишь обязательная по
ч. 7 ст. 24 ФЗ «О рекламе» строка о противопоказаниях — закон требует
отдать под неё ≥5 % площади, а в 81 символ описания она не влезает.

Отличия Венеции: гамма лагуна/алебастр (без золота), шрифт Onest,
полоса дисклеймера в цвете чернил. ⚠️ В кадрах нет детей и нет намёков
на КТ — детского приёма и томографа в клинике не существует.

Запуск: python3 venecia-ads.py
"""
from PIL import Image, ImageDraw, ImageFont
import os

HERE = os.path.dirname(os.path.abspath(__file__))
BG, OUT = os.path.join(HERE, 'bg'), os.path.join(HERE, 'out')
FONTS = os.path.join(HERE, 'fonts')
os.makedirs(OUT, exist_ok=True)

SIDE = 1200
INK = (19, 41, 42)                 # чернила Венеции
DISCLAIMER = 'Имеются противопоказания, необходима консультация специалиста'

SHOTS = [
    ('karies', '01-karies.png', 0.42), ('kanaly', '02-kanaly.png', 0.45),
    ('bol', '03-bol.png', 0.42), ('mudrosti', '04-mudrosti.png', 0.35),
    ('plan', '05-plan.png', 0.45), ('cirkon', '06-cirkon.png', 0.40),
    ('implant', '07-implant.png', 0.40), ('allon4', '08-allon4.png', 0.40),
    ('protez', '09-protez.png', 0.40), ('brekety', '10-brekety.png', 0.40),
    ('elaynery', '11-elaynery.png', 0.40), ('otbelivanie', '12-otbelivanie.png', 0.40),
    ('desny', '13-desny.png', 0.40), ('gigiena', '14-gigiena.png', 0.45),
    # +6 от 13.08.2026 — добор до 20 (лимит кабинета)
    ('viniry', '15-viniry.png', 0.38), ('udalenie', '16-udalenie.png', 0.45),
    ('restavraciya', '17-restavraciya.png', 0.38), ('koronka', '18-koronka.png', 0.38),
    ('osstem', '19-osstem.png', 0.38), ('semya', '20-semya.png', 0.42),
]


def square(im, focus=0.45):
    w, h = im.size
    if w > h:
        x = (w - h) // 2
        im = im.crop((x, 0, x + h, h))
    elif h > w:
        y = round((h - w) * focus)
        im = im.crop((0, y, w, y + w))
    return im.resize((SIDE, SIDE), Image.LANCZOS)


def disclaimer(im):
    d = ImageDraw.Draw(im, 'RGBA')
    f = ImageFont.truetype(os.path.join(FONTS, 'Onest[wght].ttf'), 21)
    f.set_variation_by_axes([450])
    tw = d.textlength(DISCLAIMER, font=f)
    bar = round(SIDE * 0.052)               # ≥5 % площади — требование закона
    d.rectangle([0, SIDE - bar, SIDE, SIDE], fill=INK + (190,))
    d.text(((SIDE - tw) / 2, SIDE - bar + (bar - 26) / 2), DISCLAIMER,
           font=f, fill=(247, 250, 248, 235))
    return im


if __name__ == '__main__':
    n = 0
    for key, src, focus in SHOTS:
        p = os.path.join(BG, src)
        if not os.path.exists(p):
            print('нет фона:', src); continue
        im = disclaimer(square(Image.open(p).convert('RGB'), focus))
        im.save(os.path.join(OUT, f'venecia-ad-{key}.jpg'), quality=92, subsampling=0)
        n += 1
    print(f'готово: {n} картинок 1200×1200 в out/')
