from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.user_model import UserModel
from app.dtos import user_dtos
from app.dtos.error_response_dtos import ErrorResponseDto
from app.services.admin_filter_utils import normalize_optional_filter, validate_allowed_filter
from app.utils import optional


ADMIN_USER_LIST_MESSAGE = "Admin user list accessed successfully"
ADMIN_USER_DETAIL_MESSAGE = "Admin user detail accessed successfully"
ADMIN_USER_STATUS_MESSAGE = "Admin user status updated successfully"
ALLOWED_ADMIN_USER_ROLES = {"admin", "customer"}


def _to_user_summary(user: UserModel) -> user_dtos.AdminUserInfoDto:
    return user_dtos.AdminUserInfoDto(
        id=user.id,
        firstname=user.firstname,
        lastname=user.lastname,
        email=user.email,
        phone=user.phone,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


def list_all_users(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    role: str | None = None,
    is_active: bool | None = None,
):
    try:
        stmt = select(UserModel)

        normalized_role = validate_allowed_filter(
            value=role,
            allowed_values=ALLOWED_ADMIN_USER_ROLES,
            field_name="User role",
        )

        if normalized_role:
            stmt = stmt.where(UserModel.role == normalized_role)
        if is_active is not None:
            stmt = stmt.where(UserModel.is_active == is_active)

        user_models = db.execute(
            stmt.order_by(UserModel.created_at.desc()).offset(skip).limit(limit)
        ).scalars().all()

        user_items = [_to_user_summary(user) for user in user_models]

        return optional.build(data=user_dtos.AdminUserListResponseDto(
            status_code=status.HTTP_200_OK,
            message=ADMIN_USER_LIST_MESSAGE,
            data=user_items,
            meta=user_dtos.AdminUserListMetaDto(
                skip=skip,
                limit=limit,
                count=len(user_items),
            ),
        ))

    except SQLAlchemyError as e:
        return optional.build(error=HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message=f"Database error occurred while fetching users. {str(e)}"
            ).dict()
        ))


def get_user_detail_admin(db: Session, user_id: str):
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

        return optional.build(data=user_dtos.AdminUserDetailResponseDto(
            status_code=status.HTTP_200_OK,
            message=ADMIN_USER_DETAIL_MESSAGE,
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
        return optional.build(error=HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message=f"Database error occurred while fetching user detail. {str(e)}"
            ).dict()
        ))


def update_user_active_status_admin(db: Session, user_id: str, is_active: bool):
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

        if normalize_optional_filter(user.role) == "admin":
            return optional.build(error=HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_403_FORBIDDEN,
                    error="Forbidden",
                    message="Admin account status must not be changed from this endpoint."
                ).dict()
            ))

        user.is_active = is_active
        db.commit()
        db.refresh(user)

        return optional.build(data=user_dtos.AdminUserStatusUpdateResponseDto(
            status_code=status.HTTP_200_OK,
            message=ADMIN_USER_STATUS_MESSAGE,
            data=user_dtos.AdminUserStatusUpdateDto(
                id=user.id,
                email=user.email,
                role=user.role,
                is_active=user.is_active,
            )
        ))

    except SQLAlchemyError as e:
        db.rollback()
        return optional.build(error=HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message=f"Database error occurred while updating user status. {str(e)}"
            ).dict()
        ))
