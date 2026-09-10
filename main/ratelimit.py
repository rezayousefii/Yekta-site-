"""
محدودکردن نرخ درخواست.

جلوی سه چیز را می‌گیرد: حدس‌زدن رمز، ثبت‌نام انبوه ربات‌ها، و اسپم فرم
پشتیبانی. قفلِ حساب (در مدل Account) مکمل این است نه جایگزینش: آن یکی
یک حساب را می‌بندد، این یکی یک IP را.

شمارنده در کش می‌نشیند. با کش پیش‌فرضِ درون‌حافظه، هر پردازه شمارنده‌ی
خودش را دارد؛ یعنی با N ورکر، سقف عملاً N برابر می‌شود. برای سخت‌گیری
دقیق‌تر روی سرور، CACHES را به Redis وصل کن (نگاه کن به DEPLOY.md).
"""

from functools import wraps

from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import render


def client_key(request, tag):
    fwd = request.META.get("HTTP_X_FORWARDED_FOR")
    ip = fwd.split(",")[0].strip() if fwd else request.META.get("REMOTE_ADDR", "?")
    return "rl:%s:%s" % (tag, ip)


def hit(request, tag, limit, window):
    """
    یک ضربه ثبت می‌کند و می‌گوید آیا از سقف رد شده یا نه.

    شمارنده با اولین ضربه ساخته می‌شود و پس از window ثانیه خودش می‌رود؛
    یعنی پنجره‌ی ثابت است، نه لغزان — برای این کار کافی است و ساده می‌ماند.
    """
    key = client_key(request, tag)

    try:
        added = cache.add(key, 1, window)
        count = 1 if added else (cache.incr(key) if cache.get(key) is not None else 1)
    except ValueError:
        # کلید بین add و incr منقضی شده؛ از نو می‌شماریم
        cache.set(key, 1, window)
        count = 1

    return count > limit


def throttle(tag, limit, window, message="تعداد درخواست‌ها زیاد شد. کمی بعد دوباره امتحان کن."):
    """
    فقط روی POST می‌شمارد (مگر tag با «get:» شروع شود).

    خواندن صفحه‌ها آزاد می‌ماند؛ چیزی که باید محدود شود، فرستادن است.
    """
    count_gets = tag.startswith("get:")

    def wrap(view):
        @wraps(view)
        def guard(request, *args, **kwargs):
            if (count_gets or request.method == "POST") and hit(request, tag, limit, window):
                if request.headers.get("X-Requested-With") == "fetch":
                    return JsonResponse({"ok": False, "error": message}, status=429)
                return render(request, "429.html", {"message": message}, status=429)
            return view(request, *args, **kwargs)
        return guard
    return wrap
