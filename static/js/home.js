/* ===== یکتا — موتور صفحه اول ===== */

(function () {
  'use strict';

  var soft = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var doc  = document.documentElement;

  function faNum(n) {
    return String(n).replace(/[0-9]/g, function (d) { return '۰۱۲۳۴۵۶۷۸۹'[+d]; });
  }

  function pad2(n) { return faNum(n < 10 ? '0' + n : n); }

  /* ================= دارک مود ================= */

  var wave  = document.querySelector('.wave');
  var lamps = document.querySelectorAll('[data-lamp]');

  try { if (localStorage.getItem('yekta-theme') === 'dark') doc.classList.add('dark'); } catch (e) {}

  function flip(origin) {
    var next = !doc.classList.contains('dark');
    var b = origin.getBoundingClientRect();

    wave.style.setProperty('--wx', (b.left + b.width / 2) + 'px');
    wave.style.setProperty('--wy', (b.top + b.height / 2) + 'px');
    wave.style.setProperty('--wave-bg', next ? '#0B0E0D' : '#FBFAF7');
    wave.style.setProperty('--flash', next ? 'var(--copper)' : 'var(--sun)');
    wave.classList.add('is-on');

    lamps.forEach(function (l) { l.classList.add('is-firing'); });
    setTimeout(function () { lamps.forEach(function (l) { l.classList.remove('is-firing'); }); }, 330);

    setTimeout(function () {
      doc.classList.toggle('dark', next);
      try { localStorage.setItem('yekta-theme', next ? 'dark' : 'light'); } catch (e) {}
    }, 190);

    setTimeout(function () { wave.classList.remove('is-on'); }, 430);
  }

  lamps.forEach(function (el) { el.addEventListener('click', function () { flip(el); }); });

  /* ================= نوار بالا ================= */

  var lastY = window.scrollY;

  function nav(y) {
    if (!bar) return;
    if (y > lastY + 6 && y > 140) bar.classList.add('is-hidden');
    else if (y < lastY - 6)       bar.classList.remove('is-hidden');
    bar.classList.toggle('is-solid', y > window.innerHeight * 0.82);
  }

  /* ================= ساقه و پارالاکس ================= */

  var rail   = document.querySelector('.rail');
  var svg    = document.querySelector('.rail__svg');
  var stem   = document.querySelector('.rail__stem');
  var flower = document.querySelector('.rail__flower');
  var stalks = document.querySelectorAll('.rail__stalk');
  var leaves = document.querySelectorAll('.rail__leaf');
  var spine  = document.querySelector('.spine');
  var spNum  = document.querySelector('.spine__num');
  var hero   = document.querySelector('.hero');
  var pin    = document.querySelector('.hero__pin');
  var floats = document.querySelectorAll('[data-par]');
  var banner = document.querySelector('.banner');
  var bar    = document.querySelector('.bar');

  /* جای هر برگ روی مسیر ساقه و سمتی که باز می‌شود */
  var LEAF_AT   = [0.13, 0.26, 0.40, 0.54, 0.68, 0.82];
  var LEAF_SIDE = [1, -1, 1, -1, 1, -1];

  var stemLen = stem ? stem.getTotalLength() : 0;
  if (stem) stem.style.setProperty('--len', stemLen);

  var barH = bar ? bar.offsetHeight : 54;   /* گل از وسط نوار بالا راه می‌افتد */
  var kx = 1, ky = 1, topPad = 0;

  /* ضریب تبدیل مختصات ویوباکس به پیکسل — چون preserveAspectRatio خاموش است */
  /* ماتریس تبدیل مختصات ویوباکس به پیکسلِ واقعیِ صفحه.
     چون rail از نوع fixed است، با اسکرول عوض نمی‌شود و یک‌بار گرفتنش کافی است. */
  var ctm = null, railBox = null;

  function gauge() {
    if (!rail || !svg) return;
    barH   = bar ? bar.offsetHeight : 54;
    topPad = barH / 2;
    kx = rail.clientWidth / 40;
    ky = Math.max(1, rail.clientHeight - topPad) / 1000;

    /* جای گل را از روی همین ماتریس حساب می‌کنیم، نه با ضرب دستی kx/ky؛
       آن روش موقع کشیده‌شدن ویوباکس (preserveAspectRatio=none) کمی خطا داشت
       و نوک ساقه با مرکز گل یکی درنمی‌آمد — مخصوصاً پایین صفحه. */
    try {
      ctm = stem ? stem.getScreenCTM() : null;
      railBox = rail.getBoundingClientRect();
    } catch (e) { ctm = null; }

    placeLeaves();
  }

  function placeLeaves() {
    if (!stem || !stalks.length || !stemLen) return;
    var squash = ky > 0 ? kx / ky : 1;

    stalks.forEach(function (g, i) {
      var pt = stem.getPointAtLength(stemLen * LEAF_AT[i]);
      var ang = LEAF_SIDE[i] > 0 ? -34 : 214;
      g.setAttribute('transform',
        'translate(' + pt.x.toFixed(1) + ',' + pt.y.toFixed(1) + ') ' +
        'scale(1,' + squash.toFixed(3) + ') rotate(' + ang + ')');
    });
  }

  var tilt = 0;

  /* ایستگاه‌هایی از مسیر که یک پَر می‌افتد — از پرهای خود گل کم نمی‌شود */
  var SHED = [0.19, 0.45, 0.71];
  var shed = [false, false, false];

  function dropPetal() {
    if (soft || !flower) return;

    var r  = flower.getBoundingClientRect();
    var cx = r.left + r.width / 2;
    var cy = r.top + r.height / 2;

    /* از لبه‌ی گل جدا می‌شود، نه از مرکزش */
    var ang = -Math.PI / 2 + (Math.random() - 0.5) * 1.8;
    var rad = r.width * 0.36;

    var p = document.createElement('span');
    p.className = 'petal';
    p.appendChild(document.createElement('i'));
    p.style.left = (cx + Math.cos(ang) * rad).toFixed(0) + 'px';
    p.style.top  = (cy + Math.sin(ang) * rad).toFixed(0) + 'px';
    p.style.setProperty('--a',  (Math.random() * 70 - 35).toFixed(0) + 'deg');
    p.style.setProperty('--dx', (-22 - Math.random() * 76).toFixed(0) + 'px');

    document.body.appendChild(p);
    setTimeout(function () { p.remove(); }, 3400);
  }

  /* گل را دقیقاً روی نقطه‌ی p از طول ساقه می‌نشاند — جدا از frame() چون این
     یکی با p هموارشده (flowerP) صدا زده می‌شود، نه p خام اسکرول. */
  function placeFlowerAt(pp) {
    if (!flower || !stem || !stemLen) return;

    var pt = stem.getPointAtLength(stemLen * pp);
    var fx, fy;

    if (ctm && railBox) {
      var sp = pt.matrixTransform(ctm);        // مختصات واقعی روی صفحه
      fx = sp.x - railBox.left;
      fy = sp.y - railBox.top;
    } else {
      fx = pt.x * kx;                          // مسیر پشتیبان
      fy = pt.y * ky + topPad;
    }

    flower.style.setProperty('--fx', fx.toFixed(1) + 'px');
    flower.style.setProperty('--fy', fy.toFixed(1) + 'px');
  }

  /* موقعیت خام گل (targetP) با همان سرعتِ رویداد اسکرول عوض می‌شود که
     روی موبایل یکنواخت نیست؛ برای همین رندر واقعی از flowerP می‌آید که هر
     فریم کمی به سمت targetP می‌لغزد — نتیجه، دنبال‌کردنی نرم به‌جای پرش. */
  var targetP = 0, flowerP = 0, flRaf = 0, flowerInited = false;

  function flowerLoop() {
    var d = targetP - flowerP;

    if (soft || Math.abs(d) < 0.0004) {
      flowerP = targetP;
      placeFlowerAt(flowerP);
      flRaf = 0;
      return;
    }

    flowerP += d * 0.16;
    placeFlowerAt(flowerP);
    flRaf = requestAnimationFrame(flowerLoop);
  }

  function kickFlower() {
    if (!flRaf) flRaf = requestAnimationFrame(flowerLoop);
  }

  function frame(y) {
    var max = doc.scrollHeight - window.innerHeight;
    var p   = max > 0 ? Math.min(1, Math.max(0, y / max)) : 0;
    var vh  = window.innerHeight;

    if (rail) {
      rail.style.setProperty('--p', p.toFixed(4));

      targetP = p;
      /* اولین فراخوانی (بارگذاری صفحه) بی‌درنگ جا می‌افتد؛ فقط اسکرول‌های
         بعدی نرم دنبال می‌شوند — وگرنه موقع لود، گل از گوشه‌ی صفحه «می‌دوید». */
      if (!flowerInited) { flowerInited = true; flowerP = p; placeFlowerAt(flowerP); }
      kickFlower();
      if (flower) flower.style.setProperty('--tilt', tilt.toFixed(1) + 'deg');

      leaves.forEach(function (l, i) {
        l.classList.toggle('is-on', p > LEAF_AT[i] + 0.015);
      });

      for (var k = 0; k < SHED.length; k++) {
        if (!shed[k] && p > SHED[k]) { shed[k] = true; dropPetal(); }
      }
    }

    if (spine) {
      spine.style.setProperty('--p', p.toFixed(4));
      if (spNum) spNum.textContent = String(Math.round(p * 100)).padStart(2, '0');
    }

    if (pin && hero) {
      var hp = Math.max(0, Math.min(1, y / (hero.offsetHeight || 1)));
      pin.style.setProperty('--hp', hp.toFixed(4));
    }

    if (soft) return;

    floats.forEach(function (el) {
      var b = el.getBoundingClientRect();
      if (b.bottom < -250 || b.top > vh + 250) return;
      var mid = (b.top + b.height / 2 - vh / 2) / vh;
      el.style.setProperty('--py', (mid * -(parseFloat(el.dataset.par) || 34)).toFixed(1) + 'px');
    });

    if (banner) {
      var bb = banner.getBoundingClientRect();
      if (bb.bottom > -200 && bb.top < vh + 200) {
        var m = (bb.top + bb.height / 2 - vh / 2) / vh;
        banner.style.setProperty('--wy2', (m * 40).toFixed(1) + 'px');
        banner.style.setProperty('--cy',  (m * -18).toFixed(1) + 'px');
      }
    }
  }

  gauge();

  /* ================= اسکرول صفحه ================= */

  var busy = false;
  var calm = null;

  window.addEventListener('scroll', function () {
    var y = window.scrollY;
    var d = y - lastY;

    if (Math.abs(d) > 2) tilt = d > 0 ? 9 : -9;
    clearTimeout(calm);
    calm = setTimeout(function () {
      tilt = 0;
      if (flower) flower.style.setProperty('--tilt', '0deg');
    }, 260);

    nav(y);
    if (!busy) {
      busy = true;
      requestAnimationFrame(function () { frame(y); busy = false; });
    }
    lastY = y;
  }, { passive: true });

  window.addEventListener('resize', function () { gauge(); frame(window.scrollY); });
  window.addEventListener('load', function () { gauge(); frame(window.scrollY); });
  frame(window.scrollY);
  nav(window.scrollY);

  /* ================= ظاهر شدن ================= */

  var reveal = document.querySelectorAll('.reveal');

  if (!('IntersectionObserver' in window)) {
    reveal.forEach(function (el) { el.classList.add('is-in'); });
  } else {
    var io = new IntersectionObserver(function (rows) {
      rows.forEach(function (r) {
        if (!r.isIntersecting) return;
        r.target.classList.add('is-in');
        io.unobserve(r.target);
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -8% 0px' });
    reveal.forEach(function (el) { io.observe(el); });
  }

  /* ================= کشیدن افقی (لاین و لایت‌باکس) ================= */

  var canHover = window.matchMedia('(hover: hover) and (pointer: fine)').matches;

  function dragScroll(el) {
    if (!canHover) return;          /* روی لمسی، اسکرول بومی مرورگر دست‌نخورده می‌ماند */
    var down = false, x0 = 0, l0 = 0, moved = 0;
    var vx = 0, lx = 0, lt = 0, glide = null;

    /* بعد از رها کردن، نوار با اصطکاک می‌سُرد و آرام می‌ایستد */
    function coast() {
      vx *= 0.93;
      el.scrollLeft -= vx * 16;
      if (Math.abs(vx) < 0.02) {
        glide = null;
        el.classList.remove('is-drag');
        return;
      }
      glide = requestAnimationFrame(coast);
    }

    el.addEventListener('mousedown', function (e) {
      down = true; moved = 0; vx = 0;
      x0 = e.pageX; l0 = el.scrollLeft; lx = e.pageX; lt = Date.now();
      if (glide) { cancelAnimationFrame(glide); glide = null; }
      el.classList.add('is-drag');
    });

    function stop() {
      if (!down) return;
      down = false;
      if (Math.abs(vx) > 0.05) glide = requestAnimationFrame(coast);
      else el.classList.remove('is-drag');
    }

    ['mouseup', 'mouseleave'].forEach(function (ev) { el.addEventListener(ev, stop); });

    el.addEventListener('mousemove', function (e) {
      if (!down) return;
      e.preventDefault();
      moved = Math.abs(e.pageX - x0);
      el.scrollLeft = l0 - (e.pageX - x0);

      var t = Date.now();
      if (t - lt > 16) { vx = (e.pageX - lx) / (t - lt); lx = e.pageX; lt = t; }
    });

    el.addEventListener('click', function (e) {
      if (moved > 6) { e.preventDefault(); e.stopPropagation(); }
    }, true);
  }

  /* ================= لاین افقی ================= */

  var reel = document.querySelector('[data-reel]');
  var reelFill = document.querySelector('.reel__fill');

  if (reel) {
    dragScroll(reel);

    var rtick = false;
    var items = [].slice.call(reel.querySelectorAll('.reel__item'));

    function reelPaint() {
      var box = reel.getBoundingClientRect();
      var mid = box.left + box.width / 2;
      var half = box.width / 2 || 1;

      /* هرچه از مرکز نوار دورتر، کمی کوچک‌تر، پایین‌تر و کم‌رنگ‌تر */
      if (!soft) {
        for (var i = 0; i < items.length; i++) {
          var el = items[i];
          var r  = el.getBoundingClientRect();
          if (r.right < box.left - 80 || r.left > box.right + 80) continue;

          var k = (r.left + r.width / 2 - mid) / half;
          if (k > 1.3) k = 1.3; else if (k < -1.3) k = -1.3;
          var a = Math.abs(k);

          el.style.transform =
            'translate3d(0,' + (a * a * 11).toFixed(1) + 'px,0) ' +
            'rotate(' + (k * 2.1).toFixed(2) + 'deg) ' +
            'scale(' + (1 - a * 0.055).toFixed(3) + ')';
          el.style.opacity = (1 - a * 0.24).toFixed(3);
        }
      }

      if (!reelFill) return;
      var m = reel.scrollWidth - reel.clientWidth;
      /* در حالت راست‌به‌چپ scrollLeft منفی می‌شود */
      var v = Math.abs(reel.scrollLeft);
      reelFill.style.width = (m > 0 ? Math.min(100, (v / m) * 100) : 0) + '%';
    }

    reel.addEventListener('scroll', function () {
      if (rtick) return;
      rtick = true;
      requestAnimationFrame(function () { reelPaint(); rtick = false; });
    }, { passive: true });

    reelPaint();
    window.addEventListener('resize', reelPaint);
    window.addEventListener('load', reelPaint);
  }

  /* ================= اسلایدر کمانی حوزه‌ها ================= */

  var stage = document.querySelector('[data-arc]');

  if (stage) {
    var cards  = [].slice.call(stage.querySelectorAll('[data-arc-card]'));
    var ghost  = stage.querySelector('[data-arc-ghost]');
    var pivot  = stage.querySelector('.arc__pivot svg');
    var nowEl  = document.querySelector('[data-arc-now]');
    var allEl  = document.querySelector('[data-arc-all]');
    var goBtns = document.querySelectorAll('[data-arc-go]');
    var toggle = document.querySelector('[data-arc-toggle]');
    var list   = document.querySelector('[data-arc-list]');
    var rows   = list ? list.querySelectorAll('.fieldrow[data-i]') : [];

    var n = cards.length;

    if (n) {
      var STEP  = 24 * Math.PI / 180;   /* فاصله‌ی زاویه‌ای دو کارت */
      var DEG   = 24;
      var R     = 300;
      var pxStep = 120;

      var pos = 0, target = 0, vel = 0, spread = 0, raf = null, cur = -1;
      var ready = false;

      if (allEl) allEl.textContent = pad2(n);

      function measure() {
        R = Math.max(265, Math.min(560, stage.clientWidth * 0.78));
        pxStep = R * Math.sin(STEP);
        var h = cards[0].offsetHeight || 260;
        stage.style.setProperty('--R', R.toFixed(0) + 'px');
        stage.style.setProperty('--ringtop', (h / 2).toFixed(0) + 'px');
      }

      function announce(k) {
        if (cur === k) return;
        var first = cur === -1;
        cur = k;

        cards.forEach(function (el, i) { el.classList.toggle('is-on', i === k); });

        if (nowEl) nowEl.textContent = pad2(k + 1);

        if (ghost && !first) {
          var name = cards[k].querySelector('.card__en').textContent.trim();
          ghost.classList.remove('is-swap');
          void ghost.offsetWidth;
          ghost.classList.add('is-swap');
          setTimeout(function () { ghost.textContent = name; }, 165);
        }

        rows.forEach(function (r) { r.classList.toggle('is-on', +r.dataset.i === k); });

        goBtns.forEach(function (b) {
          var dir = parseInt(b.dataset.arcGo, 10);
          b.disabled = (dir < 0 && k === 0) || (dir > 0 && k === n - 1);
        });
      }

      function layout() {
        for (var i = 0; i < n; i++) {
          var el = cards[i];
          var d  = i - pos;
          var ad = Math.abs(d);

          if (ad > 2.8) {
            el.style.opacity = '0';
            el.style.visibility = 'hidden';
            el.style.pointerEvents = 'none';
            continue;
          }

          el.style.visibility = 'visible';
          el.style.pointerEvents = 'auto';

          var a  = d * STEP;
          var x  = R * Math.sin(a) * spread;
          var y  = R * (1 - Math.cos(a)) * spread;
          var sc = (1 - Math.min(ad, 3) * 0.16) * (0.88 + 0.12 * spread);

          el.style.transform =
            'translate3d(' + x.toFixed(1) + 'px,' + y.toFixed(1) + 'px,0) ' +
            'rotate(' + (d * DEG * spread).toFixed(2) + 'deg) ' +
            'scale(' + sc.toFixed(3) + ')';

          el.style.opacity = (Math.max(0, 1 - ad * 0.36) * spread).toFixed(3);
          el.style.zIndex  = String(50 - Math.round(ad * 10));
        }

        if (pivot) pivot.style.setProperty('--spin', (pos * 46).toFixed(1) + 'deg');

        announce(Math.max(0, Math.min(n - 1, Math.round(pos))));
      }

      /* فنر نرم — فقط وقتی حرکتی هست کار می‌کند */
      function tick() {
        var d = target - pos;
        vel = vel * 0.76 + d * 0.17;
        pos += vel;

        if (spread < 1) spread = Math.min(1, spread + (soft ? 1 : 0.042));

        if (spread >= 1 && Math.abs(d) < 0.0007 && Math.abs(vel) < 0.0007) {
          pos = target; vel = 0; ready = true;
          layout(); raf = null; return;
        }

        layout();
        raf = requestAnimationFrame(tick);
      }

      function run() { if (!raf) raf = requestAnimationFrame(tick); }

      function goTo(k) {
        target = Math.max(0, Math.min(n - 1, k));
        run();
      }

      measure();
      layout();

      /* باز شدنِ بادبزنی وقتی بخش وارد کادر می‌شود */
      if (!('IntersectionObserver' in window) || soft) {
        spread = 1; ready = true; layout();
      } else {
        var aio = new IntersectionObserver(function (rw) {
          rw.forEach(function (r) {
            if (!r.isIntersecting) return;
            aio.disconnect();
            run();
          });
        }, { threshold: 0.2 });
        aio.observe(stage);
      }

      /* ---- کشیدن ---- */
      var down = false, sx = 0, p0 = 0, lx = 0, lt = 0, vpx = 0, moved = 0;

      function grab(e) {
        if (!ready) return;
        down = true; moved = 0;
        sx = e.clientX; p0 = pos; lx = e.clientX; lt = Date.now(); vpx = 0;
        vel = 0;
        if (raf) { cancelAnimationFrame(raf); raf = null; }
        stage.classList.add('is-drag');
        if (stage.setPointerCapture && e.pointerId != null) {
          try { stage.setPointerCapture(e.pointerId); } catch (err) {}
        }
      }

      function move(e) {
        if (!down) return;
        var dx = e.clientX - sx;
        moved = Math.abs(dx);
        pos = Math.max(-0.65, Math.min(n - 1 + 0.65, p0 - dx / pxStep));
        var t = Date.now();
        if (t - lt > 20) { vpx = (e.clientX - lx) / (t - lt); lx = e.clientX; lt = t; }
        layout();
      }

      function release() {
        if (!down) return;
        down = false;
        stage.classList.remove('is-drag');
        var flick = -vpx * 130 / pxStep;
        flick = Math.max(-1.5, Math.min(1.5, flick));
        goTo(Math.round(pos + flick));
      }

      stage.addEventListener('pointerdown', grab);
      stage.addEventListener('pointermove', move);
      stage.addEventListener('pointerup', release);
      stage.addEventListener('pointercancel', release);
      stage.addEventListener('lostpointercapture', release);
      stage.addEventListener('dragstart', function (e) { e.preventDefault(); });

      /* ---- کلیک روی کارت ---- */
      cards.forEach(function (el, i) {
        el.addEventListener('click', function (e) {
          if (moved > 6) { e.preventDefault(); return; }
          if (i === cur) { location.hash = '#works'; return; }
          goTo(i);
        });
      });

      /* ---- دکمه‌ها، کیبورد، ترک‌پد ---- */
      goBtns.forEach(function (b) {
        b.addEventListener('click', function () {
          goTo(cur + parseInt(b.dataset.arcGo, 10));
        });
      });

      stage.addEventListener('keydown', function (e) {
        if (e.key === 'ArrowLeft')  { e.preventDefault(); goTo(cur + 1); }
        if (e.key === 'ArrowRight') { e.preventDefault(); goTo(cur - 1); }
      });

      stage.addEventListener('wheel', function (e) {
        if (Math.abs(e.deltaX) < 6 || Math.abs(e.deltaX) <= Math.abs(e.deltaY)) return;
        e.preventDefault();
        goTo(cur + (e.deltaX > 0 ? 1 : -1));
      }, { passive: false });

      window.addEventListener('resize', function () { measure(); layout(); });

      /* ---- فهرست همه‌ی حوزه‌ها ---- */
      if (toggle && list) {
        toggle.addEventListener('click', function () {
          var open = list.hasAttribute('hidden');
          if (open) {
            list.removeAttribute('hidden');
            /* انیمیشن ردیف‌ها دوباره پخش شود */
            list.querySelectorAll('.fieldrow').forEach(function (r) {
              r.style.animation = 'none';
              void r.offsetWidth;
              r.style.animation = '';
            });
          } else {
            list.setAttribute('hidden', '');
          }
          toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
          toggle.textContent = open ? 'بستن فهرست' : 'نمایش همه‌ی حوزه‌ها';
        });

        rows.forEach(function (r) {
          r.addEventListener('click', function () { goTo(+r.dataset.i); });
        });
      }
    }
  }

  /* ================= تقویم ================= */

  var cal = document.querySelector('.cal');

  if (cal) {
    var months = JSON.parse(document.getElementById('cal-data').textContent);
    var idx = 0, pickDay = null, pickTime = null, pickHour = null, pickEnd = null;

    var dayEnd  = parseInt(cal.dataset.end, 10) || 19;
    var maxHour = parseInt(cal.dataset.max, 10) || 4;

    var durBox = cal.querySelector('.cal__dur');
    var durs   = cal.querySelector('.durs');

    function fa(n) {
      return String(n).replace(/[0-9]/g, function (d) { return '۰۱۲۳۴۵۶۷۸۹'[+d]; });
    }

    function clock(h) { return fa(h < 10 ? '0' + h : h) + ':۰۰'; }

    /* بعد از انتخاب ساعت شروع، گزینه‌های «تا ساعت» ساخته می‌شوند */
    function buildDurs() {
      if (!durs || pickHour === null) return;
      var n = Math.min(maxHour, dayEnd - pickHour);
      var html = '';

      for (var i = 1; i <= n; i++) {
        html += '<button class="dur" data-h="' + i + '">' +
                  '<span class="dur__t">' + clock(pickHour + i) + '</span>' +
                  '<span class="dur__h">' + fa(i) + ' ساعت</span>' +
                '</button>';
      }

      durs.innerHTML = html;
      durBox.hidden = false;
      cal.classList.add('is-dur');
    }

    function clearDurs() {
      pickEnd = null;
      if (!durs) return;
      durs.innerHTML = '';
      durBox.hidden = true;
      cal.classList.remove('is-dur');
    }

    var grid  = cal.querySelector('.cal__grid');
    var label = cal.querySelector('.cal__month');
    var prev  = cal.querySelector('[data-go="prev"]');
    var next  = cal.querySelector('[data-go="next"]');
    var sum   = cal.querySelector('.cal__sum');
    var go    = cal.querySelector('.cal__go');

    var WD = ['ش', 'ی', 'د', 'س', 'چ', 'پ', 'ج'];

    function draw() {
      var m = months[idx];
      label.textContent = m.label;
      prev.disabled = idx === 0;
      next.disabled = idx === months.length - 1;

      var html = WD.map(function (w) { return '<div class="cal__wd">' + w + '</div>'; }).join('');

      m.cells.forEach(function (c) {
        if (!c.d) { html += '<div class="cal__cell"></div>'; return; }
        var cls = 'cal__day';
        if (c.past)      cls += ' cal__day--past';
        else if (c.free) cls += ' cal__day--free';
        else             cls += ' cal__day--busy';
        if (c.today) cls += ' cal__today';
        html += '<div class="cal__cell"><button class="' + cls + '" data-free="' +
                (c.free && !c.past ? 1 : 0) + '"><span>' + c.fa + '</span></button></div>';
      });

      grid.innerHTML = html;
    }

    function say() {
      go.disabled = true;

      if (!pickDay) { sum.innerHTML = 'یک روز آزاد را انتخاب کنید.'; return; }
      if (!pickTime) { sum.innerHTML = '<b>' + pickDay + '</b> — ساعت شروع را انتخاب کنید.'; return; }

      if (!pickEnd) {
        sum.innerHTML = '<b>' + pickDay + '</b>، از <b>' + pickTime + '</b> — تا چه ساعتی؟';
        return;
      }

      sum.innerHTML = '<b>' + pickDay + '</b>، از <b>' + pickTime + '</b> تا <b>' +
                      clock(pickEnd) + '</b> (' + fa(pickEnd - pickHour) + ' ساعت)';
      go.disabled = false;
    }

    grid.addEventListener('click', function (e) {
      var b = e.target.closest('.cal__day');
      if (!b || b.dataset.free !== '1') return;
      grid.querySelectorAll('.cal__day').forEach(function (x) { x.classList.remove('is-pick'); });
      b.classList.add('is-pick');
      pickDay = b.querySelector('span').textContent + ' ' + months[idx].label;
      say();
    });

    function resetTime() {
      pickTime = null; pickHour = null;
      cal.querySelectorAll('.slot').forEach(function (x) { x.classList.remove('is-pick'); });
      clearDurs();
    }

    prev.addEventListener('click', function () { if (idx > 0) { idx--; pickDay = null; resetTime(); draw(); say(); } });
    next.addEventListener('click', function () { if (idx < months.length - 1) { idx++; pickDay = null; resetTime(); draw(); say(); } });

    cal.querySelectorAll('.slot').forEach(function (el) {
      el.addEventListener('click', function () {
        cal.querySelectorAll('.slot').forEach(function (x) { x.classList.remove('is-pick'); });
        el.classList.add('is-pick');
        pickTime = el.textContent.trim();
        pickHour = parseInt(el.dataset.h, 10);
        clearDurs();
        buildDurs();
        say();
      });
    });

    if (durs) {
      durs.addEventListener('click', function (e) {
        var b = e.target.closest('.dur');
        if (!b) return;
        durs.querySelectorAll('.dur').forEach(function (x) { x.classList.remove('is-pick'); });
        b.classList.add('is-pick');
        pickEnd = pickHour + parseInt(b.dataset.h, 10);
        say();
      });
    }

    cal.querySelectorAll('.cal__tab').forEach(function (tab) {
      tab.addEventListener('click', function () {
        cal.querySelectorAll('.cal__tab').forEach(function (t) { t.classList.remove('is-on'); });
        tab.classList.add('is-on');
        cal.querySelectorAll('.cal__pane').forEach(function (p) {
          p.hidden = p.dataset.pane !== tab.dataset.tab;
        });
      });
    });

    cal.querySelectorAll('.wday--free').forEach(function (w) {
      w.addEventListener('click', function () {
        cal.querySelectorAll('.wday').forEach(function (x) { x.classList.remove('is-pick'); });
        w.classList.add('is-pick');
        pickDay = w.dataset.day;
        say();
      });
    });

    draw();
    say();
  }

  /* ================= لایت‌باکس ================= */

  var box    = document.querySelector('.box');
  var track  = document.querySelector('.box__track');
  var nameEl = document.querySelector('.box__name');
  var fill   = document.querySelector('.box__fill');

  function paint() {
    if (!track) return;
    var b  = track.getBoundingClientRect();
    var cx = b.left + b.width / 2;

    track.querySelectorAll('.shot').forEach(function (s) {
      var r = s.getBoundingClientRect();
      var d = (r.left + r.width / 2) - cx;
      var k = Math.max(-1.6, Math.min(1.6, d / (b.width * 0.42)));
      var a = Math.abs(k);
      s.style.transform =
        'rotateY(' + (-k * 30) + 'deg) translateZ(' + (-a * 120) + 'px) scale(' + (1 - a * 0.1) + ')';
      s.style.filter  = 'blur(' + (a * 2).toFixed(2) + 'px) brightness(' + (1 - a * 0.22) + ')';
      s.style.opacity = String(Math.max(0.3, 1 - a * 0.45));
      s.style.zIndex  = String(100 - Math.round(a * 100));
    });

    if (fill) {
      var m = track.scrollWidth - track.clientWidth;
      var v = Math.abs(track.scrollLeft);
      fill.style.width = (m > 0 ? (v / m) * 100 : 0) + '%';
    }
  }

  function openBox(name, shots) {
    if (!box) return;
    nameEl.textContent = name;
    track.innerHTML = shots.map(function (src) {
      return '<div class="shot"><img src="' + src + '" alt="" draggable="false"></div>';
    }).join('');
    box.classList.add('is-open');
    document.body.classList.add('is-locked');
    track.scrollLeft = 0;
    setTimeout(paint, 80);
  }

  function closeBox() {
    if (!box) return;
    box.classList.remove('is-open');
    document.body.classList.remove('is-locked');
  }

  document.querySelectorAll('.work').forEach(function (w) {
    w.addEventListener('click', function () {
      openBox(w.dataset.name || '', JSON.parse(w.dataset.shots || '[]'));
    });
  });

  var closer = document.querySelector('.box__close');
  if (closer) closer.addEventListener('click', closeBox);
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') closeBox(); });

  if (track) {
    var tick = false;
    track.addEventListener('scroll', function () {
      if (tick) return;
      tick = true;
      requestAnimationFrame(function () { paint(); tick = false; });
    }, { passive: true });

    dragScroll(track);
  }
})();
