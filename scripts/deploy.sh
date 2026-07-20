#!/usr/bin/env bash
# Венеция — деплой на reg.ru.
#
# Скрипт запускается ПРЯМО НА СЕРВЕРЕ reg.ru (Shell-клиент в ISPmanager).
# Подтягивает свежий код с GitHub в ~/venecia-dent.ru/ и синхронизирует
# его в публичную папку ~/www/venecia-dent.ru/ (то, что отдаёт Apache).
#
# Использование:
#   ./scripts/deploy.sh         — выкатить
#   ./scripts/deploy.sh --dry   — показать план, ничего не менять
#
# Удобный шорткат на сервере (симлинк), делается один раз:
#   ln -s ~/venecia-dent.ru/scripts/deploy.sh ~/venecia-dent.sh
# Тогда команда становится просто ~/venecia-dent.sh.
#
# api/config.php (токен Telegram-бота) живёт только на сервере, он в
# .gitignore — git pull его не трогает. Создаётся один раз вручную
# из api/config.php.example.

set -euo pipefail

# Резолвим симлинк, чтобы найти настоящий путь до scripts/deploy.sh
# даже когда запускают через ~/deploy.sh.
SCRIPT="$(readlink -f "$0")"
REPO="$(cd "$(dirname "$SCRIPT")/.."; pwd)"
DOCROOT="$HOME/www/venecia-dent.ru"

DRY=0
case "${1:-}" in
    --dry|--dry-run) DRY=1 ;;
    "" ) ;;
    -h|--help)
        sed -n '2,17p' "$SCRIPT" | sed 's/^# \{0,1\}//'
        exit 0
        ;;
    *) echo "Неизвестный флаг: $1 (см. --help)" >&2; exit 2 ;;
esac

if [ ! -d "$REPO/.git" ]; then
    echo "✗ $REPO — не git-репо." >&2
    exit 1
fi

if [ ! -d "$DOCROOT" ]; then
    echo "✗ Не найдена публичная папка $DOCROOT." >&2
    exit 1
fi

if [ ! -f "$REPO/api/config.php" ]; then
    echo "✗ $REPO/api/config.php нет." >&2
    echo "  Создайте его по шаблону $REPO/api/config.php.example —" >&2
    echo "  пропишите TELEGRAM_BOT_TOKEN и TELEGRAM_CHAT_ID." >&2
    exit 1
fi

echo "→ git pull в $REPO"
cd "$REPO"
git pull --ff-only

OPTS=(-av --delete)
[ "$DRY" -eq 1 ] && OPTS+=(--dry-run --itemize-changes)

EXCLUDES=(
    --exclude='.git/'
    --exclude='.github/'
    --exclude='.claude/'
    --exclude='scripts/'
    --exclude='CLAUDE.md'
    --exclude='README.md'
    --exclude='BRAND.md'
    --exclude='.gitignore'
    --exclude='api/config.php.example'
    --exclude='assets/img/portfolio/_originals/'
    --exclude='_materials/'
    --exclude='preview.html'
    --exclude='.DS_Store'
    --exclude='Thumbs.db'
)

echo "→ rsync $REPO/ → $DOCROOT/"
rsync "${OPTS[@]}" "${EXCLUDES[@]}" "$REPO/" "$DOCROOT/"

if [ "$DRY" -eq 1 ]; then
    echo "✓ DRY-RUN завершён, на диске ничего не изменилось."
else
    # Подстраховка: _materials — внутренняя папка (паспорт, объявления и т.п.),
    # на публичном сайте её быть не должно. rsync --exclude не удаляет уже
    # лежащую на сервере копию, поэтому чистим её явно при каждой выкатке.
    rm -rf "$DOCROOT/_materials"
    echo "✓ Готово. Сайт обновлён в $DOCROOT/"
fi
