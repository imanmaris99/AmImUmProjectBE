# services/auth_service.py
from sqlalchemy.orm import Session
from sqlalchemy.exc import DataError
from fastapi import HTTPException, status
from psycopg2.errors import StringDataRightTruncation

from firebase_admin import auth as firebase_auth
from firebase_admin.exceptions import FirebaseError

from app.models.user_model import UserModel
from app.dtos.user_dtos import UserCreateResponseDto 
from app.dtos.error_response_dtos import ErrorResponseDto
from app.utils import optional

def login_with_google(db: Session, id_token: str):
    try:
        updated_existing_user = False
        if not id_token:
            return optional.build(error=HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    error="Bad Request",
                    message="Google id token must be provided."
                ).dict()
            ))

        # Verifikasi ID token dengan Firebase
        decoded_token = firebase_auth.verify_id_token(id_token)
        uid = decoded_token.get('uid')
        email = decoded_token.get('email')

        # Cek apakah pengguna sudah ada di database
        user = db.query(UserModel).filter(UserModel.email == email).first()
        if not user:
            # Jika pengguna tidak ada, buat pengguna baru dengan data yang tersedia
            user = UserModel(
                firebase_uid=uid,
                email=email,
                firstname=decoded_token.get('given_name', 'Unknown'),
                lastname=decoded_token.get('family_name', 'Unknown'),
                gender=decoded_token.get('gender', 'male'),
                phone=decoded_token.get('phone') or f"google-{uid[:12]}",
                address='No address provided',
                role='customer',
                is_active=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        else:
            # Jika pengguna sudah ada, periksa dan lengkapi data yang kosong
            if not user.firstname:
                user.firstname = decoded_token.get('given_name', 'Unknown')
                updated_existing_user = True
            if not user.lastname:
                user.lastname = decoded_token.get('family_name', 'Unknown')
                updated_existing_user = True
            if not user.gender:
                user.gender = decoded_token.get('gender', 'Not specified')
                updated_existing_user = True
            if not user.phone:
                user.phone = decoded_token.get('phone', f'google-{uid[:12]}')
                updated_existing_user = True
            if not user.address:
                user.address = 'No address provided'
                updated_existing_user = True
            if not user.role:
                user.role = 'customer'
                updated_existing_user = True

        # Pastikan UID Firebase selalu diperbarui jika ada perubahan
        if user.firebase_uid != uid:
            user.firebase_uid = uid
            updated_existing_user = True

        if updated_existing_user:
            db.commit()
            db.refresh(user)

        # Mapping ke UserCreateResponseDto untuk response
        user_response = UserCreateResponseDto(
            id=str(user.id),  # Pastikan ID dikonversi menjadi string
            firebase_uid=user.firebase_uid,
            firstname=user.firstname,
            lastname=user.lastname,
            gender=user.gender,
            email=user.email,
            phone=user.phone,
            address=user.address,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at
        )

        return optional.build(data=user_response)
    
    # Tangkap error SQLAlchemy untuk string yang terlalu panjang
    except DataError as e:
        db.rollback()
        if isinstance(e.orig, StringDataRightTruncation):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    error="Bad Request",
                    message="Data value is too long for one of the fields."
                ).dict()
            )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message="Database error occurred: " + str(e)            
            ).dict()
        )
    
    except FirebaseError as e:
        db.rollback()
        return optional.build(error=HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorResponseDto(
                status_code=status.HTTP_401_UNAUTHORIZED,
                error="Unauthorized",
                message="Invalid token or Google login failed: " + str(e)
            ).dict()
        ))

    except Exception as e:
        db.rollback()
        return optional.build(error=HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message="An unexpected error occurred :" + str(e)
            ).dict()
        ))
