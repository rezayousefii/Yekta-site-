/* ===== یکتا — اسکریپت مشترک همه‌ی صفحه‌ها ===== */
/* تم، نوار بالا، ورود نرم بلوک‌ها، شمارنده‌ها و صحنه‌ی چمنزار.
   هرچه روی «همه‌ی» صفحه‌ها هست اینجاست، نه در home.js — وگرنه دارک‌مود و
   نوار بالا فقط در صفحه‌ی اول کار می‌کردند. */

(function () {
  'use strict';

  var soft = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var doc  = document.documentElement;

  function faNum(n) {
    return String(n).replace(/[0-9]/g, function (d) { return '۰۱۲۳۴۵۶۷۸۹'[+d]; });
  }

  window.yekta = window.yekta || {};
  window.yekta.faNum = faNum;
  window.yekta.soft = soft;

  /* ================= تم (لامپ) ================= */
  /* کلاس dark را همان اسکریپت کوچک داخل <head> پیش از رنگ‌آمیزی گذاشته؛
     اینجا فقط کلیک را می‌گیریم. */

  var wave  = document.querySelector('.wave');
  var lamps = document.querySelectorAll('[data-lamp]');

  function flip(origin) {
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
      var meta = document.querySelector('meta[name="theme-color"]');
      if (meta) meta.setAttribute('content', next ? '#0B0E0D' : '#F4F1E9');
    }, 190);

    setTimeout(function () { if (wave) wave.classList.remove('is-on'); }, 430);
  }

  lamps.forEach(function (el) {
    el.addEventListener('click', function () { flip(el); });
  });

  /* ================= نوار بالا ================= */
  /* پایین رفتن → پنهان، بالا آمدن → پیدا. پس‌زمینه فقط وقتی محتوا زیرش رسید. */

  var bar = document.querySelector('[data-bar]');

  if (bar) {
    var lastY = window.scrollY;
    var solidAt = document.querySelector('.hero') ? 0.82 : 0.02;

    var paintBar = function (y) {
      if (y > lastY + 6 && y > 140) bar.classList.add('is-hidden');
      else if (y < lastY - 6)       bar.classList.remove('is-hidden');
      bar.classList.toggle('is-solid', y > window.innerHeight * solidAt);
      lastY = y;
    };

    var barBusy = false;
    window.addEventListener('scroll', function () {
      if (barBusy) return;
      barBusy = true;
      requestAnimationFrame(function () { paintBar(window.scrollY); barBusy = false; });
    }, { passive: true });

    paintBar(window.scrollY);
  }

  /* ================= ورود نرم بلوک‌ها ================= */

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
      }, { rootMargin: '0px 0px -8% 0px', threshold: 0.06 });

      rises.forEach(function (el) { io.observe(el); });
    }
  }

  /* ================= شمارنده‌ها ================= */
  /* <b data-count="7"> از صفر تا ۷ بالا می‌رود، با رقم فارسی. */

  document.querySelectorAll('[data-count]').forEach(function (el) {
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
  /* «YEKTA» آرام چپ و راست می‌رود؛ سرِ گل رو به آن می‌چرخد و باد — که خودش
     نوسانی نامنظم از چند سینوس است — چمن، برگ‌ها و ساقه را با هم می‌جنباند.
     زاویه‌ها یک‌بار اندازه گرفته می‌شوند و بعد فقط ریاضی است. */

  var meadow = document.querySelector('[data-meadow]');

  if (meadow) {
    var word = meadow.querySelector('[data-meadow-word]');
    var head = meadow.querySelector('[data-meadow-head]');
    var neck = meadow.querySelector('[data-meadow-neck]');
    var motes = meadow.querySelector('[data-meadow-motes]');

    var YAW   = 52;   // بیشترین چرخش سر دور محور عمودی (بُعد سوم)
    var PITCH = 9;    // نگاه‌به‌بالای همیشگی — انگار همیشه کمی رو به خورشید است
    var TURN_UP = 16; // نگاه‌به‌بالای اضافه، وقتی سر بیشتر می‌چرخد
    var span  = 0;    // نصف مسیر رفت‌وبرگشت متن، به پیکسل
    var limit = 14;   // بیشترین خم‌شدن گردن — بیشتر از این مصنوعی می‌شود

    /* ---- گرده‌های معلق ---- */
    if (motes && !soft) {
      var seeds = window.innerWidth < 640 ? 7 : 14;
      var frag = document.createDocumentFragment();

      for (var s = 0; s < seeds; s++) {
        var m = document.createElement('span');
        m.className = 'mote';
        m.style.left = (5 + Math.random() * 90).toFixed(1) + '%';
        m.style.bottom = (Math.random() * 45).toFixed(1) + '%';
        m.style.setProperty('--dur', (11 + Math.random() * 10).toFixed(1) + 's');
        m.style.setProperty('--delay', (-Math.random() * 14).toFixed(1) + 's');
        m.style.setProperty('--dx', (-90 + Math.random() * 180).toFixed(0) + 'px');
        m.style.width = m.style.height = (2 + Math.random() * 3).toFixed(1) + 'px';
        frag.appendChild(m);
      }

      motes.appendChild(frag);
    }

    /* زاویه با نسبت جای متن داده می‌شود، نه با قطع‌کردن زاویه‌ی هندسی؛
       این‌طور سر گل در دو سر مسیر «گیر» نمی‌کند و حرکتش نرم می‌ماند. */
    var put = function (x, wind) {
      word.style.transform = 'translateX(' + x.toFixed(1) + 'px)';

      var r = span ? x / span : 0;          // -۱ تا ۱

      /* صورت گل در بُعد سوم می‌چرخد و رو به متن می‌ایستد؛ هرچه بیشتر
         می‌چرخد، کمی بیشتر هم رو به بالا می‌گیرد — دقیقاً مثل واقعی که
         موقع دنبال‌کردن خورشید در آسمان، سرش را بالا هم می‌آورد. */
      var pitch = -(PITCH + TURN_UP * Math.abs(r));
      head.style.transform =
        'perspective(360px) rotateX(' + pitch.toFixed(2) + 'deg)' +
        ' rotateY(' + (YAW * r).toFixed(2) + 'deg)' +
        ' rotateZ(' + (wind * 3.4).toFixed(2) + 'deg)';

      /* گردن از نوک ساقه خم می‌شود — چرخاندنِ خودِ گلِ متقارن دیده نمی‌شد،
         چیزی که واقعاً حرکت را باورپذیر می‌کند همین خم‌شدن ساقه است.
         باد هم روی همین می‌نشیند، پس گل در وزش کمی عقب می‌رود. */
      if (neck) {
        neck.setAttribute('transform',
          'translate(148 156) rotate(' + (limit * r + wind * 4.5).toFixed(2) + ')');
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
      put(0, 0);
    } else {
      var raf = 0, t0 = 0, seen = false;

      /* باد: جمعِ چند سینوس با دوره‌های نامتناسب، پس الگویش عملاً تکرار
         نمی‌شود — همان چیزی که وزش واقعی را از یک لوپِ ماشینی جدا می‌کند. */
      var gust = function (t) {
        return (Math.sin(t * 0.00021) * 0.55 +
                Math.sin(t * 0.00047 + 1.3) * 0.28 +
                Math.sin(t * 0.00113 + 2.7) * 0.17);
      };

      var frame = function (ts) {
        if (!t0) t0 = ts;
        var t = ts - t0;
        var wind = gust(t);

        meadow.style.setProperty('--wind', wind.toFixed(3));
        put(Math.sin(t * 0.00026) * span, wind);

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

  /* ================= پیام‌ها ================= */
  /* پیام موفقیت بعد از چند ثانیه خودش می‌رود؛ خطا می‌ماند تا خوانده شود. */

  document.querySelectorAll('.msg.success').forEach(function (el) {
    setTimeout(function () {
      el.style.transition = 'opacity .5s, transform .5s';
      el.style.opacity = '0';
      el.style.transform = 'translateY(-.5rem)';
      setTimeout(function () { el.remove(); }, 520);
    }, 6000);
  });

})();
