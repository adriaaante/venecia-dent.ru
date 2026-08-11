# -*- coding: utf-8 -*-
"""
Акции Яндекс.Бизнеса — «Венеция». Full-bleed баннер 1800×960
(горизонталь под родное поле «Фото акции», минимум Яндекса 900×480).

Композиция (правила выработаны на Angel, стиль — Венеции):
фото во весь холст → слева градиент лагуны → лого на белом чипе +
«ВЕНЕЦИЯ / Стоматология · Мытищи» → терракотовый бейдж → заголовок
белым → ВЫГОДА крупно + зачёркнутая старая цена → мелкий дисклеймер
«Имеются противопоказания…».

⚠️ Состав акций = сайт (promotions.html). Обычные цены прайса акциями
не оформлять. Первая акция попадает в Карты — туда самый универсальный
оффер.

Запуск: python3 venecia-promo.py   (фоны в bg/)
"""
from PIL import Image, ImageDraw, ImageFont
import os

W, H = 1800, 960
LAGOON = (15, 110, 102)
LAGOON_DEEP = (10, 74, 70)
TERRA = (199, 91, 57)
ALAB = (247, 250, 248)
TINT = (217, 231, 226)

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, '..', 'buklet', 'fonts')
LOGO = os.path.join(HERE, '..', '..', 'assets', 'img', 'logo.png')

def prata(s):
    return ImageFont.truetype(os.path.join(FONTS, 'Prata-Regular.ttf'), s)

def onest(s, w=500):
    f = ImageFont.truetype(os.path.join(FONTS, 'Onest[wght].ttf'), s)
    f.set_variation_by_axes([w]); return f

def cover(img, w, h, focus_right=True):
    """Кроп «cover» с сохранением правой части кадра (там человек)."""
    sc = max(w / img.width, h / img.height)
    img = img.resize((round(img.width * sc), round(img.height * sc)), Image.LANCZOS)
    x = img.width - w if focus_right else (img.width - w) // 2
    y = max(0, (img.height - h) // 3)
    return img.crop((x, y, x + w, y + h))

# ── акции: bg, бейдж, заголовок, выгода, старая цена, подпись ──
CARDS = [
    dict(key='implant3', bg='promo-implant.png', badge='ПОДАРОК',
         title=['Каждый 3-й имплант'], gain='в подарок', old=None,
         sub='Гарантия на имплантаты до 10 лет по договору'),
    dict(key='ortho0', bg='promo-braces.png', badge='0 ₽',
         title=['Консультация', 'ортодонта'], gain='бесплатно', old='1 000 ₽',
         sub='С расчётом ТРГ · брекеты или элайнеры — без обязательств'),
    dict(key='whitening', bg='promo-smile.png', badge='−30 %',
         title=['Отбеливание', 'Amazing White'], gain='17 500 ₽', old='25 000 ₽',
         sub='Обе челюсти под ключ · осветление до 6–8 тонов за визит'),
    dict(key='family', bg='promo-family.png', badge='СЕМЬЯ',
         title=['Семейная', 'программа'], gain='−3–10 %', old=None,
         sub='Скидка всем членам семьи при лечении троих и более'),
    dict(key='benefit', bg='promo-senior.png', badge='ЛЬГОТЫ',
         title=['Пенсионерам,', 'многодетным,', 'военнослужащим'], gain='−10 %', old=None,
         sub='На лечение, протезирование и гигиену · по удостоверению'),
    dict(key='hygiene', bg='promo-hygiene.png', badge='ПОДАРОК',
         title=['Чистка при импланта-', 'ции и брекетах'], gain='в подарок', old='5 000 ₽',
         sub='Ультразвук + Air Flow + полировка при заключении договора'),
]

def build(c):
    photo = Image.open(os.path.join(HERE, 'bg', c['bg'])).convert('RGB')
    im = cover(photo, W, H)

    # градиент лагуны слева (читаемость текста)
    grad = Image.new('L', (W, 1))
    for x in range(W):
        t = x / (W - 1)
        a = 255 if t < 0.30 else max(0, int(255 * (1 - (t - 0.30) / 0.42)))
        grad.putpixel((x, 0), a)
    grad = grad.resize((W, H))
    im.paste(Image.new('RGB', (W, H), LAGOON_DEEP), (0, 0), grad)

    d = ImageDraw.Draw(im)
    X = 90

    # лого на белом чипе + имя клиники
    chip = 104
    d.rounded_rectangle([X, 66, X + chip, 66 + chip], radius=26, fill=ALAB)
    logo = Image.open(LOGO).convert('RGBA').resize((chip - 18, chip - 18), Image.LANCZOS)
    im.paste(logo, (X + 9, 66 + 9), logo)
    d.text((X + chip + 26, 74), 'ВЕНЕЦИЯ', font=prata(46), fill=ALAB)
    d.text((X + chip + 28, 130), 'Стоматология · Мытищи', font=onest(26, 500), fill=TINT)

    # бейдж
    bf = onest(34, 700)
    bw = d.textlength(c['badge'], font=bf)
    d.rounded_rectangle([X, 250, X + bw + 64, 250 + 68], radius=34, fill=TERRA)
    d.text((X + 32, 250 + 15), c['badge'], font=bf, fill=(255, 255, 255))

    # заголовок
    y = 356
    for line in c['title']:
        d.text((X, y), line, font=prata(62), fill=ALAB)
        y += 82

    # выгода крупно + зачёркнутая старая цена
    y += 18
    gf = prata(112)
    d.text((X, y), c['gain'], font=gf, fill=(255, 255, 255))
    gw = d.textlength(c['gain'], font=gf)
    if c['old']:
        of = onest(44, 500)
        ox, oy = X + gw + 30, y + 52
        d.text((ox, oy), c['old'], font=of, fill=TINT)
        ow = d.textlength(c['old'], font=of)
        d.line([ox - 4, oy + 30, ox + ow + 4, oy + 30], fill=TINT, width=4)

    # подпись + дисклеймер
    d.text((X, H - 148), c['sub'], font=onest(28, 500), fill=TINT)
    d.text((X, H - 92), 'Имеются противопоказания, необходима консультация специалиста.',
           font=onest(22, 400), fill=(190, 205, 200))

    out = os.path.join(HERE, f"venecia-promo-{c['key']}.jpg")
    im.save(out, quality=92)
    print('built', os.path.basename(out))

if __name__ == '__main__':
    for c in CARDS:
        build(c)
