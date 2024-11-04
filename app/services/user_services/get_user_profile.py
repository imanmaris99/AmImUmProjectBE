from typing import Type
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from fastapi import HTTPException, status

from app.models.user_model import UserModel
from app.dtos import user_dtos
from app.dtos.error_response_dtos import ErrorResponseDto

from app.utils import optional
from app.utils.result import build, Result


def get_user_profile(
        db: Session, 
        user_id: str
    ) -> optional.Optional[Type[UserModel], HTTPException]:
    try:
        user_model: Type[UserModel] = db.query(UserModel) \
            .filter(UserModel.id == user_id).first()
        
        if not user_model:
            return optional.build(error=HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message=f"User with this ID {user_id} not found"
                ).dict()
            ))
            # return build(error=HTTPException(
            #     status_code=status.HTTP_404_NOT_FOUND, 
            #     error="Not Found",
            #     message="User not found"
            # ))

        # Buat instance dari UserCreateResponseDto
        user_response = user_dtos.UserCreateResponseDto(
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
            updated_at=user_model.updated_at,
        )

        return optional.build(data=user_dtos.UserResponseDto(
            status_code=200,
            message="User profile retrieved successfully.",
            data=user_response
        ))

    except SQLAlchemyError:
        return optional.build(error= HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorResponseDto(
                status_code=status.HTTP_409_CONFLICT,
                error="Conflict",
                message=f"Database conflict: {str(e)}"
            ).dict()
        ))
    
    except HTTPException as e:
        # Menangani error yang dilempar oleh Firebase atau proses lainnya
        return optional.build(error=e)

    except Exception as e:
        return optional.build(error=HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message=f"An error occurred: {str(e)}"
            ).dict()
        ))

    # except Exception as e:
    #     return HTTPException(
    #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #         error="Internal Server Error",
    #         message=f"An error occurred: {str(e)}"
    #     )

