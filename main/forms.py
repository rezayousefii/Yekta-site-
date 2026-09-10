"""فرم‌های سایت یکتا."""

import re

from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth.password_validation import validate_password

from .models import (Account, BookingSettings, CollabKind, CollabRequest, Employer,
                     Field, ModelType, Photo, Place, clean_phone)
from .validators import validate_clean, validate_image_upload

FA_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")


def _attrs(hint="", extra=None):
    """
    placeholder خالی برای «برچسب شناور» لازم است،
    data-hint همان نمونه‌ای است که موقع کلیک، سبزرنگ زیر فیلد نشان داده می‌شود.
    """
    base = {"placeholder": " "}
    if hint:
        base["data-hint"] = hint
    if extra:
        base.update(extra)
    return base


# ══════════════════════════════════════════════════════════
#  ورود، ثبت‌نام، بازیابی رمز
# ══════════════════════════════════════════════════════════

class LoginForm(AuthenticationForm):
    """
    ورود با جی‌میل یا شماره تلفن.

    فیلد username همان فیلد استاندارد جنگوست؛ فقط برچسب و راهنمایش عوض شده.
    تبدیل شماره به حساب، کار بک‌اند (main/backends.py) است نه این فرم — تا
    قفلِ تلاش‌های ناموفق هم سر جای خودش بماند.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "جی‌میل یا شماره تلفن"
        self.fields["username"].widget.attrs.update(
            _attrs("مثلاً name@gmail.com یا ۰۹۱۲۳۴۵۶۷۸۹",
                   {"autocomplete": "username", "dir": "ltr"}))
        self.fields["password"].label = "رمز عبور"
        self.fields["password"].widget.attrs.update(
            _attrs("", {"autocomplete": "current-password"}))

    def get_invalid_login_error(self):
        raw = (self.cleaned_data.get("username") or "").strip()
        phone = clean_phone(raw)

        user = (Account.objects.filter(phone=phone).first() if phone
                else Account.objects.filter(email=raw.lower()).first())

        if user and user.is_locked:
            return forms.ValidationError(
                "به‌خاطر چند تلاش ناموفق، این حساب موقتاً قفل شده. کمی بعد دوباره امتحان کن.")

        return forms.ValidationError("جی‌میل/شماره یا رمز درست نیست.")


class YektaPasswordResetForm(PasswordResetForm):
    """همان فرم بازیابی رمز جنگو، فقط با placeholder برای برچسب شناور."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].label = "ایمیل"
        self.fields["email"].widget.attrs.update(
            _attrs("همان ایمیلی که با آن ثبت‌نام کرده‌ای",
                   {"autocomplete": "email", "inputmode": "email", "dir": "ltr"}))


class YektaSetPasswordForm(SetPasswordForm):
    """همان فرم تعیین رمز تازه‌ی جنگو، فقط با placeholder برای برچسب شناور."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["new_password1"].label = "رمز عبور تازه"
        self.fields["new_password1"].widget.attrs.update(
            _attrs("دست‌کم ۸ نویسه، شامل حرف و یک نشانه مثل ! یا @",
                   {"autocomplete": "new-password"}))
        self.fields["new_password2"].label = "تکرار رمز تازه"
        self.fields["new_password2"].widget.attrs.update(
            _attrs("همان رمز بالا را دوباره بنویس", {"autocomplete": "new-password"}))


class SignupForm(forms.Form):

    # ── گام ۱: حساب ──
    full_name = forms.CharField(
        label="نام و نام خانوادگی", max_length=80,
        widget=forms.TextInput(attrs=_attrs(
            "مثلاً: سارا محمدی", {"autocomplete": "name"})))

    email = forms.EmailField(
        label="جی‌میل",
        widget=forms.EmailInput(attrs=_attrs(
            "مثلاً: name@gmail.com",
            {"autocomplete": "email", "inputmode": "email", "dir": "ltr"})))

    phone = forms.CharField(
        label="شماره تلفن همراه", max_length=20,
        widget=forms.TextInput(attrs=_attrs(
            "مثلاً: ۰۹۱۲۳۴۵۶۷۸۹",
            {"inputmode": "tel", "autocomplete": "tel", "dir": "ltr"})))

    password = forms.CharField(
        label="رمز عبور",
        widget=forms.PasswordInput(attrs=_attrs(
            "دست‌کم ۸ نویسه، شامل حرف و یک نشانه مثل ! یا @",
            {"autocomplete": "new-password"})))

    password2 = forms.CharField(
        label="تکرار رمز عبور",
        widget=forms.PasswordInput(attrs=_attrs(
            "همان رمز بالا را دوباره بنویس", {"autocomplete": "new-password"})))

    # ── گام ۲: کسب‌وکار ──
    company = forms.CharField(
        label="نام برند / فروشگاه", max_length=120,
        widget=forms.TextInput(attrs=_attrs("مثلاً: گالری رها")))

    activity = forms.ChoiceField(
        label="حیطه‌ی فعالیت", choices=Employer.ACTIVITY,
        widget=forms.Select(attrs={"data-hint": "نزدیک‌ترین گزینه به کارت را انتخاب کن"}))

    contact_name = forms.CharField(
        label="نام رابط پروژه", max_length=80, required=False,
        widget=forms.TextInput(attrs=_attrs("اگر خودت رابطی، خالی بگذار")))

    instagram = forms.CharField(
        label="پیج اینستاگرام", max_length=80, required=False,
        widget=forms.TextInput(attrs=_attrs(
            "مثلاً: raha.gallery — بدون @", {"dir": "ltr"})))

    links = forms.CharField(required=False, widget=forms.HiddenInput())

    # ── گام ۳: موقعیت ──
    city = forms.CharField(
        label="شهر", max_length=40, required=False,
        widget=forms.TextInput(attrs=_attrs("مثلاً: اهواز")))

    address = forms.CharField(
        label="نشانی مغازه یا محل کار", required=False,
        widget=forms.Textarea(attrs=_attrs(
            "مثلاً: کیانپارس، خیابان ۱۰ غربی، پلاک ۲۲", {"rows": 3})))

    lat = forms.FloatField(required=False, widget=forms.HiddenInput())
    lng = forms.FloatField(required=False, widget=forms.HiddenInput())

    # تله‌ی ربات: آدم این را نمی‌بیند، ربات پرش می‌کند
    website = forms.CharField(required=False, widget=forms.HiddenInput())

    def clean_website(self):
        if (self.cleaned_data.get("website") or "").strip():
            raise forms.ValidationError("ثبت‌نام نامعتبر است.")
        return ""

    def clean_full_name(self):
        return validate_clean(self.cleaned_data["full_name"].strip(), "نام")

    def clean_company(self):
        return validate_clean(self.cleaned_data["company"].strip(), "نام برند")

    def clean_contact_name(self):
        v = (self.cleaned_data.get("contact_name") or "").strip()
        return validate_clean(v, "نام رابط") if v else v

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if Account.objects.filter(email=email).exists():
            raise forms.ValidationError("این ایمیل قبلاً ثبت شده.")
        validate_clean(email.split("@")[0], "ایمیل")
        return email

    def clean_phone(self):
        """ارقام فارسی/عربی را به لاتین برمی‌گرداند و شکل شماره را چک می‌کند."""
        v = clean_phone(self.cleaned_data["phone"])
        if not v or not v.startswith("09"):
            raise forms.ValidationError("شماره‌ی موبایل باید ۱۱ رقم باشد و با ۰۹ شروع شود.")
        if Account.objects.filter(phone=v).exists():
            raise forms.ValidationError("این شماره قبلاً ثبت شده.")
        return v

    def clean_instagram(self):
        """@ و آدرس کامل را می‌پذیرد ولی فقط نام کاربری را نگه می‌دارد."""
        v = (self.cleaned_data.get("instagram") or "").strip()
        if not v:
            return ""
        v = v.replace("https://", "").replace("http://", "")
        v = v.replace("www.", "").replace("instagram.com/", "")
        v = v.lstrip("@").strip("/")
        return validate_clean(v, "نام پیج")

    def clean_links(self):
        """هر لینک در یک خط؛ خط‌های خالی و تکراری حذف می‌شوند."""
        raw = (self.cleaned_data.get("links") or "").splitlines()
        out = []
        for ln in raw:
            ln = ln.strip()
            if not ln or ln in out:
                continue
            if not re.match(r"^https?://[\w.\-]+", ln):
                if re.match(r"^[\w.\-]+\.[a-z]{2,}", ln, re.I):
                    ln = "https://" + ln
                else:
                    continue
            out.append(ln)
        return "\n".join(out[:8])

    def clean_address(self):
        v = (self.cleaned_data.get("address") or "").strip()
        return validate_clean(v, "نشانی") if v else v

    def clean_password(self):
        pw = self.cleaned_data["password"]
        validate_password(pw)
        return pw

    def clean(self):
        cleaned = super().clean()

        p1, p2 = cleaned.get("password"), cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "رمزها یکی نیستند.")

        # اگر نام رابط خالی ماند، همان نام صاحب حساب می‌نشیند
        if not cleaned.get("contact_name") and cleaned.get("full_name"):
            cleaned["contact_name"] = cleaned["full_name"]

        return cleaned


# ══════════════════════════════════════════════════════════
#  درخواست همکاری
# ══════════════════════════════════════════════════════════

class CollabForm(forms.Form):
    """
    ویزارد درخواست همکاری. اعتبارسنجی زمان (تداخل، پنجره‌ی رزرو) اینجا نیست
    — آن در ویو انجام می‌شود چون به قفل تراکنشی نیاز دارد.
    """

    model_type = forms.ModelChoiceField(
        label="چه مدلی می‌خواهی؟", required=False,
        queryset=ModelType.objects.filter(is_active=True))
    place_ref = forms.ModelChoiceField(
        label="محل کار", required=False,
        queryset=Place.objects.filter(is_active=True))
    kind = forms.ModelChoiceField(
        label="نوع همکاری", required=False,
        queryset=CollabKind.objects.filter(is_active=True))

    budget_mode = forms.ChoiceField(
        label="بودجه", choices=CollabRequest.BUDGET_MODES,
        initial=CollabRequest.BUDGET_SET)
    budget_amount = forms.CharField(label="مبلغ پیشنهادی (تومان)", required=False)

    date = forms.DateField(label="تاریخ")
    start_hour = forms.IntegerField(label="ساعت شروع", min_value=0, max_value=23)
    hours = forms.IntegerField(label="مدت (ساعت)", min_value=1, max_value=12)

    place = forms.CharField(label="نشانی دقیق", max_length=140, required=False)
    crew = forms.CharField(label="تیم و همراهان", max_length=140, required=False)
    brief = forms.CharField(label="توضیح کار", required=False,
                            widget=forms.Textarea(attrs={"rows": 4}))

    def clean_budget_amount(self):
        raw = (self.cleaned_data.get("budget_amount") or "").translate(FA_DIGITS)
        raw = re.sub(r"[^\d]", "", raw)
        return int(raw) if raw else None

    def clean_brief(self):
        v = (self.cleaned_data.get("brief") or "").strip()
        return validate_clean(v, "توضیح کار") if v else v

    def clean_place(self):
        v = (self.cleaned_data.get("place") or "").strip()
        return validate_clean(v, "نشانی") if v else v

    def clean(self):
        cleaned = super().clean()
        book = BookingSettings.load()

        if cleaned.get("budget_mode") == CollabRequest.BUDGET_SET:
            amount = cleaned.get("budget_amount")
            if not amount:
                self.add_error("budget_amount",
                               "یا مبلغ را بنویس یا «در درخواست ذکر می‌کنم» را بزن.")
            elif book.floor_price and amount < book.floor_price:
                self.add_error(
                    "budget_amount",
                    "کف بودجه %s تومان است." % book.floor_fa)

        hours = cleaned.get("hours")
        if hours and hours > book.max_hours:
            self.add_error("hours", "بیشترین مدت هر آفیش %d ساعت است." % book.max_hours)

        return cleaned


class SupportForm(forms.Form):
    """پشتیبانی — فقط شماره و متن."""

    name = forms.CharField(
        label="نام (اختیاری)", max_length=60, required=False,
        widget=forms.TextInput(attrs=_attrs("مثلاً: مریم")))
    phone = forms.CharField(
        label="شماره تماس", max_length=20,
        widget=forms.TextInput(attrs=_attrs(
            "مثلاً: ۰۹۱۲۳۴۵۶۷۸۹", {"inputmode": "tel", "dir": "ltr"})))
    body = forms.CharField(
        label="پیام", widget=forms.Textarea(attrs=_attrs("چه چیزی لازم داری؟", {"rows": 5})))

    website = forms.CharField(required=False, widget=forms.HiddenInput())

    def clean_website(self):
        if (self.cleaned_data.get("website") or "").strip():
            raise forms.ValidationError("ارسال نامعتبر است.")
        return ""

    def clean_phone(self):
        v = clean_phone(self.cleaned_data["phone"])
        if not v:
            raise forms.ValidationError("شماره باید ۱۱ رقم باشد و با ۰ شروع شود.")
        return v

    def clean_body(self):
        v = self.cleaned_data["body"].strip()
        if len(v) < 8:
            raise forms.ValidationError("پیام خیلی کوتاه است.")
        return validate_clean(v, "پیام")

    def clean_name(self):
        v = (self.cleaned_data.get("name") or "").strip()
        return validate_clean(v, "نام") if v else v


# ══════════════════════════════════════════════════════════
#  فرم‌های پنل یکتا
# ══════════════════════════════════════════════════════════

class PhotoForm(forms.ModelForm):
    """افزودن عکس از پنل یکتا — همان چیزی که روی گوشی پر می‌شود."""

    class Meta:
        model = Photo
        fields = ["image", "title", "story", "field", "model_type", "place",
                  "brand", "photographer", "year", "on_strip", "is_published"]
        widgets = {
            "story": forms.Textarea(attrs={"rows": 3, "placeholder": " "}),
            "title": forms.TextInput(attrs={"placeholder": " "}),
            "brand": forms.TextInput(attrs={"placeholder": " "}),
            "photographer": forms.TextInput(attrs={"placeholder": " "}),
            "year": forms.TextInput(attrs={"placeholder": " "}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["field"].queryset = Field.objects.filter(is_active=True)
        self.fields["model_type"].queryset = ModelType.objects.filter(is_active=True)
        self.fields["place"].queryset = Place.objects.filter(is_active=True)
        self.fields["field"].empty_label = "— مجموعه را انتخاب کن —"
        self.fields["model_type"].empty_label = "— نوع مدلینگ —"
        self.fields["place"].empty_label = "— محل —"

    def clean_image(self):
        return validate_image_upload(self.cleaned_data.get("image"))

    def clean_title(self):
        v = (self.cleaned_data.get("title") or "").strip()
        return validate_clean(v, "عنوان") if v else v

    def clean_story(self):
        v = (self.cleaned_data.get("story") or "").strip()
        return validate_clean(v, "توضیح") if v else v


class FieldQuickForm(forms.ModelForm):
    """ساخت سریع یک مجموعه از پنل یکتا."""

    class Meta:
        model = Field
        fields = ["name_fa", "en", "note", "on_arc", "is_active"]
        widgets = {f: forms.TextInput(attrs={"placeholder": " "})
                   for f in ("name_fa", "en", "note")}

    def clean_name_fa(self):
        return validate_clean(self.cleaned_data["name_fa"].strip(), "نام مجموعه")


class TagQuickForm(forms.Form):
    """افزودن یک گزینه به نوع مدلینگ / محل / نوع همکاری."""

    KINDS = [("type", "نوع مدلینگ"), ("place", "محل"), ("kind", "نوع همکاری")]

    group = forms.ChoiceField(label="فهرست", choices=KINDS)
    name = forms.CharField(label="نام", max_length=60,
                           widget=forms.TextInput(attrs={"placeholder": " "}))
    note = forms.CharField(label="توضیح", max_length=90, required=False,
                           widget=forms.TextInput(attrs={"placeholder": " "}))

    MODELS = {"type": ModelType, "place": Place, "kind": CollabKind}

    def clean_name(self):
        return validate_clean(self.cleaned_data["name"].strip(), "نام")

    def save(self):
        model = self.MODELS[self.cleaned_data["group"]]
        last = model.objects.order_by("-order").first()
        return model.objects.create(
            name=self.cleaned_data["name"],
            note=self.cleaned_data.get("note", ""),
            order=(last.order + 1) if last else 0,
        )


class ManualEmployerForm(forms.Form):
    """کارفرمایی که یکتا خودش دستی اضافه می‌کند (مثلاً از دایرکت اینستاگرام)."""

    company = forms.CharField(label="نام برند", max_length=120,
                              widget=forms.TextInput(attrs={"placeholder": " "}))
    contact_name = forms.CharField(label="نام رابط", max_length=80,
                                   widget=forms.TextInput(attrs={"placeholder": " "}))
    phone = forms.CharField(label="شماره تماس", max_length=20,
                            widget=forms.TextInput(attrs={"placeholder": " ", "dir": "ltr"}))
    email = forms.EmailField(label="ایمیل (اختیاری)", required=False,
                             widget=forms.EmailInput(attrs={"placeholder": " ", "dir": "ltr"}))
    activity = forms.ChoiceField(label="حیطه", choices=Employer.ACTIVITY, initial="other")
    city = forms.CharField(label="شهر", max_length=40, required=False,
                           widget=forms.TextInput(attrs={"placeholder": " "}))
    instagram = forms.CharField(label="اینستاگرام", max_length=80, required=False,
                                widget=forms.TextInput(attrs={"placeholder": " ", "dir": "ltr"}))
    note = forms.CharField(label="یادداشت خصوصی", required=False,
                           widget=forms.Textarea(attrs={"rows": 2, "placeholder": " "}))

    def clean_company(self):
        return validate_clean(self.cleaned_data["company"].strip(), "نام برند")

    def clean_phone(self):
        v = clean_phone(self.cleaned_data["phone"])
        if not v:
            raise forms.ValidationError("شماره باید ۱۱ رقم باشد.")
        return v

    def clean_email(self):
        v = (self.cleaned_data.get("email") or "").strip().lower()
        if v and Account.objects.filter(email=v).exists():
            raise forms.ValidationError("این ایمیل قبلاً ثبت شده.")
        return v

    def save(self, actor=None):
        """
        حسابِ بدون رمز می‌سازد: کارفرما هنوز نمی‌تواند وارد شود، ولی درخواست‌ها
        و پیام‌هایش جای درست خودشان را دارند. هر وقت خواست، با «فراموشی رمز»
        روی همان ایمیل، حسابش را فعال می‌کند.
        """
        d = self.cleaned_data
        email = d.get("email") or "manual+%s@yekta.local" % clean_phone(d["phone"])

        account = Account.objects.filter(email=email).first()
        if not account:
            account = Account.objects.create_user(email=email, password=None)
            account.set_unusable_password()
            account.full_name = d["contact_name"]
            account.phone = clean_phone(d["phone"])
            if Account.objects.filter(phone=account.phone).exclude(pk=account.pk).exists():
                account.phone = None
            account.save()

        employer, _ = Employer.objects.get_or_create(
            account=account,
            defaults={"company": d["company"], "contact_name": d["contact_name"],
                      "phone": clean_phone(d["phone"])},
        )
        employer.company = d["company"]
        employer.contact_name = d["contact_name"]
        employer.phone = clean_phone(d["phone"])
        employer.activity = d["activity"]
        employer.city = d.get("city", "")
        employer.instagram = d.get("instagram", "")
        employer.note = d.get("note", "")
        employer.added_by_model = True
        employer.save()
        return employer


class AdminInviteForm(forms.Form):
    """
    افزودن مدیر — فقط از دست مدیر سایت.
    ایمیل/شماره + رمزی که خودت تعیین می‌کنی، به‌علاوه‌ی سطح دسترسی.
    """

    LEVELS = [
        (Account.MODEL, "یکتا — پنل استودیو"),
        (Account.OWNER, "مدیر کامل — پنل استودیو و پنل جنگو"),
    ]

    full_name = forms.CharField(label="نام", max_length=80,
                                widget=forms.TextInput(attrs={"placeholder": " "}))
    email = forms.EmailField(label="جی‌میل",
                             widget=forms.EmailInput(attrs={"placeholder": " ", "dir": "ltr"}))
    phone = forms.CharField(label="شماره تلفن", max_length=20, required=False,
                            widget=forms.TextInput(attrs={"placeholder": " ", "dir": "ltr"}))
    password = forms.CharField(label="رمز عبوری که به او می‌دهی",
                               widget=forms.PasswordInput(attrs={"placeholder": " "}))
    level = forms.ChoiceField(label="سطح دسترسی", choices=LEVELS, initial=Account.MODEL)

    def clean_email(self):
        v = self.cleaned_data["email"].strip().lower()
        if Account.objects.filter(email=v).exists():
            raise forms.ValidationError("این ایمیل قبلاً ثبت شده. از پنل جنگو نقشش را عوض کن.")
        return v

    def clean_phone(self):
        raw = (self.cleaned_data.get("phone") or "").strip()
        if not raw:
            return None
        v = clean_phone(raw)
        if not v:
            raise forms.ValidationError("شماره باید ۱۱ رقم باشد.")
        if Account.objects.filter(phone=v).exists():
            raise forms.ValidationError("این شماره قبلاً ثبت شده.")
        return v

    def clean_password(self):
        pw = self.cleaned_data["password"]
        validate_password(pw)
        return pw

    def save(self):
        d = self.cleaned_data
        account = Account.objects.create_user(
            email=d["email"], password=d["password"], full_name=d["full_name"])
        account.phone = d.get("phone")
        account.role = d["level"]
        account.email_verified = True

        # فقط مدیر کامل به پنل جنگو راه دارد. یکتا با نقش MODEL به پنل
        # استودیو می‌رود؛ دادن is_staff به او فقط یک پنلِ خالی و گیج‌کننده
        # باز می‌کرد، بی‌آنکه کاری اضافه کند.
        account.is_staff = (d["level"] == Account.OWNER)
        account.is_superuser = (d["level"] == Account.OWNER)
        account.save()
        return account


class BookingRulesForm(forms.ModelForm):
    """تنظیمات رزرو، همان چند عددی که یکتا واقعاً عوض می‌کند."""

    class Meta:
        model = BookingSettings
        fields = ["is_open", "closed_note", "floor_price", "price_note",
                  "day_end", "max_hours", "min_notice", "horizon_days", "request_ttl"]
        widgets = {
            "closed_note": forms.TextInput(attrs={"placeholder": " "}),
            "price_note": forms.TextInput(attrs={"placeholder": " "}),
        }


class DecisionForm(forms.Form):
    """پاسخ یکتا به یک درخواست."""

    CHOICES = [
        (CollabRequest.APPROVED, "تایید"),
        (CollabRequest.REJECTED, "رد"),
        (CollabRequest.ALTERNATIVE, "پیشنهاد زمان دیگر"),
        (CollabRequest.DONE, "انجام شد"),
    ]

    status = forms.ChoiceField(choices=CHOICES)
    reply = forms.CharField(required=False,
                            widget=forms.Textarea(attrs={"rows": 3, "placeholder": " "}))

    def clean_reply(self):
        v = (self.cleaned_data.get("reply") or "").strip()
        return validate_clean(v, "پیام") if v else v


class ChatForm(forms.Form):
    """یک پیام در گفتگوی یک درخواست."""

    body = forms.CharField(widget=forms.Textarea(
        attrs={"rows": 2, "placeholder": " ", "data-hint": "پیامت را بنویس"}))

    def clean_body(self):
        v = self.cleaned_data["body"].strip()
        if not v:
            raise forms.ValidationError("پیام خالی است.")
        if len(v) > 2000:
            raise forms.ValidationError("پیام خیلی بلند است.")
        return validate_clean(v, "پیام")
