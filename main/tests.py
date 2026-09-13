"""
تست‌های سایت یکتا.

اجرا:  python manage.py test main

اینجا فقط چیزهایی تست می‌شوند که اگر بشکنند، بی‌سروصدا بد عمل می‌کنند:
قواعد رزرو، تداخل ساعت، فیلتر واژه‌های زشت، ورود با شماره، و دسترسی‌ها.
"""

from datetime import date, timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import (Account, BookingSettings, Calendar, CollabKind, CollabRequest,
                     Employer, ModelType, Photo, Place, TimeSlot, WeekdayRule,
                     clean_phone)
from .profanity import find_bad


def open_all_days():
    for wd in range(7):
        WeekdayRule.objects.update_or_create(weekday=wd, defaults={"is_open": True})


def make_hours():
    for h in range(9, 20):
        TimeSlot.objects.get_or_create(hour=h, defaults={"is_active": True})


class PhoneTests(TestCase):

    def test_shapes(self):
        for raw in ["09121234567", "۰۹۱۲۱۲۳۴۵۶۷", "0912 123 4567",
                    "+989121234567", "00989121234567", "9121234567",
                    "0912-123-4567"]:
            self.assertEqual(clean_phone(raw), "09121234567", raw)

    def test_bad(self):
        for raw in ["", "0912", "123456789012", "abcdefghijk", None]:
            self.assertIsNone(clean_phone(raw))


class ProfanityTests(TestCase):

    def test_blocks(self):
        for bad in ["کیری", "ک.و.ن.ی", "کووونی", "جـنده", "fuck off", "Fu.ck",
                    "آتلیه سکس", "مادر جنده"]:
            self.assertIsNotNone(find_bad(bad), bad)

    def test_allows_real_names(self):
        for ok in ["گالری رها", "مزون آوا", "پت شاپ سگ و گربه", "خرید آنلاین",
                   "بوتیک کیمیا", "استودیو کاج", "سارا محمدی", "Nike Store"]:
            self.assertIsNone(find_bad(ok), ok)


class CalendarTests(TestCase):

    def setUp(self):
        open_all_days()
        self.acc = Account.objects.create_user("a@b.com", "Aa!12345")
        self.emp = Employer.objects.create(account=self.acc, company="رها",
                                           contact_name="سارا", phone="09120000000")

    def test_pending_holds_the_slot(self):
        """
        درخواست در انتظار هم باید ساعت را «گرفته» کند.

        بدون این، دو کارفرما می‌توانستند هم‌زمان یک ساعت را بگیرند و تداخل
        تازه موقع تایید معلوم می‌شد.
        """
        day = date.today() + timedelta(days=5)

        CollabRequest.objects.create(employer=self.emp, date=day,
                                     start_hour=10, hours=2,
                                     status=CollabRequest.PENDING)

        self.assertEqual(Calendar().taken_hours(day), {10, 11})

    def test_expired_pending_frees_the_slot(self):
        day = date.today() + timedelta(days=5)

        row = CollabRequest.objects.create(employer=self.emp, date=day,
                                           start_hour=10, hours=2,
                                           status=CollabRequest.PENDING)
        row.expires = timezone.now() - timedelta(hours=1)
        row.save(update_fields=["expires"])

        self.assertEqual(Calendar().taken_hours(day), set())

    def test_rejected_frees_the_slot(self):
        day = date.today() + timedelta(days=5)
        CollabRequest.objects.create(employer=self.emp, date=day,
                                     start_hour=10, hours=2,
                                     status=CollabRequest.REJECTED)
        self.assertEqual(Calendar().taken_hours(day), set())


class BookingViewTests(TestCase):

    def setUp(self):
        open_all_days()
        make_hours()

        book = BookingSettings.load()
        book.is_open = True
        book.min_notice = 1
        book.horizon_days = 90
        book.max_hours = 4
        book.day_end = 19
        book.floor_price = 2_000_000
        book.save()

        self.kind = CollabKind.objects.create(name="عکاسی")
        self.mtype = ModelType.objects.create(name="لباس")
        self.place = Place.objects.create(name="استودیو")

        self.acc = Account.objects.create_user("boss@b.com", "Aa!12345")
        self.acc.phone = "09121112233"
        self.acc.save()
        self.emp = Employer.objects.create(account=self.acc, company="رها",
                                           contact_name="سارا", phone="09121112233")

        self.day = date.today() + timedelta(days=7)

    def payload(self, **over):
        data = {
            "kind": self.kind.pk,
            "model_type": self.mtype.pk,
            "place_ref": self.place.pk,
            "budget_mode": "set",
            "budget_amount": "3500000",
            "date": self.day.isoformat(),
            "start_hour": 10,
            "hours": 2,
            "place": "",
            "crew": "",
            "brief": "دو لوک",
        }
        data.update(over)
        return data

    def test_guest_is_sent_to_signup_and_draft_is_kept(self):
        r = self.client.post(reverse("collab_submit"), self.payload())
        self.assertEqual(r.status_code, 401)
        self.assertEqual(r.json()["need"], "signup")
        self.assertEqual(self.client.session["collab_draft"]["start_hour"], 10)
        self.assertFalse(CollabRequest.objects.exists())

    def test_employer_can_book(self):
        self.client.force_login(self.acc)
        r = self.client.post(reverse("collab_submit"), self.payload())
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()["ok"])
        self.assertEqual(CollabRequest.objects.count(), 1)

    def test_overlapping_booking_is_refused(self):
        self.client.force_login(self.acc)
        self.client.post(reverse("collab_submit"), self.payload())

        r = self.client.post(reverse("collab_submit"),
                             self.payload(start_hour=11, hours=1))
        self.assertEqual(r.status_code, 409)
        self.assertEqual(CollabRequest.objects.count(), 1)

    def test_budget_below_floor_is_refused(self):
        self.client.force_login(self.acc)
        r = self.client.post(reverse("collab_submit"),
                             self.payload(budget_amount="500000"))
        self.assertEqual(r.status_code, 400)
        self.assertFalse(CollabRequest.objects.exists())

    def test_budget_can_be_left_open(self):
        self.client.force_login(self.acc)
        r = self.client.post(reverse("collab_submit"),
                             self.payload(budget_mode="ask", budget_amount=""))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(CollabRequest.objects.first().budget_amount, None)

    def test_too_soon_is_refused(self):
        self.client.force_login(self.acc)
        r = self.client.post(reverse("collab_submit"),
                             self.payload(date=date.today().isoformat()))
        self.assertEqual(r.status_code, 400)

    def test_work_must_end_before_day_end(self):
        self.client.force_login(self.acc)
        r = self.client.post(reverse("collab_submit"),
                             self.payload(start_hour=18, hours=4))
        self.assertEqual(r.status_code, 400)

    def test_hours_api_reports_taken(self):
        self.client.force_login(self.acc)
        self.client.post(reverse("collab_submit"), self.payload())

        r = self.client.get(reverse("api_hours"), {"date": self.day.isoformat()})
        self.assertEqual(r.json()["taken"], [10, 11])

    def test_hours_api_rejects_bad_date(self):
        r = self.client.get(reverse("api_hours"), {"date": "نه‌تاریخ"})
        self.assertEqual(r.status_code, 400)


class SignupTests(TestCase):

    def form(self, **over):
        data = {
            "full_name": "سارا محمدی",
            "email": "sara@example.com",
            "phone": "09121234567",
            "password": "Sara!12345",
            "password2": "Sara!12345",
            "company": "گالری رها",
            "activity": "apparel",
            "contact_name": "",
            "instagram": "",
            "links": "",
            "city": "تهران",
            "address": "",
            "website": "",
        }
        data.update(over)
        return data

    def test_signup_creates_employer(self):
        r = self.client.post(reverse("signup"), self.form())
        self.assertEqual(r.status_code, 302)
        acc = Account.objects.get(email="sara@example.com")
        self.assertEqual(acc.phone, "09121234567")
        self.assertEqual(acc.employer.company, "گالری رها")

    def test_dirty_company_is_refused(self):
        r = self.client.post(reverse("signup"), self.form(company="گالری کیری"))
        self.assertEqual(r.status_code, 200)
        self.assertFalse(Account.objects.filter(email="sara@example.com").exists())

    def test_dirty_name_is_refused(self):
        r = self.client.post(reverse("signup"), self.form(full_name="ک.و.ن.ی"))
        self.assertEqual(r.status_code, 200)
        self.assertFalse(Account.objects.exists())

    def test_honeypot_blocks_bots(self):
        r = self.client.post(reverse("signup"), self.form(website="http://spam"))
        self.assertEqual(r.status_code, 200)
        self.assertFalse(Account.objects.exists())

    def test_duplicate_phone_is_refused(self):
        self.client.post(reverse("signup"), self.form())
        # ثبت‌نام کاربر را وارد حساب می‌کند؛ برای ثبت‌نام دوم باید بیرون بیاید
        self.client.logout()
        r = self.client.post(reverse("signup"),
                             self.form(email="other@example.com"))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Account.objects.count(), 1)


class LoginTests(TestCase):

    def setUp(self):
        self.acc = Account.objects.create_user("a@b.com", "Aa!12345",
                                               full_name="سارا")
        self.acc.phone = "09121234567"
        self.acc.save()
        Employer.objects.create(account=self.acc, company="رها",
                                contact_name="سارا", phone="09121234567")

    def test_login_with_email(self):
        ok = self.client.login(username="a@b.com", password="Aa!12345")
        self.assertTrue(ok)

    def test_login_with_phone(self):
        ok = self.client.login(username="09121234567", password="Aa!12345")
        self.assertTrue(ok)

    def test_login_with_persian_digits(self):
        ok = self.client.login(username="۰۹۱۲۱۲۳۴۵۶۷", password="Aa!12345")
        self.assertTrue(ok)

    def test_lockout_after_five_tries(self):
        for _ in range(5):
            self.client.login(username="a@b.com", password="wrong!")
        self.acc.refresh_from_db()
        self.assertTrue(self.acc.is_locked)
        self.assertFalse(self.client.login(username="a@b.com", password="Aa!12345"))


class AccessTests(TestCase):
    """پنل استودیو نباید حتی وجودش برای کاربر عادی معلوم شود."""

    def setUp(self):
        self.boss = Account.objects.create_user("boss@b.com", "Aa!12345")
        Employer.objects.create(account=self.boss, company="رها",
                                contact_name="س", phone="09120000000")

        self.yekta = Account.objects.create_user("y@b.com", "Aa!12345")
        self.yekta.role = Account.MODEL
        self.yekta.save()

    def test_guest_is_sent_to_login(self):
        r = self.client.get(reverse("studio"))
        self.assertEqual(r.status_code, 302)
        self.assertIn(reverse("login"), r.url)

    def test_employer_gets_404(self):
        self.client.force_login(self.boss)
        self.assertEqual(self.client.get(reverse("studio")).status_code, 404)

    def test_model_gets_in(self):
        self.client.force_login(self.yekta)
        self.assertEqual(self.client.get(reverse("studio")).status_code, 200)

    def test_model_is_sent_from_dashboard_to_studio(self):
        self.client.force_login(self.yekta)
        r = self.client.get(reverse("dashboard"))
        self.assertEqual(r.status_code, 302)
        self.assertIn("studio", r.url)


class GalleryTests(TestCase):

    def setUp(self):
        self.shot = Photo.objects.create(title="قاب", is_published=True)

    def test_opening_a_photo_counts_a_click(self):
        self.client.get(reverse("photo", args=[self.shot.pk]))
        self.shot.refresh_from_db()
        self.assertEqual(self.shot.clicks, 1)
        self.assertEqual(self.shot.click_rows.count(), 1)

    def test_hidden_photo_is_not_public(self):
        self.shot.is_published = False
        self.shot.save()
        r = self.client.get(reverse("photo", args=[self.shot.pk]))
        self.assertEqual(r.status_code, 404)


class SupportTests(TestCase):

    def test_message_is_saved(self):
        r = self.client.post(reverse("support"), {
            "name": "نیما", "phone": "09125556677",
            "body": "برای یک کمپین دو روزه امکانش هست؟", "website": "",
        })
        self.assertEqual(r.status_code, 302)

    def test_dirty_message_is_refused(self):
        r = self.client.post(reverse("support"), {
            "name": "", "phone": "09125556677", "body": "برو بابا کیری", "website": "",
        })
        self.assertEqual(r.status_code, 200)
