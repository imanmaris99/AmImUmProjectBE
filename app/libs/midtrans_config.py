import midtransclient
import os
from dotenv import load_dotenv

load_dotenv()

# Konfigurasi Midtrans
MIDTRANS_SERVER_KEY = os.getenv("MIDTRANS_SERVER_KEY")
MIDTRANS_CLIENT_KEY = os.getenv("MIDTRANS_CLIENT_KEY")

if not MIDTRANS_SERVER_KEY or not MIDTRANS_CLIENT_KEY:
    raise ValueError(
        "MIDTRANS_SERVER_KEY dan MIDTRANS_CLIENT_KEY harus diatur dalam file .env"
        )

snap = midtransclient.Snap(
    is_production=False,  # Ubah menjadi True saat produksi
    server_key=MIDTRANS_SERVER_KEY,
    client_key=MIDTRANS_CLIENT_KEY
)
