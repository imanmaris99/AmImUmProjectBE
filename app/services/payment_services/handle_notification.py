from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.dtos.payment_dtos import InfoTransactionIdDto
from app.services.payment_services.handler_notification import handler_notification
from app.utils.result import build, Result


def handle_notification(
    notification_data: InfoTransactionIdDto,
    db: Session,
    user_id: str,
) -> Result[dict, Exception]:
    if not user_id:
        return build(error=HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized"
        ))

    return handler_notification(
        notification_data={"order_id": notification_data.order_id},
        db=db,
    )
