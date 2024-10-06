import firebase_admin
from firebase_admin import credentials, auth, initialize_app
from fastapi import HTTPException, status

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

from dotenv import load_dotenv
import json

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
            error="Bad Request",
            message="The email address is already in use by another account."
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error="Internal Server Error",
            message=f"Error creating user in Firebase: {str(e)}"
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
            error="Not Found",
            message="User with the provided email does not exist in Firebase."
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error="Internal Server Error",
            message=f"Error authenticating user in Firebase: {str(e)}"
        )

# Fungsi umum untuk mengirim email
# def send_email(to_email: str, subject: str, body: str):
#     """Mengirim email melalui SMTP."""
#     smtp_server = os.getenv("SMTP_SERVER")
#     smtp_port = int(os.getenv("SMTP_PORT"))
#     smtp_user = os.getenv("SMTP_USER")
#     smtp_password = os.getenv("SMTP_PASSWORD")
#     from_email = os.getenv("FROM_EMAIL")

#     msg = MIMEMultipart()
#     msg['From'] = from_email
#     msg['To'] = to_email
#     msg['Subject'] = subject
#     msg.attach(MIMEText(body, 'plain'))

#     try:
#         with smtplib.SMTP(smtp_server, smtp_port) as server:
#             server.starttls()
#             server.login(smtp_user, smtp_password)
#             server.send_message(msg)
#         print(f"Email with subject '{subject}' sent successfully!")
    
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             error="Internal Server Error",
#             message=f"Error sending email: {str(e)}"
#         )
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
            detail={
                "status_code": 500,
                "error": "Internal Server Error",
                "message": f"Error sending email: {str(e)}"
            }
        )

# Fungsi khusus untuk verifikasi email
# def send_email_verification(to_email: str, verification_link: str):
#     """Mengirim email verifikasi dengan tautan."""
#     subject = "Email Verification"
#     body = f"""
#     Hi,
    
#     Please verify your email by clicking on the following link: 
    
#     {verification_link}

#     Regards,
#     AmImUm Herbal Team
#     """
#     send_email(to_email, subject, body)
def send_email_verification(to_email: str, verification_link: str, firstname: str):
    """Mengirim email verifikasi dengan tautan berformat HTML, logo, dan alamat di footer."""
    subject = "Email Verification"
    
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
            .email-body p {{
                margin-bottom: 20px;
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
                text-align: center;
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #e0e0e0;
                font-size: 12px;
                color: #888;
            }}
            .email-footer img {{
                width: 100px;
                margin-bottom: 10px;
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="email-header">
                <h1>Verifikasi Email Anda</h1>
            </div>
            <div class="email-body">
                <p>Halo {firstname},</p>
                <p>Terima kasih telah mendaftar di AmImUm Herbal! Untuk mengaktifkan akun Anda, silakan verifikasi email Anda dengan mengklik tombol di bawah ini:</p>
                <p>
                    <a href="{verification_link}" class="verify-button">Verifikasi Email</a>
                </p>
                <p>Jika tombol tidak berfungsi, Anda juga dapat mengklik tautan di bawah ini:</p>
                <p><a href="{verification_link}">{verification_link}</a></p>
            </div>
            <div class="email-footer">
                <img src="{logo_url}" alt="Logo AmImUm Herbal" />
                <p>AmImUm Herbal<br>Jl. Contoh Alamat No. 123, Jakarta, Indonesia</p>
            </div>
        </div>
    </body>
    </html>
    """
    # Mengirim email dengan format HTML
    send_email(to_email, subject, body, html=True)



# Fungsi khusus untuk reset password
def send_email_reset_password(to_email: str, reset_link: str):
    """Mengirim email reset password dengan tautan."""
    subject = "Reset Password"
    body = f"""
    Hi,

    You requested a password reset. Click the link below to reset your password:

    {reset_link}

    If you did not request this, please ignore this email.

    Regards,
    AmImUm Herbal Team
    """
    send_email(to_email, subject, body)

# Fungsi untuk mengirim email verifikasi pengguna Firebase
def send_verification_email(firebase_user):
    """Mengirim email verifikasi ke pengguna Firebase."""
    try:
        email = firebase_user.email
        if not email:
            raise ValueError("Email address is empty.")
        
        verification_link = auth.generate_email_verification_link(email)
        send_email_verification(email, verification_link)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error="Internal Server Error",
            message=f"Error sending verification email: {str(e)}"
        )



















# def initialize_firebase():
#     try:
#         # Replace literal '\n' with actual new lines
#         private_key = os.getenv("FIREBASE_PRIVATE_KEY").replace("\\n", "\n")

#         cred = credentials.Certificate({
#             "type": os.getenv("FIREBASE_TYPE"),
#             "project_id": os.getenv("FIREBASE_PROJECT_ID"),
#             "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
#             "private_key": private_key,
#             "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
#             "client_id": os.getenv("FIREBASE_CLIENT_ID"),
#             "auth_uri": os.getenv("FIREBASE_AUTH_URI"),
#             "token_uri": os.getenv("FIREBASE_TOKEN_URI"),
#             "auth_provider_x509_cert_url": os.getenv("FIREBASE_AUTH_PROVIDER_CERT_URL"),
#             "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_CERT_URL")
#         })
        
#         # Initialize the Firebase app
#         firebase_admin.initialize_app(cred)
#         print("Firebase initialized successfully")

#     except Exception as e:
#         raise ValueError(f"Kesalahan saat menginisialisasi Firebase: {str(e)}")

# def initialize_firebase():
#     firebase_config_str = os.getenv("FIREBASE_CONFIG")
    
#     if not firebase_config_str:
#         raise ValueError("Environment variable 'FIREBASE_CONFIG' tidak ditemukan atau kosong.")
    
#     print(f"FIREBASE_CONFIG (panjang: {len(firebase_config_str)}): {firebase_config_str}")  # Debug: lihat panjang dan nilai
    
#     try:
#         firebase_config = json.loads(firebase_config_str)
#     except json.JSONDecodeError as e:
#         raise ValueError(f"FIREBASE_CONFIG tidak berisi JSON valid: {e}")

#     # Inisialisasi Firebase
#     cred = credentials.Certificate(firebase_config)
#     if not firebase_admin._apps:
#         firebase_admin.initialize_app(cred)
#         print("Firebase initialized successfully.")