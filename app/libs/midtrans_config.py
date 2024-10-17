import midtransclient
import os
from dotenv import load_dotenv

load_dotenv()

# Konfigurasi Midtrans
MIDTRANS_SERVER_KEY = os.getenv("MIDTRANS_SERVER_KEY")
MIDTRANS_CLIENT_KEY = os.getenv("MIDTRANS_CLIENT_KEY")

snap = midtransclient.Snap(
    is_production=False,  # Ubah menjadi True saat produksi
    server_key=MIDTRANS_SERVER_KEY,
    client_key=MIDTRANS_CLIENT_KEY
)
