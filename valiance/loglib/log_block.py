# log_block.py
import uuid
import random
from contextlib import contextmanager
from valiance.loglib.logging_config import (
    log_block_id,
    log_block_color,
    COLORS,
)


@contextmanager
def log_block(name: str | None = None):
    block_id = name or str(uuid.uuid4())[:8]
    color = random.choice(COLORS)

    token_id = log_block_id.set(block_id)
    token_color = log_block_color.set(color)

    try:
        yield
    finally:
        log_block_id.reset(token_id)
        log_block_color.reset(token_color)
