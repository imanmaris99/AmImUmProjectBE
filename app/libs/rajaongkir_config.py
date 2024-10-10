import os
from dotenv import load_dotenv

load_dotenv()  # Memuat file .env

class Config:
    RAJAONGKIR_API_KEY = os.getenv('RAJAONGKIR_API_KEY')
    RAJAONGKIR_API_HOST = os.getenv('RAJAONGKIR_API_HOST')