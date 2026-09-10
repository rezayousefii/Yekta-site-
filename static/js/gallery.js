/* ===== یکتا — گالری ===== */
/* دو کار: ورودِ پلکانی قاب‌ها، و «بیشتر»ی که به‌جای پریدن به صفحه‌ی بعد،
   قاب‌های تازه را همان‌جا به ته شبکه می‌چسباند. */

(function () {
  'use strict';

  var soft = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ================= ورود قاب‌ها ================= */

  var seen = null;

  function watch(list) {
    if (soft || !('IntersectionObserver' in window)) {
      list.forEach(function (el) { el.classList.add('is-in'); });
      return;
    }

    if (!seen) {
      seen = new IntersectionObserver(function (rows) {
        rows.forEach(function (r) {
          if (!r.isIntersecting) return;
          /* تاخیر کوچکِ پلکانی بر اساس جای عکس در همان صفحه — نه ترتیب کلی،
             وگرنه قاب صدم یک ثانیه دیر می‌آمد. */
          var i = +(r.target.dataset.step || 0);
          setTimeout(function () { r.target.classList.add('is-in'); }, i * 45);
          seen.unobserve(r.target);
        });
      }, { rootMargin: '0px 0px 8% 0px', threshold: 0.02 });
    }

    list.forEach(function (el, i) {
      el.dataset.step = i % 8;
      seen.observe(el);
    });
  }

  watch([].slice.call(document.querySelectorAll('[data-pin]')));

  /* ================= «قاب‌های بیشتر» ================= */

  var grid = document.querySelector('[data-pins]');
  var btn  = document.querySelector('.more__btn');

  if (grid && btn && window.fetch) {
    btn.addEventListener('click', function (e) {
      e.preventDefault();

      var url = btn.getAttribute('href');
      if (!url || btn.classList.contains('is-busy')) return;

      btn.classList.add('is-busy');
      btn.textContent = 'در حال آوردن…';

      fetch(url, { headers: { 'X-Requested-With': 'fetch' } })
        .then(function (r) { return r.text(); })
        .then(function (html) {
          var doc = new DOMParser().parseFromString(html, 'text/html');
          var fresh = doc.querySelectorAll('[data-pins] [data-pin]');
          var next = doc.querySelector('.more__btn');

          var added = [];
          fresh.forEach(function (el) {
            var node = document.importNode(el, true);
            node.classList.remove('is-in');
            grid.appendChild(node);
            added.push(node);
          });

          watch(added);

          if (next) {
            btn.setAttribute('href', next.getAttribute('href'));
            btn.classList.remove('is-busy');
            btn.textContent = 'قاب‌های بیشتر';
          } else {
            btn.remove();
          }

          /* آدرس صفحه هم به‌روز می‌شود تا رفرش یا اشتراک‌گذاری همین‌جا بماند */
          try { history.replaceState(null, '', url); } catch (err) {}
        })
        .catch(function () {
          /* اگر شبکه قطع بود، همان رفتار عادی لینک انجام می‌شود */
          window.location.href = url;
        });
    });
  }

})();
