from typing import Type, Optional, Callable
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, UploadFile, status

from app.models.user_model import UserModel
from app.dtos import user_dtos

from app.utils import optional, find_errr_from_args


def user_edit(
        user_id: str,
        user: user_dtos.UserEditProfileDto, 
        db: Session 
    ):
    try:
        user_model: Type[UserModel] = db.query(UserModel).filter(UserModel.id == user_id).first()
        if user_model:
            for field, value in user.dict().items():
                setattr(user_model, field, value)

            db.commit()
            db.refresh(user_model)
            # return optional.build(data=user_model)
            return optional.build(data=user_dtos.UserEditResponseDto(
            status_code=status.HTTP_200_OK,
            message="Your profile has been successfully updated",
            data=user
        ))
        
        else:
            return optional.build(error=HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                error="Not Found",
                message="User not found"
                )
            )

    except SQLAlchemyError as e:
        db.rollback()
        return optional.build(error=HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            error="Conflict",
            message="Database conflict: " + str(e)
            )
        )
