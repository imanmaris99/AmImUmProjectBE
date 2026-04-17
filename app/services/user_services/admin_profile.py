from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.dtos import user_dtos
from app.dtos.error_response_dtos import ErrorResponseDto
from app.services.user_services.get_user_profile import get_user_profile
from app.services.user_services.update_profile import user_edit
from app.services.user_services.update_photo import update_my_photo
from app.services.user_services.change_password import change_password
from app.utils import optional


ADMIN_PROFILE_MESSAGE = "Admin profile retrieved successfully"


def get_admin_profile(db: Session, user_id: str):
    profile_result = get_user_profile(db=db, user_id=user_id)

    if profile_result.error:
        return profile_result

    profile_response = profile_result.unwrap()
    profile_response.status_code = status.HTTP_200_OK
    profile_response.message = ADMIN_PROFILE_MESSAGE

    return optional.build(data=user_dtos.AdminSelfProfileResponseDto(
        status_code=profile_response.status_code,
        message=profile_response.message,
        data=profile_response.data,
    ))


def update_admin_profile(db: Session, user_id: str, payload: user_dtos.UserEditProfileDto):
    return user_edit(user_id=user_id, user=payload, db=db)


async def update_admin_photo(db: Session, user_id: str, file):
    return await update_my_photo(db=db, user_id=user_id, file=file)


async def change_admin_password(db: Session, user_id: str, payload: user_dtos.ChangePasswordDto):
    return await change_password(user_id=user_id, payload=payload, db=db)
