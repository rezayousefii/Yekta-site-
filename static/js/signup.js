/* ===== ثبت‌نام کارفرما ===== */

(function () {
  'use strict';

  var form = document.querySelector('[data-wiz]');
  if (!form) return;

  var FA = '۰۱۲۳۴۵۶۷۸۹';
  function toLatin(s) {
    return String(s).replace(/[۰-۹٠-٩]/g, function (d) {
      var i = FA.indexOf(d);
      return i > -1 ? i : '٠١٢٣٤٥٦٧٨٩'.indexOf(d);
    });
  }

  /* ================= اعتبارسنجی زنده ================= */

  var RULES = {
    full_name: function (v) {
      if (v.trim().length < 3) return 'نام کامل را بنویس.';
    },
    email: function (v) {
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v.trim())) return 'ایمیل معتبر نیست.';
    },
    password: function (v) {
      var miss = [];
      if (v.length < 8) miss.push('۸ نویسه');
      if (!/[A-Za-z\u0600-\u06FF]/.test(v)) miss.push('یک حرف');
      if (!/[^\w\s]|_/.test(v)) miss.push('یک نشانه مثل ! یا @');
      if (miss.length) return 'کم دارد: ' + miss.join('، ');
    },
    password2: function (v) {
      var p = form.querySelector('[name="password"]');
      if (p && v !== p.value) return 'با رمز بالا یکی نیست.';
    },
    company: function (v) {
      if (v.trim().length < 2) return 'نام برند را بنویس.';
    },
    phone: function (v) {
      var n = toLatin(v).replace(/[\s\-()]/g, '').replace(/^\+98/, '0').replace(/^0098/, '0');
      if (!/^0\d{10}$/.test(n)) return 'شماره باید ۱۱ رقم باشد و با ۰ شروع شود.';
    },
  };

  var OPTIONAL = ['contact_name', 'instagram', 'city', 'address'];

  function fieldOf(el) { return el.closest('.fl'); }

  function say(el, msg) {
    var box = fieldOf(el);
    if (!box) return;

    var bad = box.querySelector('.fl__bad');
    box.classList.toggle('has-error', !!msg);
    box.classList.toggle('is-good', !msg && el.value.trim() !== '');

    if (msg) {
      if (!bad) {
        bad = document.createElement('small');
        bad.className = 'fl__bad';
        box.appendChild(bad);
      }
      bad.textContent = msg;
    } else if (bad) {
      bad.remove();
    }
  }

  /* آیا این فیلد الان قابل قبول است؟ (بدون نشان دادن خطا) */
  function ok(el) {
    var name = el.name;
    var v = el.value;

    if (OPTIONAL.indexOf(name) === -1 && !v.trim() && el.type !== 'hidden') return false;
    if (!v.trim()) return true;

    var rule = RULES[name];
    return rule ? !rule(v) : true;
  }

  function check(el) {
    var name = el.name;
    var v = el.value;

    if (!v.trim()) {
      say(el, OPTIONAL.indexOf(name) === -1 ? 'این فیلد لازم است.' : '');
      return;
    }

    var rule = RULES[name];
    say(el, rule ? (rule(v) || '') : '');
  }

  /* ================= نمونه‌ی سبز زیر فیلد ================= */

  form.querySelectorAll('.fl').forEach(function (box) {
    var el = box.querySelector('input, textarea, select');
    if (!el) return;

    var hint = el.dataset.hint;
    if (hint) {
      var eg = document.createElement('div');
      eg.className = 'fl__eg';
      eg.innerHTML = '<span>' + hint + '</span>';
      box.appendChild(eg);
    }

    el.addEventListener('focus', function () { box.classList.add('is-focus'); });

    el.addEventListener('blur', function () {
      box.classList.remove('is-focus');
      check(el);
      gate();
    });

    el.addEventListener('input', function () {
      if (box.classList.contains('has-error')) check(el);
      if (el.name === 'password') meter(el.value);
      gate();
    });
  });

  /* ================= سنجه‌ی رمز ================= */

  var meterEl = form.querySelector('.meter');

  function meter(v) {
    if (!meterEl) return;
    var score = 0;
    if (v.length >= 8) score++;
    if (/[A-Za-z\u0600-\u06FF]/.test(v) && /\d/.test(v)) score++;
    if (/[^\w\s]|_/.test(v)) score++;
    meterEl.dataset.level = v ? score : 0;
  }

  /* ================= گام‌ها ================= */

  var panes = [].slice.call(form.querySelectorAll('.wiz__pane'));
  var steps = [].slice.call(document.querySelectorAll('.wiz__steps li'));
  var bar   = document.querySelector('.wiz__bar');
  var bloom = document.querySelector('.auth__bloom .spin');
  var back  = form.querySelector('[data-back]');
  var next  = form.querySelector('[data-next]');
  var send  = form.querySelector('[data-send]');

  var at = 0;

  /* فقط فیلدهای واقعی فرم — کادر کمکی «افزودن لینک» نام ندارد و شمرده نمی‌شود */
  function fieldsOf(pane) {
    return [].slice.call(pane.querySelectorAll('[name]:not([type=hidden])'));
  }

  function labelOf(el) {
    var box = fieldOf(el);
    var sp = box && box.querySelector(':scope > span');
    return sp ? sp.textContent.trim() : el.name;
  }

  /* دکمه خاموش نمی‌شود — فقط کم‌رنگ می‌شود تا بشود زد و دلیلش را شنید */
  function gate() {
    var bad = fieldsOf(panes[at]).filter(function (el) { return !ok(el); });
    if (next) next.classList.toggle('is-wait', bad.length > 0);
    if (send) send.classList.toggle('is-wait', bad.length > 0);
  }

  /* پیام بالای گام: دقیقاً چه چیزی مانده */
  function alertMissing(list) {
    var box = panes[at].querySelector('.wiz__alert');

    if (!list.length) {
      if (box) box.remove();
      return;
    }

    if (!box) {
      box = document.createElement('div');
      box.className = 'wiz__alert';
      panes[at].insertBefore(box, panes[at].firstChild);
    }

    var names = list.map(labelOf);
    box.innerHTML = '<b>برای ادامه این‌ها مانده:</b> ' + names.join('، ');
  }

  function paint() {
    panes.forEach(function (p, i) { p.classList.toggle('is-on', i === at); });

    steps.forEach(function (s, i) {
      s.classList.toggle('is-on', i === at);
      s.classList.toggle('is-done', i < at);
    });

    if (bar) bar.style.setProperty('--prog', Math.round((at + 1) / panes.length * 100));
    if (bloom) bloom.style.setProperty('--turn', at);

    back.hidden = at === 0;
    next.hidden = at === panes.length - 1;
    send.hidden = at !== panes.length - 1;

    gate();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  next.addEventListener('click', function () {
    var bad = fieldsOf(panes[at]).filter(function (el) { return !ok(el); });

    fieldsOf(panes[at]).forEach(function (el) { check(el); });
    alertMissing(bad);

    if (bad.length) {
      bad[0].focus();
      bad[0].scrollIntoView({ behavior: 'smooth', block: 'center' });
      return;
    }

    at = Math.min(panes.length - 1, at + 1);
    paint();
  });

  /* موقع ارسال نهایی هم همان توضیح داده شود، نه یک ردِ خاموش */
  form.addEventListener('submit', function (e) {
    var bad = fieldsOf(panes[at]).filter(function (el) { return !ok(el); });
    if (!bad.length) return;

    e.preventDefault();
    fieldsOf(panes[at]).forEach(function (el) { check(el); });
    alertMissing(bad);
    bad[0].focus();
    bad[0].scrollIntoView({ behavior: 'smooth', block: 'center' });
  });

  back.addEventListener('click', function () {
    at = Math.max(0, at - 1);
    paint();
  });

  /* وقتی کاربر فیلد را درست کرد، پیام بالا هم تازه شود */
  form.addEventListener('input', function () {
    var box = panes[at].querySelector('.wiz__alert');
    if (!box) return;
    var bad = fieldsOf(panes[at]).filter(function (el) { return !ok(el); });
    alertMissing(bad);
  });

  /* اگر سرور خطا برگرداند، برو روی اولین گامی که خطا دارد */
  var firstBad = panes.findIndex(function (p) { return p.querySelector('.errorlist'); });
  if (firstBad > -1) at = firstBad;

  paint();

  /* ================= لینک‌های اختیاری ================= */

  var linkBox = form.querySelector('[data-links]');

  if (linkBox) {
    var list  = linkBox.querySelector('.links__list');
    var input = linkBox.querySelector('.links__in');
    var add   = linkBox.querySelector('[data-link-add]');
    var store = form.querySelector('[name="links"]');
    var urls  = [];

    function sync() {
      store.value = urls.join('\n');

      list.innerHTML = urls.map(function (u, i) {
        return '<li><a href="' + u + '" target="_blank" rel="noopener">' + u + '</a>' +
               '<button type="button" data-drop="' + i + '" aria-label="حذف">&times;</button></li>';
      }).join('');
    }

    function addLink() {
      var v = input.value.trim();
      if (!v) return;
      if (!/^https?:\/\//i.test(v)) v = 'https://' + v;
      if (urls.indexOf(v) === -1 && urls.length < 8) urls.push(v);
      input.value = '';
      sync();
    }

    add.addEventListener('click', addLink);

    input.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') { e.preventDefault(); addLink(); }
    });

    list.addEventListener('click', function (e) {
      var b = e.target.closest('[data-drop]');
      if (!b) return;
      urls.splice(+b.dataset.drop, 1);
      sync();
    });
  }

  /* ================= نقشه ================= */

  var frame = document.getElementById('map');
  if (!frame) return;

  var latIn  = form.querySelector('[name="lat"]');
  var lngIn  = form.querySelector('[name="lng"]');
  var addr   = form.querySelector('[name="address"]');
  var cityIn = form.querySelector('[name="city"]');
  var said   = document.querySelector('.mapbox__said');
  var here   = form.querySelector('[data-here]');
  var pick   = form.querySelector('[data-pick]');

  if (typeof window.L === 'undefined') {
    frame.innerHTML = '<div class="mapbox__off">' +
      '<b>نقشه در دسترس نیست</b>' +
      '<span>اشکالی ندارد — نشانی متنی بالا کافی است.</span></div>';
    if (here) here.disabled = true;
    if (pick) pick.disabled = true;
    return;
  }

  var AHVAZ = [31.3183, 48.6706];
  var start = (latIn.value && lngIn.value) ? [+latIn.value, +lngIn.value] : AHVAZ;

  var map = L.map(frame, { zoomControl: true }).setView(start, latIn.value ? 16 : 12);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; OpenStreetMap',
  }).addTo(map);

  var marker = L.marker(start, { draggable: true }).addTo(map);
  map.on('click', function (e) { marker.setLatLng(e.latlng); });

  function tell(text) {
    if (!said) return;
    said.textContent = text;
    said.classList.add('is-on');
  }

  function fillAddress(lat, lng) {
    tell('در حال یافتن نشانی…');

    var url = 'https://nominatim.openstreetmap.org/reverse'
            + '?format=json&zoom=18&addressdetails=1&accept-language=fa'
            + '&lat=' + lat + '&lon=' + lng;

    var stop = new AbortController();
    var timer = setTimeout(function () { stop.abort(); }, 8000);

    fetch(url, { headers: { 'Accept': 'application/json' }, signal: stop.signal })
      .then(function (r) {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.json();
      })
      .then(function (d) {
        clearTimeout(timer);

        if (d && d.display_name && addr) {
          addr.value = d.display_name;
          var a = d.address || {};
          var city = a.city || a.town || a.village || a.county;
          if (city && cityIn && !cityIn.value.trim()) cityIn.value = city;
          gate();
          tell('موقعیت و نشانی ثبت شد ✓');
        } else {
          tell('موقعیت ثبت شد ✓ — نشانی پیدا نشد، دستی بنویس');
        }
      })
      .catch(function (err) {
        clearTimeout(timer);
        console.warn('reverse geocode failed:', err);
        tell('موقعیت ثبت شد ✓ — سرویس نشانی در دسترس نیست، دستی بنویس');
      });
  }

  function confirmHere() {
    var p = marker.getLatLng();
    latIn.value = p.lat.toFixed(6);
    lngIn.value = p.lng.toFixed(6);
    fillAddress(latIn.value, lngIn.value);
  }

  if (pick) pick.addEventListener('click', confirmHere);

  if (here) {
    here.addEventListener('click', function () {
      if (!navigator.geolocation) { here.disabled = true; return; }

      here.textContent = 'در حال یافتن…';
      navigator.geolocation.getCurrentPosition(
        function (pos) {
          var p = [pos.coords.latitude, pos.coords.longitude];
          map.setView(p, 17);
          marker.setLatLng(p);
          here.textContent = 'موقعیت فعلی من';
          confirmHere();
        },
        function () { here.textContent = 'دسترسی داده نشد'; },
        { enableHighAccuracy: true, timeout: 8000 }
      );
    });
  }

  next.addEventListener('click', function () {
    setTimeout(function () { map.invalidateSize(); }, 250);
  });
})();
