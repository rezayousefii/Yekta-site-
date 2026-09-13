"""
تبدیل تاریخ میلادی به شمسی و ساختن سلول‌های تقویم.

فقط ریاضی است و به هیچ مدلی وابسته نیست، تا هم قابل تست باشد و هم هرجای
دیگری از سایت لازم شد بدون دردسر وارد شود.
"""

from datetime import date, timedelta

MONTH_NAMES = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
               "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"]

DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def fa(value):
    return str(value).translate(DIGITS)


def g2j(gy, gm, gd):
    """میلادی → شمسی"""
    gdm = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    if gy > 1600:
        jy, gy = 979, gy - 1600
    else:
        jy, gy = 0, gy - 621
    gy2 = gy + 1 if gm > 2 else gy
    days = (365 * gy + (gy2 + 3) // 4 - (gy2 + 99) // 100 + (gy2 + 399) // 400
            - 80 + gd + gdm[gm - 1])
    jy += 33 * (days // 12053); days %= 12053
    jy += 4 * (days // 1461);    days %= 1461
    if days > 365:
        jy += (days - 1) // 365
        days = (days - 1) % 365
    if days < 186:
        jm, jd = 1 + days // 31, 1 + days % 31
    else:
        jm, jd = 7 + (days - 186) // 30, 1 + (days - 186) % 30
    return jy, jm, jd


def j_leap(jy):
    return ((jy + 12) % 33) in {1, 5, 9, 13, 17, 22, 26, 30}


def j_days(jy, jm):
    if jm <= 6:
        return 31
    if jm <= 11:
        return 30
    return 30 if j_leap(jy) else 29


def stamp(day):
    """یک تاریخ میلادی → «۲۵ آذر ۱۴۰۴»"""
    jy, jm, jd = g2j(day.year, day.month, day.day)
    return "%s %s %s" % (fa(jd), MONTH_NAMES[jm - 1], fa(jy))


def short_stamp(day):
    """→ «۲۵ آذر»"""
    jy, jm, jd = g2j(day.year, day.month, day.day)
    return "%s %s" % (fa(jd), MONTH_NAMES[jm - 1])


def build_month(cal, first_g, jy, jm):
    """
    یک ماه شمسی را به سلول‌های تقویم تبدیل می‌کند.

    هر سلول علاوه بر برچسب فارسی، تاریخ میلادیِ واقعی (iso) و شماره‌ی روز
    هفته (wd، شنبه = ۰) را هم دارد — بدون این‌ها جاوااسکریپت هیچ تاریخ
    واقعی‌ای برای فرستادن به سرور نداشت.
    """
    today = date.today()
    total = j_days(jy, jm)
    offset = (first_g.weekday() + 2) % 7          # شنبه = ۰

    cells = [{"d": None} for _ in range(offset)]

    for i in range(total):
        g = first_g + timedelta(days=i)
        cells.append({
            "d": i + 1,
            "fa": fa(i + 1),
            "iso": g.isoformat(),
            "wd": (g.weekday() + 2) % 7,
            "free": cal.is_free(g),
            "past": g < today,
            "today": g == today,
        })

    return {"label": "%s %s" % (MONTH_NAMES[jm - 1], fa(jy)), "cells": cells}


def months_data(cal, ahead=2):
    """ماه جاری به‌علاوه‌ی چند ماه بعد."""
    today = date.today()
    jy, jm, jd = g2j(today.year, today.month, today.day)

    first_g = today - timedelta(days=jd - 1)      # اول ماه جاری
    out = [build_month(cal, first_g, jy, jm)]

    cy, cm, cf = jy, jm, first_g
    for _ in range(ahead):
        cf = cf + timedelta(days=j_days(cy, cm))
        cm += 1
        if cm > 12:
            cm, cy = 1, cy + 1
        out.append(build_month(cal, cf, cy, cm))

    return out
