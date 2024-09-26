import smtplib
import os
from dotenv import load_dotenv

# Muat variabel lingkungan dari file .env
load_dotenv()

# Ambil nilai dari variabel lingkungan
smtp_server = os.getenv("SMTP_SERVER")
smtp_port = 587  # Menggunakan port standar untuk TLS
smtp_user = os.getenv("SMTP_USER")
smtp_password = os.getenv("SMTP_PASSWORD")
from_email = os.getenv("FROM_EMAIL")

# Debug: Cek apakah variabel lingkungan dimuat dengan benar
print(f"SMTP_SERVER: {smtp_server}")
print(f"SMTP_USER: {smtp_user}")
print(f"FROM_EMAIL: {from_email}")

try:
    # Menghubungkan ke server SMTP
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()  # Mengamankan koneksi
    
    # Login menggunakan kredensial
    server.login(smtp_user, smtp_password)
    print("Login successful!")
    
    # Tutup koneksi setelah login berhasil
    server.quit()
    
except smtplib.SMTPAuthenticationError as auth_err:
    print(f"SMTP Authentication Error: {str(auth_err)}")
except smtplib.SMTPConnectError as conn_err:
    print(f"SMTP Connection Error: {str(conn_err)}")
except Exception as e:
    print(f"General Error: {str(e)}")
