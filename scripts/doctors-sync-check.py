#!/usr/bin/env python3
"""
Сверка общих врачей между тремя сайтами клиник.

Появился по требованию владельца (22.08.2026): у Дробковой в «Венеции»
оказалось 7 карточек документов против 8 на Ангеле и Версале — расхождение
заметил владелец, а не проверка. Правило: врач, который принимает в
нескольких клиниках, на всех их сайтах представлен ОДИНАКОВО — те же
сканы документов, тот же список квалификации, те же работы.

Что сверяется для каждого врача, чья страница есть более чем в одном репо:
  1. набор карточек документов (имена файлов сканов без префикса пути);
  2. пункты списков «Образование» и «Документы и квалификация» (текст);
  3. названия работ в portfolio.js.

Известные ОСОЗНАННЫЕ отличия «Венеции» перечислены в ALLOW — там нет КТ и
детского кабинета, поэтому формулировки кейсов адаптированы (КТ → ТРГ/ОПТГ,
марки сканеров → «цифровое сканирование»). Пункт списка/кейс, попавший под
ALLOW, из сверки исключается. Всё остальное расхождение = ошибка, код 1.

  python3 scripts/doctors-sync-check.py
"""
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
REPOS = {
    'Ангел': HERE.parent / 'Angel-Dent-site',
    'Версаль': HERE.parent / 'Versal-Dent-site',
    'Венеция': HERE.parent / 'venecia-dent.ru',
}

# Осознанные отличия: (репо, врач, фрагмент текста) — не считать расхождением.
ALLOW = [
    # тексты кейсов «Венеции» чистятся от КТ и марок сканеров — сверяем
    # только заголовки работ, они должны совпадать (см. п. 3), поэтому
    # текстовых исключений для портфолио не требуется.
]

READ_JS = '''
const fs = require('fs');
const code = fs.readFileSync(process.argv[1], 'utf8');
global.window = {};
global.document = { readyState: 'complete', addEventListener() {},
  querySelectorAll() { return []; }, querySelector() { return null; } };
new Function('window', 'document', code)(global.window, global.document);
const out = {};
for (const [slug, items] of Object.entries(global.window.AD_PORTFOLIO || {}))
  out[slug] = items.map(i => i.title);
process.stdout.write(JSON.stringify(out));
'''


def doctor_data(repo: Path):
    """slug → {cards:set, quals:[..], works:[..]} по одному репозиторию."""
    res = {}
    titles = json.loads(subprocess.run(
        ['node', '-e', READ_JS, str(repo / 'assets/js/portfolio.js')],
        capture_output=True, text=True, check=True).stdout)
    for page in sorted((repo / 'doctors').glob('*.html')):
        if page.name == 'index.html':
            continue
        s = page.read_text(encoding='utf-8')
        slug = page.stem
        cards = set(re.findall(r'docs/([a-z0-9-]+)\.webp', s))
        cards = {c for c in cards if not c.endswith('-thumb')}
        quals = []
        for m in re.finditer(r'<h2>(Образование|Документы и квалификация)</h2><ul>(.*?)</ul>', s, re.S):
            for li in re.findall(r'<li>(.*?)</li>', m.group(2), re.S):
                quals.append(re.sub(r'\s+', ' ', re.sub(r'<!--.*?-->', '', li)).strip())
        res[slug] = {'cards': cards, 'quals': quals, 'works': titles.get(slug, [])}
    return res


def main() -> int:
    data = {name: doctor_data(path) for name, path in REPOS.items() if path.is_dir()}
    problems = []
    slugs = {}
    for site, doctors in data.items():
        for slug in doctors:
            slugs.setdefault(slug, []).append(site)

    for slug, sites in sorted(slugs.items()):
        if len(sites) < 2:
            continue
        base_site = sites[0]
        base = data[base_site][slug]
        for other in sites[1:]:
            cur = data[other][slug]
            for missing in sorted(base['cards'] - cur['cards']):
                problems.append(f'{slug}: карточка «{missing}» есть на «{base_site}», нет на «{other}»')
            for extra in sorted(cur['cards'] - base['cards']):
                problems.append(f'{slug}: карточка «{extra}» есть на «{other}», нет на «{base_site}»')
            bq, cq = set(base['quals']), set(cur['quals'])
            for q in sorted(bq - cq):
                if not any(a[0] == other and a[1] == slug and a[2] in q for a in ALLOW):
                    problems.append(f'{slug}: пункт квалификации только на «{base_site}»: «{q[:70]}…»')
            for q in sorted(cq - bq):
                if not any(a[0] == base_site and a[1] == slug and a[2] in q for a in ALLOW):
                    problems.append(f'{slug}: пункт квалификации только на «{other}»: «{q[:70]}…»')
            if base['works'] != cur['works']:
                problems.append(f'{slug}: состав/порядок работ различается — '
                                f'«{base_site}»: {len(base["works"])}, «{other}»: {len(cur["works"])} '
                                f'({set(base["works"]) ^ set(cur["works"]) or "разный порядок"})')
        print(f'  · {slug}: {", ".join(sites)}')

    if problems:
        print('\nРасхождения:')
        for x in problems:
            print(f'  ⚠️  {x}')
    else:
        print('\n  ✓ общие врачи синхронны на всех сайтах, где они принимают')
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
