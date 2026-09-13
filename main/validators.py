"""قاعده‌های اعتبارسنجی سایت یکتا — رمز، شماره، آپلود، واژه‌های زشت."""

import re

from django.core.exceptions import ValidationError

from .profanity import find_bad

# هر چیزی که حرف، رقم یا فاصله نباشد «نشانه‌ی ویژه» حساب می‌شود: ! @ # $ % ...
SPECIAL = re.compile(r"[^\w\s]|_")
LETTER = re.compile(r"[A-Za-z؀-ۿ]")

# فقط این پسوندها آپلود می‌شوند. لیست سفید است، نه سیاه: هرچه اینجا نیست رد می‌شود.
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".avif"}
VIDEO_EXT = {".mp4", ".webm", ".mov"}

MAX_IMAGE_MB = 8
MAX_VIDEO_MB = 60


class StrongPassword:
    """دست‌کم ۸ نویسه، شامل حداقل یک حرف و یک نشانه‌ی ویژه."""

    def __init__(self, min_length=8):
        self.min_length = min_length

    def validate(self, password, user=None):
        problems = []

        if len(password) < self.min_length:
            problems.append("دست‌کم %d نویسه" % self.min_length)

        if not LETTER.search(password):
            problems.append("حداقل یک حرف")

        if not SPECIAL.search(password):
            problems.append("حداقل یک نشانه‌ی ویژه مثل ! یا @ یا #")

        if problems:
            raise ValidationError(
                "رمز باید این‌ها را داشته باشد: " + "، ".join(problems),
                code="password_too_weak",
            )

    def get_help_text(self):
        return ("دست‌کم %d نویسه، شامل حداقل یک حرف و یک نشانه‌ی ویژه مثل ! یا @"
                % self.min_length)


def validate_phone(value):
    """شماره‌ی موبایل ایران — خروجی همیشه ۱۱ رقمیِ «۰۹…» است."""
    # داخل تابع وارد می‌شود: این ماژول را جنگو ممکن است پیش از آماده‌شدن
    # اپ‌ها برای اعتبارسنجی رمز بخواند و آن‌وقت import مدل خطا می‌دهد.
    from .models import clean_phone

    out = clean_phone(value)
    if not out:
        raise ValidationError("شماره باید ۱۱ رقم باشد و با ۰۹ شروع شود.")
    if not out.startswith("09"):
        raise ValidationError("فقط شماره‌ی موبایل پذیرفته می‌شود (۰۹…).")
    return out


def validate_clean(value, what="این متن"):
    """اگر واژه‌ی زشتی در متن باشد، جلوی ثبت را می‌گیرد."""
    bad = find_bad(value)
    if bad:
        raise ValidationError(
            "%s واژه‌ی نامناسب دارد و پذیرفته نمی‌شود. لطفاً درستش کن." % what)
    return value


def _ext(name):
    return ("." + name.rsplit(".", 1)[-1].lower()) if "." in name else ""


def validate_image_upload(f):
    """
    پسوند و حجم تصویر را چک می‌کند.

    این جای اعتبارسنجی خودِ ImageField را نمی‌گیرد (که واقعاً فایل را باز
    می‌کند)؛ کنارش می‌نشیند تا فایل غول‌پیکر یا پسوند اجراشدنی اصلاً به
    دیسک نرسد.
    """
    if not f:
        return f
    if _ext(f.name) not in IMAGE_EXT:
        raise ValidationError("فقط JPG، PNG، WEBP یا AVIF قبول می‌شود.")
    if f.size > MAX_IMAGE_MB * 1024 * 1024:
        raise ValidationError("حجم تصویر بیشتر از %d مگابایت است." % MAX_IMAGE_MB)
    return f


def validate_video_upload(f):
    if not f:
        return f
    if _ext(f.name) not in VIDEO_EXT:
        raise ValidationError("فقط MP4، WEBM یا MOV قبول می‌شود.")
    if f.size > MAX_VIDEO_MB * 1024 * 1024:
        raise ValidationError("حجم ویدیو بیشتر از %d مگابایت است." % MAX_VIDEO_MB)
    return f
