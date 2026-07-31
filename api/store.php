<?php
/**
 * Общее хранилище и анти-спам-логика для api/lead.php и api/tg-webhook.php.
 *
 * ВАЖНО про место хранения. Состояние (чёрный список, счётчики лимитов,
 * журнал отправленных сообщений) лежит НЕ в публичной папке сайта, а рядом
 * с домашним каталогом. Причина: deploy.sh синхронизирует репозиторий в
 * ~/www/<домен>/ через `rsync --delete`, и любой файл, созданный в публичной
 * папке во время работы сайта, был бы снесён при следующей выкатке. Плюс
 * каталог вне docroot физически недоступен по HTTP.
 *
 * Путь по умолчанию: <домашний каталог>/.leadstate-<домен>
 * Переопределяется константой LEAD_STATE_DIR в api/config.php.
 */

declare(strict_types=1);

// Файл подключается только из lead.php / tg-webhook.php. Прямой вызов из
// браузера ничего не должен отдавать.
if (!defined('LEAD_APP')) {
    http_response_code(403);
    exit;
}

/* ============================================================
   Файловое состояние
   ============================================================ */

function lead_state_dir(): string
{
    static $cached = null;
    if ($cached !== null) {
        return $cached;
    }

    if (defined('LEAD_STATE_DIR') && LEAD_STATE_DIR !== '') {
        $dir = rtrim((string)LEAD_STATE_DIR, '/');
    } else {
        // .../www/<домен>/api → на три уровня вверх это домашний каталог.
        $dir = dirname(__DIR__, 3) . '/.leadstate-' . basename(dirname(__DIR__));
    }

    if (!is_dir($dir)) {
        @mkdir($dir, 0700, true);
    }
    if (!is_dir($dir) || !is_writable($dir)) {
        // Не смогли создать — не роняем приём заявок, уходим во временный
        // каталог. Чёрный список там переживёт меньше, но заявки не потеряем.
        $dir = sys_get_temp_dir() . '/leadstate-' . substr(md5($dir), 0, 12);
        if (!is_dir($dir)) {
            @mkdir($dir, 0700, true);
        }
    }

    return $cached = $dir;
}

function lead_file(string $name): string
{
    return lead_state_dir() . '/' . $name;
}

function lead_json_read(string $name, array $default = []): array
{
    $f = lead_file($name);
    if (!is_file($f)) {
        return $default;
    }
    $raw = @file_get_contents($f);
    if ($raw === false || $raw === '') {
        return $default;
    }
    $data = json_decode($raw, true);
    return is_array($data) ? $data : $default;
}

function lead_json_write(string $name, array $data): void
{
    $f = lead_file($name);
    @file_put_contents(
        $f,
        json_encode($data, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT),
        LOCK_EX
    );
    @chmod($f, 0600);
}

function lead_log(string $name, string $line): void
{
    $f = lead_file($name);
    @file_put_contents($f, date('c') . ' ' . $line . "\n", FILE_APPEND | LOCK_EX);
    @chmod($f, 0600);
    // Не даём журналу расти бесконечно: раз в сотню записей подрезаем хвост.
    if (@filesize($f) > 512 * 1024) {
        $lines = @file($f, FILE_IGNORE_NEW_LINES) ?: [];
        @file_put_contents($f, implode("\n", array_slice($lines, -500)) . "\n", LOCK_EX);
    }
}

/* ============================================================
   Телефон
   ============================================================ */

/** Приводит номер к 11 цифрам вида 7XXXXXXXXXX. Пустая строка = не разобрали. */
function lead_normalize_phone(string $raw): string
{
    $d = preg_replace('/\D/', '', $raw);
    if ($d === '') {
        return '';
    }
    if (strlen($d) === 11 && $d[0] === '8') {
        $d = '7' . substr($d, 1);
    }
    if (strlen($d) === 10) {
        $d = '7' . $d;
    }
    return $d;
}

/**
 * Проверка «это вообще похоже на настоящий российский номер».
 * Ловит и спам-заглушки вроде +7 (799) 900-00-00, и наши плейсхолдеры
 * +7 (000) 000-00-00, которые бот мог подцепить со страницы.
 */
function lead_phone_is_valid(string $digits): bool
{
    if (strlen($digits) !== 11 || $digits[0] !== '7') {
        return false;
    }
    // Действующие российские коды начинаются с 3, 4, 8 (география) и 9
    // (мобильные). Коды на 7 — это Казахстан, на 0/1/2/5/6 не выдаются.
    if (!in_array($digits[1], ['3', '4', '8', '9'], true)) {
        return false;
    }
    $rest = substr($digits, 1);
    // 79999999999 и подобное — одна цифра на весь номер.
    if (preg_match('/^(\d)\1{9}$/', $rest)) {
        return false;
    }
    // Хвост из нулей: 7 900 000-00-00 и т.п.
    if (preg_match('/0{7,}/', $digits)) {
        return false;
    }
    return true;
}

/** Вытаскивает первый телефоноподобный кусок из произвольного текста. */
function lead_extract_phone(string $text): string
{
    if (preg_match('/(?:\+?[78])[\s\-()]*\d{3}[\s\-()]*\d{3}[\s\-]*\d{2}[\s\-]*\d{2}/u', $text, $m)) {
        return lead_normalize_phone($m[0]);
    }
    return '';
}

/* ============================================================
   Чёрный список номеров
   ============================================================ */

function lead_blacklist(): array
{
    $list = lead_json_read('blacklist.json', []);
    return array_values(array_filter(array_map('strval', $list)));
}

function lead_is_blacklisted(string $digits): bool
{
    return $digits !== '' && in_array($digits, lead_blacklist(), true);
}

function lead_blacklist_add(string $digits): bool
{
    if ($digits === '') {
        return false;
    }
    $list = lead_blacklist();
    if (in_array($digits, $list, true)) {
        return false;
    }
    $list[] = $digits;
    lead_json_write('blacklist.json', $list);
    return true;
}

function lead_blacklist_remove(string $digits): bool
{
    $list = lead_blacklist();
    $new  = array_values(array_diff($list, [$digits]));
    if (count($new) === count($list)) {
        return false;
    }
    lead_json_write('blacklist.json', $new);
    return true;
}

/** 79104588808 → +7 (910) 458-88-08 */
function lead_format_phone(string $digits): string
{
    if (strlen($digits) !== 11) {
        return $digits;
    }
    return sprintf(
        '+7 (%s) %s-%s-%s',
        substr($digits, 1, 3),
        substr($digits, 4, 3),
        substr($digits, 7, 2),
        substr($digits, 9, 2)
    );
}

/* ============================================================
   Ограничение частоты по IP
   ============================================================ */

function lead_client_ip(): string
{
    $remote = (string)($_SERVER['REMOTE_ADDR'] ?? '');
    // За прокси reg.ru REMOTE_ADDR может быть локальным — тогда берём
    // заголовок. В остальных случаях доверяем только REMOTE_ADDR:
    // X-Forwarded-For подделывается, и лимит по нему обходится тривиально.
    $isLocal = $remote === '' || filter_var(
        $remote,
        FILTER_VALIDATE_IP,
        FILTER_FLAG_NO_PRIV_RANGE | FILTER_FLAG_NO_RES_RANGE
    ) === false;

    if ($isLocal) {
        $fwd = (string)($_SERVER['HTTP_X_REAL_IP'] ?? $_SERVER['HTTP_X_FORWARDED_FOR'] ?? '');
        if ($fwd !== '') {
            $first = trim(explode(',', $fwd)[0]);
            if (filter_var($first, FILTER_VALIDATE_IP) !== false) {
                return $first;
            }
        }
    }
    return $remote !== '' ? $remote : 'unknown';
}

/**
 * true — заявку принимаем. Лимиты: 3 в час и 8 в сутки с одного адреса.
 * Живому человеку столько не нужно, а рассыльщику мешает.
 */
function lead_rate_ok(string $ip, int $perHour = 3, int $perDay = 8): bool
{
    $now  = time();
    $key  = substr(md5($ip), 0, 16);
    $data = lead_json_read('rate.json', []);

    // Чистим протухшее, заодно не даём файлу расти.
    foreach ($data as $k => $stamps) {
        $keep = array_values(array_filter((array)$stamps, function ($t) use ($now) {
            return is_int($t) && $t > $now - 86400;
        }));
        if ($keep) {
            $data[$k] = $keep;
        } else {
            unset($data[$k]);
        }
    }

    $mine  = $data[$key] ?? [];
    $hour  = count(array_filter($mine, function ($t) use ($now) { return $t > $now - 3600; }));
    $day   = count($mine);

    if ($hour >= $perHour || $day >= $perDay) {
        lead_json_write('rate.json', $data);
        return false;
    }

    $mine[]      = $now;
    $data[$key]  = $mine;
    lead_json_write('rate.json', $data);
    return true;
}

/* ============================================================
   Контентные фильтры
   ============================================================ */

/**
 * Оценка «насколько это похоже на рекламную рассылку».
 * Возвращает [score, reasons[]]. Блокируем от 3 баллов.
 *
 * Логика подобрана по реальному спаму (SEO-рассылка, июль 2026): ссылка
 * или домен в любом поле — верный признак, живой пациент их не пишет.
 */
function lead_spam_score(array $fields, int $elapsedMs = -1): array
{
    $score   = 0;
    $reasons = [];
    $all     = mb_strtolower(implode("\n", array_map('strval', $fields)), 'UTF-8');

    // 1. Ссылки, домены, телеграм-ники, почта — главный маркер.
    $linkRe = '~(https?://|www\.|t\.me/|@[a-z0-9_.-]{4,}|\b[a-z0-9-]{2,}\.(?:ru|com|net|org|su|io|biz|info|site|online|store|shop|рф)\b)~iu';
    if (preg_match($linkRe, $all)) {
        $score += 3;
        $reasons[] = 'ссылка/домен в тексте';
    }

    // 2. Лексика коммерческих рассылок.
    $words = [
        'продвижен', 'сео', 'seo', 'трафик', 'аудит', 'коммерческое предложение',
        'сотрудничеств', 'разработка сайт', 'доработ', 'маркетинг', 'лидов', 'лиды',
        'конверси', 'воронк', 'таргет', 'рассылк', 'франшиз', 'инвестиц',
        'займ', 'кредит', 'подписк', 'seo-продвижение', 'яндекс картах',
        'теряете клиентов', 'терять клиентов', 'инструмент продаж', 'бесплатный',
        'вебинар', 'обучени', 'курс', 'crm', 'битрикс', 'поставщик', 'оптом',
    ];
    $hits = 0;
    foreach ($words as $w) {
        if (mb_strpos($all, $w, 0, 'UTF-8') !== false) {
            $hits++;
        }
    }
    if ($hits > 0) {
        $score += min($hits, 4);
        $reasons[] = 'рекламных слов: ' . $hits;
    }

    // 3. Длинный текст. Пациент пишет пару строк, рассыльщик — простыню.
    $msgLen = mb_strlen((string)($fields['message'] ?? ''), 'UTF-8');
    if ($msgLen > 700) {
        $score += 2;
        $reasons[] = 'длина комментария ' . $msgLen;
    }

    // 4. Имя длиннее человеческого или с цифрами — тоже признак.
    $name = (string)($fields['name'] ?? '');
    if (mb_strlen($name, 'UTF-8') > 60 || preg_match('/\d{3,}/u', $name)) {
        $score += 2;
        $reasons[] = 'подозрительное имя';
    }

    // 5. Форма заполнена быстрее, чем физически успевает человек.
    // Учитываем только если значение пришло: у посетителя со старым
    // закэшированным main.js поля не будет, и наказывать его не за что.
    if ($elapsedMs >= 0 && $elapsedMs < 2500) {
        $score += 3;
        $reasons[] = 'форма заполнена за ' . $elapsedMs . ' мс';
    }

    return [$score, $reasons];
}
