import os
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.product_image_model import ProductImageModel
from app.utils.result import build, Result


def set_primary_product_image(db: Session, product_id: str, image_id: int) -> Result[dict, Exception]:
    image = db.query(ProductImageModel).filter(
        ProductImageModel.id == image_id,
        ProductImageModel.product_id == product_id,
    ).first()
    if not image:
        return build(error=HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found"))

    db.query(ProductImageModel).filter(ProductImageModel.product_id == product_id).update({"is_primary": False})
    image.is_primary = True
    db.add(image)
    db.commit()
    return build(data={"status_code": 200, "message": "Primary image updated"})


def delete_product_image(db: Session, product_id: str, image_id: int) -> Result[dict, Exception]:
    image = db.query(ProductImageModel).filter(
        ProductImageModel.id == image_id,
        ProductImageModel.product_id == product_id,
    ).first()
    if not image:
        return build(error=HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found"))

    was_primary = image.is_primary
    file_path = image.file_path
    db.delete(image)
    db.commit()

    if file_path and os.path.exists(file_path):
        os.remove(file_path)

    if was_primary:
        next_image = db.query(ProductImageModel).filter(ProductImageModel.product_id == product_id).order_by(ProductImageModel.sort_order.asc()).first()
        if next_image:
            next_image.is_primary = True
            db.add(next_image)
            db.commit()

    return build(data={"status_code": 200, "message": "Image deleted"})


def reorder_product_images(db: Session, product_id: str, image_ids: list[int]) -> Result[dict, Exception]:
    images = db.query(ProductImageModel).filter(ProductImageModel.product_id == product_id).all()
    existing_ids = {img.id for img in images}
    if set(image_ids) != existing_ids:
        return build(error=HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Image id list mismatch"))

    for idx, image_id in enumerate(image_ids):
        db.query(ProductImageModel).filter(
            ProductImageModel.id == image_id,
            ProductImageModel.product_id == product_id,
        ).update({"sort_order": idx})

    db.commit()
    return build(data={"status_code": 200, "message": "Image order updated"})
