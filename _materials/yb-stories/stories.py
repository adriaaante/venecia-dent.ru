# -*- coding: utf-8 -*-
"""
Истории Яндекс.Бизнеса «Венеция» — перенос готовых слайдов на страницу-хаб.

На Диске лежали две собранные истории линейки v1 (03.08.2026); они
перезалиты в постоянное хранилище. Остальные сюжеты линейки (семья,
ортодонтия, брекеты 30+, имплантация) описаны в REGISTRY.md — если их
файлы найдутся или будут пересобраны, добавляем сюда же.

Запуск: python3 stories.py  → stories.json
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = 'https://venecia-dent.ru'

STORIES = [
    ('ist1', 'Не страшно', 'Записаться', '/contacts.html',
     'Про страх боли: спокойный приём, анестезия, всё объясняем заранее.'),
    ('ist2', 'Цены честно', 'Смотреть цены', '/ceny.html',
     'Смета на все услуги до начала лечения, цены фиксируются в договоре.'),
]


def export():
    up = {k: url for k, mid, code, url in
          json.load(open(os.path.join(HERE, 'from-drive', '_uploads.json')))}
    items = []
    for pref, name, btn, link, about in STORIES:
        imgs = [up[k] for k in sorted(up) if k.startswith(pref + '-')]
        items.append({'key': pref, 'title': name, 'btn': btn, 'link': SITE + link,
                      'about': about, 'imgs': imgs})
    json.dump({'title': 'Истории (сторис)', 'items': items},
              open(os.path.join(HERE, 'stories.json'), 'w'), ensure_ascii=False, indent=1)
    for it in items:
        print(f"{it['key']}  {it['title']:14s} слайдов {len(it['imgs'])}")


if __name__ == '__main__':
    export()
