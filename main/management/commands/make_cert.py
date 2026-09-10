"""
ساخت گواهی خودامضا برای stunnel — فقط یک‌بار لازم است.

این گواهی به هیچ IP خاصی گره نیست؛ چون خودمان صادرش کرده‌ایم (نه یک
مرجع رسمی)، مرورگر همیشه هشدار «اتصال امن نیست» می‌دهد و باید یک‌بار
دستی تاییدش کنی (Advanced → Proceed) — چه IP عوض شود چه نشود.
پس نیازی به ساختن دوباره‌اش نیست، مگر بخواهی از نو بسازی‌اش.

نصب یک‌بار لازم:
    pip install cryptography

اجرا (فقط یک‌بار):
    python manage.py make_cert
"""

import datetime
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

CERT_DIR = Path(settings.BASE_DIR) / "certs"
CERT_FILE = CERT_DIR / "dev-cert.pem"
KEY_FILE = CERT_DIR / "dev-key.pem"


class Command(BaseCommand):
    help = "ساخت یک‌باره‌ی گواهی خودامضا برای stunnel"

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="حتی اگر از قبل هست، دوباره بساز")

    def handle(self, *args, **options):
        if CERT_FILE.exists() and KEY_FILE.exists() and not options["force"]:
            self.stdout.write("گواهی از قبل هست؛ کاری نکردم. (برای ساخت دوباره: --force)")
            self.stdout.write(str(CERT_FILE))
            return

        from cryptography import x509
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.x509.oid import NameOID

        CERT_DIR.mkdir(parents=True, exist_ok=True)

        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "yekta-dev")])
        now = datetime.datetime.utcnow()

        cert = (
            x509.CertificateBuilder()
            .subject_name(name)
            .issuer_name(name)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - datetime.timedelta(days=1))
            .not_valid_after(now + datetime.timedelta(days=3650))
            .add_extension(
                x509.SubjectAlternativeName([x509.DNSName("localhost")]),
                critical=False,
            )
            .sign(key, hashes.SHA256())
        )

        KEY_FILE.write_bytes(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ))
        CERT_FILE.write_bytes(cert.public_bytes(serialization.Encoding.PEM))

        self.stdout.write(self.style.SUCCESS("ساخته شد — دیگر لازم نیست دوباره بسازیش."))
        self.stdout.write("%s\n%s" % (CERT_FILE, KEY_FILE))
