import secrets

def generate_verification_code() -> str:
    return secrets.token_urlsafe(16)  # Menghasilkan kode acak yang aman dengan panjang 16 karakter
