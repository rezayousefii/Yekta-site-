/* ===== یکتا — موتور صفحه‌ی اول ===== */
/* تم و نوار بالا در base.js هستند (چون روی همه‌ی صفحه‌ها لازم‌اند).
   اینجا فقط چیزهایی است که مخصوص صفحه‌ی اول‌اند. */

(function () {
  'use strict';

  var soft = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var doc  = document.documentElement;

  function faNum(n) {
    return String(n).replace(/[0-9]/g, function (d) { return '۰۱۲۳۴۵۶۷۸۹'[+d]; });
  }

  function pad2(n) { return faNum(n < 10 ? '0' + n : n); }

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
  var pitch  = document.querySelector('[data-pitch]');
  var bar    = document.querySelector('.bar');

  /* جای هر برگ روی مسیر ساقه و سمتی که باز می‌شود */
  var LEAF_AT   = [0.13, 0.26, 0.40, 0.54, 0.68, 0.82];
  var LEAF_SIDE = [1, -1, 1, -1, 1, -1];

  var stemLen = stem ? stem.getTotalLength() : 0;
  if (stem) stem.style.setProperty('--len', stemLen);

  var barH = bar ? bar.offsetHeight : 54;   /* گل از وسط نوار بالا راه می‌افتد */
  var kx = 1, ky = 1, topPad = 0;

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

  /* گل را دقیقاً روی نقطه‌ی p از طول ساقه می‌نشاند */
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

    /* بلوک دعوت: هرچه به مرکز صفحه نزدیک‌تر می‌شود، صاف‌تر می‌ایستد و
       بالا می‌آید — انگار از کف صفحه بلند می‌شود. */
    if (pitch) {
      var pb = pitch.getBoundingClientRect();
      if (pb.bottom > -200 && pb.top < vh + 200) {
        var t = (pb.top + pb.height / 2 - vh / 2) / vh;
        var clamped = Math.max(-1, Math.min(1, t));
        pitch.style.setProperty('--tiltx', (clamped * 5).toFixed(2) + 'deg');
        pitch.style.setProperty('--liftup', (Math.abs(clamped) * 14).toFixed(1) + 'px');
      }
    }
  }

  gauge();

  /* ================= اسکرول صفحه ================= */

  var busy = false;
  var calm = null;
  var lastY = window.scrollY;

  window.addEventListener('scroll', function () {
    var y = window.scrollY;
    var d = y - lastY;

    if (Math.abs(d) > 2) tilt = d > 0 ? 9 : -9;
    clearTimeout(calm);
    calm = setTimeout(function () {
      tilt = 0;
      if (flower) flower.style.setProperty('--tilt', '0deg');
    }, 260);

    if (!busy) {
      busy = true;
      requestAnimationFrame(function () { frame(y); busy = false; });
    }
    lastY = y;
  }, { passive: true });

  window.addEventListener('resize', function () { gauge(); frame(window.scrollY); });
  window.addEventListener('load', function () { gauge(); frame(window.scrollY); });
  frame(window.scrollY);

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
    }, { threshold: 0.08, rootMargin: '0px 0px -6% 0px' });
    reveal.forEach(function (el) { io.observe(el); });
  }

  /* ================= کشیدن افقی ================= */

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

    /* اگر کاربر کشیده باشد، کلیک نباید لینک را باز کند */
    el.addEventListener('click', function (e) {
      if (moved > 6) { e.preventDefault(); e.stopPropagation(); }
    }, true);

    el.addEventListener('dragstart', function (e) { e.preventDefault(); });
  }

  /* ================= اسلایدر نیم‌دار مجموعه‌ها ================= */

  var deck = document.querySelector('[data-deck]');

  if (deck) {
    var slides = [].slice.call(deck.querySelectorAll('[data-slide]'));
    var nowEl  = document.querySelector('[data-deck-now]');
    var allEl  = document.querySelector('[data-deck-all]');
    var fillEl = document.querySelector('[data-deck-fill]');
    var goBtns = document.querySelectorAll('[data-deck-go]');

    if (allEl) allEl.textContent = pad2(slides.length);

    dragScroll(deck);

    /* در راست‌به‌چپ، scrollLeft منفی می‌شود؛ همه‌جا با قدر مطلق کار می‌کنیم
       تا کد یک‌بار نوشته شود و در هر دو جهت درست بماند. */
    function deckPos() {
      var max = deck.scrollWidth - deck.clientWidth;
      return { v: Math.abs(deck.scrollLeft), max: max };
    }

    function nearest() {
      var box = deck.getBoundingClientRect();
      var mid = box.left + box.width / 2;
      var best = 0, bestD = Infinity;

      slides.forEach(function (s, i) {
        var r = s.getBoundingClientRect();
        var d = Math.abs(r.left + r.width / 2 - mid);
        if (d < bestD) { bestD = d; best = i; }
      });

      return best;
    }

    var cur = -1;

    function paintDeck() {
      var k = nearest();

      if (k !== cur) {
        cur = k;
        if (nowEl) nowEl.textContent = pad2(k + 1);
        goBtns.forEach(function (b) {
          var dir = parseInt(b.dataset.deckGo, 10);
          b.disabled = (dir < 0 && k === 0) || (dir > 0 && k === slides.length - 1);
        });
      }

      if (fillEl) {
        var p = deckPos();
        fillEl.style.width = (p.max > 0 ? Math.min(100, (p.v / p.max) * 100) : 100) + '%';
      }

      /* اسلایدهای کناری کمی کوچک‌تر و کم‌رنگ‌ترند: عمق می‌سازد و
         نگاه را روی اسلاید وسط نگه می‌دارد. */
      if (soft) return;

      var box = deck.getBoundingClientRect();
      var mid = box.left + box.width / 2;
      var half = box.width / 2 || 1;

      slides.forEach(function (s) {
        var r = s.getBoundingClientRect();
        if (r.right < box.left - 100 || r.left > box.right + 100) return;

        var d = (r.left + r.width / 2 - mid) / half;
        if (d > 1.4) d = 1.4; else if (d < -1.4) d = -1.4;
        var a = Math.abs(d);

        s.style.transform = 'translate3d(0,' + (a * a * 13).toFixed(1) + 'px,0) ' +
                            'scale(' + (1 - a * 0.06).toFixed(3) + ')';
        s.style.opacity = (1 - a * 0.3).toFixed(3);
      });
    }

    var dtick = false;
    deck.addEventListener('scroll', function () {
      if (dtick) return;
      dtick = true;
      requestAnimationFrame(function () { paintDeck(); dtick = false; });
    }, { passive: true });

    goBtns.forEach(function (b) {
      b.addEventListener('click', function () {
        var k = Math.max(0, Math.min(slides.length - 1, cur + parseInt(b.dataset.deckGo, 10)));
        slides[k].scrollIntoView({ behavior: soft ? 'auto' : 'smooth',
                                   block: 'nearest', inline: 'center' });
      });
    });

    paintDeck();
    window.addEventListener('resize', paintDeck);
    window.addEventListener('load', paintDeck);
  }

  /* ================= نوار متحرک عکس‌ها ================= */
  /* سرعت را از روی پهنای واقعی نوار حساب می‌کنیم، نه یک عدد ثابت: با کم و
     زیاد شدن عکس‌ها، سرعتِ حرکت یکسان می‌ماند. */

  var strip = document.querySelector('[data-strip-row]');

  if (strip && !soft) {
    var tuneStrip = function () {
      var w = strip.scrollWidth / 2;
      if (w > 0) strip.style.setProperty('--dur', Math.round(w / 34) + 's');
    };
    tuneStrip();
    window.addEventListener('load', tuneStrip);
    window.addEventListener('resize', tuneStrip);
  }

  /* ================= لاین افقی ================= */

  var reel = document.querySelector('[data-reel]');
  var reelFill = document.querySelector('.reel__fill');

  if (reel) {
    dragScroll(reel);

    var rtick = false;
    var items = [].slice.call(reel.querySelectorAll('.reel__item'));

    var reelPaint = function () {
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
      var v = Math.abs(reel.scrollLeft);
      reelFill.style.width = (m > 0 ? Math.min(100, (v / m) * 100) : 0) + '%';
    };

    reel.addEventListener('scroll', function () {
      if (rtick) return;
      rtick = true;
      requestAnimationFrame(function () { reelPaint(); rtick = false; });
    }, { passive: true });

    reelPaint();
    window.addEventListener('resize', reelPaint);
    window.addEventListener('load', reelPaint);
  }

})();
