from datetime import datetime
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.dtos import inventory_dtos
from app.dtos.error_response_dtos import ErrorResponseDto
from app.models.inventory_threshold_model import InventoryThresholdModel
from app.models.pack_type_model import PackTypeModel
from app.models.stock_movement_model import StockMovementModel
from app.services.product_services.cache_utils import invalidate_product_cache
from app.utils.result import Result, build


def _movement_to_dto(row: StockMovementModel) -> inventory_dtos.StockMovementItemDto:
    return inventory_dtos.StockMovementItemDto(
        id=str(row.id),
        variant_id=int(row.variant_id),
        product_id=str(row.product_id) if row.product_id else None,
        movement_type=row.movement_type,
        delta=int(row.delta),
        stock_before=int(row.stock_before) if row.stock_before is not None else None,
        stock_after=int(row.stock_after) if row.stock_after is not None else None,
        actor_id=str(row.actor_id) if row.actor_id else None,
        reason=row.reason,
        reference=row.reference,
        created_at=row.created_at,
    )


def list_stock_movements(
    db: Session,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    variant_id: Optional[int] = None,
    product_id: Optional[str] = None,
    movement_type: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
) -> Result[inventory_dtos.StockMovementListResponseDto, Exception]:
    try:
        query = db.query(StockMovementModel)

        if from_date:
            query = query.filter(StockMovementModel.created_at >= from_date)
        if to_date:
            query = query.filter(StockMovementModel.created_at <= to_date)
        if variant_id is not None:
            query = query.filter(StockMovementModel.variant_id == variant_id)
        if product_id:
            query = query.filter(StockMovementModel.product_id == product_id)
        if movement_type:
            if movement_type not in {"in", "out", "adjust", "sale", "return", "snapshot"}:
                return build(error=HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=ErrorResponseDto(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        error="Bad Request",
                        message="Invalid movement_type filter",
                    ).model_dump(),
                ))
            query = query.filter(StockMovementModel.movement_type == movement_type)

        total = query.count()
        rows = (
            query.order_by(StockMovementModel.created_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
            .all()
        )

        return build(data=inventory_dtos.StockMovementListResponseDto(
            status_code=status.HTTP_200_OK,
            message="Success",
            data=inventory_dtos.StockMovementListDataDto(
                items=[_movement_to_dto(row) for row in rows],
                page=page,
                limit=limit,
                total=total,
            ),
        ))

    except SQLAlchemyError:
        return build(error=HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorResponseDto(
                status_code=status.HTTP_409_CONFLICT,
                error="Conflict",
                message="Database conflict while reading stock movements.",
            ).model_dump(),
        ))


def adjust_stock(
    db: Session,
    payload: inventory_dtos.StockAdjustmentRequestDto,
    actor_id: Optional[str] = None,
) -> Result[inventory_dtos.StockAdjustmentResponseDto, Exception]:
    try:
        variant = db.query(PackTypeModel).filter(PackTypeModel.id == payload.variant_id).with_for_update().first()
        if not variant:
            return build(error=HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message=f"Variant with ID {payload.variant_id} not found",
                ).model_dump(),
            ))

        stock_before = int(variant.stock or 0)
        stock_after = stock_before + int(payload.delta)
        if stock_after < 0:
            return build(error=HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    error="Bad Request",
                    message="Stock adjustment cannot make stock negative",
                ).model_dump(),
            ))

        variant.stock = stock_after
        movement = StockMovementModel(
            variant_id=variant.id,
            product_id=getattr(variant, "product_id", None),
            movement_type="adjust",
            delta=int(payload.delta),
            stock_before=stock_before,
            stock_after=stock_after,
            actor_id=actor_id,
            reason=payload.reason,
            reference=payload.reference,
        )
        db.add(movement)
        db.commit()
        db.refresh(variant)
        db.refresh(movement)
        invalidate_product_cache(variant.product_id)

        return build(data=inventory_dtos.StockAdjustmentResponseDto(
            status_code=status.HTTP_200_OK,
            message="Stock adjusted successfully",
            data=_movement_to_dto(movement),
        ))

    except HTTPException as e:
        db.rollback()
        return build(error=e)
    except SQLAlchemyError:
        db.rollback()
        return build(error=HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorResponseDto(
                status_code=status.HTTP_409_CONFLICT,
                error="Conflict",
                message="Database conflict while updating inventory.",
            ).model_dump(),
        ))


def set_variant_threshold(
    db: Session,
    variant_id: int,
    payload: inventory_dtos.InventoryThresholdRequestDto,
    actor_id: Optional[str] = None,
) -> Result[inventory_dtos.InventoryThresholdResponseDto, Exception]:
    try:
        variant = db.query(PackTypeModel).filter(PackTypeModel.id == variant_id).with_for_update().first()
        if not variant:
            return build(error=HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message=f"Variant with ID {variant_id} not found",
                ).model_dump(),
            ))

        row = db.query(InventoryThresholdModel).filter(
            InventoryThresholdModel.variant_id == variant_id
        ).first()
        if not row:
            row = InventoryThresholdModel(variant_id=variant_id)
            db.add(row)

        row.min_threshold = payload.min_threshold
        row.updated_by = actor_id
        row.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(row)

        return build(data=inventory_dtos.InventoryThresholdResponseDto(
            status_code=status.HTTP_200_OK,
            message="Inventory threshold updated successfully",
            data=inventory_dtos.InventoryThresholdDto(
                variant_id=row.variant_id,
                min_threshold=row.min_threshold,
                updated_by=row.updated_by,
                updated_at=row.updated_at,
            ),
        ))

    except HTTPException as e:
        db.rollback()
        return build(error=e)
    except SQLAlchemyError:
        db.rollback()
        return build(error=HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorResponseDto(
                status_code=status.HTTP_409_CONFLICT,
                error="Conflict",
                message="Database conflict while updating inventory.",
            ).model_dump(),
        ))
