"""
فیلتر واژه‌های زشت — روی نام، نام برند، نام رابط و متن‌های عمومی اجرا می‌شود.

چرا یک فایل جدا: فهرست باید بدون دست‌زدن به منطق فرم قابل کم و زیاد شدن باشد.
روش کار در سه گام است، چون کاربرِ بدخواه معمولاً واژه را دستکاری می‌کند:

  ۱) یکدست‌سازی: نویسه‌های عربی به فارسی، نیم‌فاصله و نویسه‌های نامرئی حذف،
     رقم‌هایی که جای حرف می‌نشینند (۳ به‌جای e، 0 به‌جای o) برگردانده می‌شوند.
  ۲) فشرده‌سازی: حرف‌های تکراری (کوووسکش) به یک حرف کم می‌شوند و
     جداکننده‌ها (فاصله، نقطه، خط تیره، ستاره) کنار می‌روند.
  ۳) تطبیق: هم روی متن یکدست‌شده و هم روی شکل فشرده‌اش جست‌وجو می‌شود.

نتیجه‌ی مثبت کاذب کم است چون فهرست فقط واژه‌های صریح است، نه واژه‌های دو پهلو.
"""

import re
import unicodedata

# نویسه‌های نامرئی و جداکننده‌هایی که برای دور زدن فیلتر استفاده می‌شوند
INVISIBLE = dict.fromkeys(map(ord, "‌‍‎‏‪‫‬﻿ـ"), None)

ARABIC_FIX = str.maketrans({
    "ي": "ی", "ك": "ک", "ۀ": "ه", "ة": "ه", "أ": "ا", "إ": "ا", "آ": "ا",
    "ؤ": "و", "ئ": "ی", "ٔ": "",
})

LEET = str.maketrans({
    "0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t", "@": "a",
    "$": "s", "۰": "o", "۱": "i", "۳": "e", "۴": "a", "۵": "s",
})

SEPARATORS = re.compile(r"[\s._\-*+~/\\|,،'\"`^()\[\]{}]+")
REPEATS = re.compile(r"(.)\1{1,}")

# فهرست واژه‌های ممنوع. همه به شکل فشرده و کوچک نوشته شده‌اند.
BAD_WORDS = {
    # فارسی — صریح
    "کیر", "کس", "کون", "کسکش", "کصکش", "جنده", "جاکش", "قحبه", "کونی",
    "کسخل", "کسمشنگ", "کیری", "کسکن", "کسلیس", "کونده", "بیناموس",
    "بیشرف", "بیغیرت", "حرومزاده", "حرومزاد", "مادرجنده", "خارکسده",
    "خارکصده", "پدرسگ", "پدرصلواتی", "لاشی", "عوضی", "اشغال", "کثافت",
    "دیوث", "گاییدم", "گایید", "بگا", "ساک زدن", "ساکزدن", "شاش",
    "ممه", "پستون", "سکس", "سکسی", "پورن", "شهوت", "شهوانی",
    "خایه", "بخورش", "جقی", "جلق", "منی", "اسپرم",
    "گوه", "گوهخوری", "زرزر", "زرنزن", "خفهشو", "خفه شو",
    "احمق", "بیشعور", "نفهم", "کوسخل",

    # انگلیسی — صریح
    "fuck", "fucking", "fucker", "motherfucker", "shit", "bullshit",
    "bitch", "bastard", "asshole", "dick", "cock", "pussy", "cunt",
    "whore", "slut", "porn", "porno", "sex", "sexy", "nigger", "nigga",
    "faggot", "retard", "rape", "cum", "boobs", "tits", "penis", "vagina",
    "wanker", "jerkoff", "blowjob", "handjob", "anal", "milf", "xxx",
}

# واژه‌هایی که کوتاه‌اند و ممکن است تکه‌ی یک واژه‌ی سالم باشند،
# پس فقط وقتی کامل و جدا بیایند رد می‌شوند (نه داخل واژه‌ی دیگر).
WHOLE_ONLY = {
    "کس", "کون", "منی", "شاش", "ممه", "سکس", "احمق",
    "sex", "cum", "anal", "xxx", "dick", "cock",
}


def normalize(text):
    """متن را برای مقایسه یکدست می‌کند."""
    s = unicodedata.normalize("NFKC", str(text or ""))
    s = s.translate(INVISIBLE).translate(ARABIC_FIX)
    # اعراب و کشیدگی (تطویل) کنار می‌روند: «جـنـ__ده» با «جنده» یکی می‌شود
    s = "".join(c for c in unicodedata.normalize("NFD", s)
                if not unicodedata.combining(c))
    return s.casefold().translate(LEET)


def squash(text):
    """جداکننده‌ها و حرف‌های تکراری را برمی‌دارد: «ک.و.ن.ی» → «کونی»"""
    s = SEPARATORS.sub("", normalize(text))
    return REPEATS.sub(r"\1", s)


def _words(text):
    return [w for w in SEPARATORS.split(normalize(text)) if w]


def find_bad(text):
    """
    اولین واژه‌ی ممنوعِ پیداشده را برمی‌گرداند، وگرنه None.
    """
    if not text:
        return None

    flat = squash(text)
    words = set(_words(text))
    words |= {REPEATS.sub(r"\1", w) for w in words}

    for bad in BAD_WORDS:
        key = squash(bad)
        if not key:
            continue
        if key in WHOLE_ONLY or bad in WHOLE_ONLY:
            if key in words:
                return bad
        elif key in flat:
            return bad
    return None


def is_clean(text):
    return find_bad(text) is None
