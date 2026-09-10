"""
پنل مدیریت جنگو — دسترسی کامل به همه‌چیز.

پنل استودیو (/studio/) برای کارهای روزمره‌ی یکتاست؛ این‌جا جای کارهای
سنگین‌تر است: ساخت مدیر، دیدن گزارش‌ها، ویرایش عمیق محتوا.
"""

from django.contrib import admin
from django.contrib.admin import widgets as admin_widgets
from django.contrib.auth.admin import UserAdmin
from django.utils import timezone
from django.utils.html import format_html

from .models import (Account, AuditLog, BookingSettings, Brand, ClosureRange,
                     CollabKind, CollabRequest, DailyReport, DateException,
                     EmailToken, Employer, Field, Message, ModelType, Photo,
                     PhotoClick, Place, Profile, Showcase, SupportTicket,
                     TimeSlot, VisitDay, WeekdayRule)

admin.site.site_header = "مدیریت سایت یکتا"
admin.site.site_title  = "یکتا"
admin.site.index_title = "بخش‌ها"


def thumb(image, size=54):
    if not image:
        return "—"
    return format_html('<img src="{}" style="height:{}px;border-radius:3px">', image.url, size)


class ColorInput(admin.ModelAdmin):
    """پایه‌ای که فیلدهای رنگ را با انتخابگر رنگ مرورگر نشان می‌دهد."""

    COLOR_FIELDS = ()

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name in self.COLOR_FIELDS:
            kwargs["widget"] = admin_widgets.AdminTextInputWidget(
                attrs={"type": "color", "style": "height:2.4rem;width:5rem;padding:2px"})
        return super().formfield_for_dbfield(db_field, request, **kwargs)


# ──────────── محتوا ────────────

@admin.register(Profile)
class ProfileAdmin(ColorInput):
    COLOR_FIELDS = ("banner_bg", "banner_bg2", "banner_ink")

    fieldsets = (
        ("معرفی", {"fields": ("name_fa", "name_en", "tagline", "statement", "about")}),
        ("مشخصات", {"fields": ("height", "weight", "hair", "eyes", "shoe", "dress", "city")}),
        ("تماس", {"fields": ("instagram", "email", "phone")}),
        ("رسانه‌ی هیرو", {"fields": ("hero_video", "hero_poster")}),
        ("بنر", {
            "fields": ("banner_cut", "banner_bg", "banner_bg2", "banner_ink"),
            "description": "اندازه‌ی پیشنهادی تصویر بنر: <b>۱۶۰۰×۲۴۰۰ پیکسل</b>، "
                           "PNG با پس‌زمینه‌ی شفاف، قدِ کامل و پاها روی لبه‌ی پایین. "
                           "رنگ‌ها را همین‌جا عوض کن؛ سایت بلافاصله آن‌ها را می‌گیرد.",
        }),
    )

    def has_add_permission(self, request):
        return not Profile.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Field)
class FieldAdmin(admin.ModelAdmin):
    list_display  = ("preview", "name_fa", "en", "slug", "shots", "on_arc",
                     "is_active", "order")
    list_editable = ("on_arc", "is_active", "order")
    list_display_links = ("preview", "name_fa")
    search_fields = ("name_fa", "en")

    fieldsets = (
        (None, {"fields": ("name_fa", "en", "slug", "note", "blurb")}),
        ("تصویر سردر", {
            "fields": ("image", "fit"),
            "description": "اگر خالی بماند، تازه‌ترین عکسِ همین مجموعه خودکار "
                           "سردر می‌شود — یعنی هر عکس تازه، صفحه را تازه می‌کند.",
        }),
        ("نمایش", {"fields": ("on_arc", "is_active", "order")}),
    )

    @admin.display(description="تصویر")
    def preview(self, obj):
        if obj.image:
            return thumb(obj.image)
        shot = obj.cover_photo
        return thumb(shot.image) if shot else "—"

    @admin.display(description="تعداد عکس")
    def shots(self, obj):
        return obj.photo_count


class TagAdmin(admin.ModelAdmin):
    list_display  = ("name", "slug", "note", "is_active", "order")
    list_editable = ("is_active", "order", "note")
    search_fields = ("name",)


admin.site.register(ModelType, TagAdmin)
admin.site.register(Place, TagAdmin)
admin.site.register(CollabKind, TagAdmin)


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display  = ("preview", "label", "field", "model_type", "place",
                     "clicks", "on_strip", "is_published", "order")
    list_editable = ("on_strip", "is_published", "order")
    list_display_links = ("preview", "label")
    list_filter   = ("is_published", "on_strip", "field", "model_type", "place")
    search_fields = ("title", "story", "brand", "photographer")
    readonly_fields = ("clicks", "created")
    list_select_related = ("field", "model_type", "place")

    fieldsets = (
        ("تصویر", {"fields": ("image", "title", "story")}),
        ("دسته‌بندی", {
            "fields": ("field", "model_type", "place"),
            "description": "هر عکس باید مجموعه‌ی خودش را داشته باشد — همین است "
                           "که با کلیک روی تصویر، کاربر جایی می‌رسد.",
        }),
        ("اعتبارات", {"fields": ("brand", "photographer", "year")}),
        ("نمایش", {"fields": ("on_strip", "is_published", "order")}),
        ("آمار", {"fields": ("clicks", "created")}),
    )

    @admin.display(description="تصویر")
    def preview(self, obj):
        return thumb(obj.image, 62)


@admin.register(Showcase)
class ShowcaseAdmin(admin.ModelAdmin):
    list_display  = ("preview", "spot", "caption", "field", "is_active", "order")
    list_editable = ("field", "is_active", "order")
    list_display_links = ("preview", "spot")
    list_filter   = ("spot", "is_active")

    @admin.display(description="تصویر")
    def preview(self, obj):
        return thumb(obj.image)


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display  = ("preview", "name", "note", "is_active", "order")
    list_editable = ("is_active", "order")
    search_fields = ("name",)

    @admin.display(description="لوگو")
    def preview(self, obj):
        return thumb(obj.logo, size=36)


# ──────────── تقویم ────────────

@admin.register(WeekdayRule)
class WeekdayRuleAdmin(admin.ModelAdmin):
    list_display  = ("get_weekday_display", "is_open")
    list_editable = ("is_open",)
    list_display_links = None

    def has_add_permission(self, request):
        return WeekdayRule.objects.count() < 7

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(DateException)
class DateExceptionAdmin(admin.ModelAdmin):
    list_display  = ("date", "is_open", "note")
    list_editable = ("is_open", "note")
    list_filter   = ("is_open",)
    date_hierarchy = "date"


@admin.register(ClosureRange)
class ClosureRangeAdmin(admin.ModelAdmin):
    list_display = ("start", "end", "days", "note")
    search_fields = ("note",)

    @admin.display(description="تعداد روز")
    def days(self, obj):
        return (obj.end - obj.start).days + 1


@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display  = ("label", "hour", "is_active")
    list_editable = ("is_active",)
    list_display_links = ("label",)


@admin.register(BookingSettings)
class BookingSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ("پذیرش", {"fields": ("is_open", "closed_note")}),
        ("بودجه", {"fields": ("floor_price", "price_note")}),
        ("قواعد زمان", {"fields": ("day_end", "max_hours", "min_notice", "horizon_days")}),
        ("اعتبار درخواست", {"fields": ("request_ttl",)}),
    )

    def has_add_permission(self, request):
        return not BookingSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


# ──────────── حساب‌ها ────────────

class EmployerInline(admin.StackedInline):
    model = Employer
    extra = 0
    fields = ("company", "activity", "contact_name", "phone", "city", "address",
              "lat", "lng", "website", "instagram", "reg_no",
              "is_trusted", "is_blocked", "added_by_model", "note")


@admin.register(Account)
class AccountAdmin(UserAdmin):
    ordering = ("-date_joined",)
    list_display  = ("email", "phone", "full_name", "role", "email_verified",
                     "is_active", "locked", "date_joined")
    list_filter   = ("role", "is_active", "is_staff", "email_verified")
    search_fields = ("email", "phone", "full_name")
    inlines = [EmployerInline]

    fieldsets = (
        (None, {"fields": ("email", "phone", "password")}),
        ("شخصی", {"fields": ("full_name",)}),
        ("نقش و دسترسی", {
            "fields": ("role", "is_active", "email_verified", "phone_verified",
                       "is_staff", "is_superuser", "groups", "user_permissions"),
            "description": "برای اینکه کسی به پنل استودیو راه پیدا کند، نقشش را "
                           "«یکتا (مدل)» یا «مدیر سایت» بگذار.",
        }),
        ("امنیت", {"fields": ("failed_logins", "locked_until", "last_ip", "last_login")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "phone", "full_name", "password1", "password2",
                       "role", "is_staff"),
        }),
    )

    readonly_fields = ("last_login", "last_ip")

    @admin.display(description="قفل", boolean=True)
    def locked(self, obj):
        return obj.is_locked


@admin.register(Employer)
class EmployerAdmin(admin.ModelAdmin):
    list_display  = ("company", "activity", "contact_name", "phone", "city",
                     "request_count", "is_trusted", "is_blocked", "added_by_model",
                     "created")
    list_editable = ("is_trusted", "is_blocked")
    list_filter   = ("activity", "is_trusted", "is_blocked", "added_by_model", "city")
    search_fields = ("company", "contact_name", "phone", "account__email", "instagram")
    readonly_fields = ("created", "updated", "on_map", "signup_ip")

    fieldsets = (
        ("کسب‌وکار", {"fields": ("account", "company", "activity", "reg_no")}),
        ("تماس", {"fields": ("contact_name", "phone", "instagram", "website", "links")}),
        ("محل", {"fields": ("city", "address", "lat", "lng", "on_map")}),
        ("داخلی", {"fields": ("is_trusted", "is_blocked", "added_by_model", "note",
                              "signup_ip", "created", "updated")}),
    )

    @admin.display(description="درخواست‌ها")
    def request_count(self, obj):
        return obj.requests.count()

    @admin.display(description="روی نقشه")
    def on_map(self, obj):
        if not obj.map_url:
            return "ثبت نشده"
        return format_html('<a href="{}" target="_blank" rel="noopener">باز کردن نقشه</a>',
                           obj.map_url)


@admin.register(EmailToken)
class EmailTokenAdmin(admin.ModelAdmin):
    list_display = ("account", "kind", "created", "expires", "used_at")
    list_filter  = ("kind",)
    readonly_fields = ("account", "token", "kind", "created", "expires", "used_at")

    def has_add_permission(self, request):
        return False


# ──────────── درخواست‌ها و پیام‌ها ────────────

class MessageInline(admin.TabularInline):
    model = Message
    extra = 1
    fields = ("sender", "body", "created", "read_at", "hidden")
    readonly_fields = ("created", "read_at")


@admin.register(CollabRequest)
class CollabRequestAdmin(admin.ModelAdmin):
    list_display  = ("snap_company", "date", "when", "status", "kind", "model_type",
                     "budget_cell", "msg_count", "created", "validity")
    list_filter   = ("status", "date", "kind", "model_type", "place_ref")
    search_fields = ("snap_company", "snap_contact", "snap_phone", "brief")
    date_hierarchy = "date"
    inlines = [MessageInline]
    list_select_related = ("kind", "model_type")

    readonly_fields = ("employer", "snap_company", "snap_contact", "snap_phone",
                       "created", "expires", "seen_at", "from_ip", "decided_at")

    fieldsets = (
        ("زمان درخواستی", {"fields": ("date", "start_hour", "hours")}),
        ("کار", {"fields": ("model_type", "place_ref", "kind", "field",
                            "budget_mode", "budget_amount", "place", "crew", "brief")}),
        ("پاسخ یکتا", {"fields": ("status", "reply", "alt_date", "alt_start", "alt_hours")}),
        ("کارفرما (ثبت‌شده در لحظه‌ی درخواست)",
         {"fields": ("employer", "snap_company", "snap_contact", "snap_phone")}),
        ("سوابق", {"fields": ("created", "expires", "seen_at", "decided_at", "from_ip")}),
    )

    actions = ["do_approve", "do_reject"]

    @admin.display(description="ساعت")
    def when(self, obj):
        return obj.span

    @admin.display(description="بودجه")
    def budget_cell(self, obj):
        return obj.budget_text

    @admin.display(description="پیام‌ها")
    def msg_count(self, obj):
        return obj.messages.count()

    @admin.display(description="اعتبار")
    def validity(self, obj):
        if obj.status != CollabRequest.PENDING:
            return "—"
        if obj.is_expired:
            return "منقضی"
        left = obj.expires - timezone.now()
        return "%s ساعت" % (left.seconds // 3600 + left.days * 24)

    def save_model(self, request, obj, form, change):
        """اگر وضعیت یا پیام عوض شد، در گفتگو و گزارش هم ثبت شود."""
        if change and "status" in form.changed_data:
            obj.decided_at = timezone.now()
        super().save_model(request, obj, form, change)

        if change and "reply" in form.changed_data and obj.reply:
            Message.objects.create(request=obj, sender=Message.MODEL, body=obj.reply)

        if change and form.changed_data:
            AuditLog.objects.create(
                actor=request.user,
                action="edit:" + ",".join(form.changed_data)[:50],
                target="CollabRequest#%s" % obj.pk,
                ip=request.META.get("REMOTE_ADDR"),
            )

    @admin.action(description="تایید درخواست‌های انتخاب‌شده")
    def do_approve(self, request, queryset):
        for obj in queryset:
            obj.decide(CollabRequest.APPROVED, actor=request.user)
        self.message_user(request, "تایید شد.")

    @admin.action(description="رد درخواست‌های انتخاب‌شده")
    def do_reject(self, request, queryset):
        for obj in queryset:
            obj.decide(CollabRequest.REJECTED, actor=request.user)
        self.message_user(request, "رد شد.")


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display  = ("request", "sender", "short", "created", "read_at", "hidden")
    list_filter   = ("sender", "hidden")
    search_fields = ("body",)
    readonly_fields = ("created",)

    @admin.display(description="متن")
    def short(self, obj):
        return obj.body[:60]


# ──────────── پشتیبانی و آمار ────────────

@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ("created", "phone", "name", "short", "is_done")
    list_editable = ("is_done",)
    list_filter = ("is_done",)
    search_fields = ("phone", "name", "body")
    readonly_fields = ("created", "ip")

    @admin.display(description="متن")
    def short(self, obj):
        return obj.body[:70]


@admin.register(VisitDay)
class VisitDayAdmin(admin.ModelAdmin):
    list_display = ("day", "hits", "guests")
    readonly_fields = ("day", "hits", "guests")

    def has_add_permission(self, request):
        return False


@admin.register(DailyReport)
class DailyReportAdmin(admin.ModelAdmin):
    list_display = ("day", "visits", "guests", "clicks", "requests", "signups", "tickets")
    readonly_fields = ("day", "visits", "guests", "clicks", "requests", "signups",
                       "tickets", "top", "created")

    def has_add_permission(self, request):
        return False


@admin.register(PhotoClick)
class PhotoClickAdmin(admin.ModelAdmin):
    list_display = ("created", "photo")
    readonly_fields = ("created", "photo")

    def has_add_permission(self, request):
        return False


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("created", "actor", "action", "target", "ip")
    list_filter  = ("action",)
    search_fields = ("target", "detail")
    readonly_fields = ("actor", "action", "target", "detail", "ip", "created")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
