from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .forms import LoginForm, YektaPasswordResetForm, YektaSetPasswordForm
from .ratelimit import throttle

urlpatterns = [
    path('', views.home, name='home'),

    # ── گالری ──
    path('gallery/', views.gallery, name='gallery'),
    path('gallery/<str:slug>/', views.collection, name='collection'),
    path('photo/<int:pk>/', views.photo_detail, name='photo'),

    # ── همکاری ──
    path('collab/', views.collab, name='collab'),
    path('collab/submit/', views.collab_submit, name='collab_submit'),
    path('api/hours/', views.api_hours, name='api_hours'),

    path('support/', views.support, name='support'),

    # ── حساب ──
    path('signup/', views.signup, name='signup'),
    path('verify/<str:token>/', views.verify_email, name='verify_email'),

    # قفلِ حسابِ Account یک حساب را می‌بندد؛ این یکی یک IP را — پس
    # کسی نمی‌تواند با امتحان‌کردن صدها ایمیل مختلف از قفل فرار کند.
    path('login/', throttle("login", limit=10, window=600)(
        auth_views.LoginView.as_view(
            template_name='registration/login.html',
            authentication_form=LoginForm,
            redirect_authenticated_user=True,
        )
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),

    path('password-reset/', throttle("reset", limit=5, window=900)(
        auth_views.PasswordResetView.as_view(
        template_name='registration/password_reset_form.html',
        email_template_name='registration/password_reset_email.txt',
        subject_template_name='registration/password_reset_subject.txt',
        form_class=YektaPasswordResetForm,
    )), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='registration/password_reset_done.html',
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='registration/password_reset_confirm.html',
        form_class=YektaSetPasswordForm,
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_complete.html',
    ), name='password_reset_complete'),

    # ── پیشخوان کارفرما ──
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/reply/<int:pk>/', views.dashboard_reply, name='dashboard_reply'),
    path('dashboard/cancel/<int:pk>/', views.cancel_request, name='cancel_request'),

    # ── پنل استودیو (یکتا) ──
    path('studio/', views.studio, name='studio'),
    path('studio/accepting/', views.studio_toggle_open, name='studio_toggle_open'),
    path('studio/photos/', views.studio_photos, name='studio_photos'),
    path('studio/photos/<int:pk>/', views.studio_photo_action, name='studio_photo_action'),
    path('studio/lists/', views.studio_lists, name='studio_lists'),
    path('studio/lists/action/', views.studio_list_action, name='studio_list_action'),
    path('studio/requests/', views.studio_requests, name='studio_requests'),
    path('studio/requests/<int:pk>/', views.studio_request, name='studio_request'),
    path('studio/people/', views.studio_people, name='studio_people'),
    path('studio/people/ticket/<int:pk>/', views.studio_ticket_done,
         name='studio_ticket_done'),
    path('studio/settings/', views.studio_settings, name='studio_settings'),
    path('studio/reports/', views.studio_reports, name='studio_reports'),
]
