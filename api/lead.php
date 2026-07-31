<?php
/**
 * Венеция — приём заявок с сайта и пересылка в Telegram.
 *
 * Главная задача — не светить токен бота в публичном JS.
 * Браузер шлёт сюда POST с полями формы, PHP уже сам дёргает Telegram
 * API серверной curl-сессией. Токен живёт в api/config.php рядом
 * (его в git нет — заливается через scripts/deploy.sh из локального
 * scripts/.deploy.env).
 */

declare(strict_types=1);

// Защита от случайного вывода в config.php (BOM, пробелы перед <?php
// и т.п.): буферизуем всё, что PHP может выдать до reply(), чтобы потом
// гарантированно отдать чистый JSON. Без этого один невидимый байт в
// config.php ломает header()/http_response_code() и JSON приходит
// «загрязнённым» — клиент его не парсит, видит «Не удалось отправить».
ob_start();

header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');

function reply(int $code, array $body): void {
    // Сбрасываем любой случайный вывод (BOM, warnings, html_errors и т.п.),
    // чтобы клиенту ушёл чистый JSON, ничего больше.
    while (ob_get_level() > 0) {
        ob_end_clean();
    }
    http_response_code($code);
    header('Content-Type: application/json; charset=utf-8');
    header('Cache-Control: no-store');
    echo json_encode($body, JSON_UNESCAPED_UNICODE);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    reply(405, ['ok' => false, 'error' => 'method_not_allowed']);
}

$config = __DIR__ . '/config.php';
if (!is_file($config)) {
    reply(500, ['ok' => false, 'error' => 'config_missing']);
}
require $config;

if (!defined('TELEGRAM_BOT_TOKEN') || !defined('TELEGRAM_CHAT_ID')
    || TELEGRAM_BOT_TOKEN === '' || TELEGRAM_CHAT_ID === '') {
    reply(500, ['ok' => false, 'error' => 'config_incomplete']);
}

define('LEAD_APP', 1);
require __DIR__ . '/store.php';

// Тихий отказ: спамеру отвечаем «принято», чтобы он не начал подбирать
// формулировки. Заявка при этом никуда не уходит, а попытка пишется
// в журнал (файл spam.log в каталоге состояния).
function drop_silently(string $why, array $ctx = []): void {
    lead_log('spam.log', $why . ' | ' . json_encode($ctx, JSON_UNESCAPED_UNICODE));
    reply(200, ['ok' => true]);
}

// Honeypot: поле "company" скрыто от людей, боты его обычно заполняют.
// Если пришло непустым — молча подтверждаем и ничего не шлём.
if (!empty($_POST['company'] ?? '')) {
    drop_silently('honeypot');
}

// Серверная проверка телефона — страховка на случай, если JS-валидация
// обойдена (бот шлёт POST напрямую или скрипт не загрузился).
// Здесь отвечаем ошибкой, а не тихо: живой человек мог опечататься,
// и ему нужно об этом сказать.
$phoneRaw    = (string)($_POST['phone'] ?? '');
$phoneDigits = lead_normalize_phone($phoneRaw);
if (!lead_phone_is_valid($phoneDigits)) {
    lead_log('spam.log', 'bad_phone | ' . json_encode(['phone' => $phoneRaw], JSON_UNESCAPED_UNICODE));
    reply(400, ['ok' => false, 'error' => 'invalid_phone']);
}

// Чёрный список: номер добавляется командой /ban в Telegram-группе.
if (lead_is_blacklisted($phoneDigits)) {
    drop_silently('blacklist', ['phone' => $phoneDigits]);
}

// Контентные фильтры: ссылки, рекламная лексика, нечеловеческая скорость
// заполнения. Порог 3 балла — см. lead_spam_score() в store.php.
$elapsed = isset($_POST['_elapsed']) && ctype_digit((string)$_POST['_elapsed'])
    ? (int)$_POST['_elapsed']
    : -1;
list($spamScore, $spamReasons) = lead_spam_score([
    'name'    => (string)($_POST['name'] ?? ''),
    'message' => (string)($_POST['message'] ?? ''),
    'service' => (string)($_POST['service'] ?? ''),
], $elapsed);
if ($spamScore >= 3) {
    drop_silently('spam_content', [
        'score'   => $spamScore,
        'reasons' => $spamReasons,
        'phone'   => $phoneDigits,
        'name'    => mb_substr((string)($_POST['name'] ?? ''), 0, 80),
    ]);
}

// Частота с одного адреса: 3 заявки в час, 8 в сутки.
$clientIp = lead_client_ip();
if (!lead_rate_ok($clientIp)) {
    drop_silently('rate_limit', ['ip' => $clientIp, 'phone' => $phoneDigits]);
}


$labels = [
    'name'    => 'Имя',
    'phone'   => 'Телефон',
    'service' => 'Услуга',
    'message' => 'Комментарий',
];

$lines = ['🦷 *Заявка с сайта «Венеция»*', ''];
foreach ($_POST as $key => $value) {
    if ($key === 'company' || $key[0] === '_') continue;
    $value = trim((string)$value);
    if ($value === '') continue;
    // Ограничиваем длину поля: спам-бот с огромным текстом иначе «уронит»
    // сообщение целиком (Telegram отклоняет тексты длиннее 4096 символов).
    if (mb_strlen($value) > 500) {
        $value = mb_substr($value, 0, 500) . '…';
    }
    $label = $labels[$key] ?? $key;
    // Экранируем markdown-метасимволы, чтобы заявка не сломала форматирование.
    $escaped = preg_replace('/([*_`\[])/u', '\\\\$1', $value);
    $lines[] = '*' . $label . ':* ' . $escaped;
}

$page = trim((string)($_POST['_page'] ?? ''));
if ($page !== '') {
    // Нормализуем в полный URL (вдруг придёт только путь), чтобы ссылка
    // была кликабельной в Telegram — менеджер тапает и открывает страницу,
    // с которой оставили заявку.
    if (!preg_match('~^https?://~i', $page)) {
        $page = 'https://venecia-dent.ru/' . ltrim($page, '/');
    }
    // URL внутри скобок Markdown-ссылки чистим от пробелов и скобок,
    // текст ссылки экранируем от markdown-метасимволов.
    $pageUrl   = str_replace([' ', '(', ')'], ['%20', '%28', '%29'], $page);
    $pageLabel = preg_replace('/([*_`\[\]])/u', '\\\\$1', $page);
    $lines[] = '';
    $lines[] = '🔗 *Страница заявки:* [' . $pageLabel . '](' . $pageUrl . ')';
}

// Источник трафика: UTM-метки и yclid/gclid складываем отдельным блоком,
// чтобы менеджер сразу видел рекламный канал. yclid — клик-ID Яндекс.Директа,
// его же используют для офлайн-конверсий в Метрике (если решат загружать).
$trackingKeys = [
    '_utm_source'   => 'utm_source',
    '_utm_medium'   => 'utm_medium',
    '_utm_campaign' => 'utm_campaign',
    '_utm_term'     => 'utm_term',
    '_utm_content'  => 'utm_content',
    '_yclid'        => 'yclid',
    '_gclid'        => 'gclid',
];
$trackingLines = [];
foreach ($trackingKeys as $postKey => $label) {
    $value = trim((string)($_POST[$postKey] ?? ''));
    if ($value === '') continue;
    // Оборачиваем значение в inline-code (`), внутри которого Markdown
    // не парсится, поэтому экранируем только сам backtick — иначе
    // UTM с подчёркиваниями (implant_msk) ломались бы.
    $clean = str_replace('`', "'", $value);
    $trackingLines[] = '`' . $label . '`: ' . $clean;
}
if (!empty($trackingLines)) {
    $lines[] = '';
    $lines[] = '📊 *Источник:*';
    foreach ($trackingLines as $tl) $lines[] = $tl;
}

$referrer = trim((string)($_POST['_referrer'] ?? ''));
if ($referrer !== '') {
    $lines[] = '_Реферер: ' . preg_replace('/[*_`\[]/u', '', $referrer) . '_';
}

$payload = json_encode([
    'chat_id'                  => TELEGRAM_CHAT_ID,
    'text'                     => implode("\n", $lines),
    'parse_mode'               => 'Markdown',
    'disable_web_page_preview' => true,
], JSON_UNESCAPED_UNICODE);

$url = 'https://api.telegram.org/bot' . TELEGRAM_BOT_TOKEN . '/sendMessage';
$ch = curl_init($url);
curl_setopt_array($ch, [
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_POST           => true,
    CURLOPT_POSTFIELDS     => $payload,
    CURLOPT_HTTPHEADER     => ['Content-Type: application/json'],
    CURLOPT_TIMEOUT        => 10,
    CURLOPT_CONNECTTIMEOUT => 5,
]);
$response = curl_exec($ch);
$httpCode = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE);
$curlErr  = curl_error($ch);
curl_close($ch);

if ($httpCode >= 200 && $httpCode < 300 && $response !== false) {
    $decoded = json_decode($response, true);
    if (is_array($decoded) && !empty($decoded['ok'])) {
        // Запоминаем id отправленного сообщения: по нему команда /delete
        // в группе понимает, что именно является заявками, и может
        // отчитаться, сколько их осталось.
        $mid = (int)($decoded['result']['message_id'] ?? 0);
        if ($mid > 0) {
            $sent = lead_json_read('sent.json', []);
            $sent[] = ['id' => $mid, 'ts' => time(), 'phone' => $phoneDigits];
            if (count($sent) > 200) {
                $sent = array_slice($sent, -200);
            }
            lead_json_write('sent.json', $sent);
        }
        reply(200, ['ok' => true]);
    }
}


// Логируем в error_log, но клиенту деталей не отдаём.
error_log('[venecia-dent lead] telegram failed: http=' . $httpCode
    . ' err=' . $curlErr . ' resp=' . substr((string)$response, 0, 500));
reply(502, ['ok' => false, 'error' => 'telegram_unreachable']);
