"""پنل مدیریت — تا وقتی پنل اختصاصی ساخته شود، همه‌چیز از همین‌جا قابل کنترل است."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils import timezone
from django.utils.html import format_html

from .models import (Account, AuditLog, BookingSettings, Brand, ClosureRange,
                     CollabRequest, DateException, EmailToken, Employer, Field,
                     Message, Profile, Showcase, TimeSlot, Work, WorkShot,
                     WeekdayRule, clock)

admin.site.site_header = "مدیریت سایت یکتا"
admin.site.site_title  = "یکتا"
admin.site.index_title = "بخش‌ها"


def thumb(image, size=54):
    if not image:
        return "—"
    return format_html('<img src="{}" style="height:{}px;border-radius:3px">', image.url, size)


# ──────────── محتوا ────────────

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    fieldsets = (
        ("معرفی", {"fields": ("name_fa", "name_en", "tagline", "statement", "about")}),
        ("مشخصات", {"fields": ("height", "weight", "hair", "eyes", "shoe", "dress", "city")}),
        ("تماس", {"fields": ("instagram", "email")}),
        ("رسانه", {"fields": ("hero_video", "hero_poster", "banner_cut")}),
    )

    def has_add_permission(self, request):
        return not Profile.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Field)
class FieldAdmin(admin.ModelAdmin):
    list_display  = ("preview", "name_fa", "en", "note", "on_arc", "is_active", "order")
    list_editable = ("on_arc", "is_active", "order")
    list_display_links = ("preview", "name_fa")
    search_fields = ("name_fa", "en")

    @admin.display(description="تصویر")
    def preview(self, obj):
        return thumb(obj.image)


class WorkShotInline(admin.TabularInline):
    model = WorkShot
    extra = 3
    fields = ("image", "caption", "order")


@admin.register(Work)
class WorkAdmin(admin.ModelAdmin):
    list_display  = ("preview", "title", "field", "year", "shot_count", "is_published", "order")
    list_editable = ("is_published", "order")
    list_display_links = ("preview", "title")
    list_filter   = ("is_published", "field")
    search_fields = ("title", "meta", "photographer")
    inlines = [WorkShotInline]

    @admin.display(description="کاور")
    def preview(self, obj):
        return thumb(obj.cover)

    @admin.display(description="تعداد قاب")
    def shot_count(self, obj):
        return obj.shots.count()


@admin.register(Showcase)
class ShowcaseAdmin(admin.ModelAdmin):
    list_display  = ("preview", "spot", "caption", "is_active", "order")
    list_editable = ("is_active", "order")
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
              "is_trusted", "is_blocked", "note")


@admin.register(Account)
class AccountAdmin(UserAdmin):
    ordering = ("-date_joined",)
    list_display  = ("email", "full_name", "email_verified", "is_active", "locked", "date_joined")
    list_filter   = ("is_active", "is_staff", "email_verified")
    search_fields = ("email", "full_name")
    inlines = [EmployerInline]

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("شخصی", {"fields": ("full_name",)}),
        ("وضعیت", {"fields": ("is_active", "email_verified", "is_staff", "is_superuser",
                              "groups", "user_permissions")}),
        ("امنیت", {"fields": ("failed_logins", "locked_until", "last_ip", "last_login")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "full_name", "password1", "password2", "is_staff"),
        }),
    )

    readonly_fields = ("last_login", "last_ip")

    @admin.display(description="قفل", boolean=True)
    def locked(self, obj):
        return obj.is_locked


@admin.register(Employer)
class EmployerAdmin(admin.ModelAdmin):
    list_display  = ("company", "activity", "contact_name", "phone", "city",
                     "request_count", "is_trusted", "is_blocked", "created")
    list_editable = ("is_trusted", "is_blocked")
    list_filter   = ("activity", "is_trusted", "is_blocked", "city")
    search_fields = ("company", "contact_name", "phone", "account__email", "instagram")
    readonly_fields = ("created", "updated", "on_map")

    fieldsets = (
        ("کسب‌وکار", {"fields": ("account", "company", "activity", "reg_no")}),
        ("تماس", {"fields": ("contact_name", "phone", "instagram", "website")}),
        ("محل", {"fields": ("city", "address", "lat", "lng", "on_map")}),
        ("داخلی", {"fields": ("is_trusted", "is_blocked", "note", "created", "updated")}),
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
    list_display  = ("snap_company", "date", "when", "status", "field",
                     "msg_count", "created", "validity")
    list_filter   = ("status", "date", "field")
    search_fields = ("snap_company", "snap_contact", "snap_phone", "brief")
    date_hierarchy = "date"
    inlines = [MessageInline]

    readonly_fields = ("employer", "snap_company", "snap_contact", "snap_phone",
                       "created", "expires", "seen_at", "from_ip", "decided_at")

    fieldsets = (
        ("زمان درخواستی", {"fields": ("date", "start_hour", "hours")}),
        ("کار", {"fields": ("field", "brief", "place", "budget")}),
        ("پاسخ یکتا", {"fields": ("status", "reply", "alt_date", "alt_start", "alt_hours")}),
        ("کارفرما (ثبت‌شده در لحظه‌ی درخواست)",
         {"fields": ("employer", "snap_company", "snap_contact", "snap_phone")}),
        ("سوابق", {"fields": ("created", "expires", "seen_at", "decided_at", "from_ip")}),
    )

    actions = ["do_approve", "do_reject"]

    @admin.display(description="ساعت")
    def when(self, obj):
        return obj.span

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
