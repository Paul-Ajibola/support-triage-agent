"""
checkpointing.py

Configures the LangGraph checkpointer (Redis) that persists conversation
state across turns, keyed by thread_id.
"""

import logging
import os
from urllib.parse import urlparse

from dotenv import load_dotenv
from langgraph.checkpoint.redis import RedisSaver
from langgraph.checkpoint.memory import MemorySaver

load_dotenv(".env")

logger = logging.getLogger(__name__)

_redis_cm = None    # keeps the context manager so we can close it on shutdown


def get_checkpointer():
    global _redis_cm

    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    if not redis_url:
        redis_url = f"redis://{os.getenv('REDIS_HOST', 'localhost')}:{os.getenv('REDIS_PORT', '6379')}"

    cm = None
    try:
        # RedisSaver is meant to be used as a context manager; we enter it
        # manually and close it later via close_checkpointer().
        cm = RedisSaver.from_conn_string(redis_url)
        checkpointer = cm.__enter__()
        checkpointer.setup()
        _redis_cm = cm
        return checkpointer
    except Exception:
        if cm is not None:
            try:
                cm.__exit__(None, None, None)
            except Exception:
                pass
        if os.getenv("APP_ENV", "development").lower() == "production":
            raise
        # log the host only: the URL contains the password
        logger.warning(
            "Redis checkpointer unavailable (host=%s) - falling back to in-memory "
            "checkpointing (state is lost on restart).",
            urlparse(redis_url).hostname, exc_info=True,
        )
        return MemorySaver()


def close_checkpointer() -> None:
    """Close the Redis connection cleanly on app shutdown."""
    global _redis_cm
    if _redis_cm is not None:
        try:
            _redis_cm.__exit__(None, None, None)
        except Exception:
            logger.warning("Error while closing Redis checkpointer", exc_info=True)
        _redis_cm = None


