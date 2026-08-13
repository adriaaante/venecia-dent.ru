# -*- coding: utf-8 -*-
"""
Картинки для «Анкеты компании» → «Загрузите изображения» (Яндекс Бизнес).

Это НЕ фотографии карточки и НЕ витрина: отсюда Яндекс собирает
автоматические объявления клиники — их видно в Поиске, на Картах и в
Рекламной сети. Требования и запреты (support/business-priority,
раздел «Правила размещения рекламно-информационных материалов»):

- минимум 650×650 px для текстовых объявлений; берём с запасом;
- изображение должно соответствовать деятельности компании;
- текста на картинке — не больше 20 % площади. Поэтому сюда НЕ годятся
  готовые баннеры акций, карточки объявлений и слайды историй: у них
  впечатаны заголовки, цены и дисклеймер;
- нельзя «до/после», контакты (телефон, почта, адрес) на картинке и
  рекламные слова вроде «скидка», «купить» вне раздела акций;
- дисклеймер о противопоказаниях в саму картинку добавлять не нужно —
  для медицинских услуг Яндекс подставляет предупреждение сам.

Водяной знак здесь тоже не ставим: в объявлении и так видно название
клиники, а знак — лишний элемент поверх кадра.

Готовим два формата: квадрат 1200×1200 (основной) и широкий 1920×1080 —
чтобы у Яндекса был выбор под разные места показа.

Запуск: python3 build-anketa.py  → out/
"""
import os

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
OUT = os.path.join(HERE, 'out')

SQUARE, WIDE = (1200, 1200), (1920, 1080)

# файл-источник, имя, делать ли широкую версию
SHOTS = [
    # реальная клиника — главный аргумент доверия
    ('assets/img/clinic/clinic-1.webp',           'klinika-resepshen',  True),
    ('assets/img/clinic/clinic-2.webp',           'klinika-holl',       True),
    ('assets/img/clinic/clinic-3.webp',           'klinika-ozhidanie',  False),
    ('assets/img/clinic/clinic-5.webp',           'klinika-stoyka',     False),
    ('assets/img/clinic/clinic-about.webp',       'klinika-interyer',   False),
    # приём и услуги — кадры с людьми, без единой надписи
    ('_materials/yb-ads/bg/05-plan.png',          'priem-plan',         True),
    ('_materials/yb-ads/bg/14-gigiena.png',       'priem-gigiena',      True),
    ('_materials/yb-ads/bg/20-semya.png',         'semya',              False),
    ('_materials/yb-ads/bg/10-brekety.png',       'ortodontiya',        False),
    ('_materials/yb-ads/bg/19-osstem.png',        'implantaciya',       False),
    ('_materials/yb-promo/bg/promo-family.png',   'semya-pokoleniya',   True),
]


def fit(im, size):
    w, h = size
    k = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
    x, y = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((x, y, x + w, y + h))


def build():
    os.makedirs(OUT, exist_ok=True)
    n = 0
    for src, name, wide in SHOTS:
        im = Image.open(os.path.join(ROOT, src)).convert('RGB')
        fit(im, SQUARE).save(os.path.join(OUT, f'{name}-1x1.jpg'),
                             'JPEG', quality=90, optimize=True)
        n += 1
        if wide:
            fit(im, WIDE).save(os.path.join(OUT, f'{name}-16x9.jpg'),
                               'JPEG', quality=90, optimize=True)
            n += 1
        print(f'  ✓ {name}{"  (+16:9)" if wide else ""}')
    print(f'готово: {n} файлов в out/')


if __name__ == '__main__':
    build()
