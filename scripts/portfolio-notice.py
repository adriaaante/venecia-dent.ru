#!/usr/bin/env python3
"""
Сноска под портфолио врача — по фактам, а не «на всякий случай».

Раньше под каждым разделом «Работы врача» стояло одно и то же:
«Иллюстративные изображения клинических ситуаций — типичные результаты
по описанной методике». Пока фото были картинками-иллюстрациями, это было
честно. Сейчас в портфолио появились реальные работы с согласия пациентов,
и та же фраза стала обесценивать их и вводить посетителя в заблуждение.

Скрипт смотрит в `assets/js/portfolio.js` (источник правды) и подставляет
на страницу врача ту сноску, которая соответствует его кейсам:
  • все фото реальные            → говорим прямо, что это работы клиники;
  • есть кейсы `illustrative`    → отделяем их (на карточке — метка
                                    «Иллюстрация методики»);
  • фото ещё нет (заглушки)      → показываем работы на консультации.

Во всех вариантах остаются две обязательные вещи: письменное согласие
пациентов (ст. 152.1 ГК, врачебная тайна) и предупреждение о
противопоказаниях (ст. 24 ФЗ «О рекламе»).

Идемпотентно. Прогонять после правок `portfolio.js`.

  python3 scripts/portfolio-notice.py [--check]
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONSENT = 'публикуются с письменного согласия пациентов'
TAIL = ('Результат индивидуален и зависит от клинической ситуации. '
        'Имеются противопоказания, необходима консультация специалиста.')

NOTICE = {
    'real': f'Фото в этом разделе — реальные работы врачей клиники, {CONSENT}. {TAIL}',
    'mixed': (f'Фото реальных работ {CONSENT}; кейсы с пометкой '
              f'«Иллюстрация методики» показаны типичной клинической картиной, '
              f'а не снимком пациента. {TAIL}'),
    'none': ('Фото работ врача показываем на консультации — с письменного '
             f'согласия пациентов. {TAIL}'),
}

READ_JS = '''
const fs = require('fs');
const code = fs.readFileSync(process.argv[1], 'utf8');
global.window = {};
global.document = { readyState: 'complete', addEventListener() {},
  querySelectorAll() { return []; }, querySelector() { return null; } };
new Function('window', 'document', code)(global.window, global.document);
const out = {};
for (const [slug, items] of Object.entries(global.window.AD_PORTFOLIO || {})) {
  const photo = items.filter(i => i.before && i.before !== 'placeholder');
  out[slug] = { photos: photo.length, illustrative: photo.filter(i => i.illustrative).length };
}
process.stdout.write(JSON.stringify(out));
'''


def kind(stat: dict) -> str:
    if not stat['photos']:
        return 'none'
    return 'mixed' if stat['illustrative'] else 'real'


def main() -> int:
    check = '--check' in sys.argv
    data = json.loads(subprocess.run(
        ['node', '-e', READ_JS, str(ROOT / 'assets/js/portfolio.js')],
        capture_output=True, text=True, check=True).stdout)

    changed = []
    for page in sorted((ROOT / 'doctors').glob('*.html')):
        src = page.read_text(encoding='utf-8')
        m = re.search(r'data-portfolio="([^"]+)"', src)
        if not m:
            continue
        stat = data.get(m.group(1), {'photos': 0, 'illustrative': 0})
        text = NOTICE[kind(stat)]
        out = re.sub(r'(<p class="disclaimer">).*?(</p>)',
                     lambda mm: mm.group(1) + text + mm.group(2), src, count=1, flags=re.S)
        mark = '·'
        if out != src:
            mark = '✓'
            changed.append(page.name)
            if not check:
                page.write_text(out, encoding='utf-8')
        print(f'  {mark} {page.name:24} {m.group(1):12} '
              f'фото {stat["photos"]}, из них иллюстраций {stat["illustrative"]} → {kind(stat)}')

    print(f'{"нужно обновить" if check else "обновлено"}: {len(changed)} страниц')
    return 1 if (check and changed) else 0


if __name__ == '__main__':
    sys.exit(main())
