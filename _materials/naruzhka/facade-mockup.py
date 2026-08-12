# -*- coding: utf-8 -*-
"""
Примерка консольной вывески-зуба на чёрном фасаде (визуализация для
владельца — «как будет выглядеть»).

Фон — сгенерированный Higgsfield кадр чёрного фасада под углом вдоль
тротуара (`bg/angle-1.png`). Ракурс важен: при фронтальном кадре
консольная панель видна с ребра и на примерке ничего не читается.

Масштаб берётся от двери (высота 2,1 м), поэтому зуб на картинке ровно
такой, каким будет в жизни при `SIGN_H_MM` = 700 мм.

Запуск: python3 facade-mockup.py   (после tooth-sign.py)
"""
from PIL import Image, ImageDraw, ImageFilter
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEME = 'white-gold-edge'            # схема, выбранная владельцем 12.08.2026
BG = os.path.join(HERE, 'bg', 'angle-1.png')

# ── масштаб сцены ────────────────────────────────────────────
# дверь на кадре: y 366…939 px = 2,1 м  →  273 px на метр
PX_PER_M = (939 - 366) / 2.1
SIGN_H_M = 0.700                      # высота зуба (см. tooth-sign.py)
BOTTOM_M = 2.55                       # низ вывески над тротуаром
SIDEWALK_Y = 1030                     # уровень тротуара у входа, px
CENTER_X = 575                        # ось вывески (над входной группой), px
SQUEEZE = 0.90                        # перспектива: дальний край панели уже

im = Image.open(BG).convert('RGB')
tooth = Image.open(os.path.join(HERE, f'tooth-{SCHEME}-cut.png')).convert('RGBA')

h = round(SIGN_H_M * PX_PER_M)
w = round(tooth.width * h / tooth.height)
tooth = tooth.resize((w, h), Image.LANCZOS)

# перспектива: правый край (у стены, дальше от зрителя) короче левого
dy = round(h * (1 - SQUEEZE) / 2)
tooth = tooth.transform(
    (w, h), Image.QUAD,
    (0, 0, 0, h, w, h - dy, w, dy), Image.BICUBIC)

# фасад в тени — приглушаем панель, иначе она выглядит наклейкой
r, g, b, a = tooth.split()
tooth = Image.merge('RGBA', [ch.point(lambda v: round(v * 0.93)) for ch in (r, g, b)] + [a])

x = CENTER_X - w // 2
y = SIDEWALK_Y - round(BOTTOM_M * PX_PER_M) - h

# ── тень на стене (пасмурно → мягкая и слабая) ──
shadow = Image.new('RGBA', im.size, (0, 0, 0, 0))
sh = Image.new('RGBA', tooth.size, (0, 0, 0, 0))
sh.paste((0, 0, 0, 150), (0, 0), tooth.split()[3])
shadow.paste(sh, (x + 16, y + 14), sh)
shadow = shadow.filter(ImageFilter.GaussianBlur(9))
im.paste(shadow.convert('RGB'), (0, 0), shadow)

# ── кронштейн: две штанги от стены + монтажная пластина ──
d = ImageDraw.Draw(im)
steel = (36, 37, 40)
mid = y + round(h * 0.46)
for yy in (mid - round(h * 0.16), mid + round(h * 0.16)):
    d.polygon([(x + w - 6, yy), (x + w + 34, yy + 3),
               (x + w + 34, yy + 12), (x + w - 6, yy + 11)], fill=steel)
d.polygon([(x + w + 30, mid - round(h * 0.24)), (x + w + 42, mid - round(h * 0.23)),
           (x + w + 42, mid + round(h * 0.25)), (x + w + 30, mid + round(h * 0.24))],
          fill=(30, 31, 34))

im.paste(tooth, (x, y), tooth)

out = os.path.join(HERE, f'facade-mockup-{SCHEME}.jpg')
im.save(out, quality=94, subsampling=0)
print(f'{out}  зуб {w}×{h} px  ({SIGN_H_M * 1000:.0f} мм при {PX_PER_M:.0f} px/м)')
