"""
فیلترهای فارسی‌سازی برای قالب‌ها.

جنگو برای زبان fa رقم‌ها را فارسی نمی‌کند، پس هرجای قالب که عددی به چشم
کاربر می‌آید باید از این‌ها رد شود:  {{ n|fa }}  /  {{ price|money }}
(عددهایی که با data-count از صفر بالا می‌روند لازم ندارند: جاوااسکریپت
خودش فارسی‌شان می‌کند.)
"""

from datetime import date, datetime

from django import template

from main.jalali import stamp
from main.models import fa as to_fa, money as to_money

register = template.Library()


@register.filter(name="fa")
def fa_digits(value):
    """۱۲۳ → «۱۲۳». روی رشته هم کار می‌کند و بقیه‌ی نویسه‌ها را دست نمی‌زند."""
    if value is None:
        return ""
    return to_fa(value)


@register.filter
def money(value):
    """۲۵۰۰۰۰۰ → «۲٬۵۰۰٬۰۰۰»"""
    return to_money(value)


@register.filter
def jdate(value):
    """تاریخ میلادی → «۲۵ آذر ۱۴۰۴»"""
    if isinstance(value, datetime):
        value = value.date()
    if not isinstance(value, date):
        return value
    return stamp(value)
