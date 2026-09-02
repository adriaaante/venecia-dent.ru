#!/usr/bin/env python3
"""Версия в ссылках на сканы документов и портреты врачей.

reg.ru отдаёт webp с кешем на 45 дней: пересобрали скан (новый водяной
знак, поворот, кроп) или заменили фото врача — а тот, кто заходил
раньше, ещё полтора месяца видит старую картинку из кеша браузера.
Лечится как у js/css: к ссылке приписывается хеш содержимого файла
(`...webp?v=1a2b3c4d`) — изменился файл, изменилась ссылка, браузер
скачивает заново.

Обрабатываются все HTML-страницы репозитория, ссылки на
`assets/img/docs/*.webp` (полная версия и миниатюра скана) и
`assets/img/doctors/*.webp` (портрет врача и миниатюра карточки).
PNG-дубли портретов не трогаем — они стоят только в `og:image`
и JSON-LD, где параметр в ссылке мессенджерам не нужен. Идемпотентно.

    python3 scripts/docs-version.py           # проставить
    python3 scripts/docs-version.py --check   # код 1, если надо прогнать
"""
import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIRS = ('docs', 'doctors')

def file_hash(p: Path) -> str:
    return hashlib.md5(p.read_bytes()).hexdigest()[:8]

def main(argv):
    check = '--check' in argv
    hashes = {}
    for d in DIRS:
        for p in (ROOT / 'assets' / 'img' / d).glob('*.webp'):
            hashes[f'{d}/{p.name}'] = file_hash(p)
    rx = re.compile(
        r'((?:\.\./)?assets/img/(' + '|'.join(DIRS) + r')/)'
        r'([A-Za-z0-9_-]+\.webp)(\?v=[0-9a-f]{8})?'
    )
    changed = []
    for page in sorted(ROOT.glob('**/*.html')):
        if any(part.startswith(('.', '_')) for part in page.relative_to(ROOT).parts):
            continue
        s = page.read_text(encoding='utf-8')
        def sub(m):
            key = f'{m.group(2)}/{m.group(3)}'
            if key not in hashes:
                return m.group(0)
            return f'{m.group(1)}{m.group(3)}?v={hashes[key]}'
        new = rx.sub(sub, s)
        if new != s:
            changed.append(str(page.relative_to(ROOT)))
            if not check:
                page.write_text(new, encoding='utf-8')
    if check:
        if changed:
            print('надо прогнать docs-version.py:', ', '.join(changed)); return 1
        print('✓ версии ссылок на документы и портреты актуальны'); return 0
    print(f'обновлено страниц: {len(changed)}' + (f' ({", ".join(changed)})' if changed else ''))
    return 0

if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
