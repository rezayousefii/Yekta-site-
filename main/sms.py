"""
ارسال پیامک.

پنل پیامکی هنوز خریده نشده، پس این ماژول عمداً «آماده ولی خاموش» است:
تا وقتی SMS_PROVIDER در تنظیمات خالی باشد، هر پیامک فقط در کنسول چاپ
می‌شود و هیچ‌جای سایت نمی‌شکند. روزی که پنل خریده شد، فقط سه متغیر محیطی
(SMS_PROVIDER, SMS_API_KEY, SMS_SENDER) ست می‌شود و همین توابع واقعی
می‌فرستند — هیچ ویو یا قالبی عوض نمی‌شود.

فرستنده‌ها با urllib استاندارد پایتون کار می‌کنند، پس هیچ کتابخانه‌ای
لازم نیست نصب شود.
"""

import json
import logging
import urllib.parse
import urllib.request

from django.conf import settings

log = logging.getLogger(__name__)

TIMEOUT = 10


def _console(phone, text):
    log.info("SMS (خاموش) → %s: %s", phone, text)
    print("\n──── پیامک (پنل هنوز وصل نیست) ────\nبه: %s\n%s\n" % (phone, text))
    return True


def _kavenegar(phone, text):
    url = "https://api.kavenegar.com/v1/%s/sms/send.json" % settings.SMS_API_KEY
    data = urllib.parse.urlencode({
        "receptor": phone, "message": text, "sender": settings.SMS_SENDER,
    }).encode()
    with urllib.request.urlopen(url, data=data, timeout=TIMEOUT) as r:
        return json.loads(r.read()).get("return", {}).get("status") == 200


def _melipayamak(phone, text):
    url = "https://console.melipayamak.com/api/send/simple/%s" % settings.SMS_API_KEY
    body = json.dumps({"from": settings.SMS_SENDER, "to": phone, "text": text}).encode()
    req = urllib.request.Request(url, data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read()).get("status") in ("ارسال موفق بود", "success")


def _ghasedak(phone, text):
    url = "https://api.ghasedak.me/v2/sms/send/simple"
    data = urllib.parse.urlencode({
        "receptor": phone, "message": text, "linenumber": settings.SMS_SENDER,
    }).encode()
    req = urllib.request.Request(url, data=data,
                                 headers={"apikey": settings.SMS_API_KEY})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read()).get("result", {}).get("code") == 200


SENDERS = {
    "kavenegar": _kavenegar,
    "melipayamak": _melipayamak,
    "ghasedak": _ghasedak,
}


def send_sms(phone, text):
    """
    یک پیامک می‌فرستد و True/False برمی‌گرداند.

    هیچ‌وقت خطا پرتاب نمی‌کند: قطعی پنل پیامکی نباید ثبت‌نام یا درخواست را
    بشکند. مشکل فقط در لاگ می‌نشیند.
    """
    provider = (settings.SMS_PROVIDER or "").strip().lower()

    if not provider or not settings.SMS_API_KEY:
        return _console(phone, text)

    sender = SENDERS.get(provider)
    if not sender:
        log.warning("پنل پیامکی ناشناخته: %s", provider)
        return _console(phone, text)

    try:
        return bool(sender(phone, text))
    except Exception as exc:
        log.warning("ارسال پیامک شکست خورد (%s): %s", provider, exc)
        return False
