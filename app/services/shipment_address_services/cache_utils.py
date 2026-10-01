import logging

from app.libs.redis_config import redis_client

logger = logging.getLogger(__name__)


def invalidate_user_address_cache(user_id: str) -> None:
    """Best-effort invalidation for cached customer shipment-address lists."""
    if not redis_client:
        return

    patterns = (
        f"origin_address:{user_id}:*",
        f"origin_address:v2:{user_id}:*",
    )
    try:
        for pattern in patterns:
            for key in redis_client.scan_iter(pattern):
                redis_client.delete(key)
    except Exception as cache_error:
        logger.warning(
            "Failed to invalidate shipping address cache for user %s: %s",
            user_id,
            cache_error,
        )
