import os
from dotenv import load_dotenv

load_dotenv()  # Memuat file .env

class Config:
    RAJAONGKIR_API_KEY = os.getenv('RAJAONGKIR_API_KEY')
    _host = os.getenv('RAJAONGKIR_API_HOST', 'rajaongkir.komerce.id')
    RAJAONGKIR_API_HOST = 'rajaongkir.komerce.id' if _host == 'api.rajaongkir.com' else _host
    RAJAONGKIR_API_BASE_PATH = os.getenv('RAJAONGKIR_API_BASE_PATH', '/api/v1')