"""
بک‌اند ورود سفارشی — همان قفل‌شدن بعد از چند تلاش ناموفق که در مدل Account
تعریف شده بود را واقعاً اجرا می‌کند. بدون این فایل، آن فیلدها فقط تزیینی بودند.
"""

from django.contrib.auth.backends import ModelBackend

from .models import Account


class LockoutBackend(ModelBackend):

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None

        try:
            user = Account.objects.get(email=username.strip().lower())
        except Account.DoesNotExist:
            # حتی وقتی کاربر پیدا نشد، یک هش بی‌مصرف چک می‌کنیم تا زمان پاسخ
            # لو ندهد که این ایمیل اصلاً ثبت‌نام کرده یا نه (همان کاری که خود جنگو می‌کند)
            Account().set_password(password)
            return None

        if user.is_locked:
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            ip = request.META.get("REMOTE_ADDR") if request else None
            user.note_good_login(ip=ip)
            return user

        user.note_failed_login()
        return None
