import secrets
from datetime import date, timedelta

from django.conf import settings as dj_settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .forms import SignupForm
from .models import (
    Account, Brand, BookingSettings, Calendar, CollabRequest, EmailToken,
    Employer, Field, Message, Profile, Showcase, TimeSlot, WEEKDAYS, Work,
    clock, fa,
)

MONTH_NAMES = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
               "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"]


# ──────────────── تبدیل تاریخ شمسی (فقط ریاضی، به هیچ مدلی وابسته نیست) ────────────────

def g2j(gy, gm, gd):
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


def build_month(cal, first_g, jy, jm):
    """یک ماه شمسی را به سلول‌های تقویم تبدیل می‌کند — «آزاد» از Calendar واقعی می‌آید."""
    today = date.today()
    total = j_days(jy, jm)
    offset = (first_g.weekday() + 2) % 7          # شنبه = ۰

    cells = [{"d": None} for _ in range(offset)]

    for i in range(total):
        g = first_g + timedelta(days=i)
        cells.append({
            "d": i + 1,
            "fa": fa(i + 1),
            "free": cal.is_free(g),
            "past": g < today,
            "today": g == today,
        })

    return {"label": "%s %s" % (MONTH_NAMES[jm - 1], fa(jy)), "cells": cells}


def months_data(cal):
    today = date.today()
    jy, jm, jd = g2j(today.year, today.month, today.day)

    first_g = today - timedelta(days=jd - 1)      # اول ماه جاری
    out = [build_month(cal, first_g, jy, jm)]

    cy, cm, cf = jy, jm, first_g
    for _ in range(2):                             # دو ماه بعد
        cf = cf + timedelta(days=j_days(cy, cm))
        cm += 1
        if cm > 12:
            cm, cy = 1, cy + 1
        out.append(build_month(cal, cf, cy, cm))

    return out


def home(request):
    profile = Profile.load()
    cal = Calendar()
    book = cal.settings                            # BookingSettings — همان‌جا لود شده

    fields = Field.objects.filter(is_active=True, on_arc=True).order_by("order")
    fields_more = Field.objects.filter(is_active=True, on_arc=False).order_by("order")

    works = (Work.objects.filter(is_published=True)
             .order_by("order", "-created")
             .prefetch_related("shots"))

    brands = Brand.objects.filter(is_active=True).order_by("order")

    minis = Showcase.objects.filter(spot="mini", is_active=True).order_by("order")[:3]
    duo = Showcase.objects.filter(spot="duo", is_active=True).order_by("order")[:2]
    plate = Showcase.objects.filter(spot="plate", is_active=True).order_by("order").first()
    covers = Showcase.objects.filter(spot="cover", is_active=True).order_by("order")
    reel = Showcase.objects.filter(spot="reel", is_active=True).order_by("order")

    features = list(Showcase.objects.filter(spot="feature", is_active=True).order_by("order")[:2])
    feature_a = features[0] if len(features) > 0 else None
    feature_b = features[1] if len(features) > 1 else None

    times = [{"fa": clock(t.hour), "h": t.hour}
             for t in TimeSlot.objects.filter(is_active=True).order_by("hour")]

    # «این هفته»: الگوی هفتگیِ ثابت (بدون احتساب استثناها/قفل‌ها — همان‌طور که از اول بود)
    week = [{"name": name, "free": cal.rules.get(wd, False)} for wd, name in WEEKDAYS]

    return render(request, "home.html", {
        "profile": profile,
        "statement_words": (profile.statement or "").split(),
        "fields": fields, "fields_more": fields_more,
        "works": works, "brands": brands,
        "minis": minis, "duo": duo, "plate": plate, "covers": covers, "reel": reel,
        "feature_a": feature_a, "feature_b": feature_b,
        "specs": profile.specs(),
        "week": week, "times": times,
        "day_end": book.day_end, "max_hours": book.max_hours,
        "months": months_data(cal),
    })


# ══════════════════════════════════════════════════════════
#  حساب کارفرما — ثبت‌نام، تایید ایمیل، پیشخوان
# ══════════════════════════════════════════════════════════

def signup(request):
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            account = Account.objects.create_user(
                email=d["email"], password=d["password"], full_name=d["full_name"],
            )
            Employer.objects.create(
                account=account,
                company=d["company"],
                activity=d["activity"],
                contact_name=d["contact_name"],
                phone=d["phone"],
                instagram=d.get("instagram", ""),
                links=d.get("links", ""),
                city=d.get("city", ""),
                address=d.get("address", ""),
                lat=d.get("lat"),
                lng=d.get("lng"),
            )

            token = secrets.token_urlsafe(32)
            EmailToken.objects.create(
                account=account, token=token, kind=EmailToken.VERIFY,
                expires=timezone.now() + timedelta(hours=48),
            )
            link = request.build_absolute_uri(reverse("verify_email", args=[token]))
            send_mail(
                "تایید ایمیل یکتا",
                "برای تایید ایمیل، این لینک را باز کن:\n%s" % link,
                dj_settings.DEFAULT_FROM_EMAIL, [account.email],
            )

            messages.success(request, "ثبت‌نام انجام شد. لینک تایید به ایمیلت ارسال شد.")
            return redirect("login")
    else:
        form = SignupForm()

    return render(request, "registration/signup.html", {"form": form})


def verify_email(request, token):
    t = get_object_or_404(EmailToken, token=token, kind=EmailToken.VERIFY)

    if t.is_valid:
        t.account.email_verified = True
        t.account.save(update_fields=["email_verified"])
        t.used_at = timezone.now()
        t.save(update_fields=["used_at"])
        messages.success(request, "ایمیل تایید شد. حالا می‌توانی وارد شوی.")
    else:
        messages.error(request, "این لینک منقضی شده یا قبلاً استفاده شده.")

    return redirect("login")


@login_required
def dashboard(request):
    """پیشخوان کارفرما — درخواست‌ها، گفتگو، کارت برند و میان‌برها."""

    employer = getattr(request.user, "employer", None)

    if employer:
        reqs = list(
            CollabRequest.objects
            .filter(employer=employer)
            .select_related("field")
            .order_by("-created")
        )

        msgs = list(
            Message.objects
            .filter(request__employer=employer, hidden=False)
            .order_by("-created")[:8]
        )

        unread = Message.objects.filter(
            request__employer=employer,
            sender=Message.MODEL,
            read_at__isnull=True,
            hidden=False,
        ).count()

        # نزدیک‌ترین آفیش تاییدشده‌ای که هنوز نگذشته
        ahead = sorted(
            (x for x in reqs
             if x.status == CollabRequest.APPROVED and x.date >= date.today()),
            key=lambda x: x.date,
        )
        upcoming = ahead[0] if ahead else None
    else:
        reqs, msgs, unread, upcoming = [], [], 0, None

    counts = {
        "all":      len(reqs),
        "pending":  sum(1 for r in reqs if r.status == CollabRequest.PENDING),
        "approved": sum(1 for r in reqs if r.status == CollabRequest.APPROVED),
        "done":     sum(1 for r in reqs if r.status == CollabRequest.DONE),
    }

    return render(request, "dashboard.html", {
        "employer": employer,
        "requests": reqs,
        "msgs": msgs,
        "unread": unread,
        "upcoming": upcoming,
        "counts": counts,
    })


# ══════════════════════════════════════════════════════════
#  نقشه‌ی تصویری سایت — برای پنل مدیریت
#  یک اسکرین‌شات واقعی از صفحه‌ی اول با نقطه‌های کلیک‌شدنی روی هر بخش.
#  مختصات به‌صورت درصد از عرض/ارتفاع کل تصویرند تا روی هر اندازه‌ی صفحه‌ای درست بنشینند.
#  اگر محتوای یک بخش (مثلاً برندها یا حوزه‌ها) به‌شکل چشمگیری بیشتر/کمتر شود،
#  ممکن است لازم شود این تصویر و مختصات دوباره ساخته شوند.
# ══════════════════════════════════════════════════════════

SITE_MAP_HOTSPOTS = [
    {"label": "هیرو (ویدیو و متن)", "href": "/admin/main/profile/1/change/", "x": 0.00, "y": 0.00, "w": 100.00, "h": 9.50},
    {"label": "سه عکس کوچک", "href": "/admin/main/showcase/?spot__exact=mini", "x": 5.02, "y": 12.79, "w": 89.96, "h": 1.74},
    {"label": "حوزه‌های کاری", "href": "/admin/main/field/", "x": 0.00, "y": 16.00, "w": 100.00, "h": 8.27},
    {"label": "کارها", "href": "/admin/main/work/", "x": 0.00, "y": 24.27, "w": 100.00, "h": 9.32},
    {"label": "عکس تمام‌عرض", "href": "/admin/main/showcase/?spot__exact=feature", "x": 0.00, "y": 33.59, "w": 100.00, "h": 6.42},
    {"label": "عکس تمام‌عرض", "href": "/admin/main/showcase/?spot__exact=feature", "x": 0.00, "y": 73.73, "w": 100.00, "h": 6.42},
    {"label": "لاین افقی", "href": "/admin/main/showcase/?spot__exact=reel", "x": 0.00, "y": 40.01, "w": 100.00, "h": 5.20},
    {"label": "بنر", "href": "/admin/main/profile/1/change/", "x": 0.00, "y": 45.22, "w": 100.00, "h": 8.74},
    {"label": "دو عکس", "href": "/admin/main/showcase/?spot__exact=duo", "x": 0.00, "y": 54.23, "w": 100.00, "h": 3.31},
    {"label": "قاب پاسپارتو", "href": "/admin/main/showcase/?spot__exact=plate", "x": 5.02, "y": 58.70, "w": 89.96, "h": 5.61},
    {"label": "شبکه‌ی ادیتوریال", "href": "/admin/main/showcase/?spot__exact=cover", "x": 0.00, "y": 64.99, "w": 100.00, "h": 7.56},
    {"label": "مشخصات", "href": "/admin/main/profile/1/change/", "x": 5.02, "y": 82.22, "w": 89.96, "h": 1.99},
    {"label": "تقویم و ساعت‌ها", "href": "/admin/main/weekdayrule/", "x": 0.00, "y": 85.04, "w": 100.00, "h": 7.64},
    {"label": "برندها", "href": "/admin/main/brand/", "x": 5.02, "y": 93.85, "w": 89.96, "h": 0.61},
]


@staff_member_required
def site_map(request):
    return render(request, "admin/site_map.html", {"hotspots": SITE_MAP_HOTSPOTS})
