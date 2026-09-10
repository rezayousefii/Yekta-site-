"""
بک‌اند ورود سفارشی.

دو کار می‌کند:
  ۱) ورود با «جی‌میل یا شماره تلفن» — هر دو به یک حساب می‌رسند.
  ۲) قفل‌شدن حساب بعد از چند تلاش ناموفق را واقعاً اجرا می‌کند؛ بدون این،
     فیلدهای failed_logins/locked_until فقط تزیینی بودند.
"""

from django.contrib.auth.backends import ModelBackend

from .models import Account, clean_phone


class LockoutBackend(ModelBackend):

    def _find(self, raw):
        """ورودی را — چه ایمیل باشد چه شماره — به یک حساب می‌رساند."""
        raw = (raw or "").strip()
        if not raw:
            return None

        phone = clean_phone(raw)
        if phone:
            return Account.objects.filter(phone=phone).first()
        return Account.objects.filter(email=raw.lower()).first()

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None

        user = self._find(username)

        if user is None:
            # حتی وقتی کاربر پیدا نشد، یک هش بی‌مصرف چک می‌کنیم تا زمان پاسخ
            # لو ندهد که این ایمیل/شماره اصلاً ثبت‌نام کرده یا نه
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
