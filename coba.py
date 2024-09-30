from urllib.parse import urlparse, parse_qs

# URL yang diberikan
url = "https://amimumherbalproject-427e5.firebaseapp.com/__/auth/action?mode=resetPassword&oobCode=5iW3-rAsJBzPmotW1oXMzLGwq8KVUg8DKhnwfuK3ShsAAAGSQlIHzA&apiKey=AIzaSyC5nNJjei821JWZA97y28ilKr59VDmwIzQ&lang=en"

# Mengurai URL
parsed_url = urlparse(url)
query_params = parse_qs(parsed_url.query)

# Mengambil oobCode
oob_code = query_params.get('oobCode', [None])[0]

if oob_code:
    print(f"oobCode: {oob_code}")
else:
    print("oobCode tidak ditemukan dalam URL.")


# import smtplib
# import os
# from dotenv import load_dotenv

# # Muat variabel lingkungan dari file .env
# load_dotenv()

# # Ambil nilai dari variabel lingkungan
# smtp_server = os.getenv("SMTP_SERVER")
# smtp_port = 587  # Menggunakan port standar untuk TLS
# smtp_user = os.getenv("SMTP_USER")
# smtp_password = os.getenv("SMTP_PASSWORD")
# from_email = os.getenv("FROM_EMAIL")

# # Debug: Cek apakah variabel lingkungan dimuat dengan benar
# print(f"SMTP_SERVER: {smtp_server}")
# print(f"SMTP_USER: {smtp_user}")
# print(f"FROM_EMAIL: {from_email}")

# try:
#     # Menghubungkan ke server SMTP
#     server = smtplib.SMTP(smtp_server, smtp_port)
#     server.starttls()  # Mengamankan koneksi
    
#     # Login menggunakan kredensial
#     server.login(smtp_user, smtp_password)
#     print("Login successful!")
    
#     # Tutup koneksi setelah login berhasil
#     server.quit()
    
# except smtplib.SMTPAuthenticationError as auth_err:
#     print(f"SMTP Authentication Error: {str(auth_err)}")
# except smtplib.SMTPConnectError as conn_err:
#     print(f"SMTP Connection Error: {str(conn_err)}")
# except Exception as e:
#     print(f"General Error: {str(e)}")
