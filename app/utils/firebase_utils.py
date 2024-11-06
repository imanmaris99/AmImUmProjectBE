from fastapi import HTTPException, status

import firebase_admin
from firebase_admin import credentials, auth, initialize_app

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

from dotenv import load_dotenv
import json

from app.dtos.error_response_dtos import ErrorResponseDto

# Load environment variables from .env file
load_dotenv()


# Mengambil kredensial dari variabel lingkungan
firebase_service_account_key = os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY')

if firebase_service_account_key and not firebase_admin._apps:
    cred = credentials.Certificate(json.loads(firebase_service_account_key))
    firebase_admin.initialize_app(cred)
else:
    raise ValueError("Firebase service account key tidak ditemukan atau sudah diinisialisasi.")

# Inisialisasi Firebase
# cred = credentials.Certificate("path/to/serviceAccountKey.json")
# if not firebase_admin._apps:
#     firebase_admin.initialize_app(cred)


# Fungsi untuk membuat user di Firebase
def create_firebase_user(email: str, password: str):
    """Membuat pengguna baru di Firebase Authentication."""
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


def send_email(to_email: str, subject: str, body: str, html: bool = False):
    """Mengirim email melalui SMTP dengan opsi HTML atau teks biasa."""
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    from_email = os.getenv("FROM_EMAIL")

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject

    # Tentukan tipe konten berdasarkan parameter html
    if html:
        msg.attach(MIMEText(body, 'html'))  # Mengirim dalam format HTML
    else:
        msg.attach(MIMEText(body, 'plain'))  # Mengirim teks biasa

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        print(f"Email with subject '{subject}' sent successfully!")
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message=f"Error sending email: {str(e)}"
            ).dict()
        )


def send_email_verification(to_email: str, verification_link: str, firstname: str):
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
        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="email-header">
                <h1>Verifikasi Email Anda</h1>
            </div>
            <div class="email-body">
                <h2>Halo {firstname},</h2>
                <p>Terima kasih telah mendaftar di AmImUm Herbal! Untuk mengaktifkan akun Anda, silakan verifikasi email Anda dengan mengklik tombol di bawah ini:</p>
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
        send_email_verification(email, verification_link, firstname)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message=f"Error sending verification email: {str(e)}"
            ).dict()
        )


def send_email_reset_password(to_email: str, reset_link: str):
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
        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="email-header">
                <h1>Permintaan Reset Password</h1>
            </div>
            <div class="email-body">
                <h2>Halo {to_email},</h2>
                <p>Anda telah meminta untuk mereset kata sandi Anda. Klik tombol di bawah ini untuk mengatur ulang kata sandi Anda:</p>
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


