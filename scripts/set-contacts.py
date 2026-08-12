#!/usr/bin/env python3
"""Венеция — подстановка реальных контактов вместо placeholder'ов.

Запуск из корня репо, примеры:
  python3 scripts/set-contacts.py --phone "+7 (916) 123-45-67"
  python3 scripts/set-contacts.py --phone "+7 (916) 123-45-67" \\
      --email info@venecia-dent.ru --metrika 12345678

Правит все *.html, assets/js/main.js и CLAUDE.md:
  телефон (отображение, tel:, wa.me, t.me, JSON-LD), email, id Метрики.
Идемпотентен, пока в файлах стоят текущие значения-плейсхолдеры —
после первой замены новые значения сами становятся «текущими»
(скрипт ищет то, что записано в CURRENT).
"""
import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

# Текущие значения в файлах сайта. После успешного прогона скрипт
# сам переписывает этот блок на новые значения.
CURRENT = {
    'phone_display': '+7 (916) 838-08-88',
    'phone_digits': '79168380888',
    'email': 'venecia.1@mail.ru',
    'metrika': '111523618',
}


def digits_of(display: str) -> str:
    d = re.sub(r'\D', '', display)
    if len(d) != 11 or d[0] not in '78':
        sys.exit(f'Телефон должен содержать 11 цифр (получилось: {d!r})')
    return '7' + d[1:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--phone', help='Отображаемый номер, напр. "+7 (916) 123-45-67"')
    ap.add_argument('--email', help='E-mail клиники')
    ap.add_argument('--metrika', help='ID счётчика Яндекс.Метрики')
    args = ap.parse_args()
    if not (args.phone or args.email or args.metrika):
        ap.error('нужен хотя бы один из --phone / --email / --metrika')

    repl = []  # (old, new)
    if args.phone:
        new_digits = digits_of(args.phone)
        repl += [
            (CURRENT['phone_display'], args.phone),
            ('tel:+' + CURRENT['phone_digits'], 'tel:+' + new_digits),
            ('wa.me/' + CURRENT['phone_digits'], 'wa.me/' + new_digits),
            ('t.me/+' + CURRENT['phone_digits'], 't.me/+' + new_digits),
            # JSON-LD "telephone": "+7-000-000-00-00"
            ('+' + CURRENT['phone_digits'][0] + '-' + CURRENT['phone_display'].replace('+7 (', '').replace(') ', '-'),
             '+' + new_digits[0] + '-' + args.phone.replace('+7 (', '').replace(') ', '-')),
        ]
    if args.email:
        repl.append((CURRENT['email'], args.email))
    if args.metrika:
        repl += [
            ('id=' + CURRENT['metrika'], 'id=' + args.metrika),
            ('ym(' + CURRENT['metrika'], 'ym(' + args.metrika),
            ('watch/' + CURRENT['metrika'], 'watch/' + args.metrika),
            ('YM_COUNTER_ID = 0;', f'YM_COUNTER_ID = {args.metrika};'),
        ]

    # Берём ВСЕ html рекурсивно, а не перечисленные папки: раздел doctors/
    # появился позже скрипта, и при жёстком списке ('*.html' + 'services/*')
    # страницы врачей молча остались с телефоном-заглушкой. Рекурсивный обход
    # переживёт появление любых новых разделов.
    files = sorted(ROOT.glob('**/*.html'))
    files = [f for f in files if '_materials' not in f.parts and '.git' not in f.parts]
    files += [ROOT / 'assets/js/main.js', ROOT / 'CLAUDE.md']
    changed = 0
    for f in files:
        text = orig = f.read_text(encoding='utf-8')
        for old, new in repl:
            text = text.replace(old, new)
        if text != orig:
            f.write_text(text, encoding='utf-8')
            changed += 1
            print(f'  ✎ {f.relative_to(ROOT)}')
    print(f'Файлов изменено: {changed}')

    # Обновляем блок CURRENT в самом скрипте, чтобы скрипт можно было
    # запускать повторно с новыми значениями.
    self_path = pathlib.Path(__file__)
    src = self_path.read_text(encoding='utf-8')
    if args.phone:
        src = src.replace(f"'phone_display': '{CURRENT['phone_display']}'",
                          f"'phone_display': '{args.phone}'")
        src = src.replace(f"'phone_digits': '{CURRENT['phone_digits']}'",
                          f"'phone_digits': '{digits_of(args.phone)}'")
    if args.email:
        src = src.replace(f"'email': '{CURRENT['email']}'", f"'email': '{args.email}'")
    if args.metrika:
        src = src.replace(f"'metrika': '{CURRENT['metrika']}'", f"'metrika': '{args.metrika}'")
    self_path.write_text(src, encoding='utf-8')
    print('CURRENT в set-contacts.py обновлён.')


if __name__ == '__main__':
    main()
