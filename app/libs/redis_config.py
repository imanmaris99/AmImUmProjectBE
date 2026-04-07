import logging
import os
from datetime import datetime
from typing import Optional

import redis
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)


class RedisClient:
    _instance: Optional[redis.StrictRedis] = None

    def __new__(cls):
        if cls._instance is None:
            logging.info(f"Connecting to Redis at {REDIS_HOST}:{REDIS_PORT}, DB={REDIS_DB}")
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
                logging.info("Successfully connected to Redis!")
            except redis.ConnectionError as e:
                logging.warning(f"Failed to connect to Redis at {REDIS_HOST}:{REDIS_PORT}. Error: {e}")
                cls._instance = None
        return cls._instance


redis_client = RedisClient()


def check_redis_connection():
    try:
        if redis_client and redis_client.ping():
            logging.info("Connected to Redis!")
            return True
    except redis.ConnectionError as e:
        logging.error(f"Redis connection failed: {e}")
    return False


def custom_json_serializer(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    if hasattr(obj, "dict"):
        return obj.dict()
    raise TypeError(f"Type {type(obj)} not serializable")
