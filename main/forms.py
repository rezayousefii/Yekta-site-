import re

from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth.password_validation import validate_password

from .models import Account, Employer

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


class LoginForm(AuthenticationForm):
    """همان فرم ورود جنگو، فقط با placeholder و پیام روشن‌تر برای حساب قفل‌شده."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "ایمیل"
        self.fields["username"].widget.attrs.update(
            _attrs("مثلاً: name@shop.com", {"autocomplete": "email", "inputmode": "email"}))
        self.fields["password"].label = "رمز عبور"
        self.fields["password"].widget.attrs.update(
            _attrs("", {"autocomplete": "current-password"}))

    def get_invalid_login_error(self):
        email = (self.cleaned_data.get("username") or "").strip().lower()
        user = Account.objects.filter(email=email).first()

        if user and user.is_locked:
            return forms.ValidationError(
                "به‌خاطر چند تلاش ناموفق، این حساب موقتاً قفل شده. کمی بعد دوباره امتحان کن.")

        return forms.ValidationError("ایمیل یا رمز درست نیست.")


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
        label="ایمیل",
        widget=forms.EmailInput(attrs=_attrs(
            "مثلاً: name@shop.com",
            {"autocomplete": "email", "inputmode": "email", "dir": "ltr"})))

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

    phone = forms.CharField(
        label="شماره تماس", max_length=20,
        widget=forms.TextInput(attrs=_attrs(
            "مثلاً: ۰۹۱۲۳۴۵۶۷۸۹",
            {"inputmode": "tel", "autocomplete": "tel", "dir": "ltr"})))

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

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if Account.objects.filter(email=email).exists():
            raise forms.ValidationError("این ایمیل قبلاً ثبت شده.")
        return email

    def clean_phone(self):
        """ارقام فارسی/عربی را به لاتین برمی‌گرداند و شکل شماره را چک می‌کند."""
        v = self.cleaned_data["phone"].translate(FA_DIGITS)
        v = re.sub(r"[\s\-()]", "", v)

        if v.startswith("+98"):
            v = "0" + v[3:]
        elif v.startswith("0098"):
            v = "0" + v[4:]

        if not re.fullmatch(r"0\d{10}", v):
            raise forms.ValidationError("شماره باید ۱۱ رقم باشد و با ۰ شروع شود.")
        return v

    def clean_instagram(self):
        """@ و آدرس کامل را می‌پذیرد ولی فقط نام کاربری را نگه می‌دارد."""
        v = (self.cleaned_data.get("instagram") or "").strip()
        if not v:
            return ""
        v = v.replace("https://", "").replace("http://", "")
        v = v.replace("www.", "").replace("instagram.com/", "")
        return v.lstrip("@").strip("/")

    def clean_links(self):
        """هر لینک در یک خط؛ خط‌های خالی و تکراری حذف می‌شوند."""
        raw = (self.cleaned_data.get("links") or "").splitlines()
        out = []
        for ln in raw:
            ln = ln.strip()
            if not ln or ln in out:
                continue
            if not ln.startswith(("http://", "https://")):
                ln = "https://" + ln
            out.append(ln)
        return "\n".join(out[:8])

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
