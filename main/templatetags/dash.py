"""
تگِ داشبورد برای صفحه‌ی اول پنل جنگو.

پنل جنگو به ویوی خودش context نمی‌دهد، پس داده را همین‌جا می‌گیریم و با
یک inclusion tag بالای فهرست بخش‌ها می‌نشانیم — بدون دست‌زدن به AdminSite.
"""

from datetime import timedelta

from django import template
from django.db.models import Count, Q
from django.utils import timezone

from main.jalali import short_stamp
from main.models import (CollabRequest, DailyReport, Employer, Photo,
                         SupportTicket, VisitDay, fa)

register = template.Library()


@register.inclusion_tag("admin/yekta_dash.html")
def yekta_dashboard():
    today = timezone.localdate()
    since = today - timedelta(days=13)

    rows = {v.day: v.hits for v in VisitDay.objects.filter(day__gte=since)}
    peak = max(list(rows.values()) or [0]) or 1

    chart = []
    for i in range(14):
        day = since + timedelta(days=i)
        hits = rows.get(day, 0)
        chart.append({
            "label": short_stamp(day),
            "hits": fa(hits),
            "pct": round(hits * 100 / peak, 1),
            "today": day == today,
        })

    week_ago = timezone.now() - timedelta(days=7)
    hot = list(Photo.objects.filter(is_published=True)
               .annotate(recent=Count("click_rows",
                                      filter=Q(click_rows__created__gte=week_ago)))
               .order_by("-recent", "-clicks")[:8])

    top = max([p.recent for p in hot] or [0]) or 1
    for p in hot:
        p.pct = round(p.recent * 100 / top, 1)

    return {
        "chart": chart,
        "hot": hot,
        "report": DailyReport.objects.order_by("-day").first(),
        "counts": {
            "pending": fa(CollabRequest.objects.filter(
                status=CollabRequest.PENDING).count()),
            "employers": fa(Employer.objects.count()),
            "photos": fa(Photo.objects.filter(is_published=True).count()),
            "tickets": fa(SupportTicket.objects.filter(is_done=False).count()),
        },
        "week": fa(sum(rows.get(today - timedelta(days=i), 0) for i in range(7))),
    }
