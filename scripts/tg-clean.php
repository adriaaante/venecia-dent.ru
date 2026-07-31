<?php
/**
 * Удаление последних СОБСТВЕННЫХ сообщений бота в группе заявок.
 *
 * Права администратора НЕ нужны: Telegram всегда разрешает боту удалять
 * то, что он отправил сам (заявки с сайта). Чужие сообщения при этом
 * не трогаются — попытка просто не проходит, и мы идём дальше.
 * Когда бот станет админом группы, удобнее пользоваться командой
 * /delete2 прямо в чате: она умеет удалять сообщения любых авторов.
 *
 * Запуск из корня репозитория:
 *   php scripts/tg-clean.php        — удалить 2 последних
 *   php scripts/tg-clean.php 5      — удалить 5 последних
 *
 * Как работает: узнать номер последнего сообщения через API нельзя,
 * поэтому бот отправляет служебное сообщение, берёт его номер и идёт
 * назад по номерам. Служебное сообщение удаляется за собой.
 *
 * ⚠️ Сообщения старше 48 часов Telegram удалять не даёт — это
 * ограничение API, обойти нечем.
 */

declare(strict_types=1);

$config = __DIR__ . '/../api/config.php';
if (!is_file($config)) {
    fwrite(STDERR, "Нет файла $config\n");
    exit(1);
}
require $config;

$want = isset($argv[1]) ? (int)$argv[1] : 2;
if ($want < 1) {
    $want = 1;
}
$scanLimit = 80; // сколько номеров назад просмотреть максимум

function tg(string $method, array $params): array
{
    $url = 'https://api.telegram.org/bot' . TELEGRAM_BOT_TOKEN . '/' . $method;
    $ch  = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_POST           => true,
        CURLOPT_POSTFIELDS     => json_encode($params, JSON_UNESCAPED_UNICODE),
        CURLOPT_HTTPHEADER     => ['Content-Type: application/json'],
        CURLOPT_TIMEOUT        => 15,
        CURLOPT_CONNECTTIMEOUT => 5,
    ]);
    $raw = curl_exec($ch);
    curl_close($ch);
    $decoded = json_decode((string)$raw, true);
    return is_array($decoded) ? $decoded : ['ok' => false, 'description' => 'нет ответа'];
}

$probe = tg('sendMessage', [
    'chat_id' => TELEGRAM_CHAT_ID,
    'text'    => 'Служебное сообщение: чищу последние заявки...',
]);

if (empty($probe['ok'])) {
    fwrite(STDERR, 'Не удалось отправить пробное сообщение: '
        . ($probe['description'] ?? '?') . "\n");
    fwrite(STDERR, "Проверьте токен и chat_id в api/config.php.\n");
    exit(1);
}

$lastId  = (int)$probe['result']['message_id'];
$deleted = 0;
$id      = $lastId - 1;
$scanned = 0;

while ($deleted < $want && $scanned < $scanLimit && $id > 0) {
    $r = tg('deleteMessage', ['chat_id' => TELEGRAM_CHAT_ID, 'message_id' => $id]);
    if (!empty($r['ok'])) {
        $deleted++;
        echo "  удалено сообщение #$id\n";
    }
    $id--;
    $scanned++;
}

// Убираем за собой служебное сообщение.
tg('deleteMessage', ['chat_id' => TELEGRAM_CHAT_ID, 'message_id' => $lastId]);

if ($deleted >= $want) {
    echo "Готово: удалено $want сообщений бота.\n";
} else {
    echo "Удалено $deleted из $want.\n";
    echo "Не удалились те, что старше 48 часов или отправлены не ботом.\n";
    echo "Чужие сообщения бот сможет удалять после выдачи прав администратора.\n";
}
