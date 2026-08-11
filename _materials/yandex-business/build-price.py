#!/usr/bin/env python3
# Генератор прайса Яндекс.Бизнеса для «Венеции» (раздел «Товары и услуги»).
#
# ВАЖНО: источник цен — САЙТ (ceny.html, services/*.html, promotions.html).
# Правим цену на сайте → перезапускаем этот скрипт → деплой. НЕ наоборот.
#
# ⚠️ У «Венеции» НЕТ КТ и НЕТ детской стоматологии — этих позиций в фиде
# быть не должно (решение владельца). Вместо детской — «Отбеливание».
#
# Запуск:  python3 _materials/yandex-business/build-price.py
# Результат:
#   _materials/yandex-business/venecia-dent-yandex-business-price.xlsx  (ручная загрузка)
#   yandex-business.yml в корне репо  (автозагрузка по ссылке — деплоится)
#
# Правила оформления позиций:
#  - цену НЕ дублировать в названии (для неё есть своя колонка);
#  - «от …» и «вместо …» — в описании;
#  - бесплатное/подарочное — цена 0: в XLSX уйдёт пустой ценой, в YML не
#    попадёт вовсе (YB требует <price>), его место — раздел «Акции».

import os, zipfile, html
from datetime import datetime

# (Название, Цена, Категория, Описание) — сверено с ceny.html 11.08.2026
rows = [
 ("Имплант Osstem (Корея)", 28000, "Имплантация", "Установка импланта Osstem (Южная Корея). Приживаемость выше 98 %, гарантия до 10 лет по договору. Цена «от»."),
 ("Имплант Dentium (Корея)", 32000, "Имплантация", "Установка импланта Dentium (Южная Корея). Стоимость фиксируется в договоре до начала лечения. Цена «от»."),
 ("Имплант Straumann (Швейцария)", 55000, "Имплантация", "Имплант премиум-класса Straumann (Швейцария). Цена «от»."),
 ("Имплант + коронка металлокерамика «под ключ»", 45000, "Имплантация", "Полная стоимость восстановления зуба: имплант, абатмент и коронка. Цена «от»."),
 ("Имплант + коронка цирконий «под ключ»", 65000, "Имплантация", "Имплантация с циркониевой коронкой под ключ, без металла и серой полоски у десны. Цена «от»."),
 ("All-on-4 — несъёмный протез на 4 имплантах", 120000, "Имплантация", "Несъёмный протез всей челюсти на 4 имплантах. Цена «от», за одну челюсть."),
 ("All-on-6 — несъёмный протез на 6 имплантах", 180000, "Имплантация", "Несъёмный протез всей челюсти на 6 имплантах. Цена «от», за одну челюсть."),
 ("Синус-лифтинг закрытый", 18000, "Имплантация", "Подготовка к имплантации на верхней челюсти. Цена «от»."),

 ("Брекет-система под ключ", 35000, "Ортодонтия", "Металлические или керамические брекеты с сопровождением до конца лечения. Цена «от»."),
 ("Элайнеры — полный курс", 120000, "Ортодонтия", "Прозрачные каппы: снимаются на время еды и чистки. План лечения показываем на цифровой модели. Цена «от»."),
 ("Консультация ортодонта", 0, "Ортодонтия", "Первичная консультация с расчётом ТРГ — бесплатно. Подберём брекеты или элайнеры, без обязательств."),
 ("ТРГ + ОПТГ (диагностика)", 2500, "Ортодонтия", "Телерентгенограмма и панорамный снимок для расчёта ортодонтического лечения."),
 ("Активация брекетов (ежемесячный приём)", 3500, "Ортодонтия", "Плановая активация брекет-системы и контроль на приёме."),
 ("Ретейнер после брекетов", 2200, "Ортодонтия", "Несъёмный ретейнер, удерживающий результат после снятия брекетов. Цена «от»."),

 ("Консультация стоматолога с планом лечения", 1000, "Лечение зубов", "Осмотр и письменный план: что лечим, в каком порядке и сколько это стоит. Сумма фиксируется в договоре."),
 ("Лечение кариеса", 5500, "Лечение зубов", "Лечение за одно посещение под анестезией, пломба подбирается по цвету эмали. Цена «от»."),
 ("Лечение пульпита (1 канал)", 7000, "Лечение зубов", "Лечение пульпита одноканального зуба. Цена «от»."),
 ("Лечение пульпита (2 канала)", 9500, "Лечение зубов", "Лечение пульпита двухканального зуба. Цена «от»."),
 ("Лечение пульпита (3 канала)", 12000, "Лечение зубов", "Лечение пульпита трёхканального зуба. Цена «от»."),
 ("Перелечивание каналов", 16000, "Лечение зубов", "Повторное эндодонтическое лечение ранее пролеченных каналов. Цена «от»."),
 ("Художественная реставрация зуба", 8000, "Лечение зубов", "Эстетическая реставрация переднего зуба композитом. Цена «от»."),

 ("Удаление зуба для взрослого", 4500, "Хирургия", "Удаление зуба под анестезией, простое и сложное. Цена «от»."),
 ("Удаление ретинированного зуба мудрости", 9500, "Хирургия", "Удаление непрорезавшегося зуба мудрости. Цена «от»."),
 ("Резекция верхушки корня", 8500, "Хирургия", "Зубосохраняющая операция при кисте или гранулёме. Цена «от»."),
 ("Костная пластика (1 единица)", 10000, "Хирургия", "Наращивание костной ткани перед имплантацией. Цена «от»."),

 ("Коронка металлокерамика", 12000, "Протезирование", "Металлокерамическая коронка. Цена «от»."),
 ("Коронка из диоксида циркония", 22000, "Протезирование", "Прочная безметалловая коронка: не темнеет и не даёт серой полоски у десны. Цена «от»."),
 ("Коронка E-max (дисиликат лития)", 28000, "Протезирование", "Максимально эстетичная коронка для зоны улыбки. Цена «от»."),
 ("Вкладка циркониевая (Inlay/Onlay)", 18000, "Протезирование", "Керамическая вкладка вместо большой пломбы. Цена «от»."),
 ("Полный съёмный протез (акрил)", 28000, "Протезирование", "Полный съёмный протез на одну челюсть. Цена «от»."),
 ("Нейлоновый протез (1 челюсть)", 35000, "Протезирование", "Мягкий эластичный протез без металлических крючков. Цена «от»."),
 ("Бюгельный протез с замками", 65000, "Протезирование", "Съёмный протез на металлическом каркасе с замковым креплением. Цена «от»."),

 ("Керамический винир E-max", 22000, "Виниры", "Тонкая керамическая накладка на передний зуб: закрывает сколы, щели и потемнения. Цена «от»."),
 ("Винир циркониевый", 25000, "Виниры", "Прочный циркониевый винир. Цена «от»."),
 ("Композитный винир (прямая реставрация)", 7500, "Виниры", "Винир прямо в кресле за один визит. Цена «от»."),
 ("Digital Smile Design — моделирование улыбки", 8000, "Виниры", "Цифровое моделирование будущей улыбки: результат виден до начала лечения. Цена «от»."),

 ("Комплексная гигиена полости рта", 5000, "Гигиена", "Ультразвук, Air Flow и полировка за один визит. Рекомендуем раз в полгода."),
 ("Комплексная гигиена с брекетами", 7000, "Гигиена", "Профессиональная чистка при установленной брекет-системе."),
 ("Комплексная гигиена с ретейнерами", 6000, "Гигиена", "Профессиональная чистка при установленных ретейнерах."),
 ("Ультразвуковая чистка — снятие зубного камня", 2500, "Гигиена", "Снятие наддёсневых и поддёсневых отложений ультразвуком."),
 ("Чистка Air Flow", 2500, "Гигиена", "Снятие пигментированного налёта от кофе, чая и сигарет."),
 ("Гигиена + чистка десневых карманов 3–4 мм", 7500, "Гигиена", "Комплексная гигиена с кюретажем десневых карманов глубиной 3–4 мм."),
 ("Гигиена + чистка десневых карманов от 5 мм", 9500, "Гигиена", "Комплексная гигиена с кюретажем глубоких десневых карманов."),
 ("Глубокое фторирование", 1200, "Гигиена", "Укрепление эмали всех зубов: фторирующий гель в каппах."),

 ("Отбеливание Amazing White", 17500, "Отбеливание", "Кабинетное отбеливание за один визит, осветление до 6–8 тонов. Цена под ключ за обе челюсти, вместо 25 000 ₽."),
 ("Комплексная гигиена перед отбеливанием", 5000, "Отбеливание", "Профессиональная чистка — обязательный этап перед отбеливанием."),
 ("Укрепление эмали Tooth Mousse (1 челюсть)", 1800, "Отбеливание", "Ремотерапия для снижения чувствительности после отбеливания."),

 ("Лечение дёсен: закрытый кюретаж (1 зуб)", 800, "Лечение дёсен", "Чистка десневого кармана при пародонтите. Цена «от»."),
 ("Открытый кюретаж (1 зуб)", 2500, "Лечение дёсен", "Хирургическая чистка глубокого пародонтального кармана. Цена «от»."),
 ("Vector-терапия (1 челюсть)", 8500, "Лечение дёсен", "Аппаратное лечение пародонтита без боли и травмы десны. Цена «от»."),
 ("Plasmolifting (1 пробирка)", 4500, "Лечение дёсен", "Плазмотерапия дёсен собственной плазмой пациента. Цена «от»."),
 ("Шинирование зубов стекловолокном (1 зуб)", 3200, "Лечение дёсен", "Укрепление подвижных зубов при пародонтите. Цена «от»."),
]

HEADER = ["Название", "Цена", "Категория", "Описание"]

IMG_BASE = "https://venecia-dent.ru/assets/img/yb/"
CAT_IMG = {
    "Имплантация": "yb-implantaciya",
    "Ортодонтия": "yb-ortodontiya",
    "Лечение зубов": "yb-terapiya",
    "Хирургия": "yb-hirurgiya",
    "Протезирование": "yb-protezirovanie",
    "Виниры": "yb-viniry",
    "Гигиена": "yb-gigiena",
    "Отбеливание": "yb-otbelivanie",
    "Лечение дёсен": "yb-parodontologiya",
    "Акции": "yb-akcii",
}

SITE = "https://venecia-dent.ru/"
UTM = "?utm_source=yandex_business&utm_medium=tovary&utm_campaign=catalog"
CAT_URL = {
    "Имплантация": "services/implantaciya.html",
    "Ортодонтия": "services/ortodontiya.html",
    "Лечение зубов": "services/terapiya.html",
    "Хирургия": "services/hirurgiya.html",
    "Протезирование": "services/protezirovanie.html",
    "Виниры": "services/viniry.html",
    "Гигиена": "services/gigiena.html",
    "Отбеливание": "services/otbelivanie.html",
    "Лечение дёсен": "services/parodontologiya.html",
    "Акции": "promotions.html",
}

def img_for(cat): return IMG_BASE + CAT_IMG.get(cat, "yb-akcii") + ".jpg"
def url_for(cat): return SITE + CAT_URL.get(cat, "services/") + UTM
def _esc(s): return html.escape(str(s), quote=False)

def _cell(ref, val):
    if isinstance(val, (int, float)):
        return f'<c r="{ref}"><v>{val}</v></c>'
    if val == "":
        return f'<c r="{ref}"/>'
    return f'<c r="{ref}" t="inlineStr"><is><t xml:space="preserve">{_esc(val)}</t></is></c>'

def _row(rn, vals):
    cells = "".join(_cell(f"{chr(ord('A')+i)}{rn}", v) for i, v in enumerate(vals))
    return f'<row r="{rn}">{cells}</row>'

def build(out_path):
    data = [_row(i, [n, ("" if p == 0 else p), c, d]) for i, (n, p, c, d) in enumerate(rows, 2)]
    sheet = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
             '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
             '<cols><col min="1" max="1" width="60"/><col min="2" max="2" width="12"/>'
             '<col min="3" max="3" width="22"/><col min="4" max="4" width="75"/></cols>'
             '<sheetData>' + _row(1, HEADER) + "".join(data) + '</sheetData></worksheet>')
    ct = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
          '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
          '<Default Extension="xml" ContentType="application/xml"/>'
          '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
          '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>')
    wb = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
          '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
          'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
          '<sheets><sheet name="Прайс" sheetId="1" r:id="rId1"/></sheets></workbook>')
    wbrels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
              '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
              '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>')
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", ct)
        z.writestr("_rels/.rels", rels)
        z.writestr("xl/workbook.xml", wb)
        z.writestr("xl/_rels/workbook.xml.rels", wbrels)
        z.writestr("xl/worksheets/sheet1.xml", sheet)
    return len(rows)

def build_yml(out_path):
    """YML-фид для автозагрузки в Яндекс.Бизнес по ссылке (цены + картинки).
    Позиции без цены (бесплатные/подарочные) в фид не идут — YB требует
    <price>; их место — раздел «Акции» карточки."""
    cats = list(CAT_IMG.keys())
    cat_id = {c: i + 1 for i, c in enumerate(cats)}
    cats_xml = "".join(f'<category id="{cat_id[c]}">{_esc(c)}</category>' for c in cats)
    offers, oid, skipped = [], 0, 0
    for name, price, cat, desc in rows:
        if not price:
            skipped += 1
            continue
        oid += 1
        offers.append(
            f'<offer id="{oid}" available="true">'
            f'<name>{_esc(name)}</name>'
            f'<url>{_esc(url_for(cat))}</url>'
            f'<price>{price}</price><currencyId>RUB</currencyId>'
            f'<categoryId>{cat_id.get(cat, cat_id["Акции"])}</categoryId>'
            f'<picture>{_esc(img_for(cat))}</picture>'
            f'<description>{_esc(desc)}</description>'
            f'</offer>')
    yml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           f'<yml_catalog date="{datetime.now().strftime("%Y-%m-%d %H:%M")}">\n<shop>\n'
           '<name>Венеция</name>\n'
           '<company>ООО «АНГЕЛ-ДЕНТ»</company>\n'
           '<url>https://venecia-dent.ru/</url>\n'
           '<currencies><currency id="RUB" rate="1"/></currencies>\n'
           f'<categories>{cats_xml}</categories>\n'
           f'<offers>{"".join(offers)}</offers>\n'
           '</shop>\n</yml_catalog>\n')
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(yml)
    return oid, skipped

if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.abspath(os.path.join(here, "..", ".."))
    n = build(os.path.join(here, "venecia-dent-yandex-business-price.xlsx"))
    print(f"XLSX: {n} позиций")
    o, sk = build_yml(os.path.join(root, "yandex-business.yml"))
    print(f"YML:  {o} офферов с ценой (пропущено без цены: {sk})")
