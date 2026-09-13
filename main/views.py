"""ویوهای سایت یکتا."""

import secrets
from datetime import date, datetime, timedelta

from django.conf import settings as dj_settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import (AdminInviteForm, BookingRulesForm, ChatForm, CollabForm,
                    DecisionForm, FieldQuickForm, ManualEmployerForm, PhotoForm,
                    SignupForm, SupportForm, TagQuickForm)
from .jalali import months_data, short_stamp, stamp
from .ratelimit import throttle
from .models import (Account, AuditLog, BookingSettings, Brand, Calendar, CollabKind,
                     CollabRequest, DailyReport, EmailToken, Employer, Field, Message,
                     ModelType, Photo, Place, Profile, Showcase, SupportTicket,
                     TimeSlot, VisitDay, WEEKDAYS, clock, fa)


# ══════════════════════════════════════════════════════════
#  کمک‌کارهای مشترک
# ══════════════════════════════════════════════════════════

def client_ip(request):
    fwd = request.META.get("HTTP_X_FORWARDED_FOR")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def nav_fields():
    """مجموعه‌هایی که در منوها و اسلایدرها نشان داده می‌شوند."""
    return Field.objects.filter(is_active=True).order_by("order", "id")


def booking_window_error(book, cal, day):
    """
    آیا این روز اصلاً قابل رزرو است؟ اگر نه، دلیلش را برمی‌گرداند.

    این تابع همه‌ی قواعد را با هم می‌بیند: پذیرش کلی، فاصله‌ی حداقلی، افق
    رزرو، و قواعد تقویمی خودِ روز. Calendar.is_free فقط لایه‌ی آخر است.
    """
    if not book.is_open:
        return book.closed_note or "پذیرش درخواست فعلاً بسته است."

    today = date.today()
    if day < today + timedelta(days=book.min_notice):
        return "برای رزرو دست‌کم %s روز فاصله لازم است." % fa(book.min_notice)

    if day > today + timedelta(days=book.horizon_days):
        return "فعلاً تا %s روز جلوتر می‌شود رزرو کرد." % fa(book.horizon_days)

    if not cal.is_free(day):
        return "این روز آزاد نیست."

    return None


def parse_iso(raw):
    try:
        return datetime.strptime((raw or "").strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


def collab_options():
    """گزینه‌های ویزارد درخواست — همه از پنل قابل کم و زیاد شدن."""
    return {
        "types": ModelType.objects.filter(is_active=True),
        "places": Place.objects.filter(is_active=True),
        "kinds": CollabKind.objects.filter(is_active=True),
        "fields": nav_fields(),
    }


# ══════════════════════════════════════════════════════════
#  صفحه‌ی اول
# ══════════════════════════════════════════════════════════

def home(request):
    profile = Profile.load()
    book = BookingSettings.load()

    slides = list(nav_fields().filter(on_arc=True))
    fields_more = nav_fields().filter(on_arc=False)

    strip = list(published_photos().filter(on_strip=True)[:14])
    if not strip:
        strip = list(published_photos()[:14])

    brands = Brand.objects.filter(is_active=True).order_by("order")

    minis = Showcase.objects.filter(spot="mini", is_active=True).order_by("order")[:3]
    duo = Showcase.objects.filter(spot="duo", is_active=True).order_by("order")[:2]
    plate = Showcase.objects.filter(spot="plate", is_active=True).order_by("order").first()
    reel = Showcase.objects.filter(spot="reel", is_active=True).order_by("order")

    features = list(Showcase.objects.filter(spot="feature", is_active=True).order_by("order")[:2])
    feature_a = features[0] if features else None
    feature_b = features[1] if len(features) > 1 else None

    latest = list(published_photos().order_by("-created", "-id")[:8])

    # ===== دیوار پینترستیِ ادیتوریال («قاب برگزیده» به بعد) =====
    # ابتدا تصویرهای دستچینِ مدیر (Showcase, spot=cover)، بعد پر می‌شود با
    # عکس‌های واقعیِ سایت — تا این بخش هیچ‌وقت خالی و کم‌جان به نظر نرسد،
    # و چون هر عکس ابعاد طبیعیِ خودش را نگه می‌دارد (بدون برش اجباری)،
    # هیچ‌کدام نمی‌توانند از قابشان بیرون بزنند.
    editorial = [
        {"href": c.href, "src": c.image.url, "caption": c.caption, "meta": c.meta}
        for c in Showcase.objects.filter(spot="cover", is_active=True).order_by("order")
        if c.image
    ]
    used_ids = {p.pk for p in strip} | {p.pk for p in latest}
    filler = (published_photos().exclude(pk__in=used_ids)
              .order_by("-created", "-id")[:16])
    editorial += [
        {"href": reverse("photo", args=[p.pk]), "src": p.src, "caption": p.label,
         "meta": p.field.name_fa if p.field else ""}
        for p in filler if p.src
    ]

    return render(request, "home.html", {
        "profile": profile,
        "statement_words": (profile.statement or "").split(),
        "slides": slides,
        "fields_more": fields_more,
        "strip": strip,
        "latest": latest,
        "brands": brands,
        "minis": minis, "duo": duo, "plate": plate, "editorial": editorial, "reel": reel,
        "feature_a": feature_a, "feature_b": feature_b,
        "specs": profile.specs(),
        "book": book,
    })


# ══════════════════════════════════════════════════════════
#  گالری — فعالیت‌ها، مجموعه، تک‌عکس
# ══════════════════════════════════════════════════════════

def published_photos():
    """عکس‌های منتشرشده‌ای که واقعاً فایل دارند."""
    return (Photo.objects.filter(is_published=True)
            .exclude(image="")
            .select_related("field", "model_type", "place"))


def _photo_page(request, qs, per=24):
    return Paginator(qs, per).get_page(request.GET.get("page"))


def gallery(request):
    """صفحه‌ی «فعالیت‌ها» — بالا فیلترها، پایین شبکه‌ی پینترستی."""

    types = ModelType.objects.filter(is_active=True)
    places = Place.objects.filter(is_active=True)

    pick_type = request.GET.get("type") or ""
    pick_place = request.GET.get("place") or ""

    qs = published_photos()

    if pick_type:
        qs = qs.filter(model_type__slug=pick_type)
    if pick_place:
        qs = qs.filter(place__slug=pick_place)

    return render(request, "gallery.html", {
        "types": types,
        "places": places,
        "pick_type": pick_type,
        "pick_place": pick_place,
        "photos": _photo_page(request, qs),
        "fields": nav_fields(),
        "total": qs.count(),
    })


def collection(request, slug):
    """یک مجموعه — همان چیزی که با کلیک روی اسلایدر صفحه‌ی اول باز می‌شود."""

    field = get_object_or_404(Field, slug=slug, is_active=True)
    qs = published_photos().filter(field=field)

    others = nav_fields().exclude(pk=field.pk)[:8]

    return render(request, "collection.html", {
        "field": field,
        "photos": _photo_page(request, qs),
        "others": others,
        "total": qs.count(),
    })


def photo_detail(request, pk):
    """
    یک عکس، توضیحش، دکمه‌ی همکاری — و بعدش بقیه‌ی عکس‌های همان مجموعه که
    کاربر بدون بازگشت به عقب، همان‌جا اسکرول می‌کند و می‌بیند.
    """

    shot = get_object_or_404(
        Photo.objects.select_related("field", "model_type", "place"),
        pk=pk, is_published=True)

    shot.note_click()

    siblings = published_photos().exclude(pk=shot.pk)
    if shot.field_id:
        siblings = siblings.filter(field_id=shot.field_id)
    siblings = list(siblings[:30])

    # اگر مجموعه کم‌عکس بود، از بقیه‌ی سایت پر می‌کنیم تا اسکرولِ کاربر
    # وسط راه به دیوار نخورد.
    if len(siblings) < 6:
        siblings += list(published_photos()
                         .exclude(pk=shot.pk)
                         .exclude(pk__in=[s.pk for s in siblings])[:12])

    back = "/gallery/%s/" % shot.field.slug if shot.field else reverse("gallery")

    return render(request, "photo.html", {
        "shot": shot,
        "siblings": siblings,
        "back": back,
    })


# ══════════════════════════════════════════════════════════
#  همکاری — صفحه‌ی جدا و ویزارد درخواست
# ══════════════════════════════════════════════════════════

def collab(request):
    """صفحه‌ی همکاری: معرفی کوتاه + ویزارد چندمرحله‌ای رزرو."""

    cal = Calendar()
    book = cal.settings

    opts = collab_options()

    employer = None
    if request.user.is_authenticated:
        employer = getattr(request.user, "employer", None)

    draft = request.session.get("collab_draft") or {}

    week = [{"wd": wd, "name": name, "free": cal.rules.get(wd, False)}
            for wd, name in WEEKDAYS]

    return render(request, "collab.html", {
        "book": book,
        "months": months_data(cal),
        "times": [{"fa": clock(t.hour), "h": t.hour}
                  for t in TimeSlot.objects.filter(is_active=True).order_by("hour")],
        "week": week,
        "employer": employer,
        "draft": draft,
        "floor_fa": book.floor_fa,
        "showcase": published_photos()[:6],
        **opts,
    })


@throttle("get:hours", limit=180, window=300)
def api_hours(request):
    """ساعت‌های پرِ یک روز — تقویم پیش از نمایش گزینه‌ها این را می‌پرسد."""

    day = parse_iso(request.GET.get("date"))
    if not day:
        return JsonResponse({"ok": False, "error": "تاریخ نامعتبر است."}, status=400)

    cal = Calendar()
    book = cal.settings

    problem = booking_window_error(book, cal, day)
    if problem:
        return JsonResponse({"ok": False, "error": problem})

    return JsonResponse({
        "ok": True,
        "date": day.isoformat(),
        "label": stamp(day),
        "taken": sorted(cal.taken_hours(day)),
        "day_end": book.day_end,
        "max_hours": book.max_hours,
    })


@require_POST
@throttle("collab", limit=12, window=600)
def collab_submit(request):
    """
    ثبت درخواست.

    مهمان هم می‌تواند فرم را پر کند: انتخابش در نشستِ سرور می‌ماند و بعد از
    ثبت‌نام کامل، خودکار ادامه پیدا می‌کند. این‌طور هیچ چیزی به localStorage
    سپرده نمی‌شود و بعد از ورود، کاربر دوباره از اول شروع نمی‌کند.
    """

    form = CollabForm(request.POST)

    if not form.is_valid():
        first = next(iter(form.errors.values()))[0]
        return JsonResponse({"ok": False, "error": first}, status=400)

    d = form.cleaned_data

    if not request.user.is_authenticated:
        request.session["collab_draft"] = {
            "model_type": d["model_type"].pk if d["model_type"] else "",
            "place_ref": d["place_ref"].pk if d["place_ref"] else "",
            "kind": d["kind"].pk if d["kind"] else "",
            "budget_mode": d["budget_mode"],
            "budget_amount": d["budget_amount"] or "",
            "date": d["date"].isoformat(),
            "start_hour": d["start_hour"],
            "hours": d["hours"],
            "place": d["place"],
            "crew": d["crew"],
            "brief": d["brief"],
        }
        return JsonResponse({
            "ok": False,
            "need": "signup",
            "next": reverse("signup"),
            "error": "برای ثبت نهایی باید حساب کارفرما بسازی — انتخابت محفوظ می‌ماند.",
        }, status=401)

    employer = getattr(request.user, "employer", None)
    if not employer:
        return JsonResponse({
            "ok": False, "need": "signup", "next": reverse("signup"),
            "error": "این حساب پروفایل کارفرما ندارد.",
        }, status=403)

    if employer.is_blocked:
        return JsonResponse({"ok": False, "error": "این حساب مسدود است."}, status=403)

    cal = Calendar()
    book = cal.settings
    day = d["date"]

    problem = booking_window_error(book, cal, day)
    if problem:
        return JsonResponse({"ok": False, "error": problem}, status=400)

    start, hours = d["start_hour"], d["hours"]

    if start + hours > book.day_end:
        return JsonResponse(
            {"ok": False, "error": "کار باید تا ساعت %s تمام شود." % clock(book.day_end)},
            status=400)

    want = set(range(start, start + hours))

    if want & cal.taken_hours(day):
        return JsonResponse(
            {"ok": False, "error": "این بازه همین حالا گرفته شد. ساعت دیگری انتخاب کن."},
            status=409)

    with transaction.atomic():
        row = CollabRequest.objects.create(
            employer=employer,
            date=day, start_hour=start, hours=hours,
            model_type=d["model_type"], place_ref=d["place_ref"], kind=d["kind"],
            budget_mode=d["budget_mode"],
            budget_amount=d["budget_amount"] if d["budget_mode"] == "set" else None,
            place=d["place"], crew=d["crew"], brief=d["brief"],
            from_ip=client_ip(request),
        )

        # قفل خوش‌بینانه: اگر در همین لحظه رقیبی زودتر ثبت شده بود، عقب می‌کشیم.
        rival = (CollabRequest.objects
                 .filter(date=day, pk__lt=row.pk)
                 .filter(Q(status=CollabRequest.APPROVED) |
                         Q(status=CollabRequest.PENDING, expires__gt=timezone.now()))
                 .exclude(pk=row.pk))

        clash = any(want & set(range(r.start_hour, r.start_hour + r.hours)) for r in rival)

        if clash:
            row.delete()
            return JsonResponse(
                {"ok": False, "error": "این بازه همین حالا گرفته شد. ساعت دیگری انتخاب کن."},
                status=409)

    request.session.pop("collab_draft", None)

    AuditLog.note(request, "collab:create", "CollabRequest#%s" % row.pk,
                  "%s %s" % (day, row.span))

    Message.objects.create(
        request=row, sender=Message.SYSTEM,
        body="درخواست ثبت شد: %s، %s" % (stamp(day), row.span))

    return JsonResponse({
        "ok": True,
        "id": row.pk,
        "next": reverse("dashboard"),
        "message": "درخواستت ثبت شد. یکتا تا %s ساعت پاسخ می‌دهد."
                   % fa(book.request_ttl),
    })


@throttle("support", limit=5, window=900)
def support(request):
    """پشتیبانی — شماره و متن، بدون نیاز به حساب."""

    if request.method == "POST":
        form = SupportForm(request.POST)
        if form.is_valid():
            SupportTicket.objects.create(
                name=form.cleaned_data.get("name", ""),
                phone=form.cleaned_data["phone"],
                body=form.cleaned_data["body"],
                ip=client_ip(request),
            )
            AuditLog.note(request, "support:new", detail=form.cleaned_data["phone"])
            messages.success(request, "پیامت رسید. به‌زودی با همین شماره تماس گرفته می‌شود.")
            return redirect("support")
    else:
        form = SupportForm()

    return render(request, "support.html", {"form": form, "profile": Profile.load()})


# ══════════════════════════════════════════════════════════
#  حساب کارفرما
# ══════════════════════════════════════════════════════════

@throttle("signup", limit=6, window=3600)
def signup(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data

            account = Account.objects.create_user(
                email=d["email"], password=d["password"], full_name=d["full_name"],
            )
            account.phone = d["phone"]
            account.role = Account.EMPLOYER
            account.save(update_fields=["phone", "role"])

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
                signup_ip=client_ip(request),
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
                fail_silently=True,
            )

            AuditLog.note(request, "account:signup", account.email, d["company"])

            auth_login(request, account,
                       backend="main.backends.LockoutBackend")

            if request.session.get("collab_draft"):
                messages.success(
                    request, "حسابت ساخته شد. درخواست نیمه‌تمامت همین‌جا منتظر است.")
                return redirect(reverse("collab") + "?resume=1")

            messages.success(request, "خوش آمدی. لینک تایید به ایمیلت فرستاده شد.")
            return redirect("dashboard")
    else:
        form = SignupForm()

    return render(request, "registration/signup.html", {
        "form": form,
        "draft": request.session.get("collab_draft"),
    })


def verify_email(request, token):
    t = get_object_or_404(EmailToken, token=token, kind=EmailToken.VERIFY)

    if t.is_valid:
        t.account.email_verified = True
        t.account.save(update_fields=["email_verified"])
        t.used_at = timezone.now()
        t.save(update_fields=["used_at"])
        messages.success(request, "ایمیل تایید شد.")
    else:
        messages.error(request, "این لینک منقضی شده یا قبلاً استفاده شده.")

    return redirect("dashboard" if request.user.is_authenticated else "login")


@login_required
def dashboard(request):
    """پیشخوان کارفرما — درخواست‌ها، گفتگو، کارت برند و میان‌برها."""

    if request.user.is_model:
        return redirect("studio")

    employer = getattr(request.user, "employer", None)

    if employer:
        reqs = list(
            CollabRequest.objects
            .filter(employer=employer)
            .select_related("field", "model_type", "place_ref", "kind")
            .prefetch_related("messages")
            .order_by("-created")
        )

        msgs = list(
            Message.objects
            .filter(request__employer=employer, hidden=False)
            .select_related("request")
            .order_by("-created")[:10]
        )

        unread_qs = Message.objects.filter(
            request__employer=employer,
            sender=Message.MODEL,
            read_at__isnull=True,
            hidden=False,
        )
        unread = unread_qs.count()
        unread_qs.update(read_at=timezone.now())

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


@login_required
@require_POST
def dashboard_reply(request, pk):
    """کارفرما در گفتگوی یک درخواست پیام می‌گذارد."""

    employer = getattr(request.user, "employer", None)
    row = get_object_or_404(CollabRequest, pk=pk, employer=employer)

    form = ChatForm(request.POST)
    if form.is_valid():
        Message.objects.create(request=row, sender=Message.EMPLOYER,
                               body=form.cleaned_data["body"])
        AuditLog.note(request, "chat:employer", "CollabRequest#%s" % row.pk,
                      form.cleaned_data["body"][:200])
        messages.success(request, "پیامت فرستاده شد.")
    else:
        messages.error(request, next(iter(form.errors.values()))[0])

    return redirect("dashboard")


@login_required
@require_POST
def cancel_request(request, pk):
    employer = getattr(request.user, "employer", None)
    row = get_object_or_404(CollabRequest, pk=pk, employer=employer)

    if row.status == CollabRequest.PENDING:
        row.status = CollabRequest.CANCELLED
        row.save(update_fields=["status"])
        AuditLog.note(request, "collab:cancel", "CollabRequest#%s" % row.pk)
        messages.success(request, "درخواست لغو شد.")

    return redirect("dashboard")


# ══════════════════════════════════════════════════════════
#  پنل استودیو — فقط یکتا و مدیر سایت
# ══════════════════════════════════════════════════════════

def model_required(view):
    """
    دروازه‌ی پنل استودیو.

    عمداً 404 برمی‌گرداند نه 403: کاربر عادی حتی نباید بفهمد چنین مسیری هست.
    """
    def guard(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("%s?next=%s" % (reverse("login"), request.path))
        if not request.user.is_model:
            raise Http404
        return view(request, *args, **kwargs)

    guard.__name__ = view.__name__
    guard.__doc__ = view.__doc__
    return guard


def studio_chrome(request):
    """داده‌های مشترک همه‌ی صفحه‌های پنل — شمارنده‌ی بالای صفحه."""
    pending = CollabRequest.objects.filter(status=CollabRequest.PENDING).count()
    unread = Message.objects.filter(sender=Message.EMPLOYER, read_at__isnull=True,
                                    hidden=False).count()
    tickets = SupportTicket.objects.filter(is_done=False).count()
    return {"nav_pending": pending, "nav_unread": unread, "nav_tickets": tickets}


@model_required
def studio(request):
    """صفحه‌ی اول پنل یکتا — یک نگاه به همه‌چیز."""

    today = timezone.localdate()
    since = today - timedelta(days=13)

    rows = {v.day: v for v in VisitDay.objects.filter(day__gte=since)}
    chart = []
    top_hits = max([r.hits for r in rows.values()] or [0]) or 1

    for i in range(14):
        day = since + timedelta(days=i)
        row = rows.get(day)
        hits = row.hits if row else 0
        chart.append({
            "day": day,
            "label": short_stamp(day),
            "hits": hits,
            "hits_fa": fa(hits),
            "pct": round(hits * 100 / top_hits, 1),
            "today": day == today,
        })

    week_ago = timezone.now() - timedelta(days=7)
    hot = list(published_photos()
               .annotate(recent=Count("click_rows",
                                      filter=Q(click_rows__created__gte=week_ago)))
               .order_by("-recent", "-clicks")[:6])

    # درصد نوار را همین‌جا حساب می‌کنیم، نه در قالب: widthratio با صفر
    # چیزی برنمی‌گرداند و نوارها بی‌سروصدا ناپدید می‌شدند.
    top_recent = max([p.recent for p in hot] or [0]) or 1
    for p in hot:
        p.pct = round(p.recent * 100 / top_recent, 1)

    pending = (CollabRequest.objects.filter(status=CollabRequest.PENDING)
               .select_related("employer")[:6])

    upcoming = (CollabRequest.objects
                .filter(status=CollabRequest.APPROVED, date__gte=today)
                .select_related("employer").order_by("date")[:5])

    return render(request, "studio/index.html", {
        "chart": chart,
        "hot": hot,
        "pending": pending,
        "upcoming": upcoming,
        "report": DailyReport.objects.order_by("-day").first(),
        "totals": {
            "photos": Photo.objects.filter(is_published=True).count(),
            "fields": Field.objects.filter(is_active=True).count(),
            "employers": Employer.objects.count(),
            "requests": CollabRequest.objects.count(),
        },
        "visits_week": sum(c["hits"] for c in chart[-7:]),
        "tickets": SupportTicket.objects.filter(is_done=False)[:4],
        "booking_open": BookingSettings.load().is_open,
        **studio_chrome(request),
    })


@model_required
@require_POST
def studio_toggle_open(request):
    """کلید «پذیرش باز/بسته» — پرکاربردترین تصمیم روزانه، با یک ضربه."""
    book = BookingSettings.load()
    book.is_open = not book.is_open
    book.save(update_fields=["is_open"])

    AuditLog.note(request, "settings:accepting", detail=str(book.is_open))
    messages.success(request,
                     "پذیرش درخواست باز شد." if book.is_open else "پذیرش درخواست بسته شد.")
    return redirect(request.POST.get("back") or "studio")


@model_required
def studio_photos(request):
    """افزودن و حذف عکس — همان صفحه‌ای که یکتا روی گوشی باز می‌کند."""

    if request.method == "POST":
        form = PhotoForm(request.POST, request.FILES)
        if form.is_valid():
            shot = form.save()
            AuditLog.note(request, "photo:add", "Photo#%s" % shot.pk, shot.label)
            messages.success(request, "عکس اضافه شد.")
            return redirect("studio_photos")
        messages.error(request, next(iter(form.errors.values()))[0])
    else:
        form = PhotoForm()

    qs = Photo.objects.select_related("field", "model_type", "place")

    pick = request.GET.get("field") or ""
    if pick:
        qs = qs.filter(field__slug=pick)

    return render(request, "studio/photos.html", {
        "form": form,
        "photos": _photo_page(request, qs, per=30),
        "fields": nav_fields(),
        "pick": pick,
        **studio_chrome(request),
    })


@model_required
@require_POST
def studio_photo_action(request, pk):
    shot = get_object_or_404(Photo, pk=pk)
    what = request.POST.get("do")

    if what == "delete":
        AuditLog.note(request, "photo:delete", "Photo#%s" % shot.pk, shot.label)
        shot.delete()
        messages.success(request, "عکس حذف شد.")
    elif what == "toggle":
        shot.is_published = not shot.is_published
        shot.save(update_fields=["is_published"])
        AuditLog.note(request, "photo:publish", "Photo#%s" % shot.pk,
                      str(shot.is_published))
    elif what == "strip":
        shot.on_strip = not shot.on_strip
        shot.save(update_fields=["on_strip"])
        AuditLog.note(request, "photo:strip", "Photo#%s" % shot.pk, str(shot.on_strip))

    return redirect(request.POST.get("back") or "studio_photos")


@model_required
def studio_lists(request):
    """مجموعه‌ها، نوع مدلینگ، محل، نوع همکاری — کم و زیاد کردن."""

    field_form = FieldQuickForm()
    tag_form = TagQuickForm()

    if request.method == "POST":
        which = request.POST.get("form")

        if which == "field":
            field_form = FieldQuickForm(request.POST)
            if field_form.is_valid():
                row = field_form.save()
                AuditLog.note(request, "field:add", "Field#%s" % row.pk, row.name_fa)
                messages.success(request, "مجموعه ساخته شد.")
                return redirect("studio_lists")
            messages.error(request, next(iter(field_form.errors.values()))[0])

        elif which == "tag":
            tag_form = TagQuickForm(request.POST)
            if tag_form.is_valid():
                row = tag_form.save()
                AuditLog.note(request, "tag:add", row.__class__.__name__, row.name)
                messages.success(request, "گزینه اضافه شد.")
                return redirect("studio_lists")
            messages.error(request, next(iter(tag_form.errors.values()))[0])

    return render(request, "studio/lists.html", {
        "field_form": field_form,
        "tag_form": tag_form,
        "fields": Field.objects.all(),
        "tag_groups": [
            ("type", "نوع مدلینگ", list(ModelType.objects.all())),
            ("place", "محل", list(Place.objects.all())),
            ("kind", "نوع همکاری", list(CollabKind.objects.all())),
        ],
        **studio_chrome(request),
    })


@model_required
@require_POST
def studio_list_action(request):
    """فعال/غیرفعال یا حذف یک گزینه از فهرست‌ها."""

    groups = {"type": ModelType, "place": Place, "kind": CollabKind, "field": Field}
    model = groups.get(request.POST.get("group"))
    if not model:
        raise Http404

    row = get_object_or_404(model, pk=request.POST.get("pk"))
    what = request.POST.get("do")

    if what == "toggle":
        row.is_active = not row.is_active
        row.save(update_fields=["is_active"])
        AuditLog.note(request, "list:toggle", "%s#%s" % (model.__name__, row.pk),
                      str(row.is_active))
    elif what == "delete":
        AuditLog.note(request, "list:delete", "%s#%s" % (model.__name__, row.pk), str(row))
        row.delete()
        messages.success(request, "حذف شد.")

    return redirect("studio_lists")


@model_required
def studio_requests(request):
    """همه‌ی درخواست‌ها با فیلتر وضعیت."""

    pick = request.GET.get("status") or ""
    qs = CollabRequest.objects.select_related(
        "employer", "model_type", "place_ref", "kind").order_by("-created")

    if pick:
        qs = qs.filter(status=pick)

    counts = dict(CollabRequest.objects.values_list("status")
                  .annotate(n=Count("id")).values_list("status", "n"))

    return render(request, "studio/requests.html", {
        "rows": Paginator(qs, 20).get_page(request.GET.get("page")),
        "pick": pick,
        # وضعیت‌ها همراه با تعدادشان، تا قالب مجبور نباشد در دیکشنری بگردد
        "states": [{"value": v, "label": label, "n": counts.get(v, 0)}
                   for v, label in CollabRequest.STATUS],
        "total": CollabRequest.objects.count(),
        **studio_chrome(request),
    })


@model_required
def studio_request(request, pk):
    """یک درخواست: جزئیات، تصمیم، و گفتگو."""

    row = get_object_or_404(
        CollabRequest.objects.select_related("employer", "employer__account"), pk=pk)

    if request.method == "POST":
        which = request.POST.get("form")

        if which == "decide":
            form = DecisionForm(request.POST)
            if form.is_valid():
                row.decide(form.cleaned_data["status"],
                           form.cleaned_data.get("reply", ""),
                           actor=request.user)
                messages.success(request, "ثبت شد و به کارفرما اطلاع داده شد.")
                return redirect("studio_request", pk=row.pk)
            messages.error(request, next(iter(form.errors.values()))[0])

        elif which == "chat":
            form = ChatForm(request.POST)
            if form.is_valid():
                Message.objects.create(request=row, sender=Message.MODEL,
                                       body=form.cleaned_data["body"])
                AuditLog.note(request, "chat:model", "CollabRequest#%s" % row.pk,
                              form.cleaned_data["body"][:200])
                return redirect("studio_request", pk=row.pk)
            messages.error(request, next(iter(form.errors.values()))[0])

    if not row.seen_at:
        row.seen_at = timezone.now()
        row.save(update_fields=["seen_at"])

    chat = row.messages.filter(hidden=False)
    chat.filter(sender=Message.EMPLOYER, read_at__isnull=True).update(
        read_at=timezone.now())

    return render(request, "studio/request.html", {
        "row": row,
        "chat": chat,
        "decide": DecisionForm(initial={"status": row.status}),
        "chat_form": ChatForm(),
        "day_label": stamp(row.date),
        **studio_chrome(request),
    })


@model_required
def studio_people(request):
    """کارفرماها + افزودن دستی + پیام‌های پشتیبانی."""

    form = ManualEmployerForm()

    if request.method == "POST":
        form = ManualEmployerForm(request.POST)
        if form.is_valid():
            emp = form.save(actor=request.user)
            AuditLog.note(request, "employer:manual", "Employer#%s" % emp.pk, emp.company)
            messages.success(request, "کارفرما اضافه شد.")
            return redirect("studio_people")
        messages.error(request, next(iter(form.errors.values()))[0])

    return render(request, "studio/people.html", {
        "form": form,
        "employers": (Employer.objects.select_related("account")
                      .annotate(n=Count("requests")).order_by("-created")[:60]),
        "tickets": SupportTicket.objects.all()[:40],
        **studio_chrome(request),
    })


@model_required
@require_POST
def studio_ticket_done(request, pk):
    row = get_object_or_404(SupportTicket, pk=pk)
    row.is_done = not row.is_done
    row.save(update_fields=["is_done"])
    AuditLog.note(request, "support:done", "SupportTicket#%s" % row.pk, str(row.is_done))
    return redirect("studio_people")


@model_required
def studio_settings(request):
    """قواعد رزرو، کف بودجه، و افزودن مدیر."""

    rules = BookingRulesForm(instance=BookingSettings.load())
    invite = AdminInviteForm()

    if request.method == "POST":
        which = request.POST.get("form")

        if which == "rules":
            rules = BookingRulesForm(request.POST, instance=BookingSettings.load())
            if rules.is_valid():
                rules.save()
                AuditLog.note(request, "settings:booking", detail=str(rules.changed_data))
                messages.success(request, "تنظیمات ذخیره شد.")
                return redirect("studio_settings")
            messages.error(request, next(iter(rules.errors.values()))[0])

        elif which == "invite":
            if not (request.user.is_superuser or request.user.role == Account.OWNER):
                raise Http404
            invite = AdminInviteForm(request.POST)
            if invite.is_valid():
                who = invite.save()
                AuditLog.note(request, "admin:add", who.email, who.role)
                messages.success(
                    request, "مدیر تازه اضافه شد: %s — با همان رمز می‌تواند وارد شود."
                    % who.email)
                return redirect("studio_settings")
            messages.error(request, next(iter(invite.errors.values()))[0])

    return render(request, "studio/settings.html", {
        "rules": rules,
        "invite": invite,
        "can_invite": request.user.is_superuser or request.user.role == Account.OWNER,
        "admins": Account.objects.filter(
            Q(role=Account.OWNER) | Q(role=Account.MODEL) | Q(is_staff=True)),
        "log": AuditLog.objects.select_related("actor")[:40],
        **studio_chrome(request),
    })


@model_required
def studio_reports(request):
    """گزارش‌های شبانه — همان چیزی که هر شب تازه می‌شود."""

    return render(request, "studio/reports.html", {
        "reports": DailyReport.objects.all()[:30],
        "top_all": published_photos().order_by("-clicks")[:20],
        **studio_chrome(request),
    })


# ══════════════════════════════════════════════════════════
#  نقشه‌ی تصویری سایت — برای پنل جنگو
# ══════════════════════════════════════════════════════════

SITE_MAP_HOTSPOTS = [
    {"label": "هیرو (ویدیو و متن)", "href": "/admin/main/profile/1/change/", "x": 0.00, "y": 0.00, "w": 100.00, "h": 9.50},
    {"label": "سه عکس کوچک", "href": "/admin/main/showcase/?spot__exact=mini", "x": 5.02, "y": 12.79, "w": 89.96, "h": 1.74},
    {"label": "اسلایدر مجموعه‌ها", "href": "/admin/main/field/", "x": 0.00, "y": 16.00, "w": 100.00, "h": 8.27},
    {"label": "عکس‌ها", "href": "/admin/main/photo/", "x": 0.00, "y": 24.27, "w": 100.00, "h": 9.32},
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
