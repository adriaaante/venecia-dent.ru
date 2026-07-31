#!/usr/bin/env python3
"""Неразрывные пробелы в ценах — чтобы число не рвалось на перенос строки.

Зачем: в таблице цен на мобиле у последней колонки `white-space: normal`
(иначе длинное «от 180 000 ₽ за челюсть» распирает таблицу на узких
экранах). При `normal` перенос разрешён по ЛЮБОМУ пробелу, включая
пробел внутри числа, и «бесплатно 1 000 ₽» рвалось как «бесплатно 1»
и «000 ₽». Обычный пробел U+0020 внутри чисел заменяем на неразрывный
U+00A0 — число становится неделимым, а «за челюсть» по-прежнему
переносится.

Запуск из корня репо (идемпотентен, можно гонять после любой правки цен):
    python3 scripts/fix-price-nbsp.py
    python3 scripts/fix-price-nbsp.py --check   # только проверить, не писать
"""
import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
NBSP = ' '

# Заменяем пробел ТОЛЬКО внутри самой суммы: разряды и знак рубля.
# Предлог «от» намеренно НЕ приклеиваем: перенос после него нормален,
# а склейка раздувала неделимый кусок до «от 180 000 ₽» и таблица
# «Протезирование» переставала помещаться в 320px (проверено).
RULES = [
    (re.compile(r'(?<=\d) (?=\d{3}(?!\d))'), NBSP),   # 1 000
    (re.compile(r'(?<=\d) (?=₽)'), NBSP),             # 000 ₽
]


def process(text: str) -> str:
    for pat, repl in RULES:
        text = pat.sub(repl, text)
    return text


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true',
                    help='только сообщить о файлах, которые надо поправить')
    args = ap.parse_args()

    files = [f for f in sorted(ROOT.glob('**/*.html'))
             if '_materials' not in f.parts and '.git' not in f.parts]
    changed = []
    for f in files:
        orig = f.read_text(encoding='utf-8')
        new = process(orig)
        if new != orig:
            changed.append(f.relative_to(ROOT))
            if not args.check:
                f.write_text(new, encoding='utf-8')

    if args.check:
        for c in changed:
            print(f'  требует правки: {c}')
        print(f'Файлов с обычным пробелом в ценах: {len(changed)}')
        return 1 if changed else 0

    for c in changed:
        print(f'  ✎ {c}')
    print(f'Файлов изменено: {len(changed)}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
