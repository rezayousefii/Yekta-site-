"""تنظیمات پروژه‌ی یکتا."""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


# ──────────── امنیت پایه ────────────
# SECURITY WARNING: این کلید فقط برای توسعه است. موقع انتشار روی لیارا عوضش کن.
SECRET_KEY = 'django-insecure-za$4phk5@uk+8t*abfq#86&+f_il17+=bvn=546kza$6*9a56b'

DEBUG = True

# در DEBUG هر آدرسی مجاز است (تست محلی، از هر IP/وای‌فای/هات‌اسپاتی).
# روی سرور واقعی، این را با دامنه‌ی خودت پر کن.
ALLOWED_HOSTS = ['*'] if DEBUG else ['yourdomain.ir', '.liara.run']

CSRF_TRUSTED_ORIGINS = [] if DEBUG else ['https://yourdomain.ir']


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'main',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

if DEBUG:
    # حذف تنها CsrfViewMiddleware کافی نبود: چند ویوی built-in جنگو (از جمله
    # LoginView/LogoutView که در main/urls.py استفاده شده‌اند) خودشان مستقیماً
    # با دکوریتور csrf_protect قفل‌اند و آن دکوریتور به MIDDLEWARE کاری ندارد.
    # برای همین اینجا میدل‌ور کوچک main.middleware.DisableCSRFInDebugMiddleware
    # را اضافه می‌کنیم که با پرچم رسمی request._dont_enforce_csrf_checks هر دو
    # مسیر (میدل‌ور سراسری + دکوریتور روی ویوهای built-in) را یکجا خاموش می‌کند.
    # این خط فقط در DEBUG اجرا می‌شود؛ روی سرور واقعی (DEBUG=False) کاملاً
    # نادیده گرفته می‌شود و CSRF عادی و کامل فعال می‌ماند.
    MIDDLEWARE.insert(0, 'main.middleware.DisableCSRFInDebugMiddleware')

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# ──────────── دیتابیس ────────────

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# ──────────── کاربر و رمز ────────────

AUTH_USER_MODEL = 'main.Account'

AUTHENTICATION_BACKENDS = ['main.backends.LockoutBackend']

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = '/'

# ترتیب هش‌ها: اولی برای رمزهای تازه استفاده می‌شود.
# اگر خواستی امنیت بیشتر: pip install argon2-cffi
# و بعد خط Argon2 را به ابتدای این لیست بیاور.
PASSWORD_HASHERS = [
    # 'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
]

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'main.validators.StrongPassword', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
]


# ──────────── کوکی و نشست ────────────

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_AGE = 60 * 60 * 24 * 14      # دو هفته
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

CSRF_COOKIE_HTTPONLY = False                # جاوااسکریپت باید بتواند توکن را بخواند
CSRF_COOKIE_SAMESITE = 'Lax'

X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'same-origin'

# فقط روی سرور واقعی (لیارا) روشن می‌شوند
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


# ──────────── ایمیل ────────────
# فعلاً ایمیل‌ها در کنسول چاپ می‌شوند تا سرویس واقعی وصل شود.

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'no-reply@yekta.local'


# ──────────── زبان و زمان ────────────

LANGUAGE_CODE = 'fa'
TIME_ZONE = 'Asia/Tehran'
USE_I18N = True
USE_TZ = True


# ──────────── فایل‌ها ────────────

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# سقف حجم آپلود در حافظه — بالاتر از این، روی دیسک نوشته می‌شود
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 20 * 1024 * 1024

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
