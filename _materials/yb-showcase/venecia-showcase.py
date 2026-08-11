# -*- coding: utf-8 -*-
"""
Витрина Яндекс.Бизнеса — «Венеция». Картинки позиций 1200×1200.

⚠️ Витрина ≠ акции: название и цена пишутся в ПОЛЯХ позиции, поэтому
на картинку текст НЕ кладём. Только реалистичный кадр в фирменной гамме
(лагуна/алебастр) + водяной знак клиники.

Ряд строится чередованием: живой кадр с людьми (доверие) ↔ предметное
макро (услуга с одного взгляда). Первые позиции видны без скролла →
туда массовые входные услуги.

Состав и цены — с сайта (ceny.html / services/*). Тексты позиций —
в TEXTS.md рядом.

Запуск: python3 venecia-showcase.py   (кадры в bg/)
"""
from PIL import Image
import os, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..', '..')
SIDE = 1200

# параметры знака берём из штатного скрипта клиники (0.32 / 0.62 / halo)
spec = importlib.util.spec_from_file_location('aw', os.path.join(ROOT, 'scripts', 'apply-watermark.py'))
aw = importlib.util.module_from_spec(spec); spec.loader.exec_module(aw)

# порядок = порядок в витрине (первые видны без скролла)
ITEMS = [
    ('01-gigiena',       'sw-hygiene.png'),
    ('02-consult',       'sw-consult.png'),
    ('03-karies',        'sw-caries.png'),
    ('04-implant',       'sw-implant.png'),
    ('05-implant-crown', 'sw-implant-crown.png'),
    ('06-brekety',       'sw-braces.png'),
    ('07-elayneri',      'sw-aligner.png'),
    ('08-otbelivanie',   'sw-whitening.png'),
    ('09-koronka',       'sw-crown.png'),
    ('10-viniry',        'sw-veneers.png'),
    ('11-pervyj-vizit',  'sw-visit.png'),
]

def build(key, bg):
    src = os.path.join(HERE, 'bg', bg)
    if not os.path.exists(src):
        print('пропуск (нет фона):', bg); return
    im = Image.open(src).convert('RGB')
    s = min(im.size)
    im = im.crop(((im.width - s) // 2, (im.height - s) // 2,
                  (im.width - s) // 2 + s, (im.height - s) // 2 + s))
    im = im.resize((SIDE, SIDE), Image.LANCZOS)

    tmp = os.path.join(HERE, '_tmp.png')
    im.save(tmp)
    out = os.path.join(HERE, f'venecia-showcase-{key}.jpg')
    wm = Image.open(aw.WM_PATH).convert('RGBA')
    from pathlib import Path
    # ⚠️ В витрине миниатюры мелкие: штатные 0.32 короткой стороны (правило
    # портфолио) съедают кадр. Для витрины знак уменьшаем до 0.18 и делаем
    # деликатнее — он тут только «подпись», а не защита от воровства.
    aw.WM_SIZE_RATIO, aw.WM_OPACITY, aw.SHADOW_OPACITY = 0.18, 0.55, 0.30
    aw.watermark_image(Path(tmp), Path(out), wm)
    os.remove(tmp)
    print('built', os.path.basename(out))

if __name__ == '__main__':
    for key, bg in ITEMS:
        build(key, bg)
