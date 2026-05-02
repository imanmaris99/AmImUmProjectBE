import io
import os
import uuid
import time
import hashlib
import requests
from PIL import Image
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from sqlalchemy import delete

from app.dtos.product_image_dtos import ProductImageInfoDto, ProductImageResponseDto
from app.models.product_model import ProductModel
from app.models.product_image_model import ProductImageModel
from app.utils.result import build, Result
from app.services.product_services.cache_utils import invalidate_product_cache
from app.libs.supabase_client import supabase

ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024
TARGET_MAX_OUTPUT_SIZE = 100 * 1024
TARGET_IDEAL_OUTPUT_SIZE = 50 * 1024


def _cloudinary_creds() -> tuple[str, str, str]:
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME", "").strip()
    api_key = os.getenv("CLOUDINARY_API_KEY", "").strip()
    api_secret = os.getenv("CLOUDINARY_API_SECRET", "").strip()
    if not cloud_name or not api_key or not api_secret:
        raise HTTPException(status_code=500, detail="Cloudinary env belum lengkap")
    return cloud_name, api_key, api_secret


def _upload_to_cloudinary(image_bytes: bytes, product_id: str, public_id_seed: str) -> tuple[str, int | None, int | None]:
    cloud_name, api_key, api_secret = _cloudinary_creds()

    timestamp = int(time.time())
    folder = f"amimum/products/{product_id}"
    public_id = f"{public_id_seed}"

    params_to_sign = f"folder={folder}&public_id={public_id}&timestamp={timestamp}{api_secret}"
    signature = hashlib.sha1(params_to_sign.encode("utf-8")).hexdigest()

    upload_url = f"https://api.cloudinary.com/v1_1/{cloud_name}/image/upload"
    files = {"file": (f"{public_id}.webp", image_bytes, "image/webp")}
    data = {
        "api_key": api_key,
        "timestamp": timestamp,
        "folder": folder,
        "public_id": public_id,
        "signature": signature,
    }

    response = requests.post(upload_url, files=files, data=data, timeout=30)
    if response.status_code >= 300:
        raise HTTPException(status_code=502, detail=f"Cloudinary upload gagal: {response.text}")

    payload = response.json()
    return payload.get("secure_url"), payload.get("width"), payload.get("height")


def _extract_public_id_from_cloudinary_url(url: str) -> str | None:
    # example: https://res.cloudinary.com/<cloud>/image/upload/v123/folder/name.webp
    if "/image/upload/" not in url:
        return None
    try:
        tail = url.split("/image/upload/", 1)[1]
        parts = tail.split("/")
        if parts and parts[0].startswith("v") and parts[0][1:].isdigit():
            parts = parts[1:]
        if not parts:
            return None
        path = "/".join(parts)
        if "." in path:
            path = path.rsplit(".", 1)[0]
        return path
    except Exception:
        return None


def _delete_from_cloudinary(url: str) -> None:
    public_id = _extract_public_id_from_cloudinary_url(url)
    if not public_id:
        return

    cloud_name, api_key, api_secret = _cloudinary_creds()
    timestamp = int(time.time())
    params_to_sign = f"public_id={public_id}&timestamp={timestamp}{api_secret}"
    signature = hashlib.sha1(params_to_sign.encode("utf-8")).hexdigest()
    destroy_url = f"https://api.cloudinary.com/v1_1/{cloud_name}/image/destroy"
    data = {
        "public_id": public_id,
        "timestamp": timestamp,
        "api_key": api_key,
        "signature": signature,
    }
    try:
        requests.post(destroy_url, data=data, timeout=20)
    except Exception:
        pass


def _upload_to_supabase_bytes(image_bytes: bytes, product_id: str, public_id_seed: str) -> tuple[str | None, None, None]:
    filename = f"images/product_picture/{product_id}_{public_id_seed}.webp"
    upload_response = supabase.storage.from_("AmimumProject-storage").upload(
        filename,
        image_bytes,
        {"content-type": "image/webp"}
    )
    if isinstance(upload_response, dict) and upload_response.get("error"):
        return None, None, None
    public_url = supabase.storage.from_("AmimumProject-storage").get_public_url(filename)
    return (public_url if isinstance(public_url, str) else None), None, None


async def upload_product_image(db: Session, product_id: str, file: UploadFile) -> Result[ProductImageResponseDto, Exception]:
    product = db.query(ProductModel).filter(ProductModel.id == product_id).first()
    if not product:
        return build(error=HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"))

    if file.content_type not in ALLOWED_MIME:
        return build(error=HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported image format"))

    raw = await file.read()
    if len(raw) > MAX_FILE_SIZE:
        return build(error=HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Image too large"))

    filename_seed = str(uuid.uuid4())
    relative_path = f"cloudinary://amimum/products/{product_id}/{filename_seed}.webp"

    width = None
    height = None
    final_bytes = raw

    try:
        img = Image.open(io.BytesIO(raw)).convert("RGB")
        max_dimension = 1600
        img.thumbnail((max_dimension, max_dimension))

        quality_steps = [82, 78, 74, 70, 66, 62, 58, 54, 50]
        current_image = img
        compressed = None

        while True:
            for quality in quality_steps:
                buffer = io.BytesIO()
                current_image.save(buffer, format="WEBP", quality=quality, optimize=True)
                size = buffer.tell()
                if size <= TARGET_IDEAL_OUTPUT_SIZE:
                    compressed = buffer.getvalue()
                    break
                if size <= TARGET_MAX_OUTPUT_SIZE:
                    compressed = buffer.getvalue()
            if compressed is not None:
                break

            w, h = current_image.size
            if max(w, h) <= 900:
                buffer = io.BytesIO()
                current_image.save(buffer, format="WEBP", quality=50, optimize=True)
                compressed = buffer.getvalue()
                break

            current_image = current_image.resize((int(w * 0.85), int(h * 0.85)))

        final_bytes = compressed or raw
        width, height = current_image.size

    except Exception:
        final_bytes = raw

    if len(final_bytes) > TARGET_MAX_OUTPUT_SIZE:
        return build(error=HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Gagal mengompres gambar ke <= 100KB. Gunakan foto resolusi lebih kecil."
        ))

    storage_provider = "cloudinary"
    try:
        image_url, uploaded_width, uploaded_height = _upload_to_cloudinary(final_bytes, product_id, filename_seed)
    except Exception:
        storage_provider = "supabase"
        image_url, uploaded_width, uploaded_height = _upload_to_supabase_bytes(final_bytes, product_id, filename_seed)

    if not image_url:
        return build(error=HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to upload image on all storage providers"))

    width = uploaded_width or width
    height = uploaded_height or height

    # Replace mode: saat upload dari halaman edit, hapus gambar lama dulu.
    existing_images = db.query(ProductImageModel).filter(ProductImageModel.product_id == product_id).all()
    for old_img in existing_images:
        if old_img.url:
            _delete_from_cloudinary(old_img.url)

    if existing_images:
        db.execute(delete(ProductImageModel).where(ProductImageModel.product_id == product_id))
        db.commit()

    image_model = ProductImageModel(
        product_id=product_id,
        storage_provider=storage_provider,
        file_path=relative_path,
        url=image_url,
        mime_type="image/webp",
        size_bytes=len(final_bytes),
        width=width,
        height=height,
        is_primary=True,
        sort_order=0,
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
