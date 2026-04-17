from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.dtos import user_dtos
from app.dtos.error_response_dtos import ErrorResponseDto
from app.models.user_model import UserModel
from app.utils import optional
from app.libs.redis_config import redis_client


ADMIN_USER_UPDATE_MESSAGE = "Admin user updated successfully"


def update_user_profile_admin(db: Session, user_id: str, payload: user_dtos.AdminUserEditRequestDto):
    try:
        user = db.execute(
            select(UserModel).where(UserModel.id == user_id)
        ).scalars().first()

        if not user:
            return optional.build(error=HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message=f"User with ID {user_id} not found."
                ).dict()
            ))

        user.fullname = payload.fullname
        user.firstname = payload.firstname
        user.lastname = payload.lastname
        user.phone = payload.phone
        user.address = payload.address

        db.commit()
        db.refresh(user)

        try:
            if redis_client:
                redis_client.delete(f"user:{user_id}")
                for key in redis_client.scan_iter(f"user:{user_id}:*"):
                    redis_client.delete(key)
        except Exception:
            pass

        return optional.build(data=user_dtos.AdminUserEditResponseDto(
            status_code=status.HTTP_200_OK,
            message=ADMIN_USER_UPDATE_MESSAGE,
            data=user_dtos.AdminUserDetailDto(
                id=user.id,
                firstname=user.firstname,
                lastname=user.lastname,
                fullname=user.fullname,
                gender=user.gender,
                email=user.email,
                phone=user.phone,
                address=user.address,
                photo_url=user.photo_url,
                role=user.role,
                firebase_uid=user.firebase_uid,
                is_active=user.is_active,
                verification_code=user.verification_code,
                verification_expiry=user.verification_expiry,
                created_at=user.created_at,
                updated_at=user.updated_at,
            )
        ))

    except SQLAlchemyError as e:
        db.rollback()
        return optional.build(error=HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message=f"Database error occurred while updating user profile. {str(e)}"
            ).dict()
        ))
