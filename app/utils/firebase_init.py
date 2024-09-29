# import firebase_admin
# from firebase_admin import credentials, auth
# from fastapi import HTTPException, status
# import os
# from dotenv import load_dotenv
# import json

# # Load environment variables from .env file
# load_dotenv()

# def initialize_firebase():
#     firebase_config_str = os.getenv("FIREBASE_CONFIG")
    
#     if not firebase_config_str:
#         raise ValueError("Environment variable 'FIREBASE_CONFIG' tidak ditemukan atau kosong.")
    
#     print(f"FIREBASE_CONFIG: {firebase_config_str}")  # Tambahkan ini untuk melihat nilai FIREBASE_CONFIG
    
#     try:
#         firebase_config = json.loads(firebase_config_str)
#     except json.JSONDecodeError as e:
#         raise ValueError(f"FIREBASE_CONFIG tidak berisi JSON valid: {e}")
    
#     cred = credentials.Certificate(firebase_config)
#     if not firebase_admin._apps:
#         firebase_admin.initialize_app(cred)
#         print("Firebase initialized successfully.")

# Inisialisasi Firebase
# cred = credentials.Certificate("path/to/serviceAccountKey.json")
# if not firebase_admin._apps:
#     firebase_admin.initialize_app(cred)