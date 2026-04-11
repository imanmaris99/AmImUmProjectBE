import logging
import os
from datetime import datetime
from typing import Optional

import redis
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)


class RedisClient:
    _instance: Optional[redis.StrictRedis] = None

    def __new__(cls):
        if cls._instance is None:
            logger.info("Connecting to Redis at %s:%s, DB=%s", REDIS_HOST, REDIS_PORT, REDIS_DB)
            try:
                client = redis.StrictRedis(
                    host=REDIS_HOST,
                    port=REDIS_PORT,
                    db=REDIS_DB,
                    password=REDIS_PASSWORD,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                )
                client.ping()
                cls._instance = client
                logger.info("Successfully connected to Redis!")
            except redis.ConnectionError as e:
                logger.warning("Failed to connect to Redis at %s:%s. Error: %s", REDIS_HOST, REDIS_PORT, e)
                cls._instance = None
        return cls._instance


redis_client = RedisClient()


def check_redis_connection():
    try:
        if redis_client and redis_client.ping():
            logger.info("Connected to Redis!")
            return True
    except redis.ConnectionError as e:
        logger.error("Redis connection failed: %s", e)
    return False


def custom_json_serializer(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    if hasattr(obj, "dict"):
        return obj.dict()
    raise TypeError(f"Type {type(obj)} not serializable")
