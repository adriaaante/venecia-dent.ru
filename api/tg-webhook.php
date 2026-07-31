<?php
/**
 * Приём команд от Telegram-бота заявок (webhook).
 *
 * Telegram шлёт сюда POST с обновлением. Отвечаем командами управления
 * группой заявок:
 *
 *   /delete2, /delete 2, /deleted2   — удалить 2 последних сообщения У ВСЕХ
 *   /ban +7 999 123-45-67            — не пропускать заявки с этого номера
 *   /ban  (ответом на заявку)        — номер берётся из самой заявки
 *   /unban +7 999 123-45-67          — вернуть номер
 *   /banlist                         — показать чёрный список
 *   /help                            — подсказка по командам
 *
 * Подключение (один раз, из шелла на сервере):
 *   curl -s "https://api.telegram.org/bot<ТОКЕН>/setWebhook" \
 *        -d "url=https://venecia-dent.ru/api/tg-webhook.php" \
 *        -d "secret_token=<TELEGRAM_WEBHOOK_SECRET из config.php>" \
 *        -d "allowed_updates=[\"message\"]"
 *
 * Безопасность: Telegram присылает секрет в заголовке
 * X-Telegram-Bot-Api-Secret-Token, мы его сверяем. Дополнительно команды
 * принимаются только из чата TELEGRAM_CHAT_ID (группа заявок), а если
 * задан TELEGRAM_ADMIN_IDS — то и только от перечисленных пользователей.
 *
 * Ограничение Telegram, которое не обойти: бот может удалять сообщения
 * не старше 48 часов и только будучи администратором группы с правом
 * «Удаление сообщений».
 */

declare(strict_types=1);

define('LEAD_APP', 1);

header('Content-Type: application/json; charset=utf-8');

$config = __DIR__ . '/config.php';
if (!is_file($config)) {
    http_response_code(500);
    exit;
}
require $config;
require __DIR__ . '/store.php';

/* ---------- Проверка, что запрос действительно от Telegram ---------- */

$secret = defined('TELEGRAM_WEBHOOK_SECRET') ? (string)TELEGRAM_WEBHOOK_SECRET : '';
$given  = (string)($_SERVER['HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN'] ?? '');
if ($secret === '' || !hash_equals($secret, $given)) {
    http_response_code(403);
    echo '{"ok":false}';
    exit;
}

$update = json_decode((string)file_get_contents('php://input'), true);
if (!is_array($update)) {
    echo '{"ok":true}';
    exit;
}

$msg = $update['message'] ?? $update['edited_message'] ?? null;
if (!is_array($msg)) {
    echo '{"ok":true}';
    exit;
}

$chatId = (string)($msg['chat']['id'] ?? '');
$fromId = (string)($msg['from']['id'] ?? '');
$text   = trim((string)($msg['text'] ?? ''));

// Команды принимаем только из рабочей группы заявок.
if ($chatId === '' || $chatId !== (string)TELEGRAM_CHAT_ID) {
    echo '{"ok":true}';
    exit;
}

// Необязательное сужение до конкретных людей.
if (defined('TELEGRAM_ADMIN_IDS')) {
    $admins = is_array(TELEGRAM_ADMIN_IDS)
        ? TELEGRAM_ADMIN_IDS
        : array_filter(array_map('trim', explode(',', (string)TELEGRAM_ADMIN_IDS)));
    if ($admins && !in_array($fromId, array_map('strval', $admins), true)) {
        echo '{"ok":true}';
        exit;
    }
}

if ($text === '' || $text[0] !== '/') {
    echo '{"ok":true}';
    exit;
}

/* ---------- Обращение к Telegram API ---------- */

function tg(string $method, array $params): array
{
    $ch = curl_init('https://api.telegram.org/bot' . TELEGRAM_BOT_TOKEN . '/' . $method);
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_POST           => true,
        CURLOPT_POSTFIELDS     => json_encode($params, JSON_UNESCAPED_UNICODE),
        CURLOPT_HTTPHEADER     => ['Content-Type: application/json'],
        CURLOPT_TIMEOUT        => 10,
        CURLOPT_CONNECTTIMEOUT => 5,
    ]);
    $raw = curl_exec($ch);
    curl_close($ch);
    $decoded = json_decode((string)$raw, true);
    return is_array($decoded) ? $decoded : ['ok' => false];
}

function tg_say(string $chatId, string $text): void
{
    tg('sendMessage', [
        'chat_id'                  => $chatId,
        'text'                     => $text,
        'parse_mode'               => 'Markdown',
        'disable_web_page_preview' => true,
    ]);
}

function tg_drop(string $chatId, int $messageId): bool
{
    $r = tg('deleteMessage', ['chat_id' => $chatId, 'message_id' => $messageId]);
    return !empty($r['ok']);
}

/* ---------- Разбор команды ---------- */

// Поддерживаем и /delete2, и /delete 2, и /delete2@ИмяБота.
if (!preg_match('~^/([a-zA-Zа-яА-Я_]+)(\d*)(?:@\S+)?\s*(.*)$~us', $text, $m)) {
    echo '{"ok":true}';
    exit;
}
$cmd      = mb_strtolower($m[1], 'UTF-8');
$cmdDigit = $m[2];
$args     = trim((string)($m[3] ?? ''));
$cmdMsgId = (int)($msg['message_id'] ?? 0);
$replyTxt = (string)($msg['reply_to_message']['text'] ?? '');

switch ($cmd) {

    /* --- Удаление последних N сообщений --- */
    case 'delete':
    case 'deleted':
    case 'del':
    case 'удалить':
        $n = $cmdDigit !== '' ? (int)$cmdDigit : (int)preg_replace('/\D/', '', $args);
        if ($n < 1) {
            $n = 1;
        }
        $n = min($n, 50);

        // Идём назад от самой команды: id сообщений в группе идут подряд,
        // поэтому предыдущие — это и есть «последние сообщения». Часть id
        // может не удалиться (сервисные события, чужие боты, возраст свыше
        // 48 часов) — такие пропускаем и берём следующее.
        $deleted = 0;
        $probe   = $cmdMsgId - 1;
        $tries   = 0;
        while ($deleted < $n && $tries < $n + 30 && $probe > 0) {
            if (tg_drop($chatId, $probe)) {
                $deleted++;
            }
            $probe--;
            $tries++;
        }

        tg_drop($chatId, $cmdMsgId); // убираем и саму команду

        if ($deleted < $n) {
            tg_say($chatId, "🗑 Удалено *{$deleted}* из *{$n}*.\n"
                . "Остальные удалить не вышло. Обычно причина одна из двух: "
                . "сообщение старше 48 часов (ограничение Telegram, обойти нельзя) "
                . "или у бота нет права «Удаление сообщений» — проверьте, "
                . "что он администратор группы.");
        }
        break;

    /* --- Чёрный список: добавить --- */
    case 'ban':
    case 'бан':
    case 'blacklist':
        $phone = lead_extract_phone($args !== '' ? $args : $replyTxt);
        if ($phone === '') {
            tg_say($chatId, "⚠️ Не понял номер.\n"
                . "Напишите `/ban +7 999 123-45-67` "
                . "или ответьте командой `/ban` на сообщение с заявкой.");
            break;
        }
        $added = lead_blacklist_add($phone);
        tg_drop($chatId, $cmdMsgId);
        tg_say($chatId, $added
            ? "⛔️ Номер *" . lead_format_phone($phone) . "* в чёрном списке. "
              . "Заявки с него в группу больше не придут."
            : "ℹ️ Номер *" . lead_format_phone($phone) . "* уже был в списке.");
        break;

    /* --- Чёрный список: убрать --- */
    case 'unban':
    case 'разбан':
        $phone = lead_extract_phone($args !== '' ? $args : $replyTxt);
        if ($phone === '') {
            tg_say($chatId, "⚠️ Не понял номер. Пример: `/unban +7 999 123-45-67`");
            break;
        }
        $removed = lead_blacklist_remove($phone);
        tg_drop($chatId, $cmdMsgId);
        tg_say($chatId, $removed
            ? "✅ Номер *" . lead_format_phone($phone) . "* убран из чёрного списка."
            : "ℹ️ Номера *" . lead_format_phone($phone) . "* в списке не было.");
        break;

    /* --- Чёрный список: показать --- */
    case 'banlist':
    case 'bans':
    case 'список':
        $list = lead_blacklist();
        if (!$list) {
            tg_say($chatId, "Чёрный список пуст.");
            break;
        }
        $out = ["⛔️ *В чёрном списке (" . count($list) . "):*"];
        foreach (array_slice($list, -50) as $p) {
            $out[] = '• ' . lead_format_phone($p);
        }
        tg_say($chatId, implode("\n", $out));
        break;

    /* --- Подсказка --- */
    case 'help':
    case 'start':
    case 'помощь':
        tg_say($chatId,
            "*Команды группы заявок*\n\n"
            . "`/delete3` — удалить 3 последних сообщения у всех "
            . "(можно и через пробел: `/delete 3`)\n"
            . "`/ban +7 999 123-45-67` — заявки с этого номера больше не приходят\n"
            . "`/ban` ответом на заявку — то же, номер возьмётся из неё\n"
            . "`/unban +7 999 123-45-67` — вернуть номер\n"
            . "`/banlist` — показать чёрный список\n\n"
            . "_Удалять можно сообщения не старше 48 часов — это ограничение "
            . "Telegram. Боту нужны права администратора группы._");
        break;
}

echo '{"ok":true}';
