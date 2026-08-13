# -*- coding: utf-8 -*-
"""
Фотографии карточки Яндекс.Бизнеса — «Венеция».

Источник — РЕАЛЬНЫЕ фото клиники `assets/img/clinic/*.webp` (Drive
владельца). Модерация ЯБ отклоняет коллажи, рамки, надписи и водяные
знаки, поэтому здесь снимки идут ЧИСТЫМИ: только конвертация в JPEG,
приведение размера и лёгкая тон-коррекция. ⚠️ Водяной знак не ставим
(в отличие от витрины, Дзена и портфолио).

На выходе `out/`:
  logo-1000.jpg      — аватар организации (квадрат из знака на алебастре)
  cover-1200x400.jpg — обложка профиля (широкий кроп интерьера)
  01…08-*.jpg        — фотогалерея, 1600 px по длинной стороне

Порядок файлов = рекомендуемый порядок загрузки (первое фото карточки
показывается в выдаче Карт — туда самый «лицевой» кадр).

Запуск: python3 build-photos.py
"""
from PIL import Image, ImageEnhance
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', '..', 'assets', 'img', 'clinic')
LOGO = os.path.join(HERE, '..', '..', 'assets', 'img', 'logo.png')
OUT = os.path.join(HERE, 'out')
os.makedirs(OUT, exist_ok=True)

ALAB = (247, 250, 248)

# порядок карточки: ресепшен → интерьер с аркой → зона ожидания → детали
GALLERY = [
    ('01-resepshen',      'clinic-1.webp'),
    ('02-arka-koridor',   'clinic-hero.webp'),
    ('03-holl',           'clinic-2.webp'),
    ('04-zona-ozhidaniya','clinic-3.webp'),
    ('05-resepshen-2',    'clinic-6.webp'),
    ('06-stoyka',         'clinic-5.webp'),
    ('07-divan',          'clinic-4.webp'),
    ('08-interyer',       'clinic-about.webp'),
]

def prep(img, long_side=1600):
    """Лёгкая доводка: чуть контраста и яркости — снимки в карточке
    смотрятся живее, но без «пережатой» обработки."""
    if max(img.size) != long_side:
        sc = long_side / max(img.size)
        img = img.resize((round(img.width * sc), round(img.height * sc)), Image.LANCZOS)
    img = ImageEnhance.Brightness(img).enhance(1.03)
    img = ImageEnhance.Contrast(img).enhance(1.04)
    return img

def build_gallery():
    n = 0
    for key, src in GALLERY:
        p = os.path.join(SRC, src)
        if not os.path.exists(p):
            print('нет файла:', src); continue
        im = Image.open(p).convert('RGB')
        prep(im).save(os.path.join(OUT, f'{key}.jpg'), quality=92, subsampling=0)
        n += 1
    print(f'галерея: {n} фото (1600 px по длинной стороне)')

def build_logo():
    """Аватар 1000×1000: фирменная плитка во весь кадр.

    ⚠️ Раньше знак занимал 62% поля и вокруг оставался алебастровый
    воздух — при загрузке кабинет открывает кадрирование, и владельцу
    приходилось вручную зумить (решение владельца 13.08.2026: должно
    вставляться «как есть»). Теперь плитка растянута до краёв, а фон
    залит той же лагуной, что и она, — скруглённые углы плитки
    растворяются в фоне, пустого места не остаётся при любом кропе,
    хоть круглом, хоть квадратном.
    """
    side, over = 1000, 1.09        # плитку берём с запасом и режем по кадру
    logo = Image.open(LOGO).convert('RGBA')
    logo = logo.crop(logo.split()[3].getbbox())

    big = round(side * over)
    logo = logo.resize((big, big), Image.LANCZOS)
    off = (big - side) // 2
    # скруглённые углы плитки уходят за границы кадра — в углах остаётся
    # чистый градиент лагуны, а не стык фона с плиткой
    im = Image.new('RGB', (big, big), logo.convert('RGB').getpixel((big // 2, 12)))
    im.paste(logo, (0, 0), logo)
    im.crop((off, off, off + side, off + side)) \
      .save(os.path.join(OUT, 'logo-1000.jpg'), quality=95, subsampling=0)
    print('логотип: 1000×1000, плитка во весь кадр без полей')

def build_cover():
    """Обложка профиля 1200×400 — широкий кроп самого «просторного» кадра."""
    im = Image.open(os.path.join(SRC, 'clinic-2.webp')).convert('RGB')
    W, H = 1200, 400
    sc = max(W / im.width, H / im.height)
    im = im.resize((round(im.width * sc), round(im.height * sc)), Image.LANCZOS)
    # берём верхнюю треть: там арка и свет, а не пол
    x = (im.width - W) // 2
    y = max(0, round((im.height - H) * 0.32))
    im = im.crop((x, y, x + W, y + H))
    im = ImageEnhance.Brightness(im).enhance(1.03)
    im.save(os.path.join(OUT, 'cover-1200x400.jpg'), quality=93, subsampling=0)
    print('обложка: 1200×400')

if __name__ == '__main__':
    build_logo()
    build_cover()
    build_gallery()
