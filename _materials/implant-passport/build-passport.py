#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Паспорт имплантов «Венеции» — печатный макет для типографии.

Формат повторяет паспорт Angel-Dent (`~/Angel-Dent-site/_materials/
implant-passport/DESIGN.md`), стиль — фирменный Венеции:
  - A4 книжная + 2 мм вылетов = 214×301 мм, 300 dpi, 2 страницы;
  - тройной фальц: лист делится на 3 равные панели по высоте, линии
    сгиба на ⅓ и ⅔; на странице 1 (внешней) верхняя и нижняя панели
    свёрстаны «вверх ногами» — после фальцовки встают правильно;
  - метки сгиба — пунктирные чёрточки у краёв (на лагуне белые,
    на белом серые); меток реза нет.

Отличия от Angel по содержанию (НЕ «чинить»):
  - гарантия — «по договору», без сроков в месяцах (у Венеции нет
    подтверждённых цифр);
  - лицензия/юрлицо НЕ указываются — реквизитов Венеции ещё нет,
    чужие вписывать нельзя (см. CLAUDE.md);
  - никаких КТ/томографии.

Запуск из каталога _materials/implant-passport/:
    python3 build-passport.py          # собрать + проверки
    python3 build-passport.py --check  # только проверки текстов

Выход в out/: passport-page-1.png, passport-page-2.png (300 dpi),
Паспорт_имплантов_Венеция.pdf, preview-page-*.jpg.
"""
import argparse
import pathlib
import sys

from PIL import Image, ImageDraw, ImageFont

BASE = pathlib.Path(__file__).resolve().parent
OUT = BASE / 'out'
FONTS = BASE.parent / 'buklet' / 'fonts'
LOGO = BASE.parent / 'buklet' / 'img' / 'logo-600.png'

DPI = 300
MM = DPI / 25.4
BLEED = round(2 * MM)                      # 24 px
TRIM_W, TRIM_H = round(210 * MM), 3507     # 2480 × 3507 (кратно 3 панелям)
W, H = TRIM_W + 2 * BLEED, TRIM_H + 2 * BLEED
PANEL = TRIM_H // 3                        # 1169
FOLD1, FOLD2 = BLEED + PANEL, BLEED + 2 * PANEL
SAFE = BLEED + round(4 * MM)               # контент не ближе 4 мм к резу

LAGOON = '#0F6E66'
LAGOON_DARK = '#0A3F3B'
TERRA = '#C75B39'
ALABASTER = '#F7FAF8'
INK = '#13292A'
TINT = '#DBEAE5'          # тонкие рамки
FILL = '#EFF6F4'          # светлая заливка панелей/строк (лагуна 5%)
WARM = '#FBEFE9'          # тёплая подложка памяток (терракота 8%)
MIST = '#BFE3DC'
MUTED = '#4A6360'

T = {
    'brand': 'Венеция',
    'brand_sub': 'СЕМЕЙНАЯ СТОМАТОЛОГИЯ',
    'title1': 'ПАСПОРТ',
    'title2': 'ИМПЛАНТОВ',
    'tagline': 'Забота о вашей улыбке',
    'values': ['НАДЁЖНО', 'БЕРЕЖНО', 'ДЛЯ ВСЕЙ СЕМЬИ'],
    'cover_contacts': 'г. Мытищи, ул. Мира, д. 37   ·   +7 (916) 838-08-88   ·   venecia-dent.ru',

    'strip_slogan': 'Ведём за руку от проблемы до результата',
    'welcome': 'Поздравляем с новой улыбкой!',
    'welcome_sub': 'Забота о вашей улыбке',
    'welcome_text': ['Установив имплантаты, Вы сделали важный шаг к новому качеству жизни.',
                     'Бережно храните этот паспорт — он содержит важную информацию',
                     'о проведённом лечении.'],
    'info1_title': 'ЗАБОТА И ВНИМАНИЕ',
    'info1': ['Семейная клиника в Мытищах.',
              'Врачи с опытом от 10 лет.',
              'Гарантия — по договору лечения.'],
    'info2_title': 'ОТ ПРОБЛЕМЫ ДО РЕЗУЛЬТАТА',
    'info2': ['Сначала диагностика и понятный план,',
              'затем — аккуратное лечение',
              'и сопровождение на каждом этапе.'],
    'contacts_title': 'КОНТАКТЫ',
    'contacts': [('АДРЕС', 'Московская область, г. Мытищи, ул. Мира, д. 37'),
                 ('РЕЖИМ', 'Ежедневно 10:00 – 20:00'),
                 ('ТЕЛЕФОН', '+7 (916) 838-08-88'),
                 ('САЙТ', 'venecia-dent.ru'),
                 ('МЕССЕНДЖЕРЫ', 'WhatsApp · Telegram · +7 (916) 838-08-88')],

    'patient_title': 'Данные пациента',
    'patient_fields': [['Ф.И.О.'],
                       ['Дата рождения', 'Телефон'],
                       ['Дата начала лечения', 'Лечащий врач'],
                       ['Аллергии / противопоказания']],
    'dear_title': 'Уважаемый пациент!',
    'dear_text': ['Этот паспорт содержит информацию о проведённой Вам имплантации',
                  'зубов в клинике «Венеция»: тип установленных имплантатов',
                  'и ортопедических конструкций, данные врачей и лаборатории.',
                  '',
                  'Использование оригинальных компонентов системы имплантации',
                  'и соблюдение рекомендаций врача — главные условия долгого',
                  'и комфортного срока службы Ваших новых зубов.',
                  '',
                  'Бережно храните этот документ и берите его с собой',
                  'на каждый приём у стоматолога.'],
    'sidebar_chip': 'ГАРАНТИЯ ПО ДОГОВОРУ',

    'p2s1_title': 'Информация об имплантации',
    'p2s1_sub': 'Данные о каждом установленном имплантате, ортопедической конструкции и лабораторном этапе.',
    'clinic_field': 'Клиника',
    'system_field': 'Система имплантации / производитель',
    'implant_card': 'ИМПЛАНТАТ № {}',
    'fills_clinic': 'заполняет клиника',
    'card_fields': ['Номер зуба', 'Дата установки', 'Врач'],
    'sticker1': 'НАКЛЕЙКА · ИМПЛАНТАТ',
    'sticker2': 'НАКЛЕЙКА · ОРТОПЕДИЯ',
    'sticker_ph': 'место для наклейки',
    'card_fields2': ['Ø × длина, мм', 'Торк, Н·см', 'Фиксация коронки'],
    'lab_line': 'ЛАБОРАТОРИЯ / МАТЕРИАЛЫ / ЗАМЕТКИ',

    'p2s2_title': 'После операции',
    'p2s2_sub': 'Что необходимо знать и делать после имплантации.',
    'memos': [('01', 'Отёк', ['Холод (лёд через ткань) на 15–20', 'мин — уменьшит отёк и боль.']),
              ('02', 'Боль', ['Препараты строго по схеме врача.', 'Антибиотики — без пропусков.']),
              ('03', 'Полоскания', ['Первые сутки не полощите рот.', 'Далее — назначенные растворы.']),
              ('04', 'Питание', ['Не жуйте на стороне импланта.', 'Избегайте горячего 2–3 дня.'])],

    'numbering_title': 'Системы нумерации зубов',
    'numbering_note': '(применяются обе системы)',
    'fdi_label': 'Система FDI',
    'fdi_note': '(международная — двухзначная по квадрантам)',
    'ada_label': 'Система ADA',
    'ada_note': '(американская — сквозная нумерация 1–32)',

    'alert': 'Если что-то беспокоит:',
    'alert_text': 'сильная боль, отёк больше 2–3 дней, кровотечение — звоните +7 (916) 838-08-88',

    'habits_title': 'Полезные привычки для долгой службы импланта',
    'habits': [('01', 'Чистка 2 раза в день', 'Мягкая щётка, неабразивная паста.'),
               ('02', 'Зубная нить ежедневно', 'Особенно вокруг имплантата.'),
               ('03', 'Ирригатор', 'На низкой мощности — между зубами.'),
               ('04', 'Профгигиена 2 раза в год', 'Профилактика периимплантита.')],

    'schedule_title': 'График контрольных осмотров',
    'schedule_sub': 'Соблюдение графика — главное условие сохранения гарантии. Отметьте даты посещений.',
    'schedule_head': ['СРОК', 'ЦЕЛЬ ВИЗИТА', 'ДАТА ПРИЁМА', 'ВРАЧ / ПОДПИСЬ'],
    'schedule': [('через 7–10 дней', 'снятие швов'),
                 ('через 1 месяц', 'контроль приживления'),
                 ('через 3 месяца', 'осмотр перед протезированием'),
                 ('через 6 месяцев', 'плановый осмотр'),
                 ('через 1 год', 'профилактика и гигиена')],

    'thanks_title': 'Спасибо за доверие!',
    'thanks_text': ['Мы заботимся о Ваших зубах и о том, как Вы себя чувствуете после лечения.',
                    'Если возникнут вопросы — звоните, пишите, приходите. Мы всегда рядом.'],
    'thanks_sign': 'С уважением, команда «Венеции»',
}

# Обычные слова ищутся подстрокой без регистра; «КТ» — отдельно, целым
# словом с учётом регистра, иначе ложно срабатывает на «КОНТАКТЫ», «практика».
FORBIDDEN = ['премиум', 'томограф', 'детск', 'микроскоп',
             '3Shape', 'Версаль', 'Ангел', 'Реутов', 'лицензия',
             '120 месяцев', 'ЛО-50']
FORBIDDEN_WORD = ['КТ', 'КЛКТ']


def prata(size):
    return ImageFont.truetype(str(FONTS / 'Prata-Regular.ttf'), size)


def onest(size, weight=400):
    f = ImageFont.truetype(str(FONTS / 'Onest[wght].ttf'), size)
    f.set_variation_by_axes([weight])
    return f


def text_c(d, cx, y, text, font, fill, tracking=0):
    if tracking:
        total = d.textlength(text, font=font) + tracking * (len(text) - 1)
        x = cx - total / 2
        for ch in text:
            d.text((x, y), ch, font=font, fill=fill)
            x += d.textlength(ch, font=font) + tracking
    else:
        d.text((cx - d.textlength(text, font=font) / 2, y), text, font=font, fill=fill)


def diamond(d, cx, cy, r, fill):
    d.polygon([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)], fill=fill)


def dotted(d, x0, y, x1, color='#9DB8B3', dot=3, gap=9):
    x = x0
    while x < x1:
        d.ellipse((x, y, x + dot, y + dot), fill=color)
        x += dot + gap


def dashed_h(d, x0, x1, y, color, wpx=2, dash=14, gap=10):
    x = x0
    while x < x1:
        d.line((x, y, min(x + dash, x1), y), fill=color, width=wpx)
        x += dash + gap


def dashed_rect(d, box, color, wpx=2, dash=12, gap=8):
    x0, y0, x1, y1 = box
    x = x0
    while x < x1:
        d.line((x, y0, min(x + dash, x1), y0), fill=color, width=wpx)
        d.line((x, y1, min(x + dash, x1), y1), fill=color, width=wpx)
        x += dash + gap
    y = y0
    while y < y1:
        d.line((x0, y, x0, min(y + dash, y1)), fill=color, width=wpx)
        d.line((x1, y, x1, min(y + dash, y1)), fill=color, width=wpx)
        y += dash + gap


def logo_img(size):
    return Image.open(LOGO).convert('RGBA').resize((size, size), Image.LANCZOS)


def field(d, x, y, w, label, f_label):
    """Подпись + пунктирная линия под заполнение. Возвращает высоту."""
    d.text((x, y), label, font=f_label, fill=MUTED)
    dotted(d, x, y + 52, x + w)
    return 70


# ============================================================ страница 1
def panel_cover(w, h):
    """Обложка (верхняя панель, будет повёрнута на 180°)."""
    p = Image.new('RGB', (w, h), LAGOON_DARK)
    d = ImageDraw.Draw(p)
    cx = w // 2
    lg = logo_img(150)
    p.paste(lg, (cx - 75, 118), lg)
    text_c(d, cx, 300, T['brand'], prata(86), ALABASTER)
    text_c(d, cx, 418, T['brand_sub'], onest(28, 600), MIST, tracking=8)
    # разделитель: две линии с ромбом по центру, шире подписи —
    # иначе концы линий читаются как рваное подчёркивание текста
    d.line((cx - 360, 502, cx - 44, 502), fill='#2A7168', width=3)
    d.line((cx + 44, 502, cx + 360, 502), fill='#2A7168', width=3)
    diamond(d, cx, 502, 11, TERRA)
    text_c(d, cx, 540, T['title1'], prata(120), ALABASTER)
    text_c(d, cx, 688, T['title2'], prata(120), ALABASTER)
    text_c(d, cx, 852, T['tagline'], onest(34, 500), MIST)

    # тройка ценностей
    vy = h - 220
    seg = w // 3
    f_v = onest(30, 700)
    for i, v in enumerate(T['values']):
        ccx = seg * i + seg // 2
        diamond(d, ccx, vy - 26, 10, TERRA)
        text_c(d, ccx, vy, v, f_v, ALABASTER, tracking=3)
        if i:
            d.line((seg * i, vy - 40, seg * i, vy + 44), fill='#1E6058', width=2)
    text_c(d, cx, h - 96, T['cover_contacts'], onest(28, 500), MIST)
    return p


def panel_middle(w, h):
    """Средняя панель (не поворачивается): приветствие + инфо + контакты."""
    p = Image.new('RGB', (w, h), '#FFFFFF')
    d = ImageDraw.Draw(p)
    cx = w // 2

    # шапка-полоса
    sh = 86
    d.rectangle((0, 0, w, sh), fill=LAGOON)
    lg = logo_img(54)
    p.paste(lg, (SAFE, (sh - 54) // 2), lg)
    d.text((SAFE + 72, (sh - 44) // 2), T['brand'], font=prata(40), fill=ALABASTER)
    sl_w = d.textlength(T['strip_slogan'], font=onest(30, 400))
    d.text((w - SAFE - sl_w, (sh - 36) // 2), T['strip_slogan'],
           font=onest(30, 400), fill=MIST)

    y = sh + 64
    text_c(d, cx, y, T['welcome'], prata(72), LAGOON)
    y += 104
    text_c(d, cx, y, T['welcome_sub'], onest(34, 500), MUTED)
    y += 66
    for line in T['welcome_text']:
        text_c(d, cx, y, line, onest(32, 400), INK)
        y += 46

    # две инфокарточки
    y += 26
    gap = 40
    cw = (w - 2 * SAFE - gap) // 2
    ch = 218
    f_it = onest(32, 700)
    f_il = onest(29, 400)
    for i, (title, lines) in enumerate(((T['info1_title'], T['info1']),
                                        (T['info2_title'], T['info2']))):
        x0 = SAFE + i * (cw + gap)
        d.rounded_rectangle((x0, y, x0 + cw, y + ch), radius=16, fill=FILL)
        d.rectangle((x0, y + 14, x0 + 8, y + ch - 14), fill=LAGOON)
        d.text((x0 + 36, y + 26), title, font=f_it, fill=LAGOON)
        ly = y + 82
        for line in lines:
            d.text((x0 + 36, ly), line, font=f_il, fill=INK)
            ly += 42
    y += ch + 52

    # контакты
    d.text((SAFE, y), T['contacts_title'], font=onest(38, 800), fill=LAGOON)
    d.line((SAFE, y + 56, SAFE + 210, y + 56), fill=TERRA, width=4)
    y += 84
    f_k = onest(27, 700)
    f_val = onest(31, 400)
    for k, v in T['contacts']:
        d.text((SAFE, y + 4), k, font=f_k, fill=MUTED)
        d.text((SAFE + 320, y), v, font=f_val, fill=INK)
        y += 52
    return p


def panel_patient(w, h):
    """Нижняя панель (будет повёрнута): данные пациента + клапан-сайдбар."""
    p = Image.new('RGB', (w, h), '#FFFFFF')
    d = ImageDraw.Draw(p)

    # сайдбар справа — лагуна, виден как «клапан» после фальцовки
    sb_w = 560
    sx = w - sb_w
    d.rectangle((sx, 0, w, h), fill=LAGOON)
    scx = sx + sb_w // 2 - 12
    lg = logo_img(120)
    p.paste(lg, (scx - 60, 96), lg)
    text_c(d, scx, 240, T['brand'], prata(56), ALABASTER)
    text_c(d, scx, 318, T['brand_sub'], onest(22, 600), MIST, tracking=4)
    chip_f = onest(26, 700)
    chw = d.textlength(T['sidebar_chip'], font=chip_f) + 2 * (len(T['sidebar_chip']) - 1) + 76
    chx = scx - chw / 2
    d.rounded_rectangle((chx, 420, chx + chw, 500), radius=14,
                        outline=ALABASTER, width=3)
    text_c(d, scx, 444, T['sidebar_chip'], chip_f, ALABASTER, tracking=2)
    ly = 620
    for line in ('г. Мытищи,', 'ул. Мира, д. 37', '', '+7 (916)', '838-08-88',
                 '', 'venecia-dent.ru'):
        if line:
            text_c(d, scx, ly, line, onest(34, 700 if '8' in line and '(' in line else 500),
                   ALABASTER if line != 'venecia-dent.ru' else MIST)
        ly += 56

    # левая часть: данные пациента + обращение
    lx = SAFE
    lw = sx - SAFE - 56
    y = 88
    d.text((lx, y), T['patient_title'], font=prata(58), fill=INK)
    d.line((lx, y + 84, lx + 380, y + 84), fill=TERRA, width=4)
    y += 130
    f_lab = onest(28, 500)
    for row in T['patient_fields']:
        cw = (lw - (len(row) - 1) * 48) // len(row)
        for i, lab in enumerate(row):
            field(d, lx + i * (cw + 48), y, cw, lab, f_lab)
        y += 96

    y += 30
    d.text((lx, y), T['dear_title'], font=onest(42, 800), fill=LAGOON)
    y += 66
    f_b = onest(29, 400)
    for line in T['dear_text']:
        if line:
            d.text((lx, y), line, font=f_b, fill=INK)
        y += 41
    return p


def fold_marks(d, on_dark_rows):
    """Пунктирные метки сгиба у краёв. on_dark_rows — множества y-линий,
    где фон тёмный (рисуем белым)."""
    for fy in (FOLD1, FOLD2):
        color = '#FFFFFF' if fy in on_dark_rows else '#737373'
        for x0, x1 in ((6, 44), (W - 44, W - 6)):
            dashed_h(d, x0, x1, fy, color, wpx=2, dash=8, gap=8)


def build_page1():
    page = Image.new('RGB', (W, H), '#FFFFFF')
    top = panel_cover(W, BLEED + PANEL).rotate(180)
    mid = panel_middle(W, PANEL)
    bot = panel_patient(W, BLEED + PANEL).rotate(180)
    page.paste(top, (0, 0))
    page.paste(mid, (0, FOLD1))
    page.paste(bot, (0, FOLD2))
    d = ImageDraw.Draw(page)
    # FOLD1: сверху лагуна обложки → метки белые не нужны, граница
    # проходит между тёмной и белой панелью — рисуем серым по белой стороне
    fold_marks(d, on_dark_rows=set())
    return page


# ============================================================ страница 2
def sec_header(d, page, y, title, sub=None):
    d.text((SAFE, y), title, font=prata(64), fill=INK)
    d.line((SAFE, y + 90, SAFE + 460, y + 90), fill=LAGOON, width=5)
    lg = logo_img(56)
    bw = d.textlength(T['brand'], font=prata(44))
    page.paste(lg, (int(W - SAFE - bw - 74), y + 8), lg)
    d.text((W - SAFE - bw, y + 14), T['brand'], font=prata(44), fill=LAGOON)
    y += 102
    if sub:
        d.text((SAFE, y), sub, font=onest(30, 400), fill=MUTED)
        y += 52
    return y


def implant_card(d, x, y, w, h, n):
    d.rounded_rectangle((x, y, x + w, y + h), radius=18, outline=TINT, width=3)
    hh = 72
    d.rounded_rectangle((x, y, x + w, y + hh + 18), radius=18, fill=LAGOON)
    d.rectangle((x, y + hh - 18, x + w, y + hh), fill=LAGOON)
    d.text((x + 30, y + 16), T['implant_card'].format(n), font=onest(34, 800), fill='#FFFFFF')
    fw = d.textlength(T['fills_clinic'], font=onest(24, 400))
    d.text((x + w - 30 - fw, y + 24), T['fills_clinic'], font=onest(24, 400), fill=MIST)

    pad = 30
    fy = y + hh + 22
    f_lab = onest(25, 500)
    cw = (w - 2 * pad - 2 * 36) // 3
    for i, lab in enumerate(T['card_fields']):
        d.text((x + pad + i * (cw + 36), fy), lab, font=f_lab, fill=MUTED)
        dotted(d, x + pad + i * (cw + 36), fy + 44, x + pad + i * (cw + 36) + cw)
    fy += 74

    # наклейки
    scw = (w - 2 * pad - 36) // 2
    sch = 138
    f_st = onest(25, 700)
    for i, lab in enumerate((T['sticker1'], T['sticker2'])):
        sxx = x + pad + i * (scw + 36)
        d.text((sxx, fy), lab, font=f_st, fill=LAGOON)
        box = (sxx, fy + 42, sxx + scw, fy + 42 + sch)
        dashed_rect(d, box, '#9DB8B3')
        ph_w = d.textlength(T['sticker_ph'], font=onest(24, 400))
        d.text((sxx + (scw - ph_w) / 2, fy + 42 + sch / 2 - 14), T['sticker_ph'],
               font=onest(24, 400), fill='#9DB8B3')
    fy += 42 + sch + 22

    for i, lab in enumerate(T['card_fields2']):
        d.text((x + pad + i * (cw + 36), fy), lab, font=f_lab, fill=MUTED)
        dotted(d, x + pad + i * (cw + 36), fy + 44, x + pad + i * (cw + 36) + cw)
    return y + h


def num_table(d, y, cells_top, cells_bottom):
    x0, x1 = SAFE, W - SAFE
    n = len(cells_top)
    cw = (x1 - x0) / n
    rh = 54
    f = onest(27, 500)
    for r, cells in enumerate((cells_top, cells_bottom)):
        yy = y + r * rh
        d.rectangle((x0, yy, x1, yy + rh), fill=FILL if r == 0 else '#FFFFFF',
                    outline=TINT, width=2)
        for i, c in enumerate(cells):
            cxx = x0 + cw * i + cw / 2
            text_c(d, cxx, yy + 12, str(c), f, INK)
        for i in range(1, n):
            d.line((x0 + cw * i, yy, x0 + cw * i, yy + rh), fill=TINT, width=1)
    return y + 2 * rh


def build_page2():
    page = Image.new('RGB', (W, H), '#FFFFFF')
    d = ImageDraw.Draw(page)
    cw_full = W - 2 * SAFE

    # --- секция 1: информация об имплантации
    y = sec_header(d, page, SAFE + 10, T['p2s1_title'], T['p2s1_sub'])
    y += 8
    half = (cw_full - 48) // 2
    f_lab = onest(27, 500)
    d.rectangle((SAFE, y, SAFE + half, y + 74), fill=FILL)
    d.text((SAFE + 22, y + 12), T['clinic_field'], font=f_lab, fill=MUTED)
    dotted(d, SAFE + 220, y + 52, SAFE + half - 22)
    d.rectangle((SAFE + half + 48, y, W - SAFE, y + 74), fill=FILL)
    d.text((SAFE + half + 70, y + 12), T['system_field'], font=f_lab, fill=MUTED)
    dotted(d, SAFE + half + 70 + 560, y + 52, W - SAFE - 22)
    y += 108

    card_h = 430
    for r in range(2):
        for c in range(2):
            implant_card(d, SAFE + c * (half + 48), y + r * (card_h + 30), half, card_h, r * 2 + c + 1)
    y += 2 * card_h + 30 + 20
    d.text((SAFE, y), T['lab_line'], font=onest(28, 700), fill=LAGOON)
    lab_w = d.textlength(T['lab_line'], font=onest(28, 700))
    dotted(d, SAFE + lab_w + 30, y + 26, W - SAFE)
    y += 56

    # --- секция 2: после операции
    y = sec_header(d, page, y, T['p2s2_title'], T['p2s2_sub'])
    y += 4
    mgap = 30
    mw = (cw_full - 3 * mgap) // 4
    mh = 204
    for i, (num, title, lines) in enumerate(T['memos']):
        x0 = SAFE + i * (mw + mgap)
        d.rounded_rectangle((x0, y, x0 + mw, y + mh), radius=14, fill=WARM)
        d.rectangle((x0, y + 12, x0 + 7, y + mh - 12), fill=TERRA)
        d.text((x0 + 30, y + 22), num, font=prata(44), fill=TERRA)
        d.text((x0 + 110, y + 32), title, font=onest(31, 700), fill=INK)
        ly = y + 96
        for line in lines:
            d.text((x0 + 30, ly), line, font=onest(25, 400), fill=INK)
            ly += 38
    y += mh + 38

    # --- нумерация зубов
    d.text((SAFE, y), T['numbering_title'], font=prata(52), fill=INK)
    tw_ = d.textlength(T['numbering_title'], font=prata(52))
    d.text((SAFE + tw_ + 26, y + 20), T['numbering_note'], font=onest(27, 400), fill=MUTED)
    d.line((SAFE, y + 74, SAFE + 420, y + 74), fill=LAGOON, width=4)
    y += 98
    for lab, note, top, bottom in (
            (T['fdi_label'], T['fdi_note'],
             [18, 17, 16, 15, 14, 13, 12, 11, 21, 22, 23, 24, 25, 26, 27, 28],
             [48, 47, 46, 45, 44, 43, 42, 41, 31, 32, 33, 34, 35, 36, 37, 38]),
            (T['ada_label'], T['ada_note'],
             list(range(1, 17)), list(range(32, 16, -1)))):
        d.text((SAFE, y), lab, font=onest(30, 800), fill=LAGOON)
        lw_ = d.textlength(lab, font=onest(30, 800))
        d.text((SAFE + lw_ + 20, y + 3), note, font=onest(25, 400), fill=MUTED)
        y += 46
        y = num_table(d, y, top, bottom) + 22
    y += 8

    # --- тревожная строка
    d.rounded_rectangle((SAFE, y, W - SAFE, y + 80), radius=14, fill=WARM)
    d.text((SAFE + 28, y + 20), T['alert'], font=onest(31, 800), fill=TERRA)
    aw = d.textlength(T['alert'], font=onest(31, 800))
    d.text((SAFE + 28 + aw + 18, y + 22), T['alert_text'], font=onest(29, 400), fill=INK)
    y += 108

    # --- привычки
    d.text((SAFE, y), T['habits_title'], font=prata(52), fill=INK)
    d.line((SAFE, y + 74, SAFE + 420, y + 74), fill=LAGOON, width=4)
    y += 100
    hw = (cw_full - 3 * mgap) // 4
    hh2 = 154
    for i, (num, title, sub) in enumerate(T['habits']):
        x0 = SAFE + i * (hw + mgap)
        d.rounded_rectangle((x0, y, x0 + hw, y + hh2), radius=14,
                            outline=TINT, width=3)
        d.text((x0 + 28, y + 18), num, font=onest(28, 800), fill=TERRA)
        d.text((x0 + 28, y + 60), title, font=onest(28, 700), fill=INK)
        d.text((x0 + 28, y + 108), sub, font=onest(24, 400), fill=MUTED)
    y += hh2 + 38

    # --- график осмотров
    y = sec_header(d, page, y, T['schedule_title'], T['schedule_sub'])
    y += 4
    cols = [0.20, 0.37, 0.215, 0.215]
    xs = [SAFE]
    for c in cols:
        xs.append(xs[-1] + cw_full * c)
    th = 66
    d.rounded_rectangle((SAFE, y, W - SAFE, y + th), radius=12, fill=LAGOON)
    f_th = onest(28, 700)
    for i, htxt in enumerate(T['schedule_head']):
        d.text((xs[i] + 28, y + 16), htxt, font=f_th, fill='#FFFFFF')
    y += th
    rh = 66
    for i, (term, goal) in enumerate(T['schedule']):
        if i % 2 == 0:
            d.rectangle((SAFE, y, W - SAFE, y + rh), fill=FILL)
        d.text((xs[0] + 28, y + 20), term, font=onest(30, 700), fill=INK)
        d.text((xs[1] + 28, y + 20), goal, font=onest(30, 400), fill=INK)
        dotted(d, xs[2] + 28, y + rh - 24, xs[3] - 40)
        dotted(d, xs[3] + 28, y + rh - 24, W - SAFE - 40)
        y += rh
    y += 40

    # --- спасибо
    d.text((SAFE, y), T['thanks_title'], font=prata(64), fill=LAGOON)
    y += 88
    for line in T['thanks_text']:
        d.text((SAFE, y), line, font=onest(31, 400), fill=INK)
        y += 42
    y += 10
    d.text((SAFE, y), T['thanks_sign'], font=onest(31, 600), fill=TERRA)
    y += 60

    assert y <= H - SAFE + 10, f'страница 2 переполнена: контент до {y}, лимит {H - SAFE}'

    # водяной знак-зуб в правом нижнем углу (как у Angel — призрачный логотип)
    lg = logo_img(300)
    ghost = lg.copy()
    ghost.putalpha(ghost.getchannel('A').point(lambda a: a * 8 // 100))
    page.paste(ghost, (W - SAFE - 300, H - SAFE - 300), ghost)

    fold_marks(d, on_dark_rows=set())
    return page


# ============================================================ проверки
def run_checks():
    errors = []
    def walk(v):
        if isinstance(v, str):
            return [v]
        if isinstance(v, (list, tuple)):
            out = []
            for x in v:
                out += walk(x)
            return out
        return []
    blob = ' '.join(walk(list(T.values())))
    for bad in FORBIDDEN:
        if bad.lower() in blob.lower():
            errors.append(f'запрещённое слово: «{bad}»')
    import re
    for bad in FORBIDDEN_WORD:
        if re.search(r'(?<![А-Яа-яA-Za-z])' + bad + r'(?![А-Яа-яA-Za-z])', blob):
            errors.append(f'запрещённое слово: «{bad}»')
    for req in ['+7 (916) 838-08-88', 'Мытищи', 'venecia-dent.ru', 'ПО ДОГОВОРУ',
                'ИМПЛАНТАТ', 'FDI', 'ADA', 'через 1 год']:
        if req not in blob:
            errors.append(f'нет обязательного фрагмента: «{req}»')
    if not LOGO.exists():
        errors.append('нет логотипа (../buklet/img/logo-600.png)')
    for f in ('Prata-Regular.ttf', 'Onest[wght].ttf'):
        if not (FONTS / f).exists():
            errors.append(f'нет шрифта {f}')
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
    print('Тексты и материалы: проверки пройдены.')
    if args.check:
        return 0

    OUT.mkdir(exist_ok=True)
    p1 = build_page1()
    p2 = build_page2()
    assert p1.size == (W, H) == p2.size
    p1.save(OUT / 'passport-page-1.png', dpi=(DPI, DPI))
    p2.save(OUT / 'passport-page-2.png', dpi=(DPI, DPI))
    p1.save(OUT / 'Паспорт_имплантов_Венеция.pdf', save_all=True,
            append_images=[p2], resolution=DPI)
    for name, im in (('preview-page-1.jpg', p1), ('preview-page-2.jpg', p2)):
        im.resize((im.width // 3, im.height // 3), Image.LANCZOS).save(
            OUT / name, quality=88)
    print(f'Готово: {W}×{H} px (A4 + вылеты 2 мм, {DPI} dpi), фальц на '
          f'y={FOLD1} и y={FOLD2} → out/')
    return 0


if __name__ == '__main__':
    sys.exit(main())
