import firebase_admin
from firebase_admin import credentials, auth
from fastapi import HTTPException, status

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv
import json

load_dotenv()

# Inisialisasi Firebase
# cred = credentials.Certificate("path/to/serviceAccountKey.json")
# if not firebase_admin._apps:
#     firebase_admin.initialize_app(cred)

# Inisialisasi Firebase dengan service account dari environment variable
def initialize_firebase():
    firebase_service_account_key = os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY')

    if not firebase_service_account_key:
        raise ValueError("FIREBASE_SERVICE_ACCOUNT_KEY is not set in the environment variables")
    
    try:
        # Parse JSON dari string environment
        cred_dict = json.loads(firebase_service_account_key)
        cred = credentials.Certificate(cred_dict)
        
        # Inisialisasi Firebase
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
    
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in FIREBASE_SERVICE_ACCOUNT_KEY: {str(e)}")
    
    except Exception as e:
        raise ValueError(f"Error initializing Firebase: {str(e)}")

# Memanggil fungsi inisialisasi
initialize_firebase()

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
def send_email(to_email: str, subject: str, body: str):
    """Mengirim email melalui SMTP."""
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    from_email = os.getenv("FROM_EMAIL")

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        print(f"Email with subject '{subject}' sent successfully!")
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error="Internal Server Error",
            message=f"Error sending email: {str(e)}"
        )

# Fungsi khusus untuk verifikasi email
def send_email_verification(to_email: str, verification_link: str):
    """Mengirim email verifikasi dengan tautan."""
    subject = "Email Verification"
    body = f"Please verify your email by clicking on the following link: {verification_link}"
    send_email(to_email, subject, body)

# Fungsi khusus untuk reset password
def send_email_reset_password(to_email: str, reset_link: str):
    """Mengirim email reset password dengan tautan."""
    subject = "Reset Password"
    body = f"Click the following link to reset your password: {reset_link}"
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
