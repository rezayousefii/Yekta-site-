"""
دیتابیس سایت یکتا.

چهار دسته مدل:
  ۱) محتوای سایت      — پروفایل، حوزه‌ها، کارها، ویترین، برندها
  ۲) تقویم و دسترسی   — الگوی هفتگی، استثنای روز، قفل بازه‌ای، ساعت‌ها، تنظیمات رزرو
  ۳) حساب کارفرما     — Account (کاربر سفارشی با ایمیل) و Employer
  ۴) درخواست و گفتگو  — CollabRequest، Message، AuditLog
"""

from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


# ══════════════════════════════════════════════════════════
#  ابزار مشترک
# ══════════════════════════════════════════════════════════

WEEKDAYS = [
    (0, "شنبه"), (1, "یکشنبه"), (2, "دوشنبه"), (3, "سه‌شنبه"),
    (4, "چهارشنبه"), (5, "پنجشنبه"), (6, "جمعه"),
]

DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def fa(value):
    """عدد لاتین را به فارسی برمی‌گرداند."""
    return str(value).translate(DIGITS)


def clock(hour):
    """۹ → «۰۹:۰۰»"""
    return fa("%02d:00" % hour)


class Singleton(models.Model):
    """مدلی که همیشه فقط یک ردیف دارد."""

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


# ══════════════════════════════════════════════════════════
#  ۱) محتوای سایت
# ══════════════════════════════════════════════════════════

class Profile(Singleton):
    """مشخصات یکتا — همان چیزی که در هیرو و بخش «مشخصات» دیده می‌شود."""

    name_fa   = models.CharField("نام فارسی", max_length=60, default="یکتا")
    name_en   = models.CharField("نام لاتین", max_length=60, default="YEKTA")
    tagline   = models.CharField("زیرنویس هیرو", max_length=160, blank=True,
                                 default="مدل پوشاک، زیورآلات و کمپین — تهران")
    statement = models.TextField("جمله‌ی معرفی", blank=True)
    about     = models.TextField("توضیح کوتاه", blank=True)

    height    = models.CharField("قد", max_length=20, blank=True)
    weight    = models.CharField("وزن", max_length=20, blank=True)
    hair      = models.CharField("رنگ مو", max_length=30, blank=True)
    eyes      = models.CharField("رنگ چشم", max_length=30, blank=True)
    shoe      = models.CharField("سایز کفش", max_length=20, blank=True)
    dress     = models.CharField("سایز لباس", max_length=20, blank=True)
    city      = models.CharField("شهر", max_length=40, blank=True, default="تهران")

    instagram = models.URLField("اینستاگرام", blank=True)
    email     = models.EmailField("ایمیل تماس", blank=True)

    hero_video  = models.FileField("ویدیوی هیرو", upload_to="hero/", blank=True)
    hero_poster = models.ImageField("پوستر ویدیو", upload_to="hero/", blank=True)
    banner_cut  = models.ImageField("تصویر بنر (PNG بدون پس‌زمینه)",
                                    upload_to="banner/", blank=True)

    updated = models.DateTimeField("آخرین ویرایش", auto_now=True)

    class Meta:
        verbose_name = "پروفایل یکتا"
        verbose_name_plural = "پروفایل یکتا"

    def __str__(self):
        return self.name_fa

    def specs(self):
        """ردیف‌های بخش مشخصات — فقط آن‌هایی که پر شده‌اند."""
        rows = [("قد", self.height), ("وزن", self.weight),
                ("رنگ مو", self.hair), ("رنگ چشم", self.eyes),
                ("سایز کفش", self.shoe), ("سایز لباس", self.dress)]
        return [{"k": k, "v": v or "—"} for k, v in rows]


class Field(models.Model):
    """حوزه‌ی کاری — کارت‌های اسلایدر کمانی."""

    FIT = [("cover", "پر کردن قاب"), ("contain", "جا شدن کامل (PNG بدون پس‌زمینه)")]

    en      = models.CharField("نام لاتین", max_length=40)
    name_fa = models.CharField("نام فارسی", max_length=40)
    note  = models.CharField("توضیح کوتاه", max_length=60, blank=True)
    image = models.ImageField("تصویر", upload_to="fields/", blank=True)
    fit   = models.CharField("نحوه‌ی نمایش تصویر", max_length=10, choices=FIT, default="cover")

    on_arc    = models.BooleanField("روی اسلایدر کمانی نمایش داده شود", default=True)
    is_active = models.BooleanField("فعال", default=True)
    order     = models.PositiveIntegerField("ترتیب", default=0)

    class Meta:
        verbose_name = "حوزه‌ی کاری"
        verbose_name_plural = "حوزه‌های کاری"
        ordering = ["order", "id"]

    def __str__(self):
        return "%s — %s" % (self.name_fa, self.en)


class Work(models.Model):
    """یک پروژه در تخته‌ی کارها؛ با کلیک، قاب‌هایش در لایت‌باکس باز می‌شود."""

    title = models.CharField("عنوان", max_length=80)
    meta  = models.CharField("زیرعنوان", max_length=120, blank=True)
    field = models.ForeignKey(Field, verbose_name="حوزه", on_delete=models.SET_NULL,
                              null=True, blank=True, related_name="works")
    cover = models.ImageField("کاور", upload_to="works/", blank=True)

    year         = models.CharField("سال", max_length=10, blank=True)
    photographer = models.CharField("عکاس", max_length=80, blank=True)

    is_published = models.BooleanField("منتشر شده", default=True)
    order        = models.PositiveIntegerField("ترتیب", default=0)
    created      = models.DateTimeField("ایجاد", auto_now_add=True)

    class Meta:
        verbose_name = "کار"
        verbose_name_plural = "کارها"
        ordering = ["order", "-created"]

    def __str__(self):
        return self.title


class WorkShot(models.Model):
    """قاب‌های یک کار."""

    work    = models.ForeignKey(Work, verbose_name="کار", on_delete=models.CASCADE,
                               related_name="shots")
    image   = models.ImageField("تصویر", upload_to="works/shots/")
    caption = models.CharField("توضیح", max_length=120, blank=True)
    order   = models.PositiveIntegerField("ترتیب", default=0)

    class Meta:
        verbose_name = "قاب"
        verbose_name_plural = "قاب‌ها"
        ordering = ["order", "id"]

    def __str__(self):
        return "%s — %s" % (self.work.title, self.caption or self.pk)


class Showcase(models.Model):
    """
    تصویرهای چیدمان صفحه‌ی اول که پروژه‌ی مستقل نیستند.
    هر «جایگاه» چند تصویر می‌گیرد و صفحه به ترتیب از آن‌ها برمی‌دارد.
    """

    SPOTS = [
        ("mini",    "سه عکس کوچک کنار جمله"),
        ("feature", "عکس تمام‌عرض"),
        ("duo",     "دو عکس چسبیده"),
        ("plate",   "قاب پاسپارتو"),
        ("cover",   "شبکه‌ی ادیتوریال"),
        ("reel",    "لاین افقی"),
    ]

    spot    = models.CharField("جایگاه", max_length=12, choices=SPOTS)
    image   = models.ImageField("تصویر", upload_to="showcase/")
    caption = models.CharField("عنوان", max_length=120, blank=True)
    meta    = models.CharField("زیرنویس", max_length=120, blank=True)

    is_active = models.BooleanField("فعال", default=True)
    order     = models.PositiveIntegerField("ترتیب", default=0)

    class Meta:
        verbose_name = "تصویر چیدمان"
        verbose_name_plural = "تصویرهای چیدمان"
        ordering = ["spot", "order", "id"]

    def __str__(self):
        return "%s — %s" % (self.get_spot_display(), self.caption or self.pk)


class Brand(models.Model):
    """برندهایی که یکتا با آن‌ها کار کرده."""

    name      = models.CharField("نام", max_length=80)
    note      = models.CharField("توضیح", max_length=80, blank=True)
    logo      = models.ImageField(
        "لوگو یا تصویر", upload_to="brands/", blank=True,
        help_text="اختیاری — اگر خالی بماند، حرف اول نام به‌جایش نشان داده می‌شود.")
    is_active = models.BooleanField("فعال", default=True)
    order     = models.PositiveIntegerField("ترتیب", default=0)

    class Meta:
        verbose_name = "برند"
        verbose_name_plural = "برندها"
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


# ══════════════════════════════════════════════════════════
#  ۲) تقویم و دسترسی
# ══════════════════════════════════════════════════════════

class WeekdayRule(models.Model):
    """الگوی همیشگی هفته — پایه‌ی تقویم."""

    weekday = models.IntegerField("روز هفته", choices=WEEKDAYS, unique=True)
    is_open = models.BooleanField("معمولاً آزاد", default=False)

    class Meta:
        verbose_name = "الگوی روز هفته"
        verbose_name_plural = "الگوی هفتگی"
        ordering = ["weekday"]

    def __str__(self):
        return "%s — %s" % (self.get_weekday_display(), "آزاد" if self.is_open else "بسته")


class DateException(models.Model):
    """یک روز مشخص، برخلاف الگوی هفتگی، باز یا بسته می‌شود."""

    date    = models.DateField("تاریخ", unique=True)
    is_open = models.BooleanField("این روز آزاد باشد", default=False)
    note    = models.CharField("یادداشت", max_length=120, blank=True)

    class Meta:
        verbose_name = "استثنای روز"
        verbose_name_plural = "استثناهای روز"
        ordering = ["date"]

    def __str__(self):
        return "%s — %s" % (self.date, "آزاد" if self.is_open else "بسته")


class ClosureRange(models.Model):
    """
    قفل بازه‌ای — یک هفته یا یک ماه یکجا بسته می‌شود.
    این از همه چیز بالاتر است؛ حتی استثنای روز را هم لغو می‌کند.
    """

    start = models.DateField("از تاریخ")
    end   = models.DateField("تا تاریخ")
    note  = models.CharField("علت", max_length=120, blank=True)

    class Meta:
        verbose_name = "قفل بازه‌ای"
        verbose_name_plural = "قفل‌های بازه‌ای"
        ordering = ["-start"]

    def __str__(self):
        return "%s تا %s" % (self.start, self.end)

    def covers(self, day):
        return self.start <= day <= self.end


class TimeSlot(models.Model):
    """ساعت‌های شروعی که کارفرما می‌تواند انتخاب کند."""

    hour      = models.PositiveSmallIntegerField("ساعت (۰ تا ۲۳)", unique=True)
    is_active = models.BooleanField("فعال", default=True)

    class Meta:
        verbose_name = "ساعت شروع"
        verbose_name_plural = "ساعت‌های شروع"
        ordering = ["hour"]

    def __str__(self):
        return clock(self.hour)

    @property
    def label(self):
        return clock(self.hour)


class BookingSettings(Singleton):
    """قواعد رزرو — همه‌چیز از پنل قابل تغییر."""

    is_open       = models.BooleanField("پذیرش درخواست باز است", default=True)
    day_end       = models.PositiveSmallIntegerField("دیرترین ساعت پایان کار", default=19)
    max_hours     = models.PositiveSmallIntegerField("بیشترین مدت هر رزرو (ساعت)", default=4)
    min_notice    = models.PositiveSmallIntegerField("حداقل فاصله تا امروز (روز)", default=1)
    horizon_days  = models.PositiveSmallIntegerField("تا چند روز جلوتر قابل رزرو", default=90)
    request_ttl   = models.PositiveSmallIntegerField("اعتبار هر درخواست (ساعت)", default=24)
    closed_note   = models.CharField("پیام وقتی پذیرش بسته است", max_length=160, blank=True)

    class Meta:
        verbose_name = "تنظیمات رزرو"
        verbose_name_plural = "تنظیمات رزرو"

    def __str__(self):
        return "تنظیمات رزرو"


class Calendar:
    """
    تصمیم‌گیرِ باز/بسته بودن یک روز.
    ترتیب: قفل بازه‌ای ← استثنای روز ← الگوی هفتگی
    """

    def __init__(self):
        self.rules   = {r.weekday: r.is_open for r in WeekdayRule.objects.all()}
        self.excs    = {e.date: e.is_open for e in DateException.objects.all()}
        self.locks   = list(ClosureRange.objects.all())
        self.settings = BookingSettings.load()

    def weekday_of(self, day):
        """شنبه = ۰"""
        return (day.weekday() + 2) % 7

    def is_free(self, day):
        for lock in self.locks:
            if lock.covers(day):
                return False
        if day in self.excs:
            return self.excs[day]
        return self.rules.get(self.weekday_of(day), False)

    def taken_hours(self, day):
        """ساعت‌هایی که با یک درخواست تاییدشده پر شده‌اند."""
        busy = set()
        rows = CollabRequest.objects.filter(date=day, status=CollabRequest.APPROVED)
        for r in rows:
            for h in range(r.start_hour, r.start_hour + r.hours):
                busy.add(h)
        return busy


# ══════════════════════════════════════════════════════════
#  ۳) حساب کارفرما
# ══════════════════════════════════════════════════════════

class AccountManager(BaseUserManager):

    def create_user(self, email, password=None, **extra):
        if not email:
            raise ValueError("ایمیل لازم است.")
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        extra.setdefault("is_active", True)
        extra.setdefault("email_verified", True)
        return self.create_user(email, password, **extra)


class Account(AbstractBaseUser, PermissionsMixin):
    """
    کاربر سایت. ورود با ایمیل است، نه نام کاربری.
    رمز هرگز خام ذخیره نمی‌شود؛ جنگو آن را هش می‌کند.
    """

    email     = models.EmailField("ایمیل", unique=True)
    full_name = models.CharField("نام و نام خانوادگی", max_length=80, blank=True)

    is_active = models.BooleanField("فعال", default=True)
    is_staff  = models.BooleanField("دسترسی به پنل", default=False)

    email_verified = models.BooleanField("ایمیل تایید شده", default=False)

    failed_logins = models.PositiveSmallIntegerField("تلاش‌های ناموفق", default=0)
    locked_until  = models.DateTimeField("قفل تا", null=True, blank=True)
    last_ip       = models.GenericIPAddressField("آخرین IP", null=True, blank=True)

    date_joined = models.DateTimeField("تاریخ عضویت", default=timezone.now)

    objects = AccountManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "حساب"
        verbose_name_plural = "حساب‌ها"
        ordering = ["-date_joined"]

    def __str__(self):
        return self.email

    @property
    def is_locked(self):
        return bool(self.locked_until and self.locked_until > timezone.now())

    def note_failed_login(self, tries=5, minutes=15):
        self.failed_logins += 1
        if self.failed_logins >= tries:
            self.locked_until = timezone.now() + timedelta(minutes=minutes)
            self.failed_logins = 0
        self.save(update_fields=["failed_logins", "locked_until"])

    def note_good_login(self, ip=None):
        self.failed_logins = 0
        self.locked_until = None
        if ip:
            self.last_ip = ip
        self.save(update_fields=["failed_logins", "locked_until", "last_ip"])


class EmailToken(models.Model):
    """توکن یک‌بارمصرف برای تایید ایمیل و بازیابی رمز."""

    VERIFY = "verify"
    RESET  = "reset"
    KINDS  = [(VERIFY, "تایید ایمیل"), (RESET, "بازیابی رمز")]

    account = models.ForeignKey(Account, verbose_name="حساب", on_delete=models.CASCADE,
                               related_name="tokens")
    token   = models.CharField("توکن", max_length=64, unique=True, db_index=True)
    kind    = models.CharField("نوع", max_length=10, choices=KINDS, default=VERIFY)
    created = models.DateTimeField("ایجاد", auto_now_add=True)
    expires = models.DateTimeField("انقضا")
    used_at = models.DateTimeField("زمان استفاده", null=True, blank=True)

    class Meta:
        verbose_name = "توکن ایمیل"
        verbose_name_plural = "توکن‌های ایمیل"
        ordering = ["-created"]

    def __str__(self):
        return "%s — %s" % (self.account.email, self.get_kind_display())

    @property
    def is_valid(self):
        return self.used_at is None and self.expires > timezone.now()


class Employer(models.Model):
    """پروفایل کارفرما — فروشگاه، برند یا آژانسی که درخواست می‌دهد."""

    ACTIVITY = [
        ("apparel",   "پوشاک"),
        ("jewellery", "زیورآلات و اکسسوری"),
        ("beauty",    "آرایشی و بهداشتی"),
        ("bridal",    "عروس و مزون"),
        ("sports",    "ورزشی"),
        ("agency",    "آژانس تبلیغاتی"),
        ("studio",    "عکاسی و استودیو"),
        ("other",     "سایر"),
    ]

    account = models.OneToOneField(Account, verbose_name="حساب", on_delete=models.CASCADE,
                                   related_name="employer")

    company      = models.CharField("نام برند / فروشگاه", max_length=120)
    activity     = models.CharField("حیطه‌ی فعالیت", max_length=20,
                                    choices=ACTIVITY, default="other")
    contact_name = models.CharField("نام رابط", max_length=80)
    phone        = models.CharField("شماره تماس", max_length=20)
    city         = models.CharField("شهر", max_length=40, blank=True)
    address      = models.TextField("نشانی", blank=True)
    website      = models.URLField("وب‌سایت", blank=True)
    links        = models.TextField("لینک‌های دیگر", blank=True,
                                    help_text="هر لینک در یک خط.")
    instagram    = models.CharField("اینستاگرام", max_length=80, blank=True)
    reg_no       = models.CharField("شناسه صنفی / ثبت", max_length=40, blank=True)

    # موقعیت روی نقشه — کارفرما خودش نشانگر را جابه‌جا می‌کند
    lat = models.FloatField("عرض جغرافیایی", null=True, blank=True)
    lng = models.FloatField("طول جغرافیایی", null=True, blank=True)

    is_trusted = models.BooleanField("کارفرمای مورد اعتماد", default=False)
    is_blocked = models.BooleanField("مسدود", default=False)
    note       = models.TextField("یادداشت داخلی یکتا", blank=True)

    created = models.DateTimeField("ایجاد", auto_now_add=True)
    updated = models.DateTimeField("ویرایش", auto_now=True)

    class Meta:
        verbose_name = "کارفرما"
        verbose_name_plural = "کارفرماها"
        ordering = ["-created"]

    def __str__(self):
        return "%s (%s)" % (self.company, self.contact_name)

    @property
    def link_list(self):
        """لینک‌های ذخیره‌شده را به‌صورت فهرست برمی‌گرداند."""
        return [ln.strip() for ln in (self.links or "").splitlines() if ln.strip()]

    @property
    def map_url(self):
        """لینک باز کردن موقعیت در نقشه — برای پنل مدیریت."""
        if self.lat is None or self.lng is None:
            return ""
        return "https://www.openstreetmap.org/?mlat=%s&mlon=%s#map=17/%s/%s" % (
            self.lat, self.lng, self.lat, self.lng)


# ══════════════════════════════════════════════════════════
#  ۴) درخواست همکاری و گفتگو
# ══════════════════════════════════════════════════════════

class CollabRequest(models.Model):
    """یک درخواست رزرو از سمت کارفرما."""

    PENDING     = "pending"
    APPROVED    = "approved"
    REJECTED    = "rejected"
    ALTERNATIVE = "alternative"
    CANCELLED   = "cancelled"
    EXPIRED     = "expired"
    DONE        = "done"

    STATUS = [
        (PENDING,     "در انتظار پاسخ"),
        (APPROVED,    "تایید شده"),
        (REJECTED,    "رد شده"),
        (ALTERNATIVE, "پیشنهاد زمان جایگزین"),
        (CANCELLED,   "لغو شده"),
        (EXPIRED,     "منقضی شده"),
        (DONE,        "انجام شده"),
    ]

    employer = models.ForeignKey(Employer, verbose_name="کارفرما", on_delete=models.PROTECT,
                                related_name="requests")

    # زمان درخواستی
    date       = models.DateField("تاریخ")
    start_hour = models.PositiveSmallIntegerField("ساعت شروع")
    hours      = models.PositiveSmallIntegerField("مدت (ساعت)", default=1)

    field   = models.ForeignKey(Field, verbose_name="حوزه", on_delete=models.SET_NULL,
                                null=True, blank=True, related_name="requests")
    brief   = models.TextField("شرح کار", blank=True)
    place   = models.CharField("محل کار", max_length=140, blank=True)
    budget  = models.CharField("بودجه‌ی پیشنهادی", max_length=60, blank=True)

    status = models.CharField("وضعیت", max_length=12, choices=STATUS, default=PENDING)

    # پاسخ یکتا
    reply         = models.TextField("پیام یکتا", blank=True)
    alt_date      = models.DateField("تاریخ جایگزین", null=True, blank=True)
    alt_start     = models.PositiveSmallIntegerField("ساعت جایگزین", null=True, blank=True)
    alt_hours     = models.PositiveSmallIntegerField("مدت جایگزین", null=True, blank=True)
    decided_at    = models.DateTimeField("زمان تصمیم", null=True, blank=True)

    # اطلاعات کارفرما در لحظه‌ی ثبت — بعداً هم عوض نمی‌شود
    snap_company = models.CharField("برند (ثبت‌شده)", max_length=120, blank=True)
    snap_contact = models.CharField("رابط (ثبت‌شده)", max_length=80, blank=True)
    snap_phone   = models.CharField("تلفن (ثبت‌شده)", max_length=20, blank=True)

    created  = models.DateTimeField("زمان ثبت", auto_now_add=True)
    expires  = models.DateTimeField("اعتبار تا", null=True, blank=True)
    seen_at  = models.DateTimeField("دیده شده", null=True, blank=True)
    from_ip  = models.GenericIPAddressField("IP ثبت", null=True, blank=True)

    class Meta:
        verbose_name = "درخواست همکاری"
        verbose_name_plural = "درخواست‌های همکاری"
        ordering = ["-created"]
        indexes = [
            models.Index(fields=["date", "status"]),
            models.Index(fields=["status", "-created"]),
        ]

    def __str__(self):
        return "%s — %s %s" % (self.snap_company or self.employer.company,
                               self.date, clock(self.start_hour))

    def save(self, *args, **kwargs):
        if not self.pk:
            emp = self.employer
            self.snap_company = emp.company
            self.snap_contact = emp.contact_name
            self.snap_phone   = emp.phone
            if not self.expires:
                ttl = BookingSettings.load().request_ttl
                self.expires = timezone.now() + timedelta(hours=ttl)
        super().save(*args, **kwargs)

    @property
    def end_hour(self):
        return self.start_hour + self.hours

    @property
    def span(self):
        return "%s تا %s" % (clock(self.start_hour), clock(self.end_hour))

    @property
    def is_expired(self):
        return self.status == self.PENDING and self.expires and self.expires < timezone.now()

    def decide(self, status, reply="", actor=None):
        """تایید / رد / پیشنهاد جایگزین — همه با امکان پیام دلخواه."""
        self.status = status
        self.reply = reply
        self.decided_at = timezone.now()
        self.save()

        if reply:
            Message.objects.create(request=self, sender=Message.MODEL, body=reply)

        AuditLog.objects.create(
            actor=actor,
            action="decide:%s" % status,
            target="CollabRequest#%s" % self.pk,
            detail=reply[:400],
        )


class Message(models.Model):
    """
    هر پیامی که بین یکتا و کارفرما رد و بدل می‌شود اینجا می‌ماند.
    هیچ پیامی پاک نمی‌شود؛ فقط علامت حذف می‌خورد.
    """

    MODEL    = "model"
    EMPLOYER = "employer"
    SYSTEM   = "system"
    SENDERS  = [(MODEL, "یکتا"), (EMPLOYER, "کارفرما"), (SYSTEM, "سیستم")]

    request = models.ForeignKey(CollabRequest, verbose_name="درخواست",
                                on_delete=models.CASCADE, related_name="messages")
    sender  = models.CharField("فرستنده", max_length=10, choices=SENDERS)
    body    = models.TextField("متن پیام")

    created = models.DateTimeField("زمان", auto_now_add=True)
    read_at = models.DateTimeField("زمان خواندن", null=True, blank=True)
    hidden  = models.BooleanField("مخفی شده", default=False)

    class Meta:
        verbose_name = "پیام"
        verbose_name_plural = "پیام‌ها"
        ordering = ["created"]

    def __str__(self):
        return "%s — %s" % (self.get_sender_display(), self.body[:40])


class AuditLog(models.Model):
    """ردِ هر کاری که در پنل انجام می‌شود — برای این‌که چیزی گم نشود."""

    actor   = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="کاربر",
                                on_delete=models.SET_NULL, null=True, blank=True)
    action  = models.CharField("عمل", max_length=60)
    target  = models.CharField("روی چه چیزی", max_length=120, blank=True)
    detail  = models.TextField("جزئیات", blank=True)
    ip      = models.GenericIPAddressField("IP", null=True, blank=True)
    created = models.DateTimeField("زمان", auto_now_add=True)

    class Meta:
        verbose_name = "گزارش فعالیت"
        verbose_name_plural = "گزارش فعالیت"
        ordering = ["-created"]

    def __str__(self):
        return "%s — %s" % (self.action, self.target)
