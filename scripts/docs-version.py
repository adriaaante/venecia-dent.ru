#!/usr/bin/env python3
"""Версия в ссылках на сканы документов — чтобы правки доезжали до людей.

reg.ru отдаёт webp с кешем на месяц: пересобрали скан (новый водяной
знак, поворот, кроп) — а тот, кто открывал документ раньше, ещё месяц
видит старую картинку из кеша браузера. Лечится как у js/css: к ссылке
приписывается хеш содержимого файла (`...webp?v=1a2b3c4d`) — изменился
файл, изменилась ссылка, браузер скачивает заново.

Обрабатываются страницы врачей (`doctors/*.html`): и `href` полной
версии, и `src` миниатюры. Идемпотентно.

    python3 scripts/docs-version.py           # проставить
    python3 scripts/docs-version.py --check   # код 1, если надо прогнать
"""
import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / 'assets' / 'img' / 'docs'

def file_hash(p: Path) -> str:
    return hashlib.md5(p.read_bytes()).hexdigest()[:8]

def main(argv):
    check = '--check' in argv
    hashes = {p.name: file_hash(p) for p in DOCS.glob('*.webp')}
    rx = re.compile(r'((?:\.\./)?assets/img/docs/)([A-Za-z0-9_-]+\.webp)(\?v=[0-9a-f]{8})?')
    changed = []
    for page in sorted((ROOT / 'doctors').glob('*.html')):
        s = page.read_text(encoding='utf-8')
        def sub(m):
            name = m.group(2)
            if name not in hashes:
                return m.group(0)
            return f'{m.group(1)}{name}?v={hashes[name]}'
        new = rx.sub(sub, s)
        if new != s:
            changed.append(page.name)
            if not check:
                page.write_text(new, encoding='utf-8')
    if check:
        if changed:
            print('надо прогнать docs-version.py:', ', '.join(changed)); return 1
        print('✓ версии ссылок на документы актуальны'); return 0
    print(f'обновлено страниц: {len(changed)}' + (f' ({", ".join(changed)})' if changed else ''))
    return 0

if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
