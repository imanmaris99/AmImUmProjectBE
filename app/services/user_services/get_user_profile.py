from typing import Type

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

import json

from fastapi import HTTPException, status

from app.models.user_model import UserModel
from app.dtos import user_dtos
from app.dtos.error_response_dtos import ErrorResponseDto

from app.utils import optional
from app.utils.result import build, Result

from app.libs.redis_config import custom_json_serializer, redis_client

CACHE_TTL = 300

def get_user_profile(
        db: Session, 
        user_id: str
    ) -> optional.Optional[Type[UserModel], HTTPException]:
    try:
        # Redis key for caching
        redis_key = f"user:{user_id}"

        # Check if product data exists in Redis
        cached_user = redis_client.get(redis_key)
        if cached_user:
            user_response = user_dtos.UserCreateResponseDto(**json.loads(cached_user))
            return build(data=user_dtos.UserResponseDto(
                status_code=200,
                message="Details info User successfully retrieved (from cache)",
                data=user_response
            ))
        
        # user_model: Type[UserModel] = db.query(UserModel) \
        #     .filter(UserModel.id == user_id).first()
        
        user_model: Type[UserModel] = db.execute(
           select(UserModel) 
           .filter(UserModel.id == user_id)
        ).scalars().first()

        if not user_model:
            return optional.build(error=HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message=f"User with this ID {user_id} not found"
                ).dict()
            ))

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

        redis_client.setex(redis_key, CACHE_TTL, json.dumps(user_response.dict(), default=custom_json_serializer))

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


