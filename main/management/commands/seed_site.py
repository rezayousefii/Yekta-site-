"""
ردیف‌های اولیه‌ی دیتابیس.

اجرا:  python manage.py seed_site

بارها قابل اجراست؛ چیزی را دوباره نمی‌سازد و چیزی را پاک نمی‌کند.
تصویرها را باید از پنل آپلود کنی — این دستور فقط متن‌ها و قواعد را می‌سازد.
"""

from django.core.management.base import BaseCommand

from main.models import (BookingSettings, Brand, Field, Profile, TimeSlot, WeekdayRule)


FIELDS = [
    ("Fashion",      "مدل لباس",     "کمپین و لوک‌بوک",  True),
    ("Jewellery",    "مدل بدلیجات",  "کاتالوگ و ویترین", True),
    ("Bridal",       "مدل عروس",     "مزون و آتلیه",     True),
    ("Beauty",       "مدل آرایشی",   "پوست، مو و گریم",  True),
    ("Editorial",    "ادیتوریال",    "مجله و تحریریه",   True),
    ("Commercial",   "تبلیغاتی",     "ویدیو و بیلبورد",  True),
    ("Runway",       "کت‌واک",       "شو و رونمایی",     True),
    ("Fitness",      "ورزشی",        "اسپرت و اکتیو",    True),
    ("Hands & Parts", "دست و جزئیات", "",                False),
    ("Lingerie",     "لباس راحتی",   "",                 False),
    ("Swimwear",     "مایو و ساحلی", "",                 False),
    ("Promotional",  "نمایشگاهی",    "",                 False),
]

# شنبه = ۰ … جمعه = ۶
OPEN_DAYS = {0, 3, 4, 6}

HOURS = [9, 10, 11, 12, 13, 14, 15, 16, 17]


class Command(BaseCommand):
    help = "ساخت ردیف‌های اولیه‌ی سایت یکتا"

    def handle(self, *args, **options):
        made = []

        # پروفایل
        profile = Profile.load()
        if not profile.height:
            profile.statement = "پروژه‌هایم را خودم انتخاب می‌کنم و سر وقت سر صحنه‌ام."
            profile.about = ("کار با برندهای پوشاک، زیورآلات و کمپین‌های تبلیغاتی. "
                             "هر قاب یک تصمیم است، نه یک اتفاق.")
            profile.hair = "مسی"
            profile.save()
            made.append("پروفایل")

        # تنظیمات رزرو
        BookingSettings.load()
        made.append("تنظیمات رزرو")

        # حوزه‌ها
        n = 0
        for i, (en, name_fa, note, on_arc) in enumerate(FIELDS):
            _, created = Field.objects.get_or_create(
                en=en,
                defaults={"name_fa": name_fa, "note": note, "on_arc": on_arc, "order": i},
            )
            n += 1 if created else 0
        if n:
            made.append("%d حوزه" % n)

        # الگوی هفتگی
        n = 0
        for wd in range(7):
            _, created = WeekdayRule.objects.get_or_create(
                weekday=wd, defaults={"is_open": wd in OPEN_DAYS}
            )
            n += 1 if created else 0
        if n:
            made.append("%d روز هفته" % n)

        # ساعت‌ها
        n = 0
        for h in HOURS:
            _, created = TimeSlot.objects.get_or_create(hour=h, defaults={"is_active": True})
            n += 1 if created else 0
        if n:
            made.append("%d ساعت" % n)

        if made:
            self.stdout.write(self.style.SUCCESS("ساخته شد: " + "، ".join(made)))
        else:
            self.stdout.write("همه‌چیز از قبل موجود بود؛ تغییری داده نشد.")

        self.stdout.write("قدم بعد: از پنل، تصویرها و کارها را اضافه کن.")
