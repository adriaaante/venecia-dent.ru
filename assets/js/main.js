(function () {
  'use strict';

  // ---------------------------------------------------------------------------
  // Яндекс.Метрика — цели для Директа. Счётчик подключается в <head> каждой
  // страницы; здесь только программная отправка целей.
  //
  //   lead_submit     — МАКРО. Успешная отправка формы заявки.
  //   call_click      — МАКРО. Клик по tel:-ссылке.
  //   whatsapp_click  — МАКРО. Клик по wa.me/...
  //   telegram_click  — МАКРО. Клик по t.me/...
  //   modal_open      — МИКРО. Открытие модалки «Записаться».
  //   form_start      — МИКРО. Первый фокус в поле формы.
  //
  // Те же идентификаторы завести в кабинете Метрики (Цели → JavaScript-событие).
  // ---------------------------------------------------------------------------
  // TODO: заменить на реальный id счётчика Метрики (сейчас placeholder,
  // тот же id — в блоке <!-- Yandex.Metrika counter --> в <head> всех страниц).
  var YM_COUNTER_ID = 0;
  function trackGoal(name, params) {
    if (typeof window.ym !== 'function' || !YM_COUNTER_ID) return;
    try {
      if (params) {
        window.ym(YM_COUNTER_ID, 'reachGoal', name, params);
      } else {
        window.ym(YM_COUNTER_ID, 'reachGoal', name);
      }
    } catch (e) { /* счётчик не загрузился — игнорим */ }
  }

  // UTM/yclid/gclid запоминаем при первом заходе и прикладываем к заявке.
  var TRACKED_PARAMS = [
    'utm_source', 'utm_medium', 'utm_campaign',
    'utm_term', 'utm_content',
    'yclid', 'gclid', 'ym_uid'
  ];
  function captureTrackingParams() {
    if (!window.sessionStorage) return;
    var url;
    try { url = new URL(window.location.href); } catch (e) { return; }
    TRACKED_PARAMS.forEach(function (key) {
      var value = url.searchParams.get(key);
      if (value && !sessionStorage.getItem('vd_' + key)) {
        try { sessionStorage.setItem('vd_' + key, value); } catch (e) {}
      }
    });
  }
  function getTrackingParams() {
    var out = {};
    if (!window.sessionStorage) return out;
    TRACKED_PARAMS.forEach(function (key) {
      var value;
      try { value = sessionStorage.getItem('vd_' + key); } catch (e) { value = null; }
      if (value) out[key] = value;
    });
    return out;
  }
  captureTrackingParams();

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  function init() {

  // Мобильное меню
  var burger = document.querySelector('[data-burger]');
  var nav = document.querySelector('[data-nav]');
  if (burger && nav) {
    burger.addEventListener('click', function () {
      nav.classList.toggle('is-open');
    });
  }

  // Маска телефона +7 (XXX) XXX-XX-XX. Полный номер — 11 цифр.
  var PHONE_FULL_DIGITS = 11;
  function phoneDigits(value) {
    return (value || '').replace(/\D/g, '');
  }
  function syncPhoneValidity(input) {
    var n = phoneDigits(input.value).length;
    if (n <= 1) {
      input.setCustomValidity('');
    } else if (n < PHONE_FULL_DIGITS) {
      input.setCustomValidity('Введите номер телефона полностью: +7 (XXX) XXX-XX-XX');
    } else {
      input.setCustomValidity('');
    }
  }
  function maskPhone(input) {
    input.addEventListener('input', function (e) {
      var digits = e.target.value.replace(/\D/g, '');
      if (digits.startsWith('8')) digits = '7' + digits.slice(1);
      if (!digits.startsWith('7')) digits = '7' + digits;
      digits = digits.slice(0, 11);
      var out = '+7';
      if (digits.length > 1) out += ' (' + digits.slice(1, 4);
      if (digits.length >= 5) out += ') ' + digits.slice(4, 7);
      if (digits.length >= 8) out += '-' + digits.slice(7, 9);
      if (digits.length >= 10) out += '-' + digits.slice(9, 11);
      e.target.value = out;
      syncPhoneValidity(e.target);
    });
    input.addEventListener('focus', function (e) {
      if (!e.target.value) e.target.value = '+7 (';
    });
    input.addEventListener('blur', function (e) {
      if (phoneDigits(e.target.value).length <= 1) e.target.value = '';
      syncPhoneValidity(e.target);
    });
  }
  document.querySelectorAll('input[type="tel"]').forEach(maskPhone);

  // Отправка заявки — POST в /api/lead.php (токен бота только на сервере).
  function sendLead(form) {
    var fd = new FormData(form);
    fd.append('_page', location.origin + (location.pathname || '/'));
    fd.append('_referrer', document.referrer || '');
    var tracking = getTrackingParams();
    Object.keys(tracking).forEach(function (key) {
      fd.append('_' + key, tracking[key]);
    });
    return fetch('/api/lead.php', { method: 'POST', body: fd })
      .then(function (r) {
        return r.json().then(function (d) {
          return d && d.ok ? d : Promise.reject(d);
        });
      });
  }

  document.querySelectorAll('form[data-form]').forEach(function (form) {
    var formStarted = false;
    form.addEventListener('focusin', function (e) {
      if (formStarted) return;
      if (!e.target.matches('input, textarea, select')) return;
      formStarted = true;
      trackGoal('form_start', { form: form.getAttribute('data-form') || 'default' });
    });

    form.addEventListener('submit', function (e) {
      e.preventDefault();

      form.querySelectorAll('input[type="tel"]').forEach(syncPhoneValidity);
      if (!form.checkValidity()) {
        form.reportValidity();
        return;
      }

      var success = form.querySelector('[data-form-success]');
      var submitBtn = form.querySelector('button[type="submit"]');
      var origLabel = submitBtn ? submitBtn.textContent : 'Отправить';

      var done = function (ok, label) {
        if (submitBtn) { submitBtn.disabled = false; submitBtn.textContent = origLabel; }
        if (success) {
          success.textContent = label;
          success.classList.add('is-active');
        }
        if (ok) {
          form.reset();
          trackGoal('lead_submit', { form: form.getAttribute('data-form') || 'default' });
        }
      };

      if (submitBtn) { submitBtn.disabled = true; submitBtn.textContent = 'Отправляем…'; }

      sendLead(form).then(
        function () { done(true, 'Спасибо! Мы перезвоним в течение 15 минут.'); },
        function (err) {
          console.warn('[lead] failed', err);
          done(false, 'Не удалось отправить. Позвоните, пожалуйста: +7 (916) 838-08-88');
        }
      );
    });
  });

  // Цели на клики по контактам — одним делегированным слушателем.
  document.addEventListener('click', function (e) {
    var link = e.target.closest && e.target.closest('a[href]');
    if (!link) return;
    var href = link.getAttribute('href') || '';
    if (href.indexOf('tel:') === 0) {
      trackGoal('call_click', { source: linkSource(link) });
    } else if (/^https?:\/\/(?:api\.)?wa\.me\//i.test(href)) {
      trackGoal('whatsapp_click', { source: linkSource(link) });
    } else if (/^https?:\/\/t\.me\//i.test(href)) {
      trackGoal('telegram_click', { source: linkSource(link) });
    }
  });

  function linkSource(link) {
    if (link.closest('[data-fab]')) return 'fab';
    if (link.closest('header, .site-header, .topbar')) return 'header';
    if (link.closest('footer, .site-footer')) return 'footer';
    if (link.closest('[data-modal]')) return 'modal';
    return 'content';
  }

  // Модалка записи
  var modal = document.querySelector('[data-modal]');
  function closeModal() {
    if (!modal) return;
    modal.classList.remove('is-open');
    modal.querySelectorAll('[data-form-success].is-active').forEach(function (el) {
      el.classList.remove('is-active');
    });
  }
  document.addEventListener('click', function (e) {
    var btn = e.target.closest && e.target.closest('[data-modal-open]');
    if (!btn) return;
    e.preventDefault();
    if (modal) modal.classList.add('is-open');
    trackGoal('modal_open', { source: linkSource(btn) });
  });
  if (modal) {
    modal.addEventListener('click', function (e) {
      if (e.target === modal || e.target.matches('[data-modal-close]') || e.target.closest('[data-modal-close]')) {
        closeModal();
      }
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') closeModal();
    });
  }

  // Подсветка активного пункта меню
  var path = location.pathname.replace(/\/+$/, '') || '/';
  document.querySelectorAll('[data-nav] a').forEach(function (a) {
    try {
      var linkPath = new URL(a.href).pathname.replace(/\/+$/, '') || '/';
      if (linkPath === path) a.classList.add('is-active');
    } catch (e) {}
  });

  // Плавный скролл для якорей
  document.querySelectorAll('a[href^="#"]').forEach(function (a) {
    a.addEventListener('click', function (e) {
      var id = a.getAttribute('href').slice(1);
      if (!id) return;
      var el = document.getElementById(id);
      if (!el) return;
      e.preventDefault();
      el.scrollIntoView({ behavior: 'smooth', block: 'start' });
      if (nav && nav.classList.contains('is-open')) nav.classList.remove('is-open');
    });
  });

  // Reveal-анимации: только контент ниже сгиба (без «вспышки» на старте).
  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if ('IntersectionObserver' in window && !reduceMotion) {
    var revealTargets = document.querySelectorAll(
      '.section h2, .section__lead, .service-card, .step, .usp, .faq__item, .related__card, .prices-table, .reviews-empty, .clinic-gallery img, .doctor-card, .pf-card'
    );
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          io.unobserve(entry.target);
        }
      });
    }, { rootMargin: '0px 0px -10% 0px', threshold: 0.08 });

    var vh = window.innerHeight || document.documentElement.clientHeight;
    revealTargets.forEach(function (el) {
      if (el.getBoundingClientRect().top < vh) return;
      el.classList.add('js-reveal');
      io.observe(el);
    });
  }

  // Прогресс чтения
  var progress = document.querySelector('[data-scroll-progress]');
  if (progress) {
    var ticking = false;
    var updateProgress = function () {
      var h = document.documentElement;
      var max = h.scrollHeight - h.clientHeight;
      var pct = max > 0 ? (h.scrollTop / max) * 100 : 0;
      progress.style.width = pct.toFixed(1) + '%';
      ticking = false;
    };
    window.addEventListener('scroll', function () {
      if (!ticking) { window.requestAnimationFrame(updateProgress); ticking = true; }
    }, { passive: true });
    updateProgress();
  }

  // FAB-виджет (WhatsApp / Telegram / Позвонить)
  var fab = document.querySelector('[data-fab]');
  if (fab) {
    var fabToggle = fab.querySelector('[data-fab-toggle]');
    var openFab = function () { fab.classList.add('is-open'); fabToggle.setAttribute('aria-expanded', 'true'); };
    var closeFab = function () { fab.classList.remove('is-open'); fabToggle.setAttribute('aria-expanded', 'false'); };
    if (fabToggle) {
      fabToggle.addEventListener('click', function (e) {
        e.preventDefault();
        if (fab.classList.contains('is-open')) closeFab(); else openFab();
      });
    }
    document.addEventListener('click', function (e) {
      if (!fab.contains(e.target)) closeFab();
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') closeFab();
    });
    setTimeout(function () { fab.classList.add('is-ready'); }, 800);
  }

  } // init
})();
