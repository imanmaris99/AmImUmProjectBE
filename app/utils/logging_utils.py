import logging

# Konfigurasi logger
logging.basicConfig(level=logging.INFO)

def log_password_reset_request(email: str, status: str):
    """
    Fungsi untuk mencatat aktivitas permintaan reset password.
    """
    logging.info(f"Password reset request for {email} - Status: {status}")

