from fastapi import HTTPException, status

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.models.user_model import UserModel
from app.dtos import user_dtos
from app.dtos.error_response_dtos import ErrorResponseDto

from app.libs import password_lib
from app.libs.verification_code import generate_verification_code

from app.services.user_services.support_function import create_firebase_user_account, handle_integrity_error, save_admin_to_db, validate_user_data

from app.utils.firebase_utils import create_firebase_user, send_verification_email
from app.utils.error_parser import is_valid_password
from app.utils import optional


# Fungsi utama untuk membuat user baru - admin
def create_admin(db: Session, user: user_dtos.UserCreateDto) -> optional.Optional[user_dtos.UserResponseDto, Exception]:
    try:
        validate_user_data(user)
        firebase_user = create_firebase_user_account(user)
        verification_code = generate_verification_code()

        user_model = save_admin_to_db(db, user, firebase_user, verification_code)

        send_verification_email(firebase_user, user.firstname, verification_code)

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
            message=f"Account is not yet active. Verification email has been sent to {user.email}.",
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
        return optional.build(error=HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message=f"Unexpected error: {str(e)}"
            ).dict()
        ))

