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
 * Частота заявок с одного адреса. Возвращает:
 *   'ok'   — обычная заявка;
 *   'mark' — многовато, но доставляем с пометкой ⚠️ (НЕ теряем);
 *   'drop' — явный поток, отбрасываем.
 *
 * ⚠️ Пороги специально высокие. Мобильные операторы прячут тысячи
 * абонентов за одним IP (CGNAT), поэтому «3 заявки в час с адреса»
 * резали бы живых пациентов с телефона. Между «пропустить немного
 * спама» и «потерять пациента» выбираем первое: до 40 в час заявка
 * всё равно дойдёт, просто с пометкой.
 */
function lead_rate_status(string $ip): string
{
    $now  = time();
    $key  = substr(md5($ip), 0, 16);
    $data = lead_json_read('rate.json', []);

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

    $mine = $data[$key] ?? [];
    $hour = count(array_filter($mine, function ($t) use ($now) { return $t > $now - 3600; }));
    $day  = count($mine);

    $mine[]     = $now;
    $data[$key] = $mine;
    lead_json_write('rate.json', $data);

    if ($hour > 40 || $day > 120) {
        return 'drop';
    }
    if ($hour > 12) {
        return 'mark';
    }
    return 'ok';
}

/** Оставлено для обратной совместимости, сейчас не используется. */
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
 * Возвращает [score, reasons[]]. Блокируем от LEAD_SPAM_THRESHOLD баллов.
 *
 * ⚠️ ГЛАВНЫЙ ПРИНЦИП (важнее, чем поймать весь спам): потерять живого
 * пациента нельзя. Поэтому признаки разделены на два класса:
 *
 *   ЖЁСТКИЕ (+3, блокируют сами по себе) — то, чего пациент не пишет
 *   в принципе: ссылка, голый домен, рекламный оборот из двух-трёх слов,
 *   отправка быстрее полутора секунд.
 *
 *   МЯГКИЕ (+1, суммарно НЕ БОЛЬШЕ 2) — косвенные приметы. Их потолок
 *   специально ниже порога: сколько бы мягких признаков ни совпало,
 *   заявка без жёсткого признака НИКОГДА не будет отброшена молча.
 *
 * Так закрыт реальный провал первой версии: развёрнутая заявка пожилой
 * пациентки («я инвалид, назначили курс лечения, можно в кредит, есть
 * ли бесплатный осмотр») набирала 6 баллов и пропадала — слова «инвалидов»,
 * «курс», «кредит», «бесплатный» ловились как рекламные.
 */
const LEAD_SPAM_THRESHOLD = 3;
const LEAD_SOFT_CAP       = 2;   // потолок мягких признаков — ниже порога

function lead_spam_score(array $fields, int $elapsedMs = -1): array
{
    $score   = 0;
    $reasons = [];
    $soft    = 0;
    $all     = mb_strtolower(implode("\n", array_map('strval', $fields)), 'UTF-8');

    // Почту вырезаем из текста ДО поиска доменов: пациент вполне может
    // написать «пришлите план на olga@mail.ru», и домен из адреса не должен
    // выглядеть как ссылка рекламщика.
    $hasEmail = (bool)preg_match('~[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}~iu', $all);
    $noEmail  = preg_replace('~[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}~iu', ' ', $all);

    /* ---------- ЖЁСТКИЕ признаки ---------- */

    // Ссылка целиком.
    if (preg_match('~(https?://|www\.|t\.me/)~iu', $noEmail)) {
        $score += 3;
        $reasons[] = 'ссылка в тексте';
    }

    // Голый домен вне почты — как «angel-denta.ru» в поле «Имя» у той рассылки.
    if (preg_match('~\b[a-z0-9-]{2,}\.(?:ru|com|net|org|su|io|biz|info|site|online|store|shop|рф)\b~iu', $noEmail)) {
        $score += 3;
        $reasons[] = 'домен в тексте';
    }

    // Обороты, которые встречаются только в коммерческих рассылках.
    // Каждый — из нескольких слов, случайно у пациента не появится.
    $phrases = [
        'коммерческое предложение', 'seo-продвижение', 'сео-продвижение',
        'продвижение сайта', 'продвижение сайтов', 'разработка сайтов',
        'разработка сайта', 'бесплатный аудит', 'бесплатный анализ',
        'конкурентный анализ', 'терять клиентов', 'теряете клиентов',
        'теряете заявки', 'инструмент продаж', 'увеличить продажи',
        'вывести в топ', 'первые позиции', 'настройка рекламы',
        'настрою рекламу', 'веду сайты', 'беру сайт на поддержку',
        'предлагаю сотрудничество', 'взаимовыгодное сотрудничество',
    ];
    foreach ($phrases as $p) {
        if (mb_strpos($all, $p, 0, 'UTF-8') !== false) {
            $score += 3;
            $reasons[] = 'рекламный оборот «' . $p . '»';
            break;
        }
    }

    // Отправлено быстрее, чем человек физически успевает заполнить форму.
    // Порог намеренно низкий (1,5 с): даже с автозаполнением браузера живой
    // человек не укладывается, а ошибиться тут дороже, чем пропустить бота.
    if ($elapsedMs >= 0 && $elapsedMs < 1500) {
        $score += 3;
        $reasons[] = 'отправлено за ' . $elapsedMs . ' мс';
    }

    /* ---------- МЯГКИЕ признаки (суммарно не больше LEAD_SOFT_CAP) ---------- */

    // Словарь вычищен от всего, что нормально для стоматологии:
    // «кредит»/«рассрочка» (спрашивают про импланты), «курс» (курс лечения),
    // «бесплатный» (у клиники есть бесплатная консультация), «обучение»
    // (обучение гигиене), «лиды» (ловилось внутри слова «инвалидов»).
    $words = [
        'продвижен', 'трафик', 'сотрудничеств', 'маркетинг', 'конверси',
        'воронк', 'таргет', 'рассылк', 'франшиз', 'инвестиц', 'вебинар',
        'битрикс', 'оптом', 'поставщик', 'закупк', 'тендер',
    ];
    $hits = 0;
    foreach ($words as $w) {
        if (mb_strpos($all, $w, 0, 'UTF-8') !== false) {
            $hits++;
        }
    }
    // Короткие латинские аббревиатуры — только как отдельные слова,
    // иначе «seo» найдётся внутри случайной строки.
    foreach (['seo', 'crm', 'смм', 'smm'] as $w) {
        if (preg_match('~\b' . $w . '\b~iu', $all)) {
            $hits++;
        }
    }
    if ($hits > 0) {
        $soft += $hits;
        $reasons[] = 'рекламных слов: ' . $hits;
    }

    // Телеграм-ник сам по себе — НЕ признак: пациент может оставить свой
    // ник для связи. А вот ник вместе с рекламным словом у пациента
    // не встречается — это уже рассылка «пишите @seo_pro, обсудим продвижение».
    $hasNick = (bool)preg_match('~(?<![a-z0-9_])@[a-z0-9_]{4,}~iu', $noEmail);
    if ($hasNick && $hits > 0) {
        $score += 3;
        $reasons[] = 'ник + рекламная лексика';
    } elseif ($hasNick) {
        $soft += 1;
        $reasons[] = 'ник в тексте';
    }

    if ($hasEmail) {
        $soft += 1;
        $reasons[] = 'почта в тексте';
    }

    // Очень длинный комментарий. Порог поднят: развёрнутая история болезни
    // на 900 символов — обычное дело, особенно у пожилых пациентов.
    $msgLen = mb_strlen((string)($fields['message'] ?? ''), 'UTF-8');
    if ($msgLen > 1200) {
        $soft += 1;
        $reasons[] = 'длина комментария ' . $msgLen;
    }

    // Имя не бывает длинным и не состоит из цифр. Но телефон, вписанный
    // в поле «Имя», — обычное поведение живого человека, поэтому мягко.
    $name = (string)($fields['name'] ?? '');
    if (mb_strlen($name, 'UTF-8') > 60) {
        $soft += 1;
        $reasons[] = 'слишком длинное имя';
    }

    $score += min($soft, LEAD_SOFT_CAP);

    return [$score, $reasons];
}
