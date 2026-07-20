# Венеция (venecia-dent.ru) — заметки для агента

Семейная стоматология «Венеция», **Мытищи, ул. Мира, д. 37** (индекс 141008,
координаты 55.918478, 37.721126 — уже в JSON-LD и карте). Третья клиника
владельца (после Angel-Dent и Versal-Dent), архитектура сайта та же:
плоская статика без сборщика. **Массовая правка хедера/футера/FAB =
трогаем каждый HTML** (или Python-патч).

Позиционирование: премиально по оформлению, но слово «премиум» в текстах
НЕ используем. Цены и услуги = Angel-Dent (сверено 2026-07-20). Тексты
написаны с нуля (не дубли Angel/Versal — важно для SEO).

## ⚠️ Открытые TODO (сайт собран до запуска клиники)

- **Телефон/email/мессенджеры** — placeholder `+7 (000) 000-00-00` /
  `venecia.dent@mail.ru` / `wa.me/70000000000` / `t.me/+70000000000`.
  Заменить одной командой: `python3 scripts/set-contacts.py --phone "+7 (9XX) XXX-XX-XX" [--email ...]`
  (правит все HTML + main.js + CLAUDE.md).
- **Яндекс.Метрика** — placeholder `00000000` в `<head>` каждой страницы
  + `YM_COUNTER_ID = 0` в `assets/js/main.js`. Заменить, когда владелец
  пришлёт id (тем же set-contacts.py, флаг `--metrika ID`).
- **Юрлицо/лицензия** — на `legal.html`, в `privacy.html` и футере стоят
  `<!-- TODO -->`-заглушки «сведения будут опубликованы». НЕ вписывать
  реквизиты ООО «АНГЕЛ-ДЕНТ» без явного указания владельца (лицензия
  привязана к адресу — у нового адреса будет своя).
- **Врачей нет** — раздела doctors/ нет; на index/about честные блоки
  «команда формируется». Когда появятся врачи — добавить раздел по
  образцу Versal (страницы, карусель, портфолио).
- **Фото клиники** — владелец пришлёт позже; сейчас весь визуал
  сгенерирован (Higgsfield soul_2, бренд-гамма). Реальные фото класть в
  `assets/img/clinic/` и заменить в галереях/OG.
- **Отзывов нет** — честные заглушки на index/reviews. Рейтинги и
  AggregateRating НЕ добавлять, пока нет реальной карточки Яндекса.
- **Telegram-бот заявок** — создать бота и группу, на сервере
  `cp api/config.php.example api/config.php` + токен/chat_id.

## Данные клиники (источник правды)

- Адрес: Московская область, г. Мытищи, ул. Мира, д. 37, 141008
- График: ежедневно 10:00–20:00
- Домен: venecia-dent.ru
- Контакты: см. TODO выше (пока placeholder'ы)
- Меняются контакты → `scripts/set-contacts.py`, руками не искать по файлам.

## Фирменный стиль

Полная палитра/типографика — **`BRAND.md`**. Коротко: лагуна `#0F6E66`,
терракота `#C75B39` (CTA), алебастр `#F7FAF8`, чернила `#13292A`.
Шрифты: **Prata** (заголовки) + **Onest** (текст), Google Fonts.
Фирменный мотив — **арка** (маски фото `--radius-arch`, мини-арки иконок)
и терракотовый ромб (буллеты, eyebrow). Токены — в `:root` styles.css.
НЕ использовать: золото (это Versal), голубой (это Angel).

Логотип: `assets/img/logo.svg` — исходник (зуб с окном-аркой на плитке
лагуны). PNG/фавиконки перегенерировать: `python3 scripts/build-favicons.py`
(нужны `pip install cairosvg pillow`).

## Структура

Корень: `index.html`, `about.html`, `promotions.html`, `reviews.html`,
`contacts.html`, `ceny.html` (полный прайс), `garantii.html`,
`pervyj-vizit.html` (маршрут пациента), правовые (`legal`, `privacy`,
`consent`, `oferta`, `cookies`), `404.html`.
`services/` — `index.html` + 9 услуг (slug-и как у Angel/Versal:
implantaciya, ortodontiya, terapiya, hirurgiya, detskaya, protezirovanie,
viniry, gigiena, parodontologiya).

Навигация: Главная · Услуги · Цены · Акции · Первый визит · О клинике ·
Контакты. «Гарантии» и «Отзывы» — в футере.

Шаблон услуги: page-hero → usps (4 факта) → «Как мы работаем» (текст +
фото) → цены → этапы (4 шага) → FAQ → перелинковка (Цены/Гарантии/Первый
визит/Акции) → смежные услуги → CTA. JSON-LD: MedicalProcedure + FAQPage +
BreadcrumbList на каждой; Dentist (`@id` `…/#clinic`) — на index, about,
contacts.

Сайт собирался Python-генератором (одноразовый, в истории сессии);
дальше правки — прямо в HTML или свежим скриптом в `scripts/`.

## Сгенерированные изображения

`assets/img/generated/` (hero 1000×1200, family 1000×1150, og-banner
1200×630) и `assets/img/services/*.webp` (1200×750) — Higgsfield `soul_2`,
16:9 → кроп. Промпт-стиль: см. BRAND.md (тёплый свет, teal-стена,
терракота, арки, «no text, no logos», candid editorial). Люди —
сгенерированные, БЕЗ имён, славянская внешность.

## Акции в прайс-таблицах — единый формат (как у Angel/Versal)

```html
<tr><td>Название <span class="badge-promo">Акция</span></td>
    <td class="price-now">17 500 ₽ <s style="font-weight:400;opacity:.55">25 000 ₽</s></td></tr>
```
Сейчас так оформлены: Amazing White (gigiena), бесплатная консультация
ортодонта (ortodontiya), КТ+план 4 200 ₽ (ceny.html).

## Форма заявки и цели Метрики

Как у Angel/Versal: `main.js` (`sendLead`) → POST `/api/lead.php` →
Telegram. Honeypot `company`, маска `+7 (XXX) XXX-XX-XX`. Цели
(`trackGoal`): lead_submit, call_click, whatsapp_click, telegram_click —
макро; modal_open, form_start — микро. Имена целей в кабинете Метрики
должны совпадать. UTM/yclid — sessionStorage → `_utm_*` в заявке.

## Деплой на reg.ru

С сервера (Shell-клиент ISPmanager): `scripts/deploy.sh` = git pull +
rsync репо → `~/www/venecia-dent.ru/`. Ярлык: `ln -s
~/venecia-dent.ru/scripts/deploy.sh ~/venecia-dent.sh`. На сервере ТРИ
клиники (Angel, Versal, Венеция) — у каждой свой репо/папка/ярлык, не
перепутать. Не деплоятся: .git, scripts/, CLAUDE.md, README.md, BRAND.md,
_materials/, api/config.php.example. Первичный сетап: клонировать репо в
`~/venecia-dent.ru/`, создать `api/config.php`, симлинк, `--dry`, деплой.

## Workflow пушей

Разработка — ветка **`claude/venetia-dental-website-vr6cb6`**:
`git push -u origin claude/venetia-dental-website-vr6cb6`.
В `main` НЕ пушить без явного разрешения владельца. PR не создавать.

## Что НЕ делать без явной просьбы

- Не выдумывать отзывы/рейтинги/врачей/реквизиты.
- Не упоминать конкретное оборудование (микроскоп, марки КТ/сканеров),
  пока владелец не подтвердил оснащение. Сейчас на сайте только
  безопасные формулировки (КТ упоминается в акции «КТ + план» — это
  подтверждённая услуга из прайса Angel).
- Не писать слово «премиум» в текстах сайта.
- Не пушить в main.
