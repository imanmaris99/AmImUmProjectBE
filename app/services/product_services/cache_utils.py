from app.libs.redis_config import redis_client


def invalidate_product_cache(product_id: str | None = None) -> None:
    if not redis_client:
        return
    patterns = ["products:*", "product:*"]
    if product_id:
        patterns.append(f"product:{product_id}")
    for pattern in patterns:
        for key in redis_client.scan_iter(pattern):
            redis_client.delete(key)
