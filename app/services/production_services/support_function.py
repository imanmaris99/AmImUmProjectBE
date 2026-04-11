from fastapi import HTTPException, status

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.dtos.error_response_dtos import ErrorResponseDto

# Utility Function for Handling Database Errors
def handle_db_error(db: Session, error: SQLAlchemyError) -> HTTPException:
    db.rollback()
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=ErrorResponseDto(
            status_code=status.HTTP_409_CONFLICT,
            error="Conflict",
            message=f"Database error: {str(error)}"
        ).dict()
    )
