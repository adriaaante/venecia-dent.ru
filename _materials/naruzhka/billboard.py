# -*- coding: utf-8 -*-
"""
Наружная реклама «Венеция» — билборд 3×6 м.
Макет 1:10 при 300 dpi → 7087×3543 px (600×300 мм). Для печати типографии
обычно достаточно 1:10 при 300 dpi; вылеты у баннеров не требуются
(люверсы/карман), но по краям оставлен безопасный отступ 120 px.

Правила: фирменный стиль Венеции (лагуна/терракота/алебастр, Prata+Onest,
арка, ромбы), русский текст только PIL, дисклеймер «Имеются
противопоказания…» полосой ≥5 % площади, место под номер лицензии.
Запуск: python3 billboard.py  (фоны должны лежать в bg/)
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os

W, H = 7087, 3543
LAGOON = (15, 110, 102)
LAGOON_DEEP = (10, 74, 70)
INK = (19, 41, 42)
TERRA = (199, 91, 57)
BG = (247, 250, 248)
TINT = (217, 231, 226)
MUTED = (84, 103, 99)

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, '..', 'buklet', 'fonts')

def prata(size):
    return ImageFont.truetype(os.path.join(FONTS, 'Prata-Regular.ttf'), size)

def onest(size, weight=400):
    f = ImageFont.truetype(os.path.join(FONTS, 'Onest[wght].ttf'), size)
    f.set_variation_by_axes([weight])
    return f

def diamond(d, cx, cy, r, fill):
    d.polygon([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)], fill=fill)

def arch_photo(img, aw, ah):
    """Фото в фирменной арке: полукруг сверху + прямые бока."""
    photo = img.copy()
    scale = max(aw / photo.width, ah / photo.height)
    photo = photo.resize((round(photo.width * scale), round(photo.height * scale)), Image.LANCZOS)
    x = (photo.width - aw) // 2
    y = max(0, (photo.height - ah) // 3)  # кадр чуть выше центра — лица
    photo = photo.crop((x, y, x + aw, y + ah))
    mask = Image.new('L', (aw, ah), 0)
    md = ImageDraw.Draw(mask)
    md.pieslice([0, 0, aw, aw], 180, 360, fill=255)
    md.rectangle([0, aw // 2, aw, ah], fill=255)
    return photo, mask

def build(variant, bg_file, headline_lines, offer, out_name):
    im = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(im)

    # ── правая часть: фото в арке ──
    aw, ah = 2850, 3543 - 240
    photo, mask = arch_photo(Image.open(os.path.join(HERE, 'bg', bg_file)).convert('RGB'), aw, ah)
    px, py = W - aw - 170, H - ah  # арка «стоит» на нижней кромке (до полосы дисклеймера)
    im.paste(photo, (px, py), mask)
    # тонкая терракотовая обводка арки
    od = ImageDraw.Draw(im)
    ow = 14
    od.arc([px - ow, py - ow, px + aw + ow, py + aw + ow], 180, 360, fill=TERRA, width=ow)
    od.line([px - ow + ow // 2, py + aw // 2, px - ow + ow // 2, H], fill=TERRA, width=ow)
    od.line([px + aw + ow // 2, py + aw // 2, px + aw + ow // 2, H], fill=TERRA, width=ow)

    # ── декоративные ромбы на свободном поле ──
    diamond(d, W - 120, 300, 46, TINT)
    diamond(d, W - 260, 480, 26, TERRA)

    # ── шапка: логотип + имя клиники ──
    logo = Image.open(os.path.join(HERE, '..', '..', 'assets', 'img', 'logo.png')).convert('RGBA')
    ls = 360
    logo = logo.resize((ls, ls), Image.LANCZOS)
    im.paste(logo, (170, 150), logo)
    d.text((170 + ls + 70, 190), 'Стоматология', font=onest(120, 500), fill=MUTED)
    d.text((170 + ls + 64, 320), 'ВЕНЕЦИЯ', font=prata(170), fill=LAGOON)

    # ── заголовок ──
    y = 780
    for line in headline_lines:
        d.text((170, y), line, font=prata(330), fill=INK)
        y += 400

    # ── оффер-чип (терракота) ──
    y += 60
    of = onest(170, 700)
    tw = d.textlength(offer, font=of)
    pad = 90
    d.rounded_rectangle([170, y, 170 + tw + pad * 2, y + 300], radius=150, fill=TERRA)
    d.text((170 + pad, y + 62), offer, font=of, fill=(255, 255, 255))

    # ── контакты ──
    cy = y + 470
    d.text((170, cy), 'Мытищи, ул. Мира, 37', font=onest(155, 600), fill=INK)
    d.text((170, cy + 210), 'ежедневно 10:00–20:00  ·  venecia-dent.ru', font=onest(120, 500), fill=MUTED)
    ph = '+7 (916) 838-08-88'
    pf = onest(275, 800)
    d.text((170, cy + 420), ph, font=pf, fill=LAGOON)

    # ── юрлицо и лицензия ──
    lic = 'ООО «АНГЕЛ-ДЕНТ» · ИНН 5012077543 · Лицензия № Л041-01162-50/00299266 от 19.07.2016'
    d.text((170, H - 240 - 90), lic, font=onest(56, 500), fill=MUTED)

    # ── дисклеймер: полоса ≥5 % площади ──
    strip_h = 240  # 240/3543 ≈ 6.8 % высоты → >5 % площади
    d.rectangle([0, H - strip_h, W, H], fill=LAGOON_DEEP)
    warn = 'ИМЕЮТСЯ ПРОТИВОПОКАЗАНИЯ. НЕОБХОДИМА КОНСУЛЬТАЦИЯ СПЕЦИАЛИСТА'
    wf = onest(110, 700)
    ww = d.textlength(warn, font=wf)
    d.text(((W - ww) / 2, H - strip_h + (strip_h - 110) / 2 - 10), warn, font=wf, fill=(255, 255, 255))

    im.save(os.path.join(HERE, out_name), quality=95, dpi=(300, 300))
    print('built', out_name)

if __name__ == '__main__':
    build('family',
          'couple.png',
          ['Стоматология', 'для всей семьи'],
          'Семейная программа — скидка до 10 %',
          'billboard-family-6x3.jpg')
    build('smile',
          'smile.png',
          ['Здоровые зубы —', 'рядом с домом'],
          'Комплексная гигиена — 5 000 ₽',
          'billboard-smile-6x3.jpg')
