"""
تنظیمات پروژه‌ی یکتا.

قاعده‌ی کلی امنیت: هر سهل‌گیریِ توسعه فقط داخل `if DEBUG:` می‌نشیند، تا روی
سرور واقعی خودکار و بدون نیاز به یادآوری خاموش شود.

روی سرور، این متغیرهای محیطی خوانده می‌شوند (نگاه کن به DEPLOY.md):
    DJANGO_DEBUG، DJANGO_SECRET_KEY، DJANGO_ALLOWED_HOSTS، DATABASE_URL،
    EMAIL_HOST، EMAIL_HOST_USER، EMAIL_HOST_PASSWORD، SMS_*
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def env(key, default=""):
    return os.environ.get(key, default)


def env_bool(key, default=False):
    raw = os.environ.get(key)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


# ──────────── امنیت پایه ────────────

DEBUG = env_bool("DJANGO_DEBUG", True)

# روی سرور حتماً DJANGO_SECRET_KEY را ست کن؛ این پیش‌فرض فقط برای توسعه است.
SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    "django-insecure-za$4phk5@uk+8t*abfq#86&+f_il17+=bvn=546kza$6*9a56b")

if not DEBUG and SECRET_KEY.startswith("django-insecure"):
    raise RuntimeError(
        "روی سرور باید DJANGO_SECRET_KEY یک کلید واقعی باشد. "
        "با `python -c \"from django.core.management.utils import get_random_secret_key as g; print(g())\"` یکی بساز."
    )

# در DEBUG هر آدرسی مجاز است (تست محلی، از هر IP/وای‌فای/هات‌اسپاتی).
_hosts = [h.strip() for h in env("DJANGO_ALLOWED_HOSTS", "").split(",") if h.strip()]
ALLOWED_HOSTS = ["*"] if DEBUG else (_hosts or [".liara.run"])

CSRF_TRUSTED_ORIGINS = [] if DEBUG else [
    ("https://" + h.lstrip(".")) for h in ALLOWED_HOSTS if h != "*"
]


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
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'main.middleware.SecurityHeadersMiddleware',
    'main.middleware.VisitCounterMiddleware',
]

# اگر whitenoise نصب نبود (توسعه‌ی محلی)، بی‌سروصدا کنار گذاشته می‌شود
try:
    import whitenoise  # noqa: F401
except ImportError:
    MIDDLEWARE.remove('whitenoise.middleware.WhiteNoiseMiddleware')

if DEBUG:
    # حذف تنها CsrfViewMiddleware کافی نیست: چند ویوی built-in جنگو (از جمله
    # LoginView/LogoutView که در main/urls.py استفاده شده‌اند) خودشان مستقیماً
    # با دکوریتور csrf_protect قفل‌اند و آن دکوریتور به MIDDLEWARE کاری ندارد.
    # main.middleware.DisableCSRFInDebugMiddleware با پرچم رسمی
    # request._dont_enforce_csrf_checks هر دو مسیر را یکجا خاموش می‌کند.
    # روی سرور (DEBUG=False) اصلاً اضافه نمی‌شود و CSRF کامل فعال می‌ماند.
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
                'main.context.site',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# ──────────── دیتابیس ────────────

if env("DATABASE_URL"):
    # لیارا رشته‌ی اتصال postgres را در همین متغیر می‌گذارد
    from urllib.parse import urlparse

    _u = urlparse(env("DATABASE_URL"))
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': _u.path.lstrip('/'),
            'USER': _u.username or '',
            'PASSWORD': _u.password or '',
            'HOST': _u.hostname or '',
            'PORT': _u.port or 5432,
            'CONN_MAX_AGE': 60,
        }
    }
else:
    # بدون DATABASE_URL (یعنی بدون خرید دیتابیس جدا)، همان SQLite ساده کافی
    # است. تنها نکته: اگر SQLITE_PATH را روی دیسکِ دائمی (همان‌جایی که
    # MEDIA_ROOT هم هست) بگذاری، فایل دیتابیس با هر دیپلوی پاک نمی‌شود.
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': Path(env("SQLITE_PATH", BASE_DIR / 'db.sqlite3')),
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
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'

# فقط روی سرور واقعی (لیارا) روشن می‌شوند
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


# ──────────── ایمیل ────────────
# اگر EMAIL_HOST ست نشده باشد، ایمیل‌ها فقط در کنسول چاپ می‌شوند.
# برای جی‌میل: EMAIL_HOST=smtp.gmail.com، پورت ۵۸۷، و «رمز عبور برنامه».

EMAIL_HOST = env("EMAIL_HOST")

if EMAIL_HOST:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_PORT = int(env("EMAIL_PORT", "587"))
    EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
    EMAIL_USE_SSL = env_bool("EMAIL_USE_SSL", False)
    EMAIL_HOST_USER = env("EMAIL_HOST_USER")
    EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
    EMAIL_TIMEOUT = 15
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL",
                         env("EMAIL_HOST_USER") or 'no-reply@yekta.local')


# ──────────── پنل پیامکی ────────────
# فعلاً خالی است: هرچه فرستاده شود در کنسول چاپ می‌شود. وقتی پنل خریدی،
# فقط همین سه متغیر را ست کن — کد سایت عوض نمی‌شود. (نگاه کن به DEPLOY.md)

SMS_PROVIDER  = env("SMS_PROVIDER")          # kavenegar | melipayamak | ghasedak
SMS_API_KEY   = env("SMS_API_KEY")
SMS_SENDER    = env("SMS_SENDER")


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
MEDIA_ROOT = Path(env("MEDIA_ROOT", BASE_DIR / 'media'))

# بعضی سرویس‌های میزبانی (مثل لیارا)، collectstatic را در یک محیطِ
# build جدا اجرا می‌کنند که env varهای پنل (از جمله DJANGO_DEBUG) را
# نمی‌بیند — پس نمی‌شود به DEBUG برای انتخاب نوع ذخیره‌سازیِ استاتیک
# اعتماد کرد؛ ممکن است در زمانِ build یک چیز باشد و در زمانِ اجرا چیز
# دیگر. اگر آن build مانیفست نساخته باشد، فایل‌های هش‌دار اصلاً روی
# دیسک وجود ندارند — پس ساختنِ آدرسِ هش‌دار (حتی بدونِ کرش‌کردن) بازهم
# ۴۰۴ می‌دهد. راهِ درست این است که وقتی مانیفستی نیست، اصلاً سراغِ
# ذخیره‌سازیِ هش‌دار نرویم و ساده و بدونِ هش برگردیم — دقیقاً هم‌خوان با
# چیزی که collectstatic واقعاً روی دیسک ساخته.
_static_manifest_exists = (STATIC_ROOT / 'staticfiles.json').exists()

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": ("whitenoise.storage.CompressedManifestStaticFilesStorage"
                    if (_static_manifest_exists and 'whitenoise.middleware.WhiteNoiseMiddleware' in MIDDLEWARE)
                    else "django.contrib.staticfiles.storage.StaticFilesStorage"),
    },
}

# لایه‌ی ایمنیِ اضافه: حتی اگر مانیفست موجود باشد ولی یک فایل خاص را کم
# داشته باشد (مثلاً یک build نصفه‌کاره)، به‌جای ۵۰۰شدنِ کل صفحه، فقط
# همان یکی آدرسِ بدونِ هش برمی‌گردد.
WHITENOISE_MANIFEST_STRICT = False

# سقف حجم آپلود در حافظه — بالاتر از این، روی دیسک نوشته می‌شود
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 20 * 1024 * 1024
DATA_UPLOAD_MAX_NUMBER_FIELDS = 300

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ──────────── گزارش خطا روی سرور ────────────

if not DEBUG:
    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "handlers": {"console": {"class": "logging.StreamHandler"}},
        "root": {"handlers": ["console"], "level": "INFO"},
        "loggers": {
            "django.request": {"handlers": ["console"], "level": "ERROR",
                               "propagate": False},
        },
    }
