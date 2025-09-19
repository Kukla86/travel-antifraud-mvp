(function (root, factory) {
  if (typeof define === 'function' && define.amd) {
    define([], factory);
  } else if (typeof module === 'object' && module.exports) {
    module.exports = factory();
  } else {
    root.CheckoutFraudCheck = factory();
  }
}(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  // Русские комментарии; логи и сообщения — на английском по требованию

  function nowMs() { return Date.now ? Date.now() : new Date().getTime(); }

  function getTimezone() {
    try { return Intl.DateTimeFormat().resolvedOptions().timeZone || null; } catch (e) { return null; }
  }

  function getLanguage() {
    return (navigator.language || navigator.userLanguage || '').toString();
  }

  function normalizeBIN(value) {
    if (!value) return null;
    var digits = (value + '').replace(/\D/g, '');
    if (digits.length < 6) return null;
    return digits.slice(0, 6);
  }

  function collectDeviceInfo() {
    var scr = (typeof screen !== 'undefined') ? screen : null;
    return {
      userAgent: (navigator.userAgent || ''),
      platform: (navigator.platform || ''),
      language: getLanguage(),
      screen: scr ? { width: scr.width, height: scr.height, pixelRatio: (window.devicePixelRatio || 1) } : null,
    };
  }

  async function fetchIP() {
    try {
      var r = await fetch('https://ipapi.co/json/');
      if (!r.ok) return null;
      var data = await r.json();
      return data && data.ip ? data.ip : null;
    } catch (e) {
      return null;
    }
  }

  function attachFraudCheck(options) {
    // options: { form, emailInput, cardInput, endpointUrl, onResult }
    if (!options || !options.form) throw new Error('form is required');
    var form = (typeof options.form === 'string') ? document.querySelector(options.form) : options.form;
    if (!form) throw new Error('form not found');

    var emailEl = (typeof options.emailInput === 'string') ? document.querySelector(options.emailInput) : options.emailInput;
    var cardEl = (typeof options.cardInput === 'string') ? document.querySelector(options.cardInput) : options.cardInput;

    var endpointUrl = options.endpointUrl || 'http://localhost:8000/api/check';
    var onResult = typeof options.onResult === 'function' ? options.onResult : function () {};

    // Сбор поведенческих метрик
    var startTs = nowMs();
    var firstClickDelayMs = null;
    var mouseMoves = 0;

    var lastKeyTs = null;
    var keyIntervals = [];

    function handleKeydown(ev) {
      var t = nowMs();
      if (lastKeyTs != null) {
        var delta = t - lastKeyTs;
        // ограничиваем неадекватные значения
        if (delta >= 0 && delta < 5000) keyIntervals.push(delta);
      }
      lastKeyTs = t;
    }

    function handleMouseMove() { mouseMoves++; }
    function handleClickOnce() {
      if (firstClickDelayMs == null) firstClickDelayMs = nowMs() - startTs;
      document.removeEventListener('click', handleClickOnce, true);
    }

    // Подписки
    document.addEventListener('mousemove', handleMouseMove, { passive: true });
    document.addEventListener('click', handleClickOnce, true);

    if (emailEl) emailEl.addEventListener('keydown', handleKeydown, true);
    if (cardEl) cardEl.addEventListener('keydown', handleKeydown, true);

    async function handleSubmit(ev) {
      try {
        // Не мешаем сабмиту формы, просто отправляем фрод-чек параллельно
        var sessionDurationMs = nowMs() - startTs;
        var avgTyping = null;
        if (keyIntervals.length) {
          var sum = 0; for (var i = 0; i < keyIntervals.length; i++) sum += keyIntervals[i];
          avgTyping = Math.round(sum / keyIntervals.length);
        }

        var payload = {
          email: emailEl ? (emailEl.value || '') : '',
          bin: normalizeBIN(cardEl ? cardEl.value : ''),
          user_agent: navigator.userAgent || '',
          ip: await fetchIP(),
          timezone: getTimezone(),
          language: getLanguage(),
          session_duration_ms: sessionDurationMs,
          typing_speed_ms_avg: avgTyping,
          mouse_moves_count: mouseMoves,
          first_click_delay_ms: firstClickDelayMs,
          device_info: collectDeviceInfo(),
        };

        var resp = await fetch(endpointUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        var data = null;
        try { data = await resp.json(); } catch (e) { data = { error: 'bad_json' }; }
        onResult(data);
      } catch (e) {
        onResult({ error: 'request_failed' });
      }
    }

    form.addEventListener('submit', handleSubmit, false);

    return {
      destroy: function () {
        document.removeEventListener('mousemove', handleMouseMove, { passive: true });
        document.removeEventListener('click', handleClickOnce, true);
        if (emailEl) emailEl.removeEventListener('keydown', handleKeydown, true);
        if (cardEl) cardEl.removeEventListener('keydown', handleKeydown, true);
        form.removeEventListener('submit', handleSubmit, false);
      }
    };
  }

  return { attachFraudCheck: attachFraudCheck };
}));
