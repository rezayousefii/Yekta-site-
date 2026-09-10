"""
گزارش کاری شبانه.

اجرا:  python manage.py nightly_report

هر شب یک ردیف DailyReport برای امروز می‌سازد (یا اگر بود، تازه‌اش می‌کند):
بازدید، کلیک، درخواست تازه، ثبت‌نام، پیام پشتیبانی، و پرکلیک‌ترین عکس‌های
همان روز. هر دو پنل همین ردیف را نشان می‌دهند.

روی لیارا در liara.json یک cron برای ۲۳:۵۵ به وقت تهران گذاشته شده.
"""

from datetime import datetime, time, timedelta

from django.core.management.base import BaseCommand
from django.db.models import Count
from django.utils import timezone

from main.models import (Account, CollabRequest, DailyReport, Photo, PhotoClick,
                         SupportTicket, VisitDay)


class Command(BaseCommand):
    help = "ساخت گزارش کاری امروز"

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=1,
                            help="چند روز گذشته دوباره ساخته شود (پیش‌فرض: فقط امروز)")

    def handle(self, *args, **options):
        today = timezone.localdate()

        for back in range(options["days"]):
            day = today - timedelta(days=back)
            self.build(day)
            self.stdout.write(self.style.SUCCESS("گزارش %s ساخته شد." % day))

    def build(self, day):
        start = timezone.make_aware(datetime.combine(day, time.min))
        end = start + timedelta(days=1)

        visit = VisitDay.objects.filter(day=day).first()

        clicks = PhotoClick.objects.filter(created__gte=start, created__lt=end)

        top = (Photo.objects
               .filter(click_rows__created__gte=start, click_rows__created__lt=end)
               .annotate(n=Count("click_rows"))
               .order_by("-n")[:8])

        DailyReport.objects.update_or_create(
            day=day,
            defaults={
                "visits": visit.hits if visit else 0,
                "guests": visit.guests if visit else 0,
                "clicks": clicks.count(),
                "requests": CollabRequest.objects.filter(
                    created__gte=start, created__lt=end).count(),
                "signups": Account.objects.filter(
                    date_joined__gte=start, date_joined__lt=end).count(),
                "tickets": SupportTicket.objects.filter(
                    created__gte=start, created__lt=end).count(),
                "top": "\n".join(
                    "%s | %s | %s" % (p.pk, p.label, p.n) for p in top),
            },
        )
