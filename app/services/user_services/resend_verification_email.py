import logging
from datetime import datetime, timedelta
from types import SimpleNamespace

from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.dtos import user_dtos
from app.dtos.error_response_dtos import ErrorResponseDto
from app.libs.verification_code import generate_verification_code
from app.models.user_model import UserModel
from app.utils import optional
from app.utils.firebase_utils import send_verification_email

logger = logging.getLogger(__name__)
GENERIC_RESEND_MESSAGE = "If the email is registered and not verified, a verification email will be sent."


def _generic_success(payload: user_dtos.ResendVerificationRequestDto):
    return user_dtos.ResendVerificationResponseDto(
        status_code=status.HTTP_200_OK,
        message=GENERIC_RESEND_MESSAGE,
        data=user_dtos.ResendVerificationRequestDto(email=payload.email),
    )


def resend_verification_email(
    db: Session,
    payload: user_dtos.ResendVerificationRequestDto,
) -> optional.Optional[user_dtos.ResendVerificationResponseDto, Exception]:
    """Resend account verification email without exposing account existence."""
    try:
        user = db.query(UserModel).filter(UserModel.email == payload.email).first()
        if not user or user.is_active:
            return optional.build(data=_generic_success(payload))

        verification_code = generate_verification_code()
        user.verification_code = verification_code
        user.verification_expiry = datetime.utcnow() + timedelta(minutes=10)

        firebase_user = SimpleNamespace(email=user.email, uid=user.firebase_uid)
        try:
            send_verification_email(firebase_user, user.firstname or "Customer", verification_code)
        except Exception:
            db.rollback()
            logger.warning("Verification email resend failed", exc_info=True)
            return optional.build(data=_generic_success(payload))

        db.commit()
        db.refresh(user)

        return optional.build(data=_generic_success(payload))

    except SQLAlchemyError:
        db.rollback()
        return optional.build(error=HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorResponseDto(
                status_code=status.HTTP_409_CONFLICT,
                error="Conflict",
                message="Database conflict while processing verification email request."
            ).model_dump()
        ))

    except HTTPException as e:
        db.rollback()
        return optional.build(error=e)

    except Exception:
        db.rollback()
        return optional.build(error=HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message="Unable to process verification email request."
            ).model_dump()
        ))
