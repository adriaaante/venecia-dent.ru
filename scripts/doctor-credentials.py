#!/usr/bin/env python3
"""
Чистит страницы врачей от неподтверждённых строк квалификации.

Правило владельца (19.08.2026): чего нет в документе или у чего вышел
срок — на сайте не показываем, и пустых мест после этого остаться не
должно. Раньше в шаблоне висели строки-заглушки вида «Высшее медицинское
образование, специальность „Стоматология“ <!-- TODO: уточните вуз -->» —
посетитель видел обещание данных, которых нет, а для медицинского сайта
это прямой удар по доверию.

Скрипт:
  • выкидывает <li> с TODO-комментарием внутри (значит, данные не
    подтверждены документом);
  • если список опустел — убирает и его, и заголовок над ним, чтобы не
    оставалось «голых» подзаголовков;
  • приводит уцелевшие блоки к единому названию «Документы и квалификация».

Комментарии-подсказки в HTML остаются: как только клиника пришлёт диплом,
строку возвращаем и добавляем скан через scripts/prepare-doc.py.

  python3 scripts/doctor-credentials.py [--check]
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HEADINGS = ('Образование', 'Сертификаты и повышение квалификации',
            'Документы и квалификация')
BLOCK = re.compile(r'\s*<h2>(' + '|'.join(HEADINGS) + r')</h2><ul>(.*?)</ul>', re.S)
LI = re.compile(r'<li>.*?</li>', re.S)


def clean(src: str) -> str:
    def repl(m: re.Match) -> str:
        title, inner = m.group(1), m.group(2)
        kept = [li for li in LI.findall(inner) if '<!--' not in li]
        # ⚠️ Только ТЕКСТ подсказок, без «<!--»/«-->»: вложенные комментарии
        # в HTML невалидны — первый внутренний «-->» закрывает внешний, и
        # хвост «-->» вылезает на страницу видимым текстом (баг 19.08.2026).
        hints = [re.sub(r'\s+', ' ', t).strip(' .').replace('TODO:', '').replace('--', '—').strip()
                 for t in re.findall(r'<!--((?:(?!-->).)*?)-->', inner, re.S)]
        hint_tail = (' Подсказки: ' + '; '.join(h for h in hints if h) + '.') if any(hints) else ''
        if not kept:
            # Блок целиком без подтверждения — убираем вместе с заголовком,
            # подсказки прячем в комментарий, чтобы не потерять контекст.
            return f'\n  <!-- {title}: данных, подтверждённых документами, пока нет.{hint_tail} -->'
        name = 'Документы и квалификация' if title != 'Образование' else title
        return f'\n  <h2>{name}</h2><ul>{"".join(kept)}</ul>'
    return BLOCK.sub(repl, src)


def main() -> int:
    check = '--check' in sys.argv
    changed = []
    for page in sorted((ROOT / 'doctors').glob('*.html')):
        if page.name == 'index.html':
            continue
        src = page.read_text(encoding='utf-8')
        out = clean(src)
        if out != src:
            changed.append(page.name)
            if not check:
                page.write_text(out, encoding='utf-8')
        print(f'  {"✓" if out != src else "·"} {page.name}')
    print(f'{"нужно почистить" if check else "почищено"}: {len(changed)} страниц')
    return 1 if (check and changed) else 0


if __name__ == '__main__':
    sys.exit(main())
