import io
import os
import uuid
from PIL import Image
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.dtos.product_image_dtos import ProductImageInfoDto, ProductImageResponseDto
from app.models.product_model import ProductModel
from app.models.product_image_model import ProductImageModel
from app.utils.result import build, Result
from app.services.product_services.cache_utils import invalidate_product_cache

ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024
TARGET_MAX_OUTPUT_SIZE = 1 * 1024 * 1024
TARGET_IDEAL_OUTPUT_SIZE = 500 * 1024


def _resolve_host_url() -> str:
    host_url = os.getenv("HOST_URL", "").rstrip("/")
    if host_url:
        return host_url

    railway_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN", "").strip()
    if railway_domain:
        return f"https://{railway_domain.strip('/')}"

    return "http://127.0.0.1:8000"


async def upload_product_image(db: Session, product_id: str, file: UploadFile) -> Result[ProductImageResponseDto, Exception]:
    product = db.query(ProductModel).filter(ProductModel.id == product_id).first()
    if not product:
        return build(error=HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"))

    if file.content_type not in ALLOWED_MIME:
        return build(error=HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported image format"))

    raw = await file.read()
    if len(raw) > MAX_FILE_SIZE:
        return build(error=HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Image too large"))

    filename = f"{uuid.uuid4()}.webp"
    relative_dir = os.path.join("images", "products", product_id)
    os.makedirs(relative_dir, exist_ok=True)
    relative_path = os.path.join(relative_dir, filename)

    width = None
    height = None
    try:
        img = Image.open(io.BytesIO(raw)).convert("RGB")
        max_dimension = 1600
        img.thumbnail((max_dimension, max_dimension))

        quality_steps = [82, 78, 74, 70, 66, 62, 58, 54, 50]
        current_image = img
        final_bytes = None

        while True:
            for quality in quality_steps:
                buffer = io.BytesIO()
                current_image.save(buffer, format="WEBP", quality=quality, optimize=True)
                size = buffer.tell()
                if size <= TARGET_IDEAL_OUTPUT_SIZE:
                    final_bytes = buffer.getvalue()
                    break
                if size <= TARGET_MAX_OUTPUT_SIZE:
                    final_bytes = buffer.getvalue()
            if final_bytes is not None:
                break

            w, h = current_image.size
            if max(w, h) <= 900:
                # last resort: take the smallest compressed version even if slightly > target
                buffer = io.BytesIO()
                current_image.save(buffer, format="WEBP", quality=50, optimize=True)
                final_bytes = buffer.getvalue()
                break

            current_image = current_image.resize((int(w * 0.85), int(h * 0.85)))

        with open(relative_path, "wb") as f:
            f.write(final_bytes)

        width, height = current_image.size

    except Exception:
        with open(relative_path, "wb") as f:
            f.write(raw)

    final_size = os.path.getsize(relative_path)
    if final_size > TARGET_MAX_OUTPUT_SIZE:
        try:
            os.remove(relative_path)
        except OSError:
            pass
        return build(error=HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Gagal mengompres gambar ke <= 1MB. Gunakan foto resolusi lebih kecil."
        ))

    host_url = _resolve_host_url()
    image_url = f"{host_url}/{relative_path}"

    current_primary = db.query(ProductImageModel).filter(
        ProductImageModel.product_id == product_id,
        ProductImageModel.is_primary == True
    ).first()

    latest_order = db.query(ProductImageModel).filter(ProductImageModel.product_id == product_id).count()
    image_model = ProductImageModel(
        product_id=product_id,
        storage_provider="local",
        file_path=relative_path,
        url=image_url,
        mime_type="image/webp",
        size_bytes=os.path.getsize(relative_path),
        width=width,
        height=height,
        is_primary=(current_primary is None),
        sort_order=latest_order,
    )

    db.add(image_model)
    db.commit()
    db.refresh(image_model)
    invalidate_product_cache(product_id)

    return build(data=ProductImageResponseDto(
        status_code=201,
        message="Product image uploaded",
        data=ProductImageInfoDto(
            id=image_model.id,
            product_id=image_model.product_id,
            url=image_model.url,
            is_primary=image_model.is_primary,
            sort_order=image_model.sort_order,
            mime_type=image_model.mime_type,
            size_bytes=image_model.size_bytes,
            width=image_model.width,
            height=image_model.height,
            created_at=image_model.created_at,
        )
    ))
