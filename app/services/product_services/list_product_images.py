from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.product_model import ProductModel
from app.models.product_image_model import ProductImageModel
from app.utils.result import build, Result


def list_product_images(db: Session, product_id: str) -> Result[dict, Exception]:
    product = db.query(ProductModel).filter(ProductModel.id == product_id).first()
    if not product:
        return build(error=HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"))

    images = db.query(ProductImageModel).filter(
        ProductImageModel.product_id == product_id
    ).order_by(ProductImageModel.sort_order.asc(), ProductImageModel.id.asc()).all()

    data = [
        {
            "id": img.id,
            "product_id": img.product_id,
            "url": img.url,
            "is_primary": img.is_primary,
            "sort_order": img.sort_order,
            "mime_type": img.mime_type,
            "size_bytes": img.size_bytes,
            "width": img.width,
            "height": img.height,
            "created_at": img.created_at,
        }
        for img in images
    ]

    return build(data={"status_code": 200, "message": "Product images fetched", "data": data})
