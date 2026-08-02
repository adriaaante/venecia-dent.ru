#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Двусторонний рекламный буклет «Венеции» — сборка печатных файлов.

⚠️ Цены в буклете ОТДЕЛЬНЫЕ от сайта: действуют только при предъявлении
буклета и могут отличаться от прайса (решение владельца, 02.08.2026).
НЕ «чинить» их по сайту.

Формат: A5 портрет, 300 DPI, вылеты 3 мм на сторону.
  Обрезной формат 148×210 мм  → 1748×2480 px
  С вылетами     154×216 мм  → 1819×2551 px
Весь русский текст рисуется PIL (Prata + Onest), фото — Higgsfield
(img/hero-woman.png, img/family.png).

Запуск из каталога _materials/buklet/:
    python3 build-booklet.py          # собрать + прогнать проверки
    python3 build-booklet.py --check  # только проверки текстов

На выходе в out/:
    buklet-front.png / buklet-back.png     — стороны с вылетами, 300 dpi
    venecia-buklet-A5-print.pdf            — двухстраничный файл в печать
    preview-front.jpg / preview-back.jpg   — лёгкие превью для согласования
"""
import argparse
import pathlib
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

BASE = pathlib.Path(__file__).resolve().parent
OUT = BASE / 'out'
IMG = BASE / 'img'
FONTS = BASE / 'fonts'

DPI = 300
MM = DPI / 25.4                     # px в миллиметре
BLEED = round(3 * MM)               # 35 px
W, H = round(148 * MM) + 2 * BLEED, round(210 * MM) + 2 * BLEED  # 1783+... считаем ниже
W, H = 1748 + 2 * BLEED, 2480 + 2 * BLEED
SAFE = BLEED + round(5 * MM)        # текст не ближе 5 мм к резу

# Палитра Венеции (BRAND.md)
LAGOON = '#0F6E66'
LAGOON_DEEP = '#0A4A46'
LAGOON_DARK = '#0A3F3B'
TERRA = '#C75B39'
TERRA_SOFT = '#E08A66'
ALABASTER = '#F7FAF8'
INK = '#13292A'
TINT = '#DBEAE5'
MIST = '#BFE3DC'          # светлая лагуна для подписей на тёмном
FADED = '#9DC4BC'         # мелкий шрифт на тёмном

# ---------------------------------------------------------------- тексты
T = {
    'brand': 'Венеция',
    'brand_sub': 'СЕМЕЙНАЯ СТОМАТОЛОГИЯ · МЫТИЩИ',
    'badge_front': 'АКЦИЯ ПО ЭТОМУ БУКЛЕТУ',
    'headline1': 'Каждый третий имплант',
    'headline2': '— в подарок',
    'front_sub': 'И ещё четыре предложения — на обороте',
    'phone': '+7 (916) 838-08-88',
    'contacts_line': 'Мытищи, ул. Мира, 37  ·  ежедневно 10:00–20:00  ·  venecia-dent.ru',
    'front_small': 'Акции действуют при предъявлении буклета. Имеются противопоказания,',
    'front_small2': 'необходима консультация специалиста.',

    'back_eyebrow': 'ВЫГОДНО ПО БУКЛЕТУ',
    'back_title': 'Акции этого буклета',
    'feat_title': 'Имплант + циркониевая коронка',
    'feat_sub': 'под ключ, в комплексе',
    'feat_price': '42 000 ₽',
    'cards': [
        ('Каждый третий имплант', None, 'В ПОДАРОК'),
        ('Установка брекетов', '50 000 ₽', None),
        ('Комплексная гигиена полости рта', '5 000 ₽', None),
        ('Многодетным, военнослужащим и пенсионерам', None, 'СКИДКА 10%'),
    ],
    'qr_url': 'https://venecia-dent.ru/?utm_source=buklet&utm_medium=print&utm_campaign=promo2026',
    'qr_caption': 'venecia-dent.ru',
    'back_invite': 'Покажите этот буклет администратору —',
    'back_invite2': 'и акционные цены будут закреплены за вами.',
    'schedule': 'Ежедневно 10:00–20:00',
    'address': 'Московская область, г. Мытищи, ул. Мира, д. 37',
    'messengers': 'WhatsApp и Telegram: +7 (916) 838-08-88',
    'back_small': 'Акции действуют при предъявлении буклета. Цены могут отличаться от прайса на сайте. Не является публичной офертой.',
    'back_small2': 'Имеются противопоказания, необходима консультация специалиста.',
}

FORBIDDEN = ['премиум', 'КТ', 'томограф', 'детск', 'микроскоп', '3Shape',
             'Версаль', 'Ангел', 'Реутов']


# ---------------------------------------------------------------- шрифты
def prata(size):
    return ImageFont.truetype(str(FONTS / 'Prata-Regular.ttf'), size)


def onest(size, weight=400):
    f = ImageFont.truetype(str(FONTS / 'Onest[wght].ttf'), size)
    f.set_variation_by_axes([weight])
    return f


def tw(draw, text, font, tracking=0):
    w = draw.textlength(text, font=font)
    if tracking:
        w += tracking * (len(text) - 1)
    return w


def text_tracked(draw, xy, text, font, fill, tracking=0, anchor_center_x=None):
    """Текст с межбуквенным трекингом; anchor_center_x — центрировать по x."""
    if not tracking:
        if anchor_center_x is not None:
            xy = (anchor_center_x - draw.textlength(text, font=font) / 2, xy[1])
        draw.text(xy, text, font=font, fill=fill)
        return
    total = tw(draw, text, font, tracking)
    x = (anchor_center_x - total / 2) if anchor_center_x is not None else xy[0]
    y = xy[1]
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        x += draw.textlength(ch, font=font) + tracking


def fit_font(draw, text, maker, size, max_w, min_size=24):
    """Подобрать размер шрифта, чтобы строка влезла в max_w."""
    while size > min_size:
        f = maker(size)
        if draw.textlength(text, font=f) <= max_w:
            return f, size
        size -= 2
    return maker(min_size), min_size


# ---------------------------------------------------------------- фигуры
def arch_mask(w, h, bottom_radius=28, arch_h=None, ss=4):
    """Маска арки: свод (полукруг или эллипс высотой arch_h) + скруглённый низ.

    Для узких арок arch_h по умолчанию w/2 (романский полукруг); для широких
    панелей задавать arch_h меньше высоты, иначе свод не помещается.
    """
    if arch_h is None:
        arch_h = w // 2
    arch_h = min(arch_h, h - bottom_radius - 1)
    m = Image.new('L', (w * ss, h * ss), 0)
    d = ImageDraw.Draw(m)
    d.ellipse((0, 0, w * ss, 2 * arch_h * ss), fill=255)
    d.rounded_rectangle((0, arch_h * ss, w * ss, h * ss),
                        radius=bottom_radius * ss, fill=255)
    return m.resize((w, h), Image.LANCZOS)


def cover_crop(img, w, h, cx=0.5, cy=0.42):
    """Вписать фото в w×h по cover; cx/cy — точка интереса."""
    k = max(w / img.width, h / img.height)
    nw, nh = round(img.width * k), round(img.height * k)
    img = img.resize((nw, nh), Image.LANCZOS)
    x = round((nw - w) * cx)
    y = round((nh - h) * cy)
    return img.crop((x, y, x + w, y + h))


def vgrad(w, h, top, bottom):
    base = Image.new('RGB', (1, h))
    t = Image.new('RGB', (1, 1), top).getpixel((0, 0))
    b = Image.new('RGB', (1, 1), bottom).getpixel((0, 0))
    px = base.load()
    for y in range(h):
        k = y / max(1, h - 1)
        px[0, y] = tuple(round(t[i] + (b[i] - t[i]) * k) for i in range(3))
    return base.resize((w, h))


def glow(canvas, center, radius, color, alpha):
    """Мягкое радиальное свечение поверх canvas."""
    layer = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    c = Image.new('RGB', (1, 1), color).getpixel((0, 0))
    d.ellipse((center[0] - radius, center[1] - radius,
               center[0] + radius, center[1] + radius), fill=c + (alpha,))
    layer = layer.filter(ImageFilter.GaussianBlur(radius / 2.2))
    canvas.alpha_composite(layer)


def pill(draw, x0, y0, x1, y1, fill):
    draw.rounded_rectangle((x0, y0, x1, y1), radius=(y1 - y0) / 2, fill=fill)


def diamond(draw, cx, cy, r, fill):
    """Фирменный ромб-буллет. Рисуем полигоном: глифа ◆ в Onest нет,
    текстом он выводится квадратом-тофу."""
    draw.polygon([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)], fill=fill)


# ---------------------------------------------------------------- стороны
def build_front():
    cv = vgrad(W, H, LAGOON_DARK, '#0C5750').convert('RGBA')
    glow(cv, (W - 260, 420), 700, LAGOON, 110)
    glow(cv, (240, H - 420), 640, TERRA, 38)
    d = ImageDraw.Draw(cv)
    cx = W // 2

    # --- шапка: логотип + имя (у знака свой скруглённый фон — без белого чипа,
    # иначе получается двойная рамка)
    logo_s = 172
    logo = Image.open(IMG / 'logo-600.png').convert('RGBA').resize(
        (logo_s, logo_s), Image.LANCZOS)
    logo_y = SAFE + 18
    cv.alpha_composite(logo, (cx - logo_s // 2, logo_y))

    y = logo_y + logo_s + 26
    f_brand = prata(96)
    text_tracked(d, (0, y), T['brand'], f_brand, ALABASTER, anchor_center_x=cx)
    y += 126
    f_sub = onest(33, 600)
    text_tracked(d, (0, y), T['brand_sub'], f_sub, MIST, tracking=9, anchor_center_x=cx)

    # --- арка с фото героини
    aw, ah = 1080, 1010
    ax, ay = cx - aw // 2, y + 80
    photo = cover_crop(Image.open(IMG / 'hero-woman.png').convert('RGB'), aw, ah,
                       cx=0.42, cy=0.26)
    mask = arch_mask(aw, ah)
    # рамка-обводка: чуть большая арка тонкой линией
    ow, oh, off = aw + 44, ah + 44, 22
    omask = arch_mask(ow, oh)
    ring = Image.new('RGBA', (ow, oh), (0, 0, 0, 0))
    ring.paste(Image.new('RGBA', (ow, oh), (247, 250, 248, 90)), (0, 0), omask)
    inner = arch_mask(ow - 6, oh - 6)
    hole = Image.new('L', (ow, oh), 0)
    hole.paste(inner, (3, 3))
    ring.putalpha(Image.composite(Image.new('L', (ow, oh), 0), ring.getchannel('A'), hole))
    cv.alpha_composite(ring, (ax - off, ay - off))
    cv.paste(photo, (ax, ay), mask)

    # --- бейдж поверх низа арки
    f_badge = onest(37, 700)
    bw = tw(d, T['badge_front'], f_badge, 4) + 92
    bh = 88
    bx, by = cx - bw / 2, ay + ah - bh / 2
    pill(d, bx, by, bx + bw, by + bh, TERRA)
    text_tracked(d, (0, by + (bh - 46) / 2), T['badge_front'], f_badge, '#FFFFFF',
                 tracking=4, anchor_center_x=cx)

    # --- заголовок
    y = by + bh + 64
    max_w = W - 2 * SAFE - 40
    f_h1, _ = fit_font(d, T['headline1'], prata, 108, max_w)
    text_tracked(d, (0, y), T['headline1'], f_h1, ALABASTER, anchor_center_x=cx)
    y += round(f_h1.size * 1.26)
    f_h2, _ = fit_font(d, T['headline2'], prata, 122, max_w)
    text_tracked(d, (0, y), T['headline2'], f_h2, TERRA_SOFT, anchor_center_x=cx)
    y += round(f_h2.size * 1.40)

    f_fs = onest(42, 500)
    text_tracked(d, (0, y), T['front_sub'], f_fs, MIST, anchor_center_x=cx)
    sub_bottom = y + 58

    # --- контактная плашка
    ph_h = 244
    px0, px1 = SAFE + 26, W - SAFE - 26
    py1 = H - SAFE - 118
    py0 = py1 - ph_h
    assert py0 - sub_bottom >= 24, f'заголовок налез на плашку ({py0 - sub_bottom}px)'
    d.rounded_rectangle((px0, py0, px1, py1), radius=34, fill=ALABASTER)
    f_phone = onest(72, 800)
    text_tracked(d, (0, py0 + 42), T['phone'], f_phone, INK, anchor_center_x=cx)
    f_c, _ = fit_font(d, T['contacts_line'], lambda s: onest(s, 500), 37,
                      px1 - px0 - 80)
    text_tracked(d, (0, py0 + 150), T['contacts_line'], f_c, '#4A6360',
                 anchor_center_x=cx)

    # --- мелкий шрифт
    f_small = onest(28, 500)
    text_tracked(d, (0, py1 + 24), T['front_small'], f_small, FADED, anchor_center_x=cx)
    text_tracked(d, (0, py1 + 62), T['front_small2'], f_small, FADED, anchor_center_x=cx)

    return cv.convert('RGB')


def build_back():
    cv = Image.new('RGBA', (W, H), ALABASTER)
    d = ImageDraw.Draw(cv)
    cx = W // 2

    # --- верх: семейное фото широкой аркой
    aw, ah = 1440, 600
    ax, ay = cx - aw // 2, SAFE + 26
    photo = cover_crop(Image.open(IMG / 'family.png').convert('RGB'), aw, ah, cy=0.30)
    cv.paste(photo, (ax, ay), arch_mask(aw, ah, bottom_radius=30, arch_h=230))

    # --- заголовок раздела (ромбы рисуем полигонами — глифа ◆ в шрифте нет)
    y = ay + ah + 40
    f_eb = onest(33, 700)
    eb_w = tw(d, T['back_eyebrow'], f_eb, 7)
    text_tracked(d, (0, y), T['back_eyebrow'], f_eb, TERRA, tracking=7,
                 anchor_center_x=cx)
    diamond(d, cx - eb_w / 2 - 40, y + 22, 11, TERRA)
    diamond(d, cx + eb_w / 2 + 40, y + 22, 11, TERRA)
    y += 56
    f_t = prata(84)
    text_tracked(d, (0, y), T['back_title'], f_t, INK, anchor_center_x=cx)
    y += 126

    # --- featured-карта (лагуна)
    card_x0, card_x1 = SAFE + 26, W - SAFE - 26
    fc_h = 192
    d.rounded_rectangle((card_x0, y, card_x1, y + fc_h), radius=30, fill=LAGOON)
    f_ft, _ = fit_font(d, T['feat_title'], lambda s: onest(s, 700), 52,
                       card_x1 - card_x0 - 108 - d.textlength(T['feat_price'],
                                                              font=prata(88)) - 60)
    f_fp = prata(88)
    fp_w = d.textlength(T['feat_price'], font=f_fp)
    d.text((card_x0 + 54, y + 38), T['feat_title'], font=f_ft, fill=ALABASTER)
    d.text((card_x0 + 54, y + 112), T['feat_sub'], font=onest(36, 400), fill=MIST)
    d.text((card_x1 - 54 - fp_w, y + (fc_h - 110) / 2), T['feat_price'],
           font=f_fp, fill='#FFD9C9')
    y += fc_h + 24

    # --- обычные карты
    ch = 138
    f_cp = prata(62)
    f_chip = onest(33, 700)
    for title, price, chiptxt in T['cards']:
        d.rounded_rectangle((card_x0, y, card_x1, y + ch), radius=26,
                            fill='#FFFFFF', outline=TINT, width=3)
        diamond(d, card_x0 + 66, y + ch / 2, 13, TERRA)
        right_w = d.textlength(price, font=f_cp) + 54 if price else 0
        chip_w = tw(d, chiptxt, f_chip, 2) + 74 + 54 if chiptxt else 0
        f_title, _ = fit_font(d, title, lambda s: onest(s, 600), 44,
                              (card_x1 - card_x0) - 150 - max(right_w, chip_w) - 30)
        d.text((card_x0 + 112, y + (ch - f_title.size * 1.15) / 2),
               title, font=f_title, fill=INK)
        if price:
            pw = d.textlength(price, font=f_cp)
            d.text((card_x1 - 54 - pw, y + (ch - 80) / 2), price, font=f_cp, fill=TERRA)
        if chiptxt:
            cw = tw(d, chiptxt, f_chip, 2) + 74
            cy0 = y + (ch - 72) / 2
            pill(d, card_x1 - 54 - cw, cy0, card_x1 - 54, cy0 + 72, TERRA)
            text_tracked(d, (card_x1 - 54 - cw + 37, cy0 + 16), chiptxt, f_chip,
                         '#FFFFFF', tracking=2)
        y += ch + 16

    # --- приглашение
    y += 10
    f_inv = onest(36, 500)
    text_tracked(d, (0, y), T['back_invite'], f_inv, '#4A6360', anchor_center_x=cx)
    text_tracked(d, (0, y + 48), T['back_invite2'], f_inv, '#4A6360', anchor_center_x=cx)
    invite_bottom = y + 48 + 46

    # --- футер-панель на лагуне (в обрез, до низа с вылетами)
    fy = H - BLEED - 600
    assert fy - invite_bottom >= 20, f'приглашение налезло на футер ({fy - invite_bottom}px)'
    d.rectangle((0, fy, W, H), fill=LAGOON_DARK)
    # QR справа на белой карточке (border=4 — полная зона тишины для сканеров)
    import qrcode
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M,
                       box_size=10, border=4)
    qr.add_data(T['qr_url'])
    qr.make(fit=True)
    qimg = qr.make_image(fill_color=INK, back_color='white').convert('RGB')
    qsize = 290
    qimg = qimg.resize((qsize, qsize), Image.NEAREST)
    qcard_w, qcard_h = 330, 376
    qx = W - SAFE - 30 - qcard_w
    qy = fy + 54
    d.rounded_rectangle((qx, qy, qx + qcard_w, qy + qcard_h), radius=26, fill='#FFFFFF')
    cv.paste(qimg, (qx + (qcard_w - qsize) // 2, qy + 18))
    f_qc = onest(32, 600)
    qc_w = d.textlength(T['qr_caption'], font=f_qc)
    d.text((qx + (qcard_w - qc_w) / 2, qy + qcard_h - 56), T['qr_caption'],
           font=f_qc, fill=INK)

    # контакты слева
    lx = SAFE + 30
    ly = fy + 58
    d.text((lx, ly), T['phone'], font=onest(62, 800), fill='#FFFFFF')
    ly += 98
    for line in (T['address'], T['schedule'], T['messengers']):
        d.text((lx, ly), line, font=onest(36, 500), fill=MIST)
        ly += 56

    # мелкий шрифт по низу, ПОД карточкой QR — на всю ширину
    sy = qy + qcard_h + 34
    f_sm = onest(26, 500)
    f_sm1, _ = fit_font(d, T['back_small'], lambda s: onest(s, 500), 26,
                        W - 2 * SAFE - 20)
    text_tracked(d, (0, sy), T['back_small'], f_sm1, FADED, anchor_center_x=cx)
    text_tracked(d, (0, sy + 38), T['back_small2'], f_sm, FADED, anchor_center_x=cx)
    assert sy + 38 + 34 <= H - SAFE + 10, 'мелкий шрифт слишком близко к резу'

    return cv.convert('RGB')


# ---------------------------------------------------------------- проверки
def run_checks():
    errors = []
    blob = ' '.join(str(v) for v in T.values())
    for bad in FORBIDDEN:
        if bad.lower() in blob.lower():
            errors.append(f'запрещённое слово в текстах: «{bad}»')
    required = ['42 000 ₽', '50 000 ₽', '5 000 ₽', 'В ПОДАРОК', 'СКИДКА 10%',
                '+7 (916) 838-08-88', 'Мытищи', 'предъявлении буклета',
                'противопоказания', 'публичной офертой', 'venecia-dent.ru']
    for req in required:
        if req not in blob:
            errors.append(f'нет обязательного фрагмента: «{req}»')
    for img in ('hero-woman.png', 'family.png', 'logo-600.png'):
        if not (IMG / img).exists():
            errors.append(f'нет файла {img}')
    return errors


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()

    errors = run_checks()
    if errors:
        for e in errors:
            print('  ✗', e)
        return 1
    print('Тексты и материалы: все проверки пройдены.')
    if args.check:
        return 0

    OUT.mkdir(exist_ok=True)
    front = build_front()
    back = build_back()
    assert front.size == (W, H) and back.size == (W, H), 'размер холста сбился'

    front.save(OUT / 'buklet-front.png', dpi=(DPI, DPI))
    back.save(OUT / 'buklet-back.png', dpi=(DPI, DPI))
    front.save(OUT / 'venecia-buklet-A5-print.pdf', save_all=True,
               append_images=[back], resolution=DPI)
    for name, im in (('preview-front.jpg', front), ('preview-back.jpg', back)):
        im.resize((im.width // 2, im.height // 2), Image.LANCZOS).save(
            OUT / name, quality=88)
    print(f'Готово: {W}×{H} px (A5 + вылеты 3 мм, {DPI} dpi) → out/')
    return 0


if __name__ == '__main__':
    sys.exit(main())
