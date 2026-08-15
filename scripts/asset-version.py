#!/usr/bin/env python3
"""
Версионирование ссылок на свои js/css: `styles.css` → `styles.css?v=1a2b3c4d`
(8 символов md5 файла). Меняется файл → меняется ссылка → браузер и кеш
хостинга обязаны скачать новую версию.

Зачем это нужно именно здесь. На reg.ru статику раздаёт nginx ПЕРЕД
Apache, и для js/css он ставит `Cache-Control: max-age=3888000` (45 дней)
независимо от `.htaccess` — проверено 15.08.2026: правки в `.htaccess`
меняют заголовки у html и webp, а у js/css остаются те же 45 дней.
Практический результат был неприятный: новая работа врача в
`portfolio.js` уезжала на прод, но посетитель, заходивший раньше,
продолжал видеть старое портфолио. Хеш в ссылке снимает вопрос.

Идемпотентно: повторный запуск без изменений в файлах ничего не пишет.
Прогонять после ЛЮБОЙ правки css/js — перед деплоем.

  python3 scripts/asset-version.py          # проставить
  python3 scripts/asset-version.py --check  # только проверить (код 1, если надо)
"""
import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# ссылка вида src="../assets/js/main.js" / href="/assets/css/styles.css"
LINK = re.compile(r'((?:src|href)=")([^"]*?assets/[^"?]+\.(?:js|css))(\?v=[0-9a-f]+)?(")')


def digest(page: Path, rel: str) -> str | None:
    """Путь из ссылки → файл в репозитории → короткий хеш содержимого."""
    target = (ROOT / rel.lstrip('/')) if rel.startswith('/') else (page.parent / rel)
    target = target.resolve()
    if not target.is_file():
        return None
    return hashlib.md5(target.read_bytes()).hexdigest()[:8]


def main() -> int:
    check = '--check' in sys.argv
    changed, missing = [], []

    for page in sorted(ROOT.glob('**/*.html')):
        if any(part in ('_materials', 'node_modules', '.git') for part in page.parts):
            continue
        src = page.read_text(encoding='utf-8')

        def repl(m: re.Match) -> str:
            h = digest(page, m.group(2))
            if h is None:
                missing.append(f'{page.relative_to(ROOT)} → {m.group(2)}')
                return m.group(0)
            return f'{m.group(1)}{m.group(2)}?v={h}{m.group(4)}'

        out = LINK.sub(repl, src)
        if out != src:
            changed.append(str(page.relative_to(ROOT)))
            if not check:
                page.write_text(out, encoding='utf-8')

    for m in missing:
        print(f'  ⚠️  файла нет: {m}')
    print(f'{"нужно обновить" if check else "обновлено"}: {len(changed)} страниц'
          + (f' (первые: {", ".join(changed[:5])})' if changed else ''))
    return 1 if (check and changed) else 0


if __name__ == '__main__':
    sys.exit(main())
