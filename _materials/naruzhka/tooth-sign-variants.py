# -*- coding: utf-8 -*-
"""
Сравнение цветовых схем вывески-зуба НА ЧЁРНОМ ФАСАДЕ (фасад клиники
чёрный — владелец, 11.08.2026). Два листа:
  tooth-variants-day.png   — дневной вид (все схемы на чёрной стене)
  tooth-variants-night.png — ночной вид (световой короб: светятся буквы
                             и — у светлых схем — всё тело зуба)
Запуск: python3 tooth-sign-variants.py   (после tooth-sign.py)
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, '..', 'buklet', 'fonts')

VARIANTS = [
    ('alabaster',       'Алебастр, надпись лагуной',   'максимальный контраст на чёрном'),
    ('alabaster-edge',  'Алебастр + лагуновая кайма',  'белый с фирменным контуром'),
    ('white-gold',      'Белый + золото',              'стиль Версаля, дороже на вид'),
    ('white-gold-edge', 'Белый + золотая кайма',       'золото читается и днём, и в подсветке'),
    ('gold',            'Золотой зуб',                 'самый заметный на чёрном фасаде'),
    ('lagoon',          'Лагуна (зелёный зуб)',        'на чёрном фасаде теряется'),
    ('terracotta',      'Терракота',                   'тёплый акцент, хорошо виден'),
]

def onest(s, w=500):
    f = ImageFont.truetype(os.path.join(FONTS, 'Onest[wght].ttf'), s)
    f.set_variation_by_axes([w]); return f

def sheet(night, out):
    COLS, CELL_W, CELL_H = 3, 760, 780
    PAD, TOP = 40, 150
    ROWS = -(-len(VARIANTS) // COLS)
    W = COLS * CELL_W + PAD * 2
    H = TOP + ROWS * CELL_H + PAD
    wall = (14, 14, 16) if not night else (8, 8, 10)
    im = Image.new('RGB', (W, H), wall)
    d = ImageDraw.Draw(im)

    # фактура чёрного фасада: горизонтальные швы панелей
    for y in range(TOP, H, 210):
        d.line([0, y, W, y], fill=(26, 26, 29) if not night else (18, 18, 21), width=3)

    title = 'Вывеска-зуб на ЧЁРНОМ фасаде — ' + ('НОЧЬ (световой короб)' if night else 'ДЕНЬ')
    d.text((PAD + 10, 44), title, font=onest(40, 700), fill=(255, 255, 255))
    d.text((PAD + 10, 96), 'высота зуба 700 мм · контур реза одинаковый у всех схем',
           font=onest(26, 450), fill=(150, 152, 156))

    for i, (key, name, note) in enumerate(VARIANTS):
        cx = PAD + (i % COLS) * CELL_W + CELL_W // 2
        cy = TOP + (i // COLS) * CELL_H

        tooth = Image.open(os.path.join(HERE, f'tooth-{key}-cut.png')).convert('RGBA')
        tooth.thumbnail((560, 560))

        if night:
            # световой короб: тело светится изнутри, вокруг — ореол света
            glow = Image.new('RGBA', im.size, (0, 0, 0, 0))
            halo = tooth.copy()
            halo = halo.filter(ImageFilter.GaussianBlur(26))
            gx, gy = cx - halo.width // 2, cy + 40
            glow.paste(halo, (gx, gy), halo)
            glow.putalpha(glow.split()[3].point(lambda a: int(a * 0.55)))
            im.paste(glow, (0, 0), glow)
            # само тело чуть ярче
            enh = tooth.copy()
            px = enh.load()
            for yy in range(enh.height):
                for xx in range(enh.width):
                    r, g, b, a = px[xx, yy]
                    if a:
                        px[xx, yy] = (min(255, int(r * 1.18 + 18)),
                                      min(255, int(g * 1.18 + 18)),
                                      min(255, int(b * 1.18 + 18)), a)
            tooth = enh

        tx, ty = cx - tooth.width // 2, cy + 40
        # кронштейн: две штанги от левого края к середине зуба
        mid = ty + round(tooth.height * 0.46)
        steel = (58, 60, 64) if not night else (40, 42, 46)
        for yy in (mid - 62, mid + 62):
            d.rectangle([tx - 150, yy, tx + 80, yy + 12], fill=steel)
        d.rectangle([tx - 158, mid - 92, tx - 140, mid + 96], fill=steel)

        im.paste(tooth, (tx, ty), tooth)

        d.text((cx - 250, cy + 40 + tooth.height + 26), name, font=onest(30, 650), fill=(255, 255, 255))
        d.text((cx - 250, cy + 40 + tooth.height + 68), note, font=onest(25, 450), fill=(150, 152, 156))

    im.save(os.path.join(HERE, out))
    print('built', out)

if __name__ == '__main__':
    sheet(False, 'tooth-variants-day.png')
    sheet(True, 'tooth-variants-night.png')
