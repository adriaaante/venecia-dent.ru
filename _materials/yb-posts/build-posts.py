# -*- coding: utf-8 -*-
"""
Картинки публикаций Яндекс.Бизнеса «Венеция».

Ничего не генерируем: берём то, что уже есть в репозитории — реальные
фото клиники (`assets/img/clinic/`), кадры услуг (`assets/img/services/`)
и портреты врачей — приводим к 4:3 1600×1200 JPEG и ставим водяной знак.

⚠️ Знак слабее портфолийного: **0.18 короткой стороны** — как в витрине.
Плашка-логотип Венеции на маленьком превью публикации при 0.32 съедает
кадр. На фото карточки ЯБ знак не ставим вообще (модерация), здесь —
можно: публикация это пост, а не фотография организации.

Портрет врача (4:5) не кадрируем в 4:3 — под него отдельный режим
`fit`: вписываем в кадр на фирменный айвори-фон, чтобы не срезать
голову и плечи.

Запуск: python3 build-posts.py  → out/*.jpg
"""
import os

from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
OUT = os.path.join(HERE, 'out')
WM = os.path.join(ROOT, 'assets', 'img', 'watermark.png')

W, H = 1600, 1200          # 4:3 — под ленту публикаций
WM_RATIO, WM_MARGIN = 0.18, 0.04
WM_OPACITY, SHADOW_OPACITY = 0.62, 0.38
BG = (244, 249, 247)       # алебастр — фон для вертикальных портретов

# файл-источник, имя на выходе, режим (cover — заполнить кадр, fit — вписать)
SHOTS = [
    ('assets/img/clinic/clinic-1.webp',            'klinika-1',   'cover'),
    ('assets/img/clinic/clinic-2.webp',            'klinika-2',   'cover'),
    ('assets/img/clinic/clinic-3.webp',            'klinika-3',   'cover'),
    ('assets/img/services/gigiena.webp',           'gigiena-1',   'cover'),
    ('assets/img/clinic/clinic-4.webp',            'gigiena-2',   'cover'),
    ('assets/img/doctors/kendabaeva.webp',         'gigiena-3',   'fit'),
    ('assets/img/clinic/clinic-5.webp',            'semya-1',     'cover'),
    ('assets/img/clinic/clinic-6.webp',            'semya-2',     'cover'),
    ('assets/img/services/ortodontiya.webp',       'ortodont-1',  'cover'),
    ('assets/img/doctors/drobkova.webp',           'ortodont-2',  'fit'),
    ('assets/img/clinic/clinic-hero.webp',         'vizit-1',     'cover'),
    ('assets/img/clinic/clinic-about.webp',        'vizit-2',     'cover'),
    ('assets/img/services/implantaciya.webp',      'implant-1',   'cover'),
    ('assets/img/services/hirurgiya.webp',         'implant-2',   'cover'),
]


def frame(im, mode):
    """Приводим кадр к 1600×1200: cover — кроп по центру, fit — вписать на фон."""
    if mode == 'cover':
        k = max(W / im.width, H / im.height)
        im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
        x, y = (im.width - W) // 2, (im.height - H) // 2
        return im.crop((x, y, x + W, y + H))
    k = min(W / im.width, H / im.height)
    im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
    canvas = Image.new('RGB', (W, H), BG)
    canvas.paste(im, ((W - im.width) // 2, (H - im.height) // 2))
    return canvas


def stamp(im, wm):
    """Знак в правом нижнем углу с мягким halo — читается и на светлом фоне."""
    side = min(im.width, im.height)
    tw = int(side * WM_RATIO)
    th = round(wm.height * tw / wm.width)
    w = wm.resize((tw, th), Image.LANCZOS)
    w.putalpha(w.split()[3].point(lambda p: int(p * WM_OPACITY)))

    m = int(side * WM_MARGIN)
    pos = (im.width - tw - m, im.height - th - m)

    blur = max(2, int(tw * 0.014))
    pad = blur * 4
    sh = Image.new('RGBA', (tw + pad * 2, th + pad * 2), (0, 0, 0, 0))
    sh.paste(Image.new('RGBA', w.size, (0, 0, 0, 255)), (pad, pad),
             w.split()[3].point(lambda p: int(p * SHADOW_OPACITY)))
    sh = sh.filter(ImageFilter.GaussianBlur(blur))

    layer = Image.new('RGBA', im.size, (0, 0, 0, 0))
    layer.paste(sh, (pos[0] - pad, pos[1] - pad), sh)
    layer.paste(w, pos, w)
    return Image.alpha_composite(im.convert('RGBA'), layer).convert('RGB')


def build():
    os.makedirs(OUT, exist_ok=True)
    wm = Image.open(WM).convert('RGBA')
    for src, name, mode in SHOTS:
        im = Image.open(os.path.join(ROOT, src)).convert('RGB')
        out = os.path.join(OUT, name + '.jpg')
        stamp(frame(im, mode), wm).save(out, 'JPEG', quality=90, optimize=True)
        print(f'  ✓ {name}.jpg  ← {src}  ({os.path.getsize(out)//1024} КБ)')


if __name__ == '__main__':
    build()
