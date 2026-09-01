#!/usr/bin/env python3
"""Пересобрать сканы документов врачей из чистых оригиналов.

Нужен, когда меняются правила отрисовки — например, появился знак клиники
(01.09.2026) или другой размер миниатюры. Скрипт берёт `_originals/*.webp`
(они всегда БЕЗ знака) и заново собирает пару картинок для страницы:

    <slug>-<name>.webp        полная версия, грузится по клику
    <slug>-<name>-thumb.webp  миниатюра 420×315 — только она стоит в HTML

Размеры миниатюр не меняются, поэтому HTML и JSON-LD трогать не нужно.
Прогон идемпотентный: знак накладывается на копию оригинала, а не поверх
уже подписанной картинки.

    python3 scripts/docs-rebuild.py            # все документы
    python3 scripts/docs-rebuild.py drobkova   # только одного врача
"""
import sys
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

spec = importlib.util.spec_from_file_location('prepare_doc', ROOT / 'scripts' / 'prepare-doc.py')
pd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pd)


def main(argv: list[str]) -> int:
    slug = argv[0] if argv else None
    originals = sorted((pd.ORIG).glob(f'{slug}-*.webp' if slug else '*.webp'))
    originals = [p for p in originals if not p.name.startswith('_')]
    if not originals:
        print('оригиналов не нашлось'); return 1
    for src in originals:
        (fp, fsize), (tp, tsize) = pd.build_images(src, src.stem, 0, '', False)
        print(f'  ✓ {src.stem:38} {fsize[0]}×{fsize[1]} + миниатюра {tsize[0]}×{tsize[1]}')
    print(f'пересобрано документов: {len(originals)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
