/* ===== یکتا — اسکریپت مشترک همه‌ی صفحه‌ها ===== */
/* این فایل در base.html و پس از {% block js %} لود می‌شود، تا بتواند بفهمد
   home.js روی این صفحه هست یا نه. */

(function () {
  'use strict';

  var soft = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var doc  = document.documentElement;

  function faNum(n) {
    return String(n).replace(/[0-9]/g, function (d) { return '۰۱۲۳۴۵۶۷۸۹'[+d]; });
  }

  /* ================= تم (لامپ) ================= */
  /* تم را همیشه اعمال می‌کنیم؛ ولی کلیک را فقط وقتی وصل می‌کنیم که home.js
     روی این صفحه نباشد، وگرنه هر کلیک دوبار پردازش می‌شد و عملاً بی‌اثر می‌ماند. */

  try { if (localStorage.getItem('yekta-theme') === 'dark') doc.classList.add('dark'); } catch (e) {}

  var hasHome = !!document.querySelector('script[src*="home.js"]');

  if (!hasHome) {
    var wave  = document.querySelector('.wave');
    var lamps = document.querySelectorAll('[data-lamp]');

    var flip = function (origin) {
      var next = !doc.classList.contains('dark');
      var b = origin.getBoundingClientRect();

      if (wave) {
        wave.style.setProperty('--wx', (b.left + b.width / 2) + 'px');
        wave.style.setProperty('--wy', (b.top + b.height / 2) + 'px');
        wave.style.setProperty('--wave-bg', next ? '#0B0E0D' : '#FBFAF7');
        wave.style.setProperty('--flash', next ? 'var(--copper)' : 'var(--sun)');
        wave.classList.add('is-on');
      }

      lamps.forEach(function (l) { l.classList.add('is-firing'); });
      setTimeout(function () {
        lamps.forEach(function (l) { l.classList.remove('is-firing'); });
      }, 330);

      setTimeout(function () {
        doc.classList.toggle('dark', next);
        try { localStorage.setItem('yekta-theme', next ? 'dark' : 'light'); } catch (e) {}
      }, 190);

      setTimeout(function () { if (wave) wave.classList.remove('is-on'); }, 430);
    };

    lamps.forEach(function (el) {
      el.addEventListener('click', function () { flip(el); });
    });
  }

  /* ================= ورود نرم بلوک‌ها ================= */
  /* هر عنصری که data-rise داشته باشد، موقع رسیدن به کادر دید بالا می‌آید. */

  var rises = document.querySelectorAll('[data-rise]');

  if (rises.length) {
    if (soft || !('IntersectionObserver' in window)) {
      rises.forEach(function (el) { el.classList.add('is-in'); });
    } else {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          if (!e.isIntersecting) return;
          e.target.classList.add('is-in');
          io.unobserve(e.target);
        });
      }, { rootMargin: '0px 0px -10% 0px', threshold: 0.08 });

      rises.forEach(function (el) { io.observe(el); });
    }
  }

  /* ================= شمارنده‌ها ================= */
  /* <b data-count="7"> از صفر تا ۷ بالا می‌رود، با رقم فارسی. */

  var counters = document.querySelectorAll('[data-count]');

  counters.forEach(function (el) {
    var target = parseInt(el.getAttribute('data-count'), 10) || 0;

    if (soft || target === 0) { el.textContent = faNum(target); return; }

    var started = false;

    var run = function () {
      if (started) return;
      started = true;

      var t0 = 0;
      var step = function (ts) {
        if (!t0) t0 = ts;
        var p = Math.min(1, (ts - t0) / 900);
        var eased = 1 - Math.pow(1 - p, 3);
        el.textContent = faNum(Math.round(target * eased));
        if (p < 1) requestAnimationFrame(step);
      };
      requestAnimationFrame(step);
    };

    if (!('IntersectionObserver' in window)) { run(); return; }

    var co = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { run(); co.unobserve(e.target); }
      });
    }, { threshold: 0.4 });

    co.observe(el);
  });

  /* ================= چمنزار و آفتابگردان ================= */
  /* «YEKTA» آرام چپ و راست می‌رود؛ سرِ گل رو به آن می‌چرخد.
     زاویه به‌جای خواندن مختصات در هر فریم (که روی سیستم ضعیف کند است)
     یک‌بار اندازه گرفته می‌شود و بعد فقط ریاضی است. */

  var meadow = document.querySelector('[data-meadow]');

  if (meadow) {
    var word = meadow.querySelector('[data-meadow-word]');
    var head = meadow.querySelector('[data-meadow-head]');
    var neck = meadow.querySelector('[data-meadow-neck]');

    var YAW   = 50;   // بیشترین چرخش سر دور محور عمودی (بُعد سوم)
    var PITCH = 9;     // نگاه‌به‌بالای همیشگی — انگار همیشه کمی رو به خورشید است
    var TURN_UP = 15;  // نگاه‌به‌بالای اضافه، وقتی سر بیشتر می‌چرخد
    var span  = 0;    // نصف مسیر رفت‌وبرگشت متن، به پیکسل
    var limit = 14;   // بیشترین خم‌شدن گردن — بیشتر از این مصنوعی می‌شود

    /* زاویه با نسبت جای متن داده می‌شود، نه با قطع‌کردن زاویه‌ی هندسی؛
       این‌طور سر گل در دو سر مسیر «گیر» نمی‌کند و حرکتش نرم می‌ماند. */
    var put = function (x) {
      word.style.transform = 'translateX(' + x.toFixed(1) + 'px)';

      var r = span ? x / span : 0;          // -۱ تا ۱

      /* صورت گل در بُعد سوم می‌چرخد و رو به متن می‌ایستد؛ هرچه بیشتر
         می‌چرخد، کمی بیشتر هم رو به بالا می‌گیرد — دقیقاً مثل واقعی که
         موقع دنبال‌کردن خورشید در آسمان، سرش را بالا هم می‌آورد. */
      var pitch = -(PITCH + TURN_UP * Math.abs(r));
      head.style.transform =
        'perspective(380px) rotateX(' + pitch.toFixed(2) + 'deg)' +
        ' rotateY(' + (YAW * r).toFixed(2) + 'deg)';

      /* گردن از نوک ساقه خم می‌شود — چرخاندن خودِ گلِ متقارن دیده نمی‌شد،
         چیزی که واقعاً حرکت را باورپذیر می‌کند همین خم‌شدن ساقه است. */
      if (neck) {
        neck.setAttribute('transform',
          'translate(148 156) rotate(' + (limit * r).toFixed(2) + ')');
      }
    };

    var measure = function () {
      var hb = head.getBoundingClientRect();
      var wb = word.getBoundingClientRect();

      var lift = Math.max(60, (hb.top + hb.height / 2) - (wb.top + wb.height / 2));
      span = Math.max(0, (meadow.clientWidth - word.offsetWidth) / 2) * 0.86;

      // هرچه متن بالاتر باشد، گل کمتر خم می‌شود — مثل نگاه‌کردن به چیز دورتر
      var geo = Math.atan2(span, lift) * 180 / Math.PI;
      limit = Math.max(7, Math.min(16, geo));
    };

    measure();

    if (soft) {
      put(0);
    } else {
      var raf = 0, t0 = 0, seen = false;

      var frame = function (ts) {
        if (!t0) t0 = ts;
        put(Math.sin((ts - t0) * 0.00026) * span);
        raf = requestAnimationFrame(frame);
      };

      var start = function () {
        if (raf) return;
        t0 = 0;
        raf = requestAnimationFrame(frame);
      };

      var stop = function () {
        if (!raf) return;
        cancelAnimationFrame(raf);
        raf = 0;
      };

      /* فقط وقتی صحنه توی دید است حرکت می‌کند — بقیه‌ی وقت هیچ باری ندارد */
      if ('IntersectionObserver' in window) {
        var mo = new IntersectionObserver(function (entries) {
          entries.forEach(function (e) {
            seen = e.isIntersecting;
            if (seen && !document.hidden) start(); else stop();
          });
        }, { threshold: 0.01 });
        mo.observe(meadow);
      } else {
        seen = true;
        start();
      }

      document.addEventListener('visibilitychange', function () {
        if (document.hidden) stop();
        else if (seen) start();
      });

      var tm = 0;
      window.addEventListener('resize', function () {
        clearTimeout(tm);
        tm = setTimeout(measure, 180);
      });
    }
  }

})();
