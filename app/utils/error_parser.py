import re


def find_errr_from_args(domain: str, message: str):
    result = re.findall(f"{domain}\\.(\\w+)", message)
    if len(result) == 0:
        return ""
    return result[0]

def is_valid_password(password: str) -> tuple[bool, str]:
    """
    Memeriksa apakah password memenuhi kebijakan keamanan.
    Password dianggap valid jika:
    - Panjang minimal 8 karakter
    - Mengandung setidaknya satu huruf besar
    - Mengandung setidaknya satu huruf kecil
    - Mengandung setidaknya satu angka
    - Mengandung setidaknya satu karakter spesial
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one number."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character."
    
    return True, ""

