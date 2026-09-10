from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from main import views as main_views

urlpatterns = [
    path('admin/site-map/', main_views.site_map, name='site_map'),
    path('admin/', admin.site.urls),
    path('', include('main.urls')),
]

# در حالت توسعه، فایل‌های آپلودشده را خود جنگو سرو می‌کند
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
