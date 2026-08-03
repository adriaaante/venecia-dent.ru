#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Истории Яндекс.Бизнеса для «Венеции» — сборка слайдов 1080×1920.

Правила (общие с Angel/Versal, см. их CLAUDE.md, раздел «Истории для ЯБ»):
  - фоны — Higgsfield (bg/*.png, 9:16), русский текст ТОЛЬКО поверх PIL;
  - люди сгенерированные, без имён; до/после НЕ используем;
  - нижние ~230 px свободнее — там кнопка Яндекса;
  - при цене на медуслугу — дисклеймер «Имеются противопоказания…»;
  - цены и факты — только с сайта (сверено 03.08.2026):
      консультация с планом — 1 000 ₽ (ceny.html),
      комплексная гигиена — 5 000 ₽ (services/gigiena.html),
      консультация ортодонта — 0 ₽ (promotions.html, акция),
      семейная программа 3–10% при лечении 3+ человек (index.html),
      −10% многодетным/военнослужащим/пенсионерам (promotions.html),
      ежедневно 10:00–20:00, Мытищи, ул. Мира, 37.

Стиль Венеции: лагуна #0F6E66, терракота #C75B39, алебастр #F7FAF8,
Prata + Onest (шрифты в ../buklet/fonts/), ромб-буллеты, лого logo-600.png.

Запуск из _materials/yb-stories/:  python3 venecia-stories.py
Выход: out/s<история>-<слайд>.jpg (6 историй по 3 слайда).
"""
import pathlib

from PIL import Image, ImageDraw, ImageFilter, ImageFont

BASE = pathlib.Path(__file__).resolve().parent
BG = BASE / 'bg'
OUT = BASE / 'out'
FONTS = BASE.parent / 'buklet' / 'fonts'
LOGO = BASE.parent / 'buklet' / 'img' / 'logo-600.png'

W, H = 1080, 1920
BOTTOM_FREE = 230          # зона кнопки Яндекса — крупный текст сюда не кладём

LAGOON = '#0F6E66'
LAGOON_DARK = '#0A3F3B'
TERRA = '#C75B39'
ALABASTER = '#F7FAF8'
MIST = '#BFE3DC'
DISCLAIMER = 'Имеются противопоказания, необходима консультация специалиста'

# ------------------------------------------------------------------ слайды
# poi — точка интереса кропа (cy), grad_top — высота верхнего затемнения
SLIDES = [
    # История 1 — «Не страшно»
    dict(bg='fear-cover.png', out='s1-1.jpg', kind='cover',
         q='Боитесь\nстоматолога?', sub='Вы не одни — так у каждого второго'),
    dict(bg='fear-hand.png', out='s1-2.jpg', kind='points',
         title='У нас — бережно',
         points=['Современная анестезия —\nукол не чувствуется',
                 'Сначала объясняем,\nпотом лечим',
                 'Приём можно\nостановить жестом']),
    dict(bg='fear-happy.png', out='s1-3.jpg', kind='cta',
         title='Сделайте\nпервый шаг',
         sub='Консультация с осмотром\nи планом лечения — 1 000 ₽',
         disclaimer=True),

    # История 2 — «Цены честно»
    dict(bg='price-cover.png', out='s2-1.jpg', kind='cover',
         q='Сколько стоит\nлечение?', sub='Посчитаем до начала. Письменно.'),
    dict(bg='price-plan.png', out='s2-2.jpg', kind='points',
         title='План — на бумаге',
         points=['Цены и сроки фиксируем\nдо начала лечения',
                 'Смета на все услуги — от\nгигиены до имплантации',
                 'Консультация с планом —\n1 000 ₽'],
         disclaimer=True),
    dict(bg='price-cta.png', out='s2-3.jpg', kind='cta',
         title='Без сюрпризов\nв конце',
         sub='Полный прайс — на сайте'),

    # История 3 — «Для всей семьи»
    dict(bg='family-cover.png', out='s3-1.jpg', kind='cover', cy=0.18,
         q='Одна клиника —\nна всю семью?', sub='Да. Так и задумано.'),
    dict(bg='family-walk.png', out='s3-2.jpg', kind='points',
         title='Семейная программа',
         points=['Скидка 3–10% всей семье\nпри лечении троих и более',
                 '−10% многодетным, военно-\nслужащим и пенсионерам',
                 'Ежедневно 10:00–20:00']),
    dict(bg='family-cta.png', out='s3-3.jpg', kind='cta',
         title='Приходите\nвместе',
         sub='Мытищи, ул. Мира, 37'),

    # История 4 — «Ровные зубы»
    dict(bg='ortho-cover.png', out='s4-1.jpg', kind='cover',
         q='Мечтаете о\nровных зубах?', sub='Начать проще, чем кажется'),
    dict(bg='ortho-mirror.png', out='s4-2.jpg', kind='points',
         title='Первый шаг — 0 ₽',
         points=['Консультация ортодонта —\nбесплатно',
                 'Врач оценит прикус\nи подберёт вариант',
                 'Брекеты или элайнеры —\nрешаете вы'],
         disclaimer=True),
    dict(bg='ortho-smile.png', out='s4-3.jpg', kind='cta',
         title='Узнайте\nсвой вариант',
         sub='Запись за пару минут',
         disclaimer=True),

    # История 5 — «Брекеты взрослым» (миф про возраст)
    dict(bg='braces-cover.png', out='s5-1.jpg', kind='cover', scrim=True,
         q='Брекеты после 30 —\nне поздно?', sub='Самый частый вопрос ортодонту'),
    dict(bg='braces-macro.png', out='s5-2.jpg', kind='points',
         title='Поздно не бывает',
         points=['Зубы двигаются\nв любом возрасте',
                 'Брекет-система под ключ —\nот 35 000 ₽',
                 'Элайнеры — почти невидимы,\nот 120 000 ₽'],
         disclaimer=True),
    dict(bg='braces-cta.png', out='s5-3.jpg', kind='cta',
         title='Ровные зубы\nидут всем',
         sub='Консультация ортодонта — бесплатно',
         disclaimer=True),

    # История 6 — «Имплантация»
    dict(bg='implant-cover.png', out='s6-1.jpg', kind='cover',
         q='Потеряли зуб —\nчто дальше?', sub='Соседние зубы уже начали сдвигаться'),
    dict(bg='implant-model.png', out='s6-2.jpg', kind='points',
         title='Имплант — навсегда',
         points=['Имплант Osstem —\nот 28 000 ₽',
                 'Имплант + коронка\nпод ключ — от 45 000 ₽',
                 'Каждый третий имплант —\nв подарок'],
         disclaimer=True),
    dict(bg='implant-cta.png', out='s6-3.jpg', kind='cta',
         title='Верните полную\nулыбку',
         sub='Жуйте, смейтесь, живите — без оглядки',
         disclaimer=True),
]


def prata(size):
    return ImageFont.truetype(str(FONTS / 'Prata-Regular.ttf'), size)


def onest(size, weight=400):
    f = ImageFont.truetype(str(FONTS / 'Onest[wght].ttf'), size)
    f.set_variation_by_axes([weight])
    return f


def cover_crop(img, w, h, cy=0.40):
    k = max(w / img.width, h / img.height)
    img = img.resize((round(img.width * k), round(img.height * k)), Image.LANCZOS)
    x = (img.width - w) // 2
    y = round((img.height - h) * cy)
    return img.crop((x, y, x + w, y + h))


def grad_overlay(size, top_h=430, bottom_h=900):
    """Тёмные градиенты сверху (под шапку) и снизу (под текст)."""
    ov = Image.new('RGBA', size, (0, 0, 0, 0))
    px = ov.load()
    tr, tg, tb = 10, 42, 40                      # тёмная лагуна-чернила
    for y in range(top_h):
        a = int(150 * (1 - y / top_h))
        for x in range(0, size[0], 1):
            pass
    # быстрее через полосы:
    ov = Image.new('RGBA', size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for y in range(top_h):
        a = int(135 * (1 - y / top_h) ** 1.3)
        d.line((0, y, size[0], y), fill=(tr, tg, tb, a))
    for i, y in enumerate(range(size[1] - bottom_h, size[1])):
        a = int(215 * (i / bottom_h) ** 1.25)
        d.line((0, y, size[0], y), fill=(tr, tg, tb, a))
    return ov


def diamond(d, cx, cy, r, fill):
    d.polygon([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)], fill=fill)


def header(cv, d):
    """Шапка: лого-чип + ВЕНЕЦИЯ + подпись — на каждом слайде."""
    chip = 92
    x0, y0 = 56, 56
    d.rounded_rectangle((x0, y0, x0 + chip, y0 + chip), radius=22, fill=ALABASTER)
    lg = Image.open(LOGO).convert('RGBA').resize((70, 70), Image.LANCZOS)
    cv.alpha_composite(lg, (x0 + 11, y0 + 11))
    d.text((x0 + chip + 26, y0 + 6), 'ВЕНЕЦИЯ', font=prata(44), fill=ALABASTER)
    f_s = onest(24, 600)
    t = 'СЕМЕЙНАЯ СТОМАТОЛОГИЯ · МЫТИЩИ'
    x = x0 + chip + 26
    for ch in t:
        d.text((x, y0 + 62), ch, font=f_s, fill=MIST)
        x += d.textlength(ch, font=f_s) + 3


def multiline(d, x, y, text, font, fill, lh, center=None):
    for line in text.split('\n'):
        if center is not None:
            d.text((center - d.textlength(line, font=font) / 2, y), line,
                   font=font, fill=fill)
        else:
            d.text((x, y), line, font=font, fill=fill)
        y += lh
    return y


def build(slide):
    bg = Image.open(BG / slide['bg']).convert('RGB')
    cv = cover_crop(bg, W, H, cy=slide.get('cy', 0.40)).convert('RGBA')
    cv.alpha_composite(grad_overlay((W, H)))
    d = ImageDraw.Draw(cv)
    header(cv, d)
    cx = W // 2

    if slide['kind'] == 'cover':
        # бейдж + крупный вопрос + подпись
        if slide.get('scrim'):
            # низ фона светлый (одежда/стена) — алебастровый текст тонет;
            # подкладываем дополнительное тёмное стекло
            extra = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            ed = ImageDraw.Draw(extra)
            for i, yy in enumerate(range(H - 800, H)):
                a = int(150 * (i / 800) ** 1.1)
                ed.line((0, yy, W, yy), fill=(10, 42, 40, a))
            cv.alpha_composite(extra)
        y = H - BOTTOM_FREE - 560
        f_q = prata(92)
        y = multiline(d, 0, y, slide['q'], f_q, ALABASTER, 122, center=cx)
        y += 26
        diamond(d, cx, y + 16, 11, TERRA)
        y += 46
        multiline(d, 0, y, slide['sub'], onest(40, 500), MIST, 54, center=cx)

    elif slide['kind'] == 'points':
        n = len(slide['points'])
        block_h = 118 + n * 148
        y = H - BOTTOM_FREE - block_h - (64 if slide.get('disclaimer') else 10)
        d.text((72, y), slide['title'], font=prata(76), fill=ALABASTER)
        y += 118
        for p in slide['points']:
            diamond(d, 88, y + 26, 12, TERRA)
            multiline(d, 126, y, p, onest(38, 500), ALABASTER, 50)
            y += 148
        if slide.get('disclaimer'):
            d.text((72, y + 6), DISCLAIMER, font=onest(24, 400), fill='#8FB5AE')

    elif slide['kind'] == 'cta':
        y = H - BOTTOM_FREE - 520 - (46 if slide.get('disclaimer') else 0)
        f_t = prata(92)
        y = multiline(d, 0, y, slide['title'], f_t, ALABASTER, 120, center=cx)
        y += 20
        y = multiline(d, 0, y, slide['sub'], onest(40, 500), MIST, 54, center=cx)
        y += 40
        # плашка-CTA со стрелкой к кнопке Яндекса
        label = 'Записаться — кнопка ниже'
        f_b = onest(40, 700)
        bw = d.textlength(label, font=f_b) + 120
        bx = cx - bw / 2
        d.rounded_rectangle((bx, y, bx + bw, y + 96), radius=48, fill=TERRA)
        d.text((bx + 60, y + 24), label, font=f_b, fill='#FFFFFF')
        ay = y + 96 + 26
        d.polygon([(cx - 20, ay), (cx + 20, ay), (cx, ay + 26)], fill=TERRA)
        if slide.get('disclaimer'):
            dw = d.textlength(DISCLAIMER, font=onest(24, 400))
            d.text((cx - dw / 2, ay + 40), DISCLAIMER, font=onest(24, 400),
                   fill='#8FB5AE')

    return cv.convert('RGB')


def main():
    OUT.mkdir(exist_ok=True)
    missing = [s['bg'] for s in SLIDES if not (BG / s['bg']).exists()]
    if missing:
        raise SystemExit('нет фонов: ' + ', '.join(missing))
    for s in SLIDES:
        im = build(s)
        assert im.size == (W, H)
        im.save(OUT / s['out'], quality=93)
        print('✓', s['out'])
    print(f'Готово: {len(SLIDES)} слайдов → out/')


if __name__ == '__main__':
    main()
