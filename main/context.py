"""
داده‌هایی که هر صفحه لازم دارد.

نوار بالا و فوتر روی همه‌ی صفحه‌ها هستند و هر دو به نام یکتا و فهرست
مجموعه‌ها نیاز دارند؛ بدون این، هر ویو باید همان دو کوئری را تکرار می‌کرد.
"""

from .models import Field, Profile


def site(request):
    return {
        "site_profile": Profile.load(),
        "site_fields": Field.objects.filter(is_active=True).order_by("order", "id")[:12],
    }
