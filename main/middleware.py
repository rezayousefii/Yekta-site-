"""میدل‌ورهای کوچک پروژه‌ی یکتا."""

from django.utils import timezone

from .models import VisitDay


class DisableCSRFInDebugMiddleware:
    """
    فقط وقتی DEBUG=True فعال می‌شود (از settings.py اضافه می‌شود، نه همیشه).

    چرا لازم بود: حذف CsrfViewMiddleware از MIDDLEWARE کافی نیست، چون
    django.contrib.auth.views.LoginView / LogoutView و چند ویوی built-in
    دیگر جنگو، خودشان مستقیماً با دکوریتور csrf_protect قفل‌شده‌اند — این
    قفل به MIDDLEWARE ربطی ندارد و همیشه اجرا می‌شود.

    request._dont_enforce_csrf_checks یک پرچم رسمی خودِ جنگوست (دقیقاً همان
    چیزی که خودِ CsrfViewMiddleware.process_view در ابتدا چک می‌کند) و هم
    میدل‌ور سراسری و هم دکوریتور csrf_protect روی ویوهای built-in را با هم
    خاموش می‌کند.

    روی سرور واقعی (DEBUG=False) این میدل‌ور اصلاً به MIDDLEWARE اضافه
    نمی‌شود، پس CSRF کامل و عادی فعال می‌ماند.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request._dont_enforce_csrf_checks = True
        return self.get_response(request)


class VisitCounterMiddleware:
    """
    شمارش بازدید برای نمودار پنل.

    فقط یک عدد در روزِ جاری بالا می‌رود. هیچ IP یا اثر انگشتی ذخیره نمی‌شود؛
    «بازدیدکننده‌ی تازه» هم فقط با یک نشانه در نشستِ خود مرورگر تشخیص داده
    می‌شود. درخواست‌های پنل، فایل‌های استاتیک و رسانه شمرده نمی‌شوند.
    """

    SKIP = ("/admin/", "/static/", "/media/", "/api/", "/favicon")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        try:
            if (request.method == "GET"
                    and response.status_code == 200
                    and not request.path.startswith(self.SKIP)):
                fresh = not request.session.get("seen")
                if fresh:
                    request.session["seen"] = timezone.now().isoformat()
                VisitDay.bump(fresh=fresh)
        except Exception:
            # شمارش بازدید هرگز نباید جلوی سرو شدن صفحه را بگیرد
            pass

        return response


class SecurityHeadersMiddleware:
    """
    سرسختی‌های امنیتی که جنگو خودش نمی‌گذارد.

    مهم‌ترینش Content-Security-Policy است: هیچ اسکریپت، استایل یا تصویری از
    دامنه‌ی دیگری بار نمی‌شود. سایت عمداً هیچ CDN خارجی ندارد، پس این قاعده
    چیزی را نمی‌شکند و در عوض دستِ مهاجم را برای بارکردن کد از بیرون می‌بندد.

    'unsafe-inline' مانده چون چند بلوک درون‌خطی هست (کلاس js در <head> و
    داده‌ی تقویم با json_script). خطِ دفاعِ اصلی در برابر XSS همچنان
    escape خودکار قالب‌های جنگوست؛ این سرآیند لایه‌ی دوم است، نه اول.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.path.startswith("/admin/"):
            return response

        response.setdefault("Content-Security-Policy", "; ".join([
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline'",
            "style-src 'self' 'unsafe-inline'",
            # کاشی‌های نقشه در فرم ثبت‌نام تنها منبع بیرونیِ مجازند؛ خودِ
            # کتابخانه‌ی Leaflet محلی است و از CDN نمی‌آید.
            "img-src 'self' data: blob: https://*.tile.openstreetmap.org",
            "media-src 'self' blob:",
            "font-src 'self' data:",
            "connect-src 'self'",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'",
            "object-src 'none'",
        ]))
        response.setdefault("Permissions-Policy",
                            "geolocation=(self), microphone=(), camera=()")
        response.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        response.setdefault("X-Content-Type-Options", "nosniff")

        return response
