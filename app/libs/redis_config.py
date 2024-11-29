import redis
import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging to show INFO level messages
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Redis configuration from environment variables
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

# Log Redis configuration
# logging.info(f"REDIS_HOST: {REDIS_HOST}, REDIS_PORT: {REDIS_PORT}, REDIS_DB: {REDIS_DB}")

# Singleton Redis connection
class RedisClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            logging.info(f"Connecting to Redis at {REDIS_HOST}:{REDIS_PORT}, DB={REDIS_DB}")
            try:
                cls._instance = redis.StrictRedis(
                    host=REDIS_HOST,
                    port=REDIS_PORT,
                    db=REDIS_DB,
                    password=REDIS_PASSWORD,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                )
                cls._instance.ping()
                logging.info("Successfully connected to Redis!")
            except redis.ConnectionError as e:
                logging.error(f"Failed to connect to Redis at {REDIS_HOST}:{REDIS_PORT}. Error: {e}")
                raise e
        return cls._instance

# Global Redis client instance
redis_client = RedisClient()

# Function to check Redis connection explicitly
def check_redis_connection():
    try:
        if redis_client.ping():
            logging.info("Connected to Redis!")
    except redis.ConnectionError as e:
        logging.error(f"Redis connection failed: {e}")
