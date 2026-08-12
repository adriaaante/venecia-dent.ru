# -*- coding: utf-8 -*-
"""
Размерный чертёж консольной вывески-зуба «Венеция» для изготовителя.
Лист A3 (420×297 мм), 150 dpi: вид спереди с габаритами + вид сбоку
с вылетом кронштейна и высотой установки.

Габариты берутся из tooth-sign.py (единый источник геометрии), поэтому
поменял SIGN_H_MM там — чертёж пересоберётся согласованно.

Запуск: python3 tooth-sign-drawing.py
"""
from PIL import Image, ImageDraw, ImageFont
import cairosvg, os

import importlib.util
spec = importlib.util.spec_from_file_location(
    'ts', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tooth-sign.py'))
ts = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ts)          # даёт TOOTH_PATH, SIGN_H_MM, MMU, U_*

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, '..', 'buklet', 'fonts')

SIGN_H = ts.SIGN_H_MM                       # 700 мм
SIGN_W = ts.U_W * ts.MMU                    # ≈ 668 мм
DEPTH = 110                                 # глубина светового короба, мм
GAP = 150                                   # зазор «стена → короб», мм
MOUNT_H = 2550                              # низ вывески над тротуаром, мм

DPI = 150
PXMM = DPI / 25.4
PW, PH = 420, 297                           # A3, альбом
W, H = round(PW * PXMM), round(PH * PXMM)
INK = (19, 41, 42)
DIMC = (176, 68, 40)

im = Image.new('RGB', (W, H), 'white')
d = ImageDraw.Draw(im)

def onest(s, w=450):
    f = ImageFont.truetype(os.path.join(FONTS, 'Onest[wght].ttf'), round(s * PXMM))
    f.set_variation_by_axes([w]); return f

def mm(v): return v * PXMM

def dim_h(x1, x2, y, label, up=True):
    """горизонтальный размер со стрелками"""
    d.line([x1, y, x2, y], fill=DIMC, width=2)
    for x in (x1, x2):
        d.line([x, y - mm(2), x, y + mm(2)], fill=DIMC, width=2)
    f = onest(4.2, 600)
    tw = d.textlength(label, font=f)
    ty = y - mm(6) if up else y + mm(2)
    d.rectangle([(x1 + x2) / 2 - tw / 2 - 4, ty - 2,
                 (x1 + x2) / 2 + tw / 2 + 4, ty + mm(4.6)], fill='white')
    d.text(((x1 + x2) / 2 - tw / 2, ty), label, font=f, fill=DIMC)

def dim_v(y1, y2, x, label, left=True):
    d.line([x, y1, x, y2], fill=DIMC, width=2)
    for y in (y1, y2):
        d.line([x - mm(2), y, x + mm(2), y], fill=DIMC, width=2)
    f = onest(4.2, 600)
    tw = d.textlength(label, font=f)
    tx = x - tw - mm(3) if left else x + mm(3)
    ty = (y1 + y2) / 2 - mm(2.3)
    d.rectangle([tx - 4, ty - 2, tx + tw + 4, ty + mm(4.6)], fill='white')
    d.text((tx, ty), label, font=f, fill=DIMC)

# ── шапка листа ──
d.text((mm(15), mm(12)), 'Консольная вывеска «ВЕНЕЦИЯ» — чертёж на изготовление',
       font=onest(7, 700), fill=INK)
d.text((mm(15), mm(21)), 'Стоматология «Венеция» · Мытищи, ул. Мира, 37 · двусторонний световой короб',
       font=onest(4.4, 450), fill=(90, 105, 105))
d.line([mm(15), mm(28), W - mm(15), mm(28)], fill=(210, 220, 218), width=2)

# ── вид спереди ──
# масштаб подобран так, чтобы оба вида уместились над спецификацией:
# высота зуба на листе = 700 × 0,17 ≈ 119 мм при поле от 48 до 205 мм
VS = 0.17                                    # ≈ 1:6
fw, fh = SIGN_W * VS, SIGN_H * VS
fx, fy = mm(40), mm(48)

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{round(mm(fw))}" height="{round(mm(fh))}"
 viewBox="{ts.U_X0} {ts.U_Y0} {ts.U_W} {ts.U_H}">
  <path d="{ts.TOOTH_PATH}" fill="none" stroke="#13292A" stroke-width="2.5"/></svg>'''
p = os.path.join(HERE, '_dw.svg'); open(p, 'w').write(svg)
cairosvg.svg2png(url=p, write_to=os.path.join(HERE, '_dw.png'),
                 output_width=round(mm(fw)), output_height=round(mm(fh)))
front = Image.open(os.path.join(HERE, '_dw.png'))
im.paste(front, (round(fx), round(fy)), front)
os.remove(p); os.remove(os.path.join(HERE, '_dw.png'))

d.text((fx, fy - mm(9)), 'ВИД СПЕРЕДИ (лицо, 2 шт.)', font=onest(4.6, 700), fill=INK)
dim_h(fx, fx + mm(fw), fy + mm(fh) + mm(10), f'{SIGN_W:.0f} мм', up=False)
dim_v(fy, fy + mm(fh), fx - mm(12), f'{SIGN_H:.0f} мм')

# ── вид сбоку ──
sy = fy
bx1 = mm(250)                                # ближний край короба
bx2 = bx1 + mm(DEPTH * VS)
wall_x = bx2 + mm(GAP * VS)                  # плоскость фасада
d.text((mm(214), sy - mm(17)), 'ВИД СБОКУ (крепление к фасаду)', font=onest(4.6, 700), fill=INK)

# стена
d.rectangle([wall_x, sy - mm(14), wall_x + mm(12), mm(196)], fill=(38, 39, 42))
for i in range(12):
    yy = sy - mm(14) + i * mm(16)
    if yy > mm(196):                         # не выходить за линию тротуара
        break
    d.line([wall_x, yy, wall_x + mm(12), yy], fill=(58, 60, 64), width=1)
d.text((wall_x + mm(16), mm(120)), 'фасад', font=onest(4, 450), fill=(90, 105, 105))

# короб (сбоку — прямоугольник глубиной DEPTH)
d.rectangle([bx1, sy, bx2, sy + mm(fh)], outline=INK, width=3, fill=(250, 250, 248))
# кронштейн: две штанги в стену + монтажная пластина
for k in (0.28, 0.60):
    yy = sy + mm(fh) * k
    d.rectangle([bx2, yy, wall_x, yy + mm(3)], fill=(70, 72, 76))
d.rectangle([wall_x - mm(3), sy + mm(fh) * 0.20, wall_x, sy + mm(fh) * 0.70], fill=(70, 72, 76))

dim_h(bx1, bx2, sy - mm(5), f'{DEPTH} мм')
dim_h(bx2, wall_x, sy + mm(fh) + mm(9), f'{GAP} мм', up=False)

# высота установки: линия с разрывом (в масштабе 2550 мм не влезают)
gy = mm(196)
lx = bx1 - mm(14)
d.line([lx, sy + mm(fh), lx, gy], fill=DIMC, width=2)
d.line([lx - mm(2.5), sy + mm(fh), lx + mm(2.5), sy + mm(fh)], fill=DIMC, width=2)
d.line([lx - mm(2.5), gy, lx + mm(2.5), gy], fill=DIMC, width=2)
brk = (sy + mm(fh) + gy) / 2                 # знак обрыва масштаба
d.rectangle([lx - mm(3), brk - mm(4), lx + mm(3), brk + mm(4)], fill='white')
for o in (-mm(2), mm(2)):
    d.line([lx - mm(3), brk + o + mm(2), lx + mm(3), brk + o - mm(2)], fill=DIMC, width=2)
fdim = onest(4.2, 600)
d.text((lx - mm(46), brk - mm(2.3)), f'{MOUNT_H} мм', font=fdim, fill=DIMC)
d.text((lx - mm(46), brk + mm(3)), 'до тротуара', font=onest(3.6, 450), fill=DIMC)
# уровень тротуара
d.line([lx - mm(20), gy, wall_x + mm(14), gy], fill=INK, width=3)
for xx in range(int(lx - mm(20)), int(wall_x + mm(14)), int(mm(4))):
    d.line([xx, gy + mm(1), xx + mm(2.5), gy + mm(4)], fill=(120, 135, 135), width=1)

# ── спецификация ──
tx, ty = mm(15), mm(212)
d.line([mm(15), ty - mm(6), W - mm(15), ty - mm(6)], fill=(210, 220, 218), width=2)
rows = [
    ('Тип изделия', 'консольный двусторонний световой короб, фигурный по контуру зуба'),
    ('Габариты', f'{SIGN_H:.0f} × {SIGN_W:.0f} мм, глубина {DEPTH} мм; вылет от стены {GAP} мм'),
    ('Лицевые панели', 'молочный акрил 3 мм, 2 шт.; печать/плёнка по макету, контур — по файлу реза'),
    ('Борт', 'алюминиевый профиль, окраска RAL 1036 «перламутровое золото» (в цвет каймы)'),
    ('Подсветка', 'LED-модули 6500 K, блок питания IP67 внутри короба, ввод кабеля через стену'),
    ('Крепление', 'настенный кронштейн, сталь с порошковой окраской RAL 9005; анкеры в несущее основание'),
    ('Цвета макета', 'поле — белый RAL 9003; кайма и надпись — золото #C2A14E / #A8842F (Pantone 4515 C)'),
    ('Высота установки', f'низ вывески {MOUNT_H} мм от уровня тротуара'),
]
f1, f2 = onest(4.3, 700), onest(4.3, 450)
for i, (k, v) in enumerate(rows):
    y = ty + i * mm(8.4)
    d.text((tx, y), k, font=f1, fill=INK)
    d.text((tx + mm(58), y), v, font=f2, fill=(60, 75, 75))

d.text((tx, mm(283)), 'Файлы: venecia-tooth-sign-white-gold-edge-print.pdf (макет 1:1) · '
                      'venecia-tooth-sign-cutline.pdf/.svg (контур реза, 1:1)',
       font=onest(4, 450), fill=(120, 135, 135))

out = os.path.join(HERE, 'venecia-tooth-sign-drawing.pdf')
im.save(out, resolution=DPI, title='Венеция — консольная вывеска, чертёж на изготовление')
im.save(os.path.join(HERE, 'venecia-tooth-sign-drawing.png'))
print('готово:', out)
