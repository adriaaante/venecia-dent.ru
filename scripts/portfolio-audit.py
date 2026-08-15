#!/usr/bin/env python3
"""
Сторож портфолио: ищет потерянные работы и пустые страницы врачей.

Появился после разбора 15.08.2026. Коммит «Убрана Смолякова Радана»
(10.08) вырезал из `portfolio.js` заодно блоки ещё четырёх врачей —
Киласонии, Савчука, Кендабаевой, Хачатрян. Пять дней их страницы
показывали пустое портфолио, и никто этого не видел: страница
открывается, ошибок нет, просто вместо работ пустота. В том числе
пропали РЕАЛЬНЫЕ работы с фото пациентов.

Что проверяет:
  1. страницы `doctors/*.html` с `data-portfolio`, для которых в
     `portfolio.js` нет ключа или массив пуст → врач без работ;
  2. фото в `assets/img/portfolio/`, на которые никто не ссылается
     («сироты») — так выглядит работа, потерянная при удалении врача;
  3. битые ссылки на фото из `portfolio.js`;
  4. ключи `portfolio.js` без страницы врача — например, врач уволился,
     а его работы остались висеть невидимыми. Реальные работы (фото
     пациентов) в этом случае **передаём действующему врачу того же
     направления**, а не удаляем.

  python3 scripts/portfolio-audit.py        # отчёт, код 1 если есть находки
  python3 scripts/portfolio-audit.py --quiet  # только находки
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PHOTO_DIR = ROOT / 'assets/img/portfolio'

READ_JS = '''
const fs = require('fs');
const code = fs.readFileSync(process.argv[1], 'utf8');
global.window = {};
global.document = { readyState: 'complete', addEventListener() {},
  querySelectorAll() { return []; }, querySelector() { return null; } };
new Function('window', 'document', code)(global.window, global.document);
const out = {};
for (const [slug, items] of Object.entries(global.window.AD_PORTFOLIO || {})) {
  out[slug] = items.map(i => ({
    title: i.title,
    illustrative: !!i.illustrative,
    photos: [i.before, i.after, i.beforeFull, i.afterFull]
      .concat((i.extra || []).map(e => e.src))
      .filter(s => s && s !== 'placeholder'),
  }));
}
process.stdout.write(JSON.stringify(out));
'''


def main() -> int:
    quiet = '--quiet' in sys.argv
    data = json.loads(subprocess.run(
        ['node', '-e', READ_JS, str(ROOT / 'assets/js/portfolio.js')],
        capture_output=True, text=True, check=True).stdout)

    problems, notes = [], []

    # 1. страницы врачей без работ
    pages = {}
    for page in sorted((ROOT / 'doctors').glob('*.html')):
        m = re.search(r'data-portfolio="([^"]+)"', page.read_text(encoding='utf-8'))
        if m:
            pages[m.group(1)] = page.name
    for slug, name in pages.items():
        if not data.get(slug):
            problems.append(f'страница {name}: в portfolio.js нет работ для «{slug}»')

    # 2. ключи без страницы врача. Сами по себе безобидны (просто не видны),
    #    но если там лежат РЕАЛЬНЫЕ работы — их надо передать действующему
    #    врачу того же направления, иначе работа потеряна.
    for slug, cases in data.items():
        if slug in pages:
            continue
        real = sum(1 for c in cases if c['photos'] and not c['illustrative'])
        if real:
            problems.append(f'ключ «{slug}» без страницы врача, а в нём {real} '
                            f'работ(ы) с реальными фото — передать действующему врачу')
        else:
            notes.append(f'ключ «{slug}» есть в portfolio.js, но страницы врача нет '
                         f'(реальных работ там нет)')

    # 3. битые ссылки
    used = set()
    for slug, cases in data.items():
        for case in cases:
            for src in case['photos']:
                used.add(Path(src).name)
                if not (ROOT / 'doctors' / src).resolve().is_file():
                    problems.append(f'{slug} / «{case["title"]}»: нет файла {src}')

    # 4. брошенные фото. Снимок с фамилией врача в имени — это реальная
    #    работа, её потеря критична. Безымянные (caries-*, ortho-*, veneers-*)
    #    — заготовки-иллюстрации, считаем их одной строкой.
    known = set(pages) | set(data)
    illus = 0
    for f in sorted(PHOTO_DIR.glob('*.webp')):
        if f.name in used:
            continue
        if f.name.split('-')[0] in known:
            problems.append(f'РЕАЛЬНАЯ РАБОТА врача потеряна: фото {f.name} '
                            f'не используется ни в одном кейсе')
        else:
            illus += 1
    if illus:
        notes.append(f'неиспользуемых картинок-иллюстраций: {illus} (не работы врачей)')

    if problems:
        print('Находки:')
        for x in problems:
            print(f'  ⚠️  {x}')
    for x in notes:
        if not quiet:
            print(f'  · {x}')
    if not problems and not quiet:
        print('  ✓ портфолио в порядке: у каждой страницы есть работы, '
              'битых ссылок и потерянных работ нет')
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
