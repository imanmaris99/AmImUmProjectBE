# app/services/create_user.py
from fastapi import HTTPException, status

from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.models.user_model import UserModel
from app.dtos import user_dtos
from app.dtos.error_response_dtos import ErrorResponseDto

from app.libs import password_lib
from app.libs.verification_code import generate_verification_code

from app.services.user_services.support_function import create_firebase_user_account, handle_integrity_error, save_user_to_db, validate_user_data, delete_unverified_users

from app.utils.firebase_utils import create_firebase_user, send_verification_email
from app.utils.error_parser import is_valid_password
from app.utils import optional


# Fungsi utama untuk membuat user baru - customer
def create_user(db: Session, user: user_dtos.UserCreateDto) -> optional.Optional[user_dtos.UserResponseDto, Exception]:
    try:
        validate_user_data(user)

        # Simpan data user ke database
        user_model, verification_code = save_user_to_db(db, user)

        # Set waktu kedaluwarsa verifikasi 10 menit setelah pembuatan akun
        user_model.verification_expiry = datetime.utcnow() + timedelta(minutes=10)

        # Buat akun Firebase
        firebase_user = create_firebase_user_account(user)

        # Update Firebase UID ke database setelah berhasil buat akun di Firebase
        user_model.firebase_uid = firebase_user.uid
        user_model.email = firebase_user.email
        db.commit()
        db.refresh(user_model)

        # Kirim email verifikasi
        send_verification_email(firebase_user, user.firstname, verification_code)

        # **Panggil fungsi untuk menghapus user yang tidak terverifikasi**
        delete_unverified_users(db)  # Menghapus user yang sudah tidak aktif dalam waktu yang ditentukan

        # Mempersiapkan response data yang sudah sesuai dengan DTO
        user_data_dto = user_dtos.UserCreateResponseDto(
            id=user_model.id,
            firebase_uid=user_model.firebase_uid,
            firstname=user_model.firstname,
            lastname=user_model.lastname,
            gender=user_model.gender,
            email=user_model.email,
            phone=user_model.phone,
            address=user_model.address,
            photo_url=user_model.photo_url,
            role=user_model.role,
            is_active=user_model.is_active,
            created_at=user_model.created_at,
            updated_at=user_model.updated_at
        )

        return optional.build(data=user_dtos.UserResponseDto(
            status_code=status.HTTP_201_CREATED,
            message=(
                f"Account is not yet active.\n"
                f"A verification email has been sent to {user.email}.\n"
                "Please verify your email within 10 minutes to activate your account."
            ),
            data=user_data_dto
        ))


    except IntegrityError as ie:
        db.rollback()
        handle_integrity_error(ie)

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorResponseDto(
                status_code=status.HTTP_409_CONFLICT,
                error="Conflict",
                message=f"Database conflict: {str(e)}"
            ).dict()
        )

    except HTTPException as e:
        return optional.build(error=e)

    except Exception as e:
        db.rollback()
        return optional.build(error=HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message=f"Unexpected error: {str(e)}"
            ).dict()
        ))

   

