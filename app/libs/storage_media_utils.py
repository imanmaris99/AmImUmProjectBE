import os
import time
import hashlib
import requests
from urllib.parse import urlparse

from app.libs.supabase_client import supabase


def cloudinary_creds() -> tuple[str, str, str]:
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME", "").strip()
    api_key = os.getenv("CLOUDINARY_API_KEY", "").strip()
    api_secret = os.getenv("CLOUDINARY_API_SECRET", "").strip()
    if not cloud_name or not api_key or not api_secret:
        raise ValueError("Cloudinary env belum lengkap")
    return cloud_name, api_key, api_secret


def extract_cloudinary_public_id(url: str) -> str | None:
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


def delete_from_cloudinary(url: str) -> None:
    public_id = extract_cloudinary_public_id(url)
    if not public_id:
        return

    cloud_name, api_key, api_secret = cloudinary_creds()
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


def extract_supabase_path(url: str) -> str | None:
    try:
        parsed = urlparse(url)
        marker = "/storage/v1/object/public/AmimumProject-storage/"
        idx = parsed.path.find(marker)
        if idx < 0:
            return None
        return parsed.path[idx + len(marker):]
    except Exception:
        return None


def delete_from_supabase(url: str) -> None:
    path = extract_supabase_path(url)
    if not path:
        return
    try:
        supabase.storage.from_("AmimumProject-storage").remove([path])
    except Exception:
        pass


def delete_media_url(url: str | None) -> None:
    if not url:
        return
    if "res.cloudinary.com" in url or "/image/upload/" in url:
        delete_from_cloudinary(url)
        return
    if "/storage/v1/object/public/AmimumProject-storage/" in url:
        delete_from_supabase(url)
