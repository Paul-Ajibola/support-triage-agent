"""
chekcpointing.py

To configure langgrap checkpointer backend (redis) used to persist
conversation state across turns, keyed by thread_id.
"""

import os
from langgraph.checkpoint.redis import RedisSaver


def get_checkpointer():
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    # designed to be used as a context manager and not callable directly
    cm = RedisSaver.from_conn_string(redis_url)
    # manually calling the .__enter__(), but ignoring the .__exit__(); to keep it open an active automatically
    checkpointer = cm.__enter__()
    checkpointer.setup()
    return checkpointer


