/* ===== یکتا — پنل استودیو ===== */
/* پنل بدون جاوااسکریپت هم کامل کار می‌کند؛ این فایل فقط کارها را
   روان‌تر می‌کند: تم، شمارنده‌ها، پیش‌نمایش عکس، شمارش معکوس، و تاییدِ حذف. */

(function () {
  'use strict';

  var doc  = document.documentElement;
  var soft = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function faNum(n) {
    return String(n).replace(/[0-9]/g, function (d) { return '۰۱۲۳۴۵۶۷۸۹'[+d]; });
  }

  /* ================= تم ================= */

  var wave = document.querySelector('.wave');

  document.querySelectorAll('[data-lamp]').forEach(function (el) {
    el.addEventListener('click', function () {
      var next = !doc.classList.contains('dark');
      var b = el.getBoundingClientRect();

      if (wave) {
        wave.style.setProperty('--wx', (b.left + b.width / 2) + 'px');
        wave.style.setProperty('--wy', (b.top + b.height / 2) + 'px');
        wave.style.setProperty('--wave-bg', next ? '#0B0E0D' : '#FBFAF7');
        wave.style.setProperty('--flash', next ? 'var(--copper)' : 'var(--sun)');
        wave.classList.add('is-on');
      }

      setTimeout(function () {
        doc.classList.toggle('dark', next);
        try { localStorage.setItem('yekta-theme', next ? 'dark' : 'light'); } catch (e) {}
      }, 170);

      setTimeout(function () { if (wave) wave.classList.remove('is-on'); }, 420);
    });
  });

  /* ================= شمارنده‌ها ================= */

  document.querySelectorAll('[data-count]').forEach(function (el) {
    var target = parseInt(el.getAttribute('data-count'), 10) || 0;

    if (soft || target === 0) { el.textContent = faNum(target); return; }

    var t0 = 0;
    var step = function (ts) {
      if (!t0) t0 = ts;
      var p = Math.min(1, (ts - t0) / 850);
      el.textContent = faNum(Math.round(target * (1 - Math.pow(1 - p, 3))));
      if (p < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  });

  /* ================= پیش‌نمایش عکسِ انتخاب‌شده ================= */
  /* روی گوشی مهم است: کاربر باید ببیند کدام عکس را از گالری برداشته،
     پیش از آنکه فرم را بفرستد. */

  var drop = document.querySelector('[data-drop]');

  if (drop) {
    var file = drop.querySelector('input[type="file"]');
    var eye  = drop.querySelector('[data-drop-eye]');
    var name = drop.querySelector('[data-drop-name]');

    file.addEventListener('change', function () {
      var f = file.files && file.files[0];
      if (!f) return;

      if (name) name.textContent = f.name;
      drop.classList.add('is-hot');

      if (eye && f.type.indexOf('image/') === 0) {
        var url = URL.createObjectURL(f);
        eye.innerHTML = '';
        var img = document.createElement('img');
        img.src = url;
        img.alt = '';
        img.onload = function () { URL.revokeObjectURL(url); };
        eye.appendChild(img);
      }
    });
  }

  /* ================= شمارش معکوس تا آفیش بعدی ================= */

  var cd = document.querySelector('[data-countdown]');

  if (cd) {
    var when = new Date(cd.getAttribute('data-countdown'));
    var dEl = cd.querySelector('[data-cd-d]');
    var hEl = cd.querySelector('[data-cd-h]');
    var mEl = cd.querySelector('[data-cd-m]');

    var tickCd = function () {
      var left = when - new Date();

      if (isNaN(left) || left < 0) {
        dEl.textContent = hEl.textContent = mEl.textContent = faNum(0);
        return;
      }

      var mins = Math.floor(left / 60000);
      dEl.textContent = faNum(Math.floor(mins / 1440));
      hEl.textContent = faNum(Math.floor(mins % 1440 / 60));
      mEl.textContent = faNum(mins % 60);
    };

    tickCd();
    setInterval(tickCd, 30000);
  }

  /* ================= تایید پیش از حذف ================= */
  /* هر دکمه‌ای که data-confirm دارد، یک‌بار می‌پرسد. کارِ حذف در سرور
     انجام می‌شود؛ این فقط جلوی ضربه‌ی اشتباهی را می‌گیرد. */

  document.addEventListener('click', function (e) {
    var el = e.target.closest('[data-confirm]');
    if (!el) return;
    if (!window.confirm(el.getAttribute('data-confirm'))) {
      e.preventDefault();
      e.stopPropagation();
    }
  }, true);

  /* ================= کپی لینک ================= */

  document.querySelectorAll('[data-copy]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var box = btn.closest('.share__row');
      var input = box && box.querySelector('[data-copy-src]');
      if (!input) return;

      var done = function () {
        var old = btn.textContent;
        btn.textContent = 'کپی شد';
        btn.classList.add('is-done');
        setTimeout(function () {
          btn.textContent = old;
          btn.classList.remove('is-done');
        }, 1600);
      };

      if (navigator.clipboard) {
        navigator.clipboard.writeText(input.value).then(done, function () {
          input.select();
          done();
        });
      } else {
        input.select();
        try { document.execCommand('copy'); } catch (err) {}
        done();
      }
    });
  });

  /* ================= گفتگو ================= */
  /* آخرین پیام باید دیده شود، نه اولین. */

  var chat = document.querySelector('.chat');
  if (chat) chat.scrollTop = chat.scrollHeight;

})();
