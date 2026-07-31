#!/usr/bin/env python3
"""Регрессия вёрстки в реальном браузере: прогон страниц по вьюпортам.

Ловит то, что глазами на одном экране не видно:
  • горизонтальную прокрутку (что-то не помещается по ширине) с указанием
    виновных элементов;
  • контент, уехавший под липкую панель «Позвонить/Записаться»;
  • разорванные переносом суммы («бесплатно 1» / «000 ₽»);
  • модалку записи: открывается ли и влезает ли в экран;
  • ошибки JS на странице.

Нужен Playwright и Chromium:
    pip install playwright && playwright install chromium

Запуск из корня репо:
    python3 scripts/check-layout.py                  # весь набор вьюпортов
    python3 scripts/check-layout.py --vw 320,375     # только указанные
    python3 scripts/check-layout.py --root ../Angel-Dent-site

Код возврата 1, если найдены проблемы — годится для CI.

⚠️ Шрифты Google не блокировать: без них подставляются системные с другой
шириной глифов и появляются ложные «переполнения». Скрипт пропускает
fonts.g*, а остальную внешку режет (Метрика в песочнице не резолвится
и вешает load).
"""
import argparse
import functools
import http.server
import os
import pathlib
import socketserver
import sys
import threading

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sys.exit('Нужен playwright: pip install playwright && playwright install chromium')

VIEWPORTS = [
    ('iPhone SE', 320, 568), ('iPhone 8', 375, 667), ('iPhone 12/13', 390, 844),
    ('iPhone 14 Pro Max', 430, 932), ('планшет-порт', 640, 900),
    ('планшет', 768, 1024), ('ноут', 1280, 800), ('широкий', 1600, 900),
]

PAGES = ['/', '/contacts.html', '/ceny.html', '/promotions.html', '/reviews.html',
         '/about.html', '/garantii.html', '/pervyj-vizit.html', '/404.html',
         '/services/index.html', '/services/implantaciya.html',
         '/services/otbelivanie.html', '/services/ortodontiya.html',
         '/doctors/index.html', '/doctors/kilasoniya.html']

MEASURE = r"""
() => {
  const de = document.documentElement;
  const q = s => document.querySelector(s);
  const res = {culprits: [], brokenPrices: [], underBar: null};

  if (de.scrollWidth > de.clientWidth + 1) {
    res.overflow = de.scrollWidth - de.clientWidth;
    document.querySelectorAll('body *').forEach(el => {
      const r = el.getBoundingClientRect();
      if (r.width > 0 && r.right > de.clientWidth + 1 &&
          getComputedStyle(el).position !== 'fixed') {
        res.culprits.push((el.tagName + '.' +
          (el.className || '').toString().split(' ')[0]).slice(0, 42));
      }
    });
    res.culprits = res.culprits.slice(0, 4);
  }

  // Сумма, разорванная переносом: у одного текстового узла больше одного
  // клиентского прямоугольника.
  document.querySelectorAll('.price-now').forEach(td => {
    const parts = [];
    td.childNodes.forEach(n => {
      if (n.nodeType === 3 && n.textContent.trim()) parts.push(n);
    });
    const s = td.querySelector('s');
    if (s) parts.push(s);
    parts.forEach(n => {
      const rg = document.createRange();
      rg.selectNodeContents(n);
      if (rg.getClientRects().length > 1) res.brokenPrices.push(n.textContent.trim());
    });
  });

  const bar = q('.sticky-cta');
  const badge = q('.ff-credit');
  if (bar && getComputedStyle(bar).display !== 'none' && badge) {
    res.underBar = Math.round(badge.getBoundingClientRect().bottom -
                              bar.getBoundingClientRect().top);
  }
  return res;
}
"""


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default=None, help='корень сайта (по умолчанию — репо скрипта)')
    ap.add_argument('--vw', default=None, help='список ширин через запятую')
    ap.add_argument('--port', type=int, default=8799)
    args = ap.parse_args()

    root = pathlib.Path(args.root).resolve() if args.root \
        else pathlib.Path(__file__).resolve().parent.parent
    views = VIEWPORTS
    if args.vw:
        keep = {v.strip() for v in args.vw.split(',')}
        views = [v for v in VIEWPORTS if str(v[1]) in keep]

    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(('127.0.0.1', args.port),
                                   functools.partial(Quiet, directory=str(root)))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()

    pages = [p for p in PAGES if (root / (p.lstrip('/') or 'index.html')).exists()]
    print(f'{root.name}: страниц {len(pages)}, вьюпортов {len(views)}')
    fails = 0

    with sync_playwright() as p:
        # PW_CHROMIUM — путь к бинарю, если в окружении стоит не тот билд,
        # что ожидает playwright (иначе launch падает с «Executable doesn't exist»)
        exe = os.environ.get('PW_CHROMIUM')
        br = p.chromium.launch(executable_path=exe) if exe else p.chromium.launch()
        for name, vw, vh in views:
            ctx = br.new_context(viewport={'width': vw, 'height': vh},
                                 is_mobile=vw <= 640, has_touch=vw <= 640)
            ctx.route('**/*', lambda r: r.continue_()
                      if ('127.0.0.1' in r.request.url or 'fonts.g' in r.request.url)
                      else r.abort())
            page = ctx.new_page()
            errs = []
            page.on('pageerror', lambda e: errs.append(str(e)[:70]))
            print(f'\n── {name}  {vw}×{vh}')
            for path in pages:
                page.goto(f'http://127.0.0.1:{args.port}{path}', wait_until='load')
                page.wait_for_timeout(300)
                for _ in range(3):
                    page.evaluate("window.scrollTo({top: document.documentElement"
                                  ".scrollHeight, behavior: 'instant'})")
                    page.wait_for_timeout(150)
                m = page.evaluate(MEASURE)
                probs = []
                if m.get('overflow'):
                    probs.append(f"горизонт. прокрутка +{m['overflow']}px"
                                 + (' | ' + '; '.join(m['culprits']) if m['culprits'] else ''))
                if m['brokenPrices']:
                    probs.append('разорвана сумма: ' + '; '.join(m['brokenPrices'][:3]))
                if m['underBar'] is not None and m['underBar'] > 0:
                    probs.append(f"низ страницы под липкой панелью на {m['underBar']}px")
                if errs:
                    probs.append('JS: ' + errs[0])
                    errs.clear()
                if probs:
                    fails += 1
                    print(f'   ✗ {path:<32} ' + ' | '.join(probs))
                else:
                    print(f'   ✓ {path}')
            if vw <= 640:
                page.goto(f'http://127.0.0.1:{args.port}/', wait_until='load')
                page.wait_for_timeout(300)
                try:
                    # первый [data-modal-open] в DOM — кнопка шапки, на мобиле
                    # она display:none; кликаем видимую, в липкой панели
                    page.click('.sticky-cta [data-modal-open]', timeout=3000)
                    page.wait_for_timeout(400)
                    st = page.evaluate("""() => {
                        const m = document.querySelector('.modal');
                        const c = document.querySelector('.modal__card');
                        if (!m || !c) return null;
                        const r = c.getBoundingClientRect();
                        return {open: m.classList.contains('is-open'),
                                top: r.top, bottom: r.bottom, ih: window.innerHeight};}""")
                    if not st or not st['open']:
                        print('   ✗ модалка записи не открылась'); fails += 1
                    elif st['top'] < 0 or st['bottom'] > st['ih'] + 1:
                        print('   ✗ модалка не влезает в экран'); fails += 1
                    else:
                        print('   ✓ модалка записи открывается и влезает')
                except Exception as e:
                    print(f'   ✗ модалка: {str(e)[:60]}'); fails += 1
            ctx.close()
        br.close()

    print(f'\nПРОБЛЕМ: {fails}')
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
