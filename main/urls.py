from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .forms import LoginForm, YektaPasswordResetForm, YektaSetPasswordForm

urlpatterns = [
    path('', views.home, name='home'),

    path('signup/', views.signup, name='signup'),
    path('verify/<str:token>/', views.verify_email, name='verify_email'),

    path('login/', auth_views.LoginView.as_view(
        template_name='registration/login.html',
        authentication_form=LoginForm,
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),

    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='registration/password_reset_form.html',
        email_template_name='registration/password_reset_email.txt',
        subject_template_name='registration/password_reset_subject.txt',
        form_class=YektaPasswordResetForm,
    ), name='password_reset'),
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

    path('dashboard/', views.dashboard, name='dashboard'),
]
