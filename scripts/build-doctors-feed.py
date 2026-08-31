#!/usr/bin/env python3
"""Фид «Врачи» для дополненного представления в поиске Яндекса.

Собирает `doctors-feed.yml` в корень репозитория (деплоится вместе с
сайтом, Яндекс перечитывает его по ссылке сам). Формат — YML тематики
DOCTORS: https://yandex.ru/support/webmaster/ru/search-appearance/doctors
Зарегистрирован в Вебмастере через API (feeds/add/start, type=DOCTORS).

    python3 scripts/build-doctors-feed.py           # собрать
    python3 scripts/build-doctors-feed.py --check   # только проверить

Встроенный сторож (он же --check) не даст фиду разойтись с сайтом — за
рассинхрон Яндекс блокирует предложения:
  · каждый врач из DOCTORS имеет страницу doctors/<slug>.html, и его
    ФИО написано на ней;
  · на КАЖДУЮ страницу врача в doctors/ есть запись в DOCTORS или
    осознанное исключение в EXCLUDE (с причиной);
  · цена услуги дословно присутствует в прайсе сайта (файл из поля
    check_price) — фид никогда не заявляет цену, которой нет на сайте;
  · фото врача существует.

⚠️ Новый врач / врач ушёл → правим DOCTORS здесь, прогоняем скрипт и
деплоим. Специальность — СТРОГО из перечня Яндекса (стоматолог,
стоматолог-хирург, стоматолог-терапевт, стоматолог-ортопед,
стоматолог-ортодонт, стоматолог-имплантолог, стоматолог-пародонтолог,
стоматолог-эндодонт, стоматолог-гигиенист). «Детского стоматолога» в
перечне нет — ставим «стоматолог» + children_appointment.
"""
from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'doctors-feed.yml'

SHOP = {
    'name': 'Венеция',
    'company': 'ООО «АНГЕЛ-ДЕНТ»',
    'url': 'https://venecia-dent.ru/',
    'picture': 'https://venecia-dent.ru/assets/img/logo.png',
    'email': 'venecia.1@mail.ru',
}

CLINIC = {
    'name': 'Стоматология «Венеция»',
    'url': 'https://venecia-dent.ru/',
    'picture': 'https://venecia-dent.ru/assets/img/logo.png',
    'city': 'г. Мытищи',
    'address': 'Московская область, г. Мытищи, ул. Мира, д. 37',
    'email': 'venecia.1@mail.ru',
    'phone': '+79168380888',
    'company_id': '104110939502',   # id организации в Яндекс.Бизнесе
}

DOCTORS = [
    {'slug': 'drobkova', 'name': 'Дробкова Кристина Олеговна',
     'speciality': 'стоматолог-ортодонт',
     'description': 'Стоматолог-ортодонт. Брекеты, элайнеры, исправление прикуса у взрослых и подростков.',
     'service': ('konsultaciya-ortodonta', 'Первичная консультация ортодонта'),
     'price': 0,
     'check_price': ('ceny.html', 'Первичная консультация ортодонта')},
    {'slug': 'kilasoniya', 'name': 'Киласония Шорена Гиулиевна',
     'speciality': 'стоматолог-хирург',
     'description': 'Стоматолог-хирург, терапевт. Удаление зубов любой сложности, зубосохраняющие операции, лечение кариеса.',
     'service': ('konsultaciya', 'Консультация стоматолога с планом лечения'),
     'price': 1000,
     'check_price': ('ceny.html', 'Консультация стоматолога с планом лечения')},
]

# Кендабаева — гигиенист (среднее медицинское образование), а тематика
# «Врачи» допускает только специалистов с высшим медицинским — не включаем.
EXCLUDE = {'kendabaeva': 'гигиенист, не врач с высшим медицинским образованием'}



def build() -> ET.Element:
    msk = timezone(timedelta(hours=3))
    shop = ET.Element('shop', version='2.0',
                      date=datetime.now(msk).strftime('%Y-%m-%d %H:%M'))
    for tag in ('name', 'company', 'url', 'picture', 'email'):
        ET.SubElement(shop, tag).text = SHOP[tag]

    doctors = ET.SubElement(shop, 'doctors')
    for d in DOCTORS:
        doc = ET.SubElement(doctors, 'doctor', id=d['slug'])
        ET.SubElement(doc, 'name').text = d['name']
        ET.SubElement(doc, 'url').text = f"{SHOP['url']}doctors/{d['slug']}.html"
        ET.SubElement(doc, 'surname').text = d['name'].split()[0]
        ET.SubElement(doc, 'first_name').text = d['name'].split()[1]
        if len(d['name'].split()) > 2:
            ET.SubElement(doc, 'patronymic').text = d['name'].split()[2]
        if d.get('photo', True):
            ET.SubElement(doc, 'picture').text = \
                f"{SHOP['url']}assets/img/doctors/{d['slug']}.png"
        if d.get('description'):
            ET.SubElement(doc, 'description').text = d['description']

    clinics = ET.SubElement(shop, 'clinics')
    cl = ET.SubElement(clinics, 'clinic', id='clinic')
    for tag in ('name', 'url', 'picture', 'city', 'address', 'email', 'phone'):
        ET.SubElement(cl, tag).text = CLINIC[tag]
    if CLINIC.get('company_id'):
        ET.SubElement(cl, 'company_id').text = CLINIC['company_id']

    services = ET.SubElement(shop, 'services')
    seen = {}
    for d in DOCTORS:
        sid, sname = d['service']
        if sid not in seen:
            seen[sid] = sname
            sv = ET.SubElement(services, 'service', id=sid)
            ET.SubElement(sv, 'name').text = sname

    offers = ET.SubElement(shop, 'offers')
    for d in DOCTORS:
        off = ET.SubElement(offers, 'offer', id=f"{d['slug']}-{d['service'][0]}")
        ET.SubElement(off, 'url').text = f"{SHOP['url']}doctors/{d['slug']}.html"
        ET.SubElement(off, 'online_schedule').text = 'false'
        ET.SubElement(off, 'oms').text = 'false'
        ET.SubElement(off, 'appointment').text = 'true'
        if d.get('price') is not None:
            pr = ET.SubElement(off, 'price')
            ET.SubElement(pr, 'base_price').text = str(d['price'])
            ET.SubElement(pr, 'currency').text = 'RUR'
        ET.SubElement(off, 'service', id=d['service'][0])
        c = ET.SubElement(off, 'clinic', id='clinic')
        doc = ET.SubElement(c, 'doctor', id=d['slug'])
        ET.SubElement(doc, 'speciality').text = d['speciality']
        ET.SubElement(doc, 'adult_appointment').text = \
            'true' if d.get('adult', True) else 'false'
        ET.SubElement(doc, 'children_appointment').text = \
            'true' if d.get('children', False) else 'false'
        ET.SubElement(doc, 'house_call').text = 'false'
        ET.SubElement(doc, 'telemed').text = 'false'
        ET.SubElement(doc, 'is_base_service').text = 'true'
    return shop


def check() -> list[str]:
    """Сторож соответствия фида сайту. Возвращает список проблем."""
    bad = []
    pages = {p.stem for p in (ROOT / 'doctors').glob('*.html')} - {'index'}
    feed_slugs = {d['slug'] for d in DOCTORS}

    for extra in feed_slugs - pages:
        bad.append(f'в фиде есть «{extra}», но страницы doctors/{extra}.html нет')
    for miss in pages - feed_slugs - set(EXCLUDE):
        bad.append(f'страница doctors/{miss}.html есть, а в фиде врача нет — '
                   f'добавьте в DOCTORS или в EXCLUDE с причиной')

    for d in DOCTORS:
        page = ROOT / 'doctors' / f"{d['slug']}.html"
        if not page.is_file():
            continue
        s = page.read_text(encoding='utf-8')
        if d['name'] not in s:
            bad.append(f"{d['slug']}: на странице не найдено ФИО «{d['name']}»")
        if d.get('photo', True) and not (ROOT / 'assets/img/doctors' / f"{d['slug']}.png").is_file():
            bad.append(f"{d['slug']}: нет фото assets/img/doctors/{d['slug']}.png")
        if d.get('check_price'):
            f, needle = d['check_price']
            src = (ROOT / f).read_text(encoding='utf-8')
            if not re.search(needle, src.replace(' ', ' ')):
                bad.append(f"{d['slug']}: в {f} не найдено «{needle}» — "
                           f'цена фида разошлась с сайтом')
    return bad


def main(argv: list[str]) -> int:
    problems = check()
    for p in problems:
        print(f'  ✗ {p}')
    if problems:
        return 1
    print(f'  ✓ фид соответствует сайту: врачей {len(DOCTORS)}, '
          f'исключены: {", ".join(EXCLUDE) or "—"}')
    if '--check' in argv:
        return 0

    shop = build()
    ET.indent(shop, space='  ')
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           + ET.tostring(shop, encoding='unicode') + '\n')
    OUT.write_text(xml, encoding='utf-8')
    print(f'  ✓ {OUT.name}: {len(xml)} байт')
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
