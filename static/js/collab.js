/* ===== یکتا — ویزارد درخواست همکاری ===== */
/* پنج قدم، یک خلاصه‌ی زنده، و یک تقویم که ساعت‌های پرِ هر روز را از سرور
   می‌پرسد. هیچ چیزی در localStorage نمی‌ماند: اگر کاربر وارد نشده باشد،
   سرور خودش انتخاب‌ها را در نشست نگه می‌دارد و بعد از ثبت‌نام برمی‌گرداند. */

(function () {
  'use strict';

  var form = document.querySelector('[data-wz]');
  if (!form) return;

  var CFG  = window.YEKTA_BOOK || {};
  var soft = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function fa(n) {
    return String(n).replace(/[0-9]/g, function (d) { return '۰۱۲۳۴۵۶۷۸۹'[+d]; });
  }

  function clock(h) { return fa(h < 10 ? '0' + h : h) + ':۰۰'; }

  function money(n) {
    return fa(String(n).replace(/\B(?=(\d{3})+(?!\d))/g, '٬'));
  }

  function digits(s) {
    return String(s || '')
      .replace(/[۰-۹]/g, function (d) { return '۰۱۲۳۴۵۶۷۸۹'.indexOf(d); })
      .replace(/[٠-٩]/g, function (d) { return '٠١٢٣٤٥٦٧٨٩'.indexOf(d); })
      .replace(/[^\d]/g, '');
  }

  /* ================= اجزا ================= */

  var panes  = [].slice.call(form.querySelectorAll('[data-wz-pane]'));
  var steps  = [].slice.call(form.querySelectorAll('[data-wz-steps] li'));
  var barFil = form.querySelector('[data-wz-bar]');
  var backBt = form.querySelector('[data-wz-back]');
  var nextBt = form.querySelector('[data-wz-next]');
  var sendBt = form.querySelector('[data-wz-send]');
  var alertB = form.querySelector('[data-wz-alert]');

  var fDate  = form.querySelector('[data-f-date]');
  var fHour  = form.querySelector('[data-f-hour]');
  var fHours = form.querySelector('[data-f-hours]');

  var sum = {
    kind:   document.querySelector('[data-sum-kind]'),
    type:   document.querySelector('[data-sum-type]'),
    place:  document.querySelector('[data-sum-place]'),
    budget: document.querySelector('[data-sum-budget]'),
    date:   document.querySelector('[data-sum-date]'),
    time:   document.querySelector('[data-sum-time]')
  };

  var at = 0;

  function say(el, text, good) {
    if (!el) return;
    el.textContent = text || '—';
    el.classList.toggle('is-set', !!good);
    if (good) {
      el.classList.remove('is-hit');
      void el.offsetWidth;
      el.classList.add('is-hit');
    }
  }

  function warn(text) {
    if (!alertB) return;
    if (!text) { alertB.hidden = true; return; }
    alertB.textContent = text;
    alertB.hidden = false;
  }

  /* ================= رفت‌وآمد بین قدم‌ها ================= */

  function show(i, quiet) {
    at = Math.max(0, Math.min(panes.length - 1, i));

    panes.forEach(function (p, k) { p.classList.toggle('is-on', k === at); });

    steps.forEach(function (s, k) {
      s.classList.toggle('is-on', k === at);
      s.classList.toggle('is-done', k < at);
    });

    if (barFil) barFil.style.width = ((at + 1) / panes.length * 100).toFixed(1) + '%';

    backBt.hidden = at === 0;
    nextBt.hidden = at === panes.length - 1;
    sendBt.hidden = at !== panes.length - 1;

    warn('');

    if (!quiet && !soft) {
      var top = form.getBoundingClientRect().top + window.scrollY - 80;
      if (window.scrollY > top) window.scrollTo({ top: top, behavior: 'smooth' });
    }
  }

  /* هر قدم شرط خودش را دارد — بدون آن‌ها کاربر تا قدم آخر می‌رفت و
     تازه آنجا می‌فهمید چیزی جا مانده. */
  function blocking(i) {
    if (i === 0) {
      if (!form.querySelector('input[name="kind"]:checked')) return 'نوع همکاری را انتخاب کن.';
      if (!form.querySelector('input[name="model_type"]:checked')) return 'نوع مدلینگ را انتخاب کن.';
    }

    if (i === 1) {
      if (!form.querySelector('input[name="place_ref"]:checked')) return 'محل کار را انتخاب کن.';
    }

    if (i === 2) {
      var mode = form.querySelector('input[name="budget_mode"]:checked');
      if (mode && mode.value === 'set') {
        var n = parseInt(digits(moneyIn.value), 10) || 0;
        if (!n) return 'مبلغ را بنویس، یا «در درخواست ذکر می‌کنم» را انتخاب کن.';
        if (CFG.floor && n < CFG.floor) return 'کف بودجه ' + money(CFG.floor) + ' تومان است.';
      }
    }

    if (i === 3) {
      if (!fDate.value) return 'یک روز آزاد را از تقویم انتخاب کن.';
      if (!fHour.value) return 'ساعت شروع را انتخاب کن.';
      if (!fHours.value) return 'مشخص کن تا چه ساعتی.';
    }

    return null;
  }

  nextBt.addEventListener('click', function () {
    var stop = blocking(at);
    if (stop) { warn(stop); return; }
    show(at + 1);
  });

  backBt.addEventListener('click', function () { show(at - 1); });

  /* روی نوار قدم‌ها هم می‌شود پرید — ولی فقط عقب، نه جلو */
  steps.forEach(function (s, k) {
    s.addEventListener('click', function () { if (k < at) show(k); });
  });

  /* ================= خلاصه‌ی زنده ================= */

  function pickLabel(name) {
    var el = form.querySelector('input[name="' + name + '"]:checked');
    return el ? (el.dataset.label || '') : '';
  }

  function refreshPicks() {
    say(sum.kind, pickLabel('kind'), !!pickLabel('kind'));
    say(sum.type, pickLabel('model_type'), !!pickLabel('model_type'));
    say(sum.place, pickLabel('place_ref'), !!pickLabel('place_ref'));
  }

  form.addEventListener('change', function (e) {
    if (e.target.type === 'radio') { refreshPicks(); warn(''); }
  });

  /* ================= بودجه ================= */

  var moneyIn  = form.querySelector('[data-money]');
  var moneySay = form.querySelector('[data-money-say]');
  var moneyBox = form.querySelector('[data-budget-field]');

  function refreshBudget() {
    var mode = form.querySelector('input[name="budget_mode"]:checked');
    var isSet = !mode || mode.value === 'set';

    if (moneyBox) moneyBox.hidden = !isSet;

    if (!isSet) {
      say(sum.budget, 'در گفتگو مشخص می‌شود', true);
      if (moneySay) { moneySay.textContent = ''; moneySay.classList.remove('is-bad'); }
      return;
    }

    var n = parseInt(digits(moneyIn.value), 10) || 0;

    if (!n) {
      say(sum.budget, '', false);
      if (moneySay) { moneySay.textContent = ''; moneySay.classList.remove('is-bad'); }
      return;
    }

    if (CFG.floor && n < CFG.floor) {
      if (moneySay) {
        moneySay.textContent = 'کمتر از کف بودجه است — دست‌کم ' + money(CFG.floor) + ' تومان.';
        moneySay.classList.add('is-bad');
      }
      say(sum.budget, '', false);
      return;
    }

    if (moneySay) {
      moneySay.textContent = money(n) + ' تومان';
      moneySay.classList.remove('is-bad');
    }
    say(sum.budget, money(n) + ' تومان', true);
  }

  if (moneyIn) {
    /* عدد را همان لحظه سه‌رقم‌سه‌رقم و فارسی نشان می‌دهیم؛ مقدار خام
       موقع ارسال دوباره از همین رشته بیرون کشیده می‌شود. */
    moneyIn.addEventListener('input', function () {
      var raw = digits(moneyIn.value);
      moneyIn.value = raw ? money(raw) : '';
      refreshBudget();
    });

    form.querySelectorAll('[data-money-set]').forEach(function (b) {
      b.addEventListener('click', function () {
        moneyIn.value = money(b.dataset.moneySet);
        refreshBudget();
      });
    });

    form.querySelectorAll('[data-money-add]').forEach(function (b) {
      b.addEventListener('click', function () {
        var now = parseInt(digits(moneyIn.value), 10) || 0;
        moneyIn.value = money(now + parseInt(b.dataset.moneyAdd, 10));
        refreshBudget();
      });
    });

    form.querySelectorAll('input[name="budget_mode"]').forEach(function (r) {
      r.addEventListener('change', refreshBudget);
    });
  }

  /* ================= تقویم ================= */

  var months = [];
  try { months = JSON.parse(document.getElementById('cal-data').textContent) || []; }
  catch (e) { months = []; }

  var calBox  = form.querySelector('[data-cal]');
  var grid    = form.querySelector('[data-cal-grid]');
  var monthEl = form.querySelector('[data-cal-month]');
  var msgEl   = form.querySelector('[data-cal-msg]');
  var timeBox = form.querySelector('[data-cal-time]');
  var durBox  = form.querySelector('[data-cal-dur]');
  var dursEl  = form.querySelector('[data-durs]');
  var slots   = [].slice.call(form.querySelectorAll('.slot'));

  var mi = 0;
  var pickedISO = '', pickedLabel = '';
  var taken = [];
  var dayEnd = CFG.dayEnd || 19;
  var maxHours = CFG.maxHours || 4;

  var WD = ['ش', 'ی', 'د', 'س', 'چ', 'پ', 'ج'];

  function drawMonth() {
    if (!months.length) return;

    var m = months[mi];
    monthEl.textContent = m.label;

    form.querySelector('[data-go="prev"]').disabled = mi === 0;
    form.querySelector('[data-go="next"]').disabled = mi === months.length - 1;

    var html = WD.map(function (w) { return '<div class="cal__wd">' + w + '</div>'; }).join('');

    m.cells.forEach(function (c) {
      if (!c.d) { html += '<div class="cal__cell"></div>'; return; }

      var cls = 'cal__day';
      if (c.past) cls += ' cal__day--past';
      else if (c.free) cls += ' cal__day--free';
      else cls += ' cal__day--busy';
      if (c.today) cls += ' cal__today';
      if (c.iso === pickedISO) cls += ' is-pick';

      html += '<div class="cal__cell"><button type="button" class="' + cls + '"' +
              ' data-iso="' + c.iso + '"' +
              ' data-free="' + (c.free && !c.past ? 1 : 0) + '"' +
              (c.free && !c.past ? '' : ' disabled') +
              '><span>' + c.fa + '</span></button></div>';
    });

    grid.innerHTML = html;
  }

  function tell(text, ok) {
    msgEl.textContent = text || '';
    msgEl.classList.toggle('is-ok', !!ok);
  }

  function resetTime() {
    fHour.value = '';
    fHours.value = '';
    slots.forEach(function (s) { s.classList.remove('is-pick'); });
    dursEl.innerHTML = '';
    durBox.hidden = true;
    say(sum.time, '', false);
  }

  function paintSlots() {
    slots.forEach(function (s) {
      var h = parseInt(s.dataset.h, 10);
      var full = taken.indexOf(h) !== -1 || h >= dayEnd;
      s.disabled = full;
      s.title = full ? 'این ساعت پر است' : '';
    });
  }

  /* گزینه‌های «تا چه ساعتی».

     حلقه به‌محض رسیدن به اولین ساعتِ پر می‌شکند و مدت‌های بلندتر پیشنهاد
     نمی‌شوند. این درست است چون بازه‌ها پیوسته‌اند و فقط رو به جلو رشد
     می‌کنند: اگر مدت i به ساعت پرِ h بخورد، هر مدت بلندتر از i هم همان h
     را در بر می‌گیرد. این ناوردا را در هر بازنویسی حفظ کن. */
  function buildDurs(start) {
    var html = '';

    for (var i = 1; i <= maxHours; i++) {
      var last = start + i - 1;
      if (last >= dayEnd) break;
      if (taken.indexOf(last) !== -1) break;

      html += '<button type="button" class="dur" data-h="' + i + '">' +
                '<span class="dur__t">' + clock(start + i) + '</span>' +
                '<span class="dur__h">' + fa(i) + ' ساعت</span>' +
              '</button>';
    }

    dursEl.innerHTML = html;
    durBox.hidden = !html;

    if (!html) tell('از این ساعت به بعد جایی باز نیست. ساعت دیگری انتخاب کن.');
  }

  var loading = 0;

  function loadDay(iso, label) {
    var ticket = ++loading;

    tell('در حال گرفتن ساعت‌های آزاد…');
    timeBox.hidden = true;
    resetTime();

    fetch('/api/hours/?date=' + encodeURIComponent(iso), {
      headers: { 'X-Requested-With': 'fetch' }
    })
      .then(function (r) { return r.json(); })
      .then(function (d) {
        /* اگر کاربر در این فاصله روز دیگری زده، پاسخ قدیمی را دور می‌ریزیم */
        if (ticket !== loading) return;

        if (!d.ok) {
          tell(d.error || 'این روز قابل رزرو نیست.');
          pickedISO = '';
          fDate.value = '';
          say(sum.date, '', false);
          drawMonth();
          return;
        }

        taken = d.taken || [];
        dayEnd = d.day_end || dayEnd;
        maxHours = d.max_hours || maxHours;

        pickedISO = d.date;
        pickedLabel = d.label || label;
        fDate.value = d.date;

        say(sum.date, pickedLabel, true);

        paintSlots();
        timeBox.hidden = false;

        var free = slots.filter(function (s) { return !s.disabled; }).length;
        if (free) tell('ساعت شروع را انتخاب کن.', true);
        else tell('این روز کاملاً پر است. روز دیگری انتخاب کن.');
      })
      .catch(function () {
        if (ticket !== loading) return;
        tell('ارتباط با سرور برقرار نشد. دوباره امتحان کن.');
      });
  }

  if (grid) {
    grid.addEventListener('click', function (e) {
      var b = e.target.closest('.cal__day');
      if (!b || b.dataset.free !== '1') return;

      grid.querySelectorAll('.cal__day').forEach(function (x) { x.classList.remove('is-pick'); });
      b.classList.add('is-pick');

      loadDay(b.dataset.iso, b.querySelector('span').textContent + ' ' + months[mi].label);
    });

    form.querySelector('[data-go="prev"]').addEventListener('click', function () {
      if (mi > 0) { mi--; drawMonth(); }
    });

    form.querySelector('[data-go="next"]').addEventListener('click', function () {
      if (mi < months.length - 1) { mi++; drawMonth(); }
    });

    slots.forEach(function (s) {
      s.addEventListener('click', function () {
        if (s.disabled) return;
        slots.forEach(function (x) { x.classList.remove('is-pick'); });
        s.classList.add('is-pick');

        var h = parseInt(s.dataset.h, 10);
        fHour.value = h;
        fHours.value = '';
        say(sum.time, clock(h) + ' — مدت را انتخاب کن', false);

        buildDurs(h);
        tell('تا چه ساعتی؟', true);
      });
    });

    dursEl.addEventListener('click', function (e) {
      var b = e.target.closest('.dur');
      if (!b) return;

      dursEl.querySelectorAll('.dur').forEach(function (x) { x.classList.remove('is-pick'); });
      b.classList.add('is-pick');

      var n = parseInt(b.dataset.h, 10);
      var start = parseInt(fHour.value, 10);
      fHours.value = n;

      say(sum.time, clock(start) + ' تا ' + clock(start + n) + ' (' + fa(n) + ' ساعت)', true);
      tell('زمان انتخاب شد.', true);
      warn('');
    });

    drawMonth();
  }

  /* ================= ارسال ================= */

  var doneBox = document.querySelector('[data-done]');
  var doneMsg = document.querySelector('[data-done-msg]');

  function csrf() {
    var el = form.querySelector('[name="csrfmiddlewaretoken"]');
    return el ? el.value : '';
  }

  form.addEventListener('submit', function (e) {
    e.preventDefault();

    for (var i = 0; i < panes.length; i++) {
      var stop = blocking(i);
      if (stop) { show(i); warn(stop); return; }
    }

    var data = new FormData(form);
    data.set('budget_amount', digits(moneyIn ? moneyIn.value : ''));

    sendBt.disabled = true;
    sendBt.textContent = 'در حال ارسال…';
    warn('');

    fetch(form.action, {
      method: 'POST',
      body: data,
      headers: { 'X-CSRFToken': csrf(), 'X-Requested-With': 'fetch' },
      credentials: 'same-origin'
    })
      .then(function (r) { return r.json().then(function (d) { return { s: r.status, d: d }; }); })
      .then(function (out) {
        var d = out.d;

        if (d.ok) {
          if (doneBox) {
            if (doneMsg) doneMsg.textContent = d.message || '';
            doneBox.hidden = false;
          } else {
            window.location.href = d.next;
          }
          return;
        }

        /* مهمان: سرور انتخاب‌ها را در نشست نگه داشته، پس فقط می‌رویم ثبت‌نام */
        if (d.need === 'signup') {
          window.location.href = d.next;
          return;
        }

        sendBt.disabled = false;
        sendBt.textContent = CFG.signedIn ? 'ثبت درخواست' : 'ادامه و ساختن حساب';

        warn(d.error || 'ثبت نشد. دوباره امتحان کن.');

        /* ۴۰۹ یعنی همین حالا کسی همان بازه را گرفت — ساعت‌ها را تازه می‌کنیم */
        if (out.s === 409 && pickedISO) {
          show(3);
          loadDay(pickedISO, pickedLabel);
        }
      })
      .catch(function () {
        sendBt.disabled = false;
        sendBt.textContent = CFG.signedIn ? 'ثبت درخواست' : 'ادامه و ساختن حساب';
        warn('ارتباط با سرور برقرار نشد. اتصالت را چک کن.');
      });
  });

  /* ================= پیش‌پرکردن ================= */

  function checkByValue(name, value) {
    if (!value) return false;
    var el = form.querySelector('input[name="' + name + '"][value="' + value + '"]');
    if (!el) return false;
    el.checked = true;
    return true;
  }

  function checkByLabel(name, label) {
    if (!label) return false;
    var hit = null;
    form.querySelectorAll('input[name="' + name + '"]').forEach(function (el) {
      if (!hit && (el.dataset.label || '') === label) hit = el;
    });
    if (!hit) return false;
    hit.checked = true;
    return true;
  }

  /* از آدرس: /collab/?type=<slug>&place=<slug> — همان لینکی که زیر هر عکس است */
  var qs = new URLSearchParams(window.location.search);

  if (qs.get('type') || qs.get('place')) {
    /* اسلاگ در HTML نیست، پس با نام تطبیق می‌دهیم: نام‌ها همان چیزی‌اند
       که در صفحه‌ی عکس هم نشان داده شده‌اند. */
    var wantType = (qs.get('type') || '').replace(/-/g, ' ');
    var wantPlace = (qs.get('place') || '').replace(/-/g, ' ');
    checkByLabel('model_type', wantType);
    checkByLabel('place_ref', wantPlace);
  }

  /* از نشست سرور: درخواست نیمه‌تمامی که پیش از ثبت‌نام پر شده بود */
  var draft = null;
  try {
    var node = document.getElementById('draft-data');
    draft = node ? JSON.parse(node.textContent) : null;
  } catch (e) { draft = null; }

  refreshPicks();
  refreshBudget();

  if (draft && draft.date) {
    checkByValue('kind', draft.kind);
    checkByValue('model_type', draft.model_type);
    checkByValue('place_ref', draft.place_ref);

    var modeEl = form.querySelector('input[name="budget_mode"][value="' + draft.budget_mode + '"]');
    if (modeEl) modeEl.checked = true;
    if (moneyIn && draft.budget_amount) moneyIn.value = money(draft.budget_amount);

    form.querySelector('[name="place"]').value = draft.place || '';
    form.querySelector('[name="crew"]').value = draft.crew || '';
    form.querySelector('[name="brief"]').value = draft.brief || '';

    refreshPicks();
    refreshBudget();

    /* تاریخ باید دوباره از سرور تایید شود — ممکن است در این فاصله پر شده باشد */
    var monthOf = months.findIndex(function (m) {
      return m.cells.some(function (c) { return c.iso === draft.date; });
    });
    if (monthOf > -1) mi = monthOf;
    drawMonth();

    loadDay(draft.date, '');

    var wantHour = parseInt(draft.start_hour, 10);
    var wantLen  = parseInt(draft.hours, 10);

    /* پس از رسیدن ساعت‌های آزاد، همان انتخاب قبلی را دوباره می‌زنیم */
    var tries = 0;
    var replay = setInterval(function () {
      if (++tries > 40) { clearInterval(replay); return; }
      if (!fDate.value) return;

      clearInterval(replay);

      var slot = slots.filter(function (s) {
        return parseInt(s.dataset.h, 10) === wantHour && !s.disabled;
      })[0];

      if (slot) {
        slot.click();
        var dur = dursEl.querySelector('.dur[data-h="' + wantLen + '"]');
        if (dur) dur.click();
      } else {
        tell('ساعت قبلی‌ات پر شده — ساعت دیگری انتخاب کن.');
      }
    }, 120);

    show(panes.length - 1, true);
    warn('انتخاب‌های قبلی‌ات برگشت. فقط زمان را دوباره تایید کن و بفرست.');
  } else {
    show(0, true);
  }

})();
