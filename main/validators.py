"""قاعده‌ی رمز عبور سایت یکتا."""

import re

from django.core.exceptions import ValidationError

# هر چیزی که حرف، رقم یا فاصله نباشد «نشانه‌ی ویژه» حساب می‌شود: ! @ # $ % ...
SPECIAL = re.compile(r"[^\w\s]|_")
LETTER = re.compile(r"[A-Za-z\u0600-\u06FF]")


class StrongPassword:
    """دست‌کم ۸ نویسه، شامل حداقل یک حرف و یک نشانه‌ی ویژه."""

    def __init__(self, min_length=8):
        self.min_length = min_length

    def validate(self, password, user=None):
        problems = []

        if len(password) < self.min_length:
            problems.append("دست‌کم %d نویسه" % self.min_length)

        if not LETTER.search(password):
            problems.append("حداقل یک حرف")

        if not SPECIAL.search(password):
            problems.append("حداقل یک نشانه‌ی ویژه مثل ! یا @ یا #")

        if problems:
            raise ValidationError(
                "رمز باید این‌ها را داشته باشد: " + "، ".join(problems),
                code="password_too_weak",
            )

    def get_help_text(self):
        return ("دست‌کم %d نویسه، شامل حداقل یک حرف و یک نشانه‌ی ویژه مثل ! یا @"
                % self.min_length)
