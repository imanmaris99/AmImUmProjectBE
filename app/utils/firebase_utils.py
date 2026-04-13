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

from dotenv import load_dotenv
import json

from app.dtos.error_response_dtos import ErrorResponseDto

# Load environment variables from .env file
load_dotenv()
logger = logging.getLogger(__name__)

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
                message=f"Error creating user in Firebase: {str(e)}"
            ).dict()
        )


# Fungsi untuk autentikasi pengguna di Firebase
def authenticate_firebase_user(email: str, password: str):
    """Autentikasi pengguna di Firebase."""
    _ensure_firebase_enabled()
    try:
        firebase_user = auth.get_user_by_email(email)
        return firebase_user
    
    except auth.UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponseDto(
                status_code=status.HTTP_404_NOT_FOUND,
                error="Not Found",
                message="User with the provided email does not exist in Firebase."
            ).dict()
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message=f"Error authenticating user in Firebase: {str(e)}"
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
                "message": f"Failed to delete Firebase user: {str(e)}"
            }
        )

    except Exception as e:
        # Jika terjadi kesalahan tak terduga
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "error": "Internal Server Error",
                "message": f"Unexpected error while deleting Firebase user: {str(e)}"
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
                message="Brevo API did not respond in time while sending email."
            ).dict()
        )
    except requests.HTTPError as exc:
        error_detail = exc.response.text if exc.response is not None else str(exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=ErrorResponseDto(
                status_code=status.HTTP_502_BAD_GATEWAY,
                error="Bad Gateway",
                message=f"Brevo API rejected email delivery request: {error_detail}"
            ).dict()
        )
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=ErrorResponseDto(
                status_code=status.HTTP_502_BAD_GATEWAY,
                error="Bad Gateway",
                message=f"Brevo API request failed: {str(exc)}"
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
                message="SMTP authentication failed. Periksa SMTP_USER, SMTP_PASSWORD, dan pastikan provider email mengizinkan login aplikasi atau app password yang digunakan masih valid."
            ).dict()
        )

    except (socket.timeout, TimeoutError):
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=ErrorResponseDto(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                error="Gateway Timeout",
                message="SMTP server did not respond in time while sending email verification."
            ).dict()
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message=f"Error sending email: {str(e)}"
            ).dict()
        )


def send_email(to_email: str, subject: str, body: str, html: bool = False):
    """Mengirim email melalui provider yang dikonfigurasi."""
    email_provider = os.getenv("EMAIL_PROVIDER", "smtp").strip().lower()
    if email_provider == "brevo_api":
        return _send_email_via_brevo_api(to_email, subject, body, html=html)
    return _send_email_via_smtp(to_email, subject, body, html=html)


def send_email_verification(to_email: str, verification_code: str, verification_link: str, firstname: str):
    """Mengirim email verifikasi dengan tautan berformat HTML, logo, dan alamat di footer."""
    subject = "Email Verification"
    
    firstname = firstname.capitalize()

    # url_verification = "https://yakuse.vercel.app/login"

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
                <h2>Halo {firstname},</h2>
                <p>Terima kasih telah mendaftar di AmImUm Herbal! Untuk mengaktifkan akun Anda, silakan salin kode verifikasi berikut di aplikasi kami:</p>

                <!-- Menampilkan kode verifikasi -->
                <div class="code-container">
                    <span class="code">{verification_code}</span>
                </div>
                <p>Salin kode di atas untuk melanjutkan verifikasi.</p>

                <p>Setelah kode berhasil disalin, silakan verifikasi email Anda dengan mengklik tombol di bawah ini:</p>
                <p><a href="{verification_link}" class="verify-button">Verifikasi Email</a></p>

                <p>Jika tombol tidak berfungsi, Anda juga dapat mengklik tautan di bawah ini:</p>
                <p><a href="{verification_link}">{verification_link}</a></p>

                <p class="team-message">Dikirim oleh, <br> AmImUm Herbal Team</p>
            </div>
            <div class="email-footer">
                <img src="{logo_url}" alt="Logo AmImUm Herbal"/>
                <div class="footer-text">
                    <p>Toko Herbal AmImUm</p>
                    <p>Jl. Mangkudipuro, Pati, Jawa Tengah, Indonesia <br> Kode Pos: 59185</p>
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
                message=f"Gagal mengirim email verifikasi ke {to_email}: {str(e)}"
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

        # # Menghasilkan tautan verifikasi berdasarkan UID
        # verification_link = auth.generate_email_verification_link(email)
        # Buat tautan verifikasi yang berisi kode verifikasi dan email user
        verification_link = f"https://amimumprojectbe-production.up.railway.app/user/verify-email?code={verification_code}&email={email}"


        # Kirim email verifikasi menggunakan tautan yang dihasilkan
        send_email_verification(email, verification_code, verification_link, firstname)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message=f"Error sending verification email: {str(e)}"
            ).dict()
        )


def send_email_reset_password(to_email: str, verification_code: str, reset_link: str):
    """Mengirim email reset password dengan tautan dalam format HTML."""
    
    subject = "Reset Password"

    # URL logo toko (sesuaikan dengan URL gambar logo kamu)
    logo_url = "https://amimumprojectbe-production.up.railway.app/images/logo_toko_amimum.png"

    url_reset = "https://yakuse.vercel.app/login"

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
                <h2>Halo {to_email},</h2>
                <p>Anda telah meminta untuk mereset kata sandi Anda. 
                silakan salin kode verifikasi berikut untuk mengatur ulang kata sandi Anda:</p>

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
                <p class="team-message">Salam, <br> AmImUm Herbal Team</p>
            </div>
            <div class="email-footer">
                <img src="{logo_url}" alt="Logo AmImUm Herbal"/>
                <div class="footer-text">
                    <p>Toko Herbal AmImUm</p>
                    <p>Jl. Mangkudipuro, Pati, Jawa Tengah, Indonesia <br> Kode Pos: 59185</p>
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
                message=f"Gagal mengirim email reset password ke {to_email}: {str(e)}"
            ).dict()
        )
