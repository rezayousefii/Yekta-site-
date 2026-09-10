"""میدل‌ورهای کوچک پروژه‌ی یکتا."""


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
