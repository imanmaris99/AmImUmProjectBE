from contextlib import contextmanager
from fastapi import HTTPException, status

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.models.user_model import UserModel
from app.dtos import user_dtos
from app.dtos.error_response_dtos import ErrorResponseDto

from app.libs import password_lib
from app.libs.verification_code import generate_verification_code
from app.utils.firebase_utils import delete_firebase_user

from app.utils.firebase_utils import create_firebase_user, send_verification_email
from app.utils.error_parser import is_valid_password
from app.utils import optional

# Fungsi untuk validasi input email dan password
def validate_user_data(user: user_dtos.UserCreateDto):
    if not user.email or not user.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponseDto(
                status_code=status.HTTP_400_BAD_REQUEST,
                error="Bad Request",
                message="Email and password must be provided."
            ).dict()
        )

    is_valid, error_message = is_valid_password(user.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status_code": status.HTTP_400_BAD_REQUEST,
                "error": "Bad Request",
                "message": error_message
            }
        )

# Fungsi untuk membuat akun Firebase
def create_firebase_user_account(user: user_dtos.UserCreateDto) -> dict:
    firebase_user = create_firebase_user(user.email, user.password)
    if not firebase_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponseDto(
                status_code=status.HTTP_400_BAD_REQUEST,
                error="Bad Request",
                message="Failed to create user in Firebase."
            ).dict()
        )
    return firebase_user

def delete_unverified_users(db: Session):
    """
    Menghapus semua user yang tidak melakukan verifikasi dalam waktu 10 menit
    setelah pembuatan akun.
    """
    expiration_time = datetime.utcnow()  # Waktu sekarang untuk perbandingan
    unverified_users = db.query(UserModel).filter(
        UserModel.is_active == False,  # Hanya untuk user yang tidak aktif (belum diverifikasi)
        UserModel.verification_expiry < expiration_time  # Jika expired lebih kecil dari waktu sekarang
    ).all()

    for user in unverified_users:
        # Hapus akun dari Firebase jika memiliki UID
        if user.firebase_uid:
            delete_firebase_user(user.firebase_uid)
        # Hapus akun dari database
        db.delete(user)

    db.commit()

# @contextmanager
# def get_db_session(db: Session):
#     try:
#         yield db
#         db.commit()  # Commit jika tidak ada error
#     except Exception as e:
#         db.rollback()  # Rollback jika terjadi error
#         raise e  # Lanjutkan melempar error agar bisa ditangani di tempat lain
#     finally:
#         db.close()  # Pastikan koneksi ditutup

# def delete_unverified_users(db: Session):
#     """
#     Menghapus pengguna yang tidak diverifikasi dalam waktu tertentu.
#     """
#     expiration_time = datetime.utcnow()

#     with get_db_session(db) as session:  # Pastikan `db` dilewatkan ke context manager
#         unverified_users = session.query(UserModel).filter(
#             UserModel.is_active == False,
#             UserModel.verification_expiry < expiration_time
#         ).all()

#         for user in unverified_users:
#             if user.firebase_uid:
#                 delete_firebase_user(user.firebase_uid)  # Hapus user dari Firebase
#             session.delete(user)  # Hapus user dari database


# Fungsi untuk membuat instance UserModel dan menyimpannya ke database
def save_user_to_db(db: Session, user: user_dtos.UserCreateDto) -> UserModel:
    verification_code = generate_verification_code()

    # Membuat instance user baru
    user_model = UserModel(
        firstname=user.firstname,
        lastname=user.lastname,
        gender=user.gender,
        email=user.email,
        phone=user.phone,
        hash_password=password_lib.get_password_hash(password=user.password),
        role="customer",
        is_active=False,  # Set is_active ke False saat pendaftaran
        verification_code=verification_code  # Simpan kode verifikasi
    )
    db.add(user_model)
    db.commit()
    db.refresh(user_model)
    return user_model, verification_code

# Fungsi untuk membuat instance UserModel dan menyimpannya ke database
def save_admin_to_db(db: Session, user: user_dtos.UserCreateDto, firebase_user, verification_code: str) -> UserModel:
    user_model = UserModel(
        firstname=user.firstname,
        lastname=user.lastname,
        gender=user.gender,
        email=firebase_user.email,
        phone=user.phone,
        hash_password=password_lib.get_password_hash(password=user.password),
        firebase_uid=firebase_user.uid,
        role="admin",
        is_active=False,
        verification_code=verification_code
    )
    db.add(user_model)
    db.commit()
    db.refresh(user_model)
    return user_model

# Fungsi untuk menangani error integrity yang spesifik
def handle_integrity_error(ie: IntegrityError):
    message = "Duplicate data found."
    if 'email' in str(ie.orig):
        message = "The email address is already in use by another account."
    elif 'phone' in str(ie.orig):
        message = "The phone number is already in use by another account."

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=ErrorResponseDto(
            status_code=status.HTTP_400_BAD_REQUEST,
            error="Bad Request",
            message=message
        ).dict()
    )
