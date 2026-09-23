from fastapi import HTTPException, status

import firebase_admin
from firebase_admin import credentials, auth
from firebase_admin.exceptions import FirebaseError

import smtplib
import socket
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
import os

import requests
from urllib.parse import urlencode, quote

from dotenv import load_dotenv
import json
from html import escape

from app.dtos.error_response_dtos import ErrorResponseDto

# Load environment variables from .env file
load_dotenv()
logger = logging.getLogger(__name__)

SHOP_NAME = "Toko Herbal AmImUm"
CUSTOMER_FRONTEND_URL = os.getenv("CUSTOMER_FRONTEND_URL", "https://amimumherbalproject.vercel.app").rstrip("/")
SHOPEE_MARKETPLACE_URL = os.getenv("SHOPEE_MARKETPLACE_URL", "https://shopee.co.id/tokoherbalamimum")
TOKOPEDIA_MARKETPLACE_URL = os.getenv("TOKOPEDIA_MARKETPLACE_URL", "https://www.tokopedia.com/herbalamimum")
ORDER_STATUS_LABELS = {
    "pending": "Menunggu pembayaran",
    "paid": "Pembayaran berhasil",
    "capture": "Pembayaran berhasil",
    "settlement": "Pembayaran berhasil",
    "processing": "Pesanan sedang diproses",
    "shipped": "Pesanan dikirim",
    "completed": "Pesanan selesai",
    "cancelled": "Pesanan dibatalkan",
    "failed": "Pesanan gagal",
    "refund": "Dana dikembalikan",
}


def _safe_text(value: object, fallback: str = "") -> str:
    text = str(value or "").strip()
    return escape(text or fallback)


def _customer_order_url(order_id: object) -> str:
    return f"{CUSTOMER_FRONTEND_URL}/transaction/{quote(str(order_id or '').strip())}"



# Mengambil kredensial dari variabel lingkungan
firebase_service_account_key = os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY')
FIREBASE_ENABLED = bool(firebase_service_account_key)

if FIREBASE_ENABLED and not firebase_admin._apps:
    try:
        cred = credentials.Certificate(json.loads(firebase_service_account_key))
        firebase_admin.initialize_app(cred)
    except (ValueError, json.JSONDecodeError) as exc:
        FIREBASE_ENABLED = False
        logger.warning("Firebase disabled because FIREBASE_SERVICE_ACCOUNT_KEY is invalid: %s", exc)


def _ensure_firebase_enabled():
    if not FIREBASE_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=ErrorResponseDto(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                error="Service Unavailable",
                message="Firebase belum dikonfigurasi pada environment."
            ).dict()
        )


# Fungsi untuk membuat user di Firebase
def create_firebase_user(email: str, password: str):
    """Membuat pengguna baru di Firebase Authentication."""
    _ensure_firebase_enabled()
    try:
        user = auth.create_user(email=email, password=password)
        return user
    
    except auth.EmailAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponseDto(
                status_code=status.HTTP_400_BAD_REQUEST,
                error="Bad Request",
                message="The email address is already in use by another account."

            ).dict()
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message="Akun belum bisa dibuat. Silakan coba beberapa saat lagi."
            ).dict()
        )


def delete_firebase_user(firebase_uid: str) -> None:
    """
    Menghapus akun user dari Firebase Authentication.

    Args:
        firebase_uid (str): UID user di Firebase yang akan dihapus.

    Raises:
        HTTPException: Jika terjadi kesalahan dalam proses penghapusan akun.
    """
    _ensure_firebase_enabled()
    try:
        # Hapus user berdasarkan Firebase UID
        auth.delete_user(firebase_uid)
        logger.info("Firebase user with UID %s has been deleted successfully.", firebase_uid)

    except FirebaseError as e:
        # Jika terjadi kesalahan dari Firebase SDK
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "error": "Firebase Error",
                "message": "Akun belum bisa dihapus dari layanan autentikasi. Silakan coba beberapa saat lagi."
            }
        )

    except Exception as e:
        # Jika terjadi kesalahan tak terduga
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "error": "Internal Server Error",
                "message": "Akun belum bisa dihapus. Silakan coba beberapa saat lagi."
            }
        )
    
    
def _send_email_via_brevo_api(to_email: str, subject: str, body: str, html: bool = False):
    brevo_api_key = os.getenv("BREVO_API_KEY")
    from_email = os.getenv("FROM_EMAIL")
    timeout_seconds = float(os.getenv("SMTP_TIMEOUT_SECONDS", "15"))

    if not brevo_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=ErrorResponseDto(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                error="Service Unavailable",
                message="BREVO_API_KEY belum dikonfigurasi pada environment."
            ).dict()
        )

    payload = {
        "sender": {"email": from_email},
        "to": [{"email": to_email}],
        "subject": subject,
    }
    if html:
        payload["htmlContent"] = body
    else:
        payload["textContent"] = body

    try:
        response = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={
                "accept": "application/json",
                "api-key": brevo_api_key,
                "content-type": "application/json",
            },
            json=payload,
            timeout=timeout_seconds,
        )
        response.raise_for_status()
        logger.info("Brevo API email with subject '%s' sent successfully.", subject)
    except requests.Timeout:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=ErrorResponseDto(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                error="Gateway Timeout",
                message="Layanan email sementara belum tersedia. Silakan coba beberapa saat lagi."
            ).dict()
        )
    except requests.HTTPError as exc:
        error_detail = exc.response.text if exc.response is not None else str(exc)
        logger.warning("Brevo API rejected email delivery request: %s", error_detail)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=ErrorResponseDto(
                status_code=status.HTTP_502_BAD_GATEWAY,
                error="Bad Gateway",
                message="Layanan email sementara belum tersedia. Silakan coba beberapa saat lagi."
            ).dict()
        )
    except requests.RequestException as exc:
        logger.warning("Brevo API request failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=ErrorResponseDto(
                status_code=status.HTTP_502_BAD_GATEWAY,
                error="Bad Gateway",
                message="Layanan email sementara belum tersedia. Silakan coba beberapa saat lagi."
            ).dict()
        )


def _send_email_via_smtp(to_email: str, subject: str, body: str, html: bool = False):
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    from_email = os.getenv("FROM_EMAIL")
    smtp_timeout = float(os.getenv("SMTP_TIMEOUT_SECONDS", "15"))

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject

    if html:
        msg.attach(MIMEText(body, 'html'))
    else:
        msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP(smtp_server, smtp_port, timeout=smtp_timeout) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        logger.info("Email with subject '%s' sent successfully.", subject)

    except smtplib.SMTPAuthenticationError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message="Layanan email sementara belum tersedia. Silakan hubungi admin toko."
            ).dict()
        )

    except (socket.timeout, TimeoutError):
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=ErrorResponseDto(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                error="Gateway Timeout",
                message="Layanan email sementara belum tersedia. Silakan coba beberapa saat lagi."
            ).dict()
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message="Layanan email sementara belum tersedia. Silakan coba beberapa saat lagi."
            ).dict()
        )


def send_email(to_email: str, subject: str, body: str, html: bool = False):
    """Mengirim email melalui provider yang dikonfigurasi.

    Prefer Brevo API when an API key is configured. This keeps production email
    working even if EMAIL_PROVIDER is missing from the runtime environment, while
    still allowing an explicit EMAIL_PROVIDER=smtp override for SMTP-only setups.
    """
    email_provider = os.getenv("EMAIL_PROVIDER", "").strip().lower()
    has_brevo_api_key = bool(os.getenv("BREVO_API_KEY"))

    if email_provider == "brevo_api" or (has_brevo_api_key and email_provider != "smtp"):
        return _send_email_via_brevo_api(to_email, subject, body, html=html)
    return _send_email_via_smtp(to_email, subject, body, html=html)


def send_email_verification(to_email: str, verification_code: str, verification_link: str, firstname: str):
    """Mengirim email verifikasi dengan tautan berformat HTML, logo, dan alamat di footer."""
    subject = "Verifikasi Akun Toko Herbal Amimum"
    
    firstname = firstname.capitalize()


    # URL logo toko (sesuaikan dengan URL gambar logo kamu)
    logo_url = "https://amimumprojectbe-production.up.railway.app/images/logo_toko_amimum.png"
    
    # Membuat body email dalam format HTML
    body = f"""
    <html>
    <head>
        <style>
            .email-container {{
                font-family: Arial, sans-serif;
                color: #333;
                background-color: #f4f4f4;
                padding: 20px;
                border-radius: 8px;
                max-width: 600px;
                margin: auto;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            }}

            .email-header {{
                background-color: #28a745;
                color: white;
                text-align: center;
                padding: 15px;
                border-radius: 8px 8px 0 0;
            }}

            .email-body {{
                padding: 20px;
                background-color: white;
                border-radius: 0 0 8px 8px;
            }}

            .email-body h2 {{
                margin-bottom: 10px;
                color: #28a745;
            }}

            .verify-button {{
                display: inline-block;
                background-color: #28a745;
                color: white;
                padding: 10px 20px;
                text-decoration: none;
                border-radius: 5px;
                font-weight: bold;
                font-size: 16px;
            }}

            .email-footer {{
                display: flex;
                margin-top: 20px;
                padding-top: 10px;
                border-top: 1px solid #e0e0e0;
                font-size: 12px;
                color: #888;
                align-items: center;
            }}

            .email-footer img {{
                max-width: 80px; /* Membatasi lebar maksimum logo */
                height: auto;    /* Memastikan tinggi logo otomatis sesuai proporsinya */
                object-fit: contain; /* Menjaga proporsi logo agar tidak terdistorsi */
                margin-right: 10px;
            }}

            .team-message {{
                margin-top: 15px;
                font-size: 14px;
                color: #555;
                font-style: italic;
            }}

            .footer-text p {{
                text-align: left;
                font-size: 12px;
                flex-grow: 1;
            }}

            .code-container {{
                display: block; /* Supaya tombol bisa berada di tengah */
                text-align: center;
                justify-content: space-between;
                background-color: #eef6ee;
                padding: 15px;
                margin: 20px 0;
                border-radius: 6px;
                box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
            }}

            .code {{
                font-family: 'Courier New', Courier, monospace;
                font-size: large;
                word-break: break-word;
                margin-right: 10px;
            }}

            .verify-button {{
                display: inline-block; /* Menyebabkan lebar tombol sesuai dengan isi */
                background-color: #6fcf97; /* Warna hijau lebih soft */
                color: white;
                padding: 10px 20px; /* Padding lebih lembut */
                text-decoration: none;
                border-radius: 5px;
                font-weight: bold;
                font-size: 16px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1); /* Bayangan lebih lembut */
                transition: background-color 0.3s ease;
                text-align: center;
                margin: 0 auto; /* Agar tombol tetap berada di tengah */
            }}

            .verify-button:hover {{
                background-color: #5ebd7d; /* Warna *hover* yang lebih soft */
            }}

        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="email-header">
                <h1>Verifikasi Email Anda</h1>
            </div>
            <div class="email-body">
                <h2>Halo {_safe_text(firstname, "Customer")},</h2>
                <p>Terima kasih telah mendaftar di Toko Herbal Amimum. Untuk mengaktifkan akun, salin kode verifikasi berikut di website kami:</p>

                <!-- Menampilkan kode verifikasi -->
                <div class="code-container">
                    <span class="code">{verification_code}</span>
                </div>
                <p>Salin kode di atas untuk melanjutkan verifikasi.</p>

                <p>Setelah kode berhasil disalin, silakan verifikasi email Anda dengan mengklik tombol di bawah ini:</p>
                <p><a href="{verification_link}" class="verify-button">Verifikasi Email</a></p>

                <p>Jika tombol tidak berfungsi, Anda juga dapat mengklik tautan di bawah ini:</p>
                <p><a href="{verification_link}">{verification_link}</a></p>

                <p class="team-message">Dikirim oleh,<br>Tim Toko Herbal Amimum</p>
            </div>
            <div class="email-footer">
                <img src="{logo_url}" alt="Logo AmImUm Herbal"/>
                <div class="footer-text">
                    <p>Toko Herbal Amimum</p>
                    <p>Jl. Mangkudipuro, Pati, Jawa Tengah, Indonesia<br>Kode Pos: 59185</p>
                    <p>Shopee: <a href="{SHOPEE_MARKETPLACE_URL}">{SHOPEE_MARKETPLACE_URL}</a></p>
                    <p>Tokopedia: <a href="{TOKOPEDIA_MARKETPLACE_URL}">{TOKOPEDIA_MARKETPLACE_URL}</a></p>
                </div>
            </div>
        </div>
    </body>
    </html>

    """
    try:
        # Mengirim email dengan format HTML
        send_email(to_email, subject, body, html=True)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message="Layanan email verifikasi sementara belum tersedia. Silakan coba beberapa saat lagi."
            ).dict()
        )


def send_verification_email(firebase_user, firstname, verification_code):
    """Mengirim email verifikasi ke pengguna Firebase."""
    try:
        # Ambil email dan UID dari objek firebase_user
        email = firebase_user.email
        uid = firebase_user.uid  # Ambil UID dari objek pengguna
        
        if not email:
            raise ValueError("Email address is empty.")

        # Buat tautan verifikasi customer yang membuka halaman frontend,
        # agar email dan kode bisa otomatis terisi di form verifikasi.
        verify_base_url = os.getenv(
            "CUSTOMER_VERIFY_ACCOUNT_URL",
            "https://amimumherbalproject.vercel.app/verify-account",
        ).rstrip("/")
        verification_link = f"{verify_base_url}?{urlencode({'code': verification_code, 'email': email})}"


        # Kirim email verifikasi menggunakan tautan yang dihasilkan
        send_email_verification(email, verification_code, verification_link, firstname)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message="Layanan email verifikasi sementara belum tersedia. Silakan coba beberapa saat lagi."
            ).dict()
        )


def send_email_reset_password(to_email: str, verification_code: str, reset_link: str):
    """Mengirim email reset password dengan tautan dalam format HTML."""
    
    subject = "Reset Password Toko Herbal Amimum"

    # URL logo toko (sesuaikan dengan URL gambar logo kamu)
    logo_url = "https://amimumprojectbe-production.up.railway.app/images/logo_toko_amimum.png"


    body = f"""
    <html>
    <head>
        <style>
            .email-container {{
                font-family: Arial, sans-serif;
                color: #333;
                background-color: #f4f4f4;
                padding: 20px;
                border-radius: 8px;
                max-width: 600px;
                margin: auto;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            }}
            .email-header {{
                background-color: #28a745;
                color: white;
                text-align: center;
                padding: 15px;
                border-radius: 8px 8px 0 0;
            }}
            .email-body {{
                padding: 20px;
                background-color: white;
                border-radius: 0 0 8px 8px;
            }}
            .email-body h2 {{
                margin-bottom: 10px;
                color: #28a745;
            }}
            .reset-button {{
                display: inline-block;
                background-color: #28a745;
                color: white;
                padding: 10px 20px;
                text-decoration: none;
                border-radius: 5px;
                font-weight: bold;
                font-size: 16px;
            }}
            .email-footer {{
                display: flex;
                margin-top: 20px;
                padding-top: 10px;
                border-top: 1px solid #e0e0e0;
                font-size: 12px;
                color: #888;
                align-items: center;
            }}
            .email-footer img {{
                max-width: 80px; /* Membatasi lebar maksimum logo */
                height: auto;    /* Memastikan tinggi logo otomatis sesuai proporsinya */
                object-fit: contain; /* Menjaga proporsi logo agar tidak terdistorsi */
                margin-right: 10px;
            }}
            .team-message {{
                margin-top: 15px;
                font-size: 14px;
                color: #555;
                font-style: italic;
            }}
            .footer-text p {{
                text-align: left;
                font-size: 12px;
                flex-grow: 1;
            }}

            .code-container {{
                display: block; /* Supaya tombol bisa berada di tengah */
                text-align: center;
                justify-content: space-between;
                background-color: #eef6ee;
                padding: 15px;
                margin: 20px 0;
                border-radius: 6px;
                box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
            }}

            .code {{
                font-family: 'Courier New', Courier, monospace;
                font-size: large;
                word-break: break-word;
                margin-right: 10px;
            }}

            .reset-button {{
                display: inline-block; /* Menyebabkan lebar tombol sesuai dengan isi */
                background-color: #6fcf97; /* Warna hijau lebih soft */
                color: white;
                padding: 10px 20px; /* Padding lebih lembut */
                text-decoration: none;
                border-radius: 5px;
                font-weight: bold;
                font-size: 16px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1); /* Bayangan lebih lembut */
                transition: background-color 0.3s ease;
                text-align: center;
                margin: 0 auto; /* Agar tombol tetap berada di tengah */
            }}

            .reset-button:hover {{
                background-color: #5ebd7d; /* Warna *hover* yang lebih soft */
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="email-header">
                <h1>Permintaan Reset Password</h1>
            </div>
            <div class="email-body">
                <h2>Halo {_safe_text(to_email, "Customer")},</h2>
                <p>Kami menerima permintaan reset password akun Toko Herbal Amimum. Salin kode verifikasi berikut untuk mengatur ulang password:</p>

                <!-- Menampilkan kode verifikasi -->
                <div class="code-container">
                    <span class="code">{verification_code}</span>
                </div>
                <p>Salin kode di atas untuk melanjutkan verifikasi.</p>

                <p>Setelah kode berhasil disalin, silakan verifikasi password baru Anda dengan mengklik tombol di bawah ini:</p>
                <p><a href="{reset_link}" class="reset-button">Reset Password</a></p>

                <p>Jika tombol tidak berfungsi, Anda juga dapat mengklik tautan di bawah ini:</p>
                <p><a href="{reset_link}">{reset_link}</a></p>
                <p>Jika Anda tidak meminta pengaturan ulang kata sandi, abaikan email ini.</p>
                <p class="team-message">Salam,<br>Tim Toko Herbal Amimum</p>
            </div>
            <div class="email-footer">
                <img src="{logo_url}" alt="Logo AmImUm Herbal"/>
                <div class="footer-text">
                    <p>Toko Herbal Amimum</p>
                    <p>Jl. Mangkudipuro, Pati, Jawa Tengah, Indonesia<br>Kode Pos: 59185</p>
                    <p>Shopee: <a href="{SHOPEE_MARKETPLACE_URL}">{SHOPEE_MARKETPLACE_URL}</a></p>
                    <p>Tokopedia: <a href="{TOKOPEDIA_MARKETPLACE_URL}">{TOKOPEDIA_MARKETPLACE_URL}</a></p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    try:
        # Mengirim email dengan format HTML
        send_email(to_email, subject, body, html=True)

    except HTTPException:
        raise

    except Exception:
        logger.exception("Unexpected error while sending reset password email to %s", to_email)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message="Layanan email sementara belum tersedia. Silakan coba beberapa saat lagi."
            ).dict()
        )


def build_order_status_email_body(
    order_id: object,
    customer_name: str | None,
    status_value: str,
    code_tracking: str | None = None,
) -> str:
    """Build customer-safe order status email body.

    This helper intentionally avoids provider/payment tokens and internal shipment IDs.
    Resi is shown only when admin has entered an actual courier tracking code.
    """
    status_key = str(status_value or "").strip().lower()
    status_label = ORDER_STATUS_LABELS.get(status_key, "Status pesanan diperbarui")
    safe_name = _safe_text(customer_name, "Customer")
    safe_order_id = _safe_text(order_id, "-")
    tracking = str(code_tracking or "").strip()
    safe_tracking = _safe_text(tracking, "Belum tersedia") if tracking and tracking.lower() not in {"in process", "processing", "none", "null"} else "Belum tersedia"
    order_url = _customer_order_url(order_id)

    tracking_note = (
        f"<p><strong>No. Resi:</strong> {safe_tracking}</p>"
        if safe_tracking != "Belum tersedia"
        else "<p><strong>No. Resi:</strong> Belum tersedia. Resi akan muncul setelah admin memasukkan kode tracking resmi dari kurir.</p>"
    )

    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #1f2937; background: #f7faf8; padding: 24px;">
      <div style="max-width: 620px; margin: 0 auto; background: #ffffff; border-radius: 14px; overflow: hidden; border: 1px solid #e5e7eb;">
        <div style="background: #006A47; color: #ffffff; padding: 18px 22px;">
          <h2 style="margin: 0; font-size: 20px;">Update Pesanan Toko Herbal Amimum</h2>
        </div>
        <div style="padding: 22px; line-height: 1.6;">
          <p>Halo {safe_name},</p>
          <p>Status pesanan Anda telah diperbarui.</p>
          <p><strong>ID Pesanan:</strong> {safe_order_id}</p>
          <p><strong>Status:</strong> {escape(status_label)}</p>
          {tracking_note}
          <p>Detail pesanan dapat dicek melalui halaman transaksi:</p>
          <p><a href="{order_url}" style="display:inline-block;background:#006A47;color:#ffffff;padding:10px 16px;border-radius:8px;text-decoration:none;font-weight:bold;">Lihat Pesanan</a></p>
          <p style="font-size: 13px; color: #6b7280;">Jika tombol tidak bisa dibuka, salin tautan ini: <br><a href="{order_url}">{order_url}</a></p>
        </div>
        <div style="padding: 16px 22px; background: #f3f4f6; font-size: 12px; color: #4b5563;">
          <p style="margin: 0 0 4px;"><strong>Toko Herbal Amimum</strong></p>
          <p style="margin: 0 0 4px;">Shopee: <a href="{SHOPEE_MARKETPLACE_URL}">{SHOPEE_MARKETPLACE_URL}</a></p>
          <p style="margin: 0 0 4px;">Tokopedia: <a href="{TOKOPEDIA_MARKETPLACE_URL}">{TOKOPEDIA_MARKETPLACE_URL}</a></p>
          <p style="margin: 0;">Email ini hanya berisi ringkasan status pesanan dan tidak memuat data rahasia atau detail internal sistem.</p>
        </div>
      </div>
    </body>
    </html>
    """


def send_order_status_email(
    to_email: str | None,
    order_id: object,
    customer_name: str | None,
    status_value: str,
    code_tracking: str | None = None,
) -> bool:
    """Send a non-critical customer order status email.

    Raises provider HTTPException only to callers that choose to handle it.
    Admin fulfillment callers should catch/log and keep status updates successful.
    """
    if not to_email:
        logger.info("Skip order status email for order %s because customer email is empty.", order_id)
        return False

    subject_label = ORDER_STATUS_LABELS.get(str(status_value or "").strip().lower(), "Status pesanan diperbarui")
    body = build_order_status_email_body(order_id, customer_name, status_value, code_tracking)
    send_email(str(to_email), f"Update Pesanan Amimum - {subject_label}", body, html=True)
    return True
