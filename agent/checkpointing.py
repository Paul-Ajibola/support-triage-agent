"""
chekcpointing.py

To configure langgrap checkpointer backend (redis) used to persist
conversation state across turns, keyed by thread_id.
"""

import logging
import os
from langgraph.checkpoint.redis import RedisSaver
from langgraph.checkpoint.memory import MemorySaver

load_dotenv(".env.local")


logger = logging.getLogger(__name__)


def get_checkpointer():
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    if not redis_url:
        redis_url = f"redis://{os.getenv('REDIS_HOST', 'localhost')}:{os.getenv('REDIS_PORT', '6379')}"

    try:
        # designed to be used as a context manager and not callable directly
        cm = RedisSaver.from_conn_string(redis_url)
        # manually calling the .__enter__(), but ignoring the .__exit__(); to keep it open an active automatically
        checkpointer = cm.__enter__()
        checkpointer.setup()
        return checkpointer
    except Exception:
        if os.getenv("APP_ENV", "development").lower() == "production":
            raise
        logger.warning(
            "Redis checkpointer unavailable at %s - falling back to in-memory "
            "checkpointing (state is lost on restart).", redis_url, exc_info=True,
        )
        return MemorySaver()


