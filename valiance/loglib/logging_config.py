# logging_config.py
import logging
import contextvars

# ── Context variables ────────────────────────────────────────────

log_block_id = contextvars.ContextVar("log_block_id", default=None)
log_block_color = contextvars.ContextVar("log_block_color", default="")

# ── ANSI colors ──────────────────────────────────────────────────

COLORS = [
    "\033[91m",  # red
    "\033[92m",  # green
    "\033[93m",  # yellow
    "\033[94m",  # blue
    "\033[95m",  # magenta
    "\033[96m",  # cyan
]
RESET = "\033[0m"

# ── Logging filter ───────────────────────────────────────────────


class BlockContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.block_id = log_block_id.get() or "-"
        record.block_color = log_block_color.get()
        record.reset = RESET
        return True


# ── Formatter ────────────────────────────────────────────────────


class ColoredFormatter(logging.Formatter):
    def format(self, record):
        msg = super().format(record)
        if record.block_color:
            return f"{record.block_color}{msg}{record.reset}"
        return msg


# ── Public setup function ────────────────────────────────────────


def setup_logging(log_level: str = "INFO"):
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log_level}")

    console = logging.StreamHandler()
    file = logging.FileHandler("app.log")

    console.setFormatter(
        ColoredFormatter(
            "%(asctime)s - %(name)s - %(levelname)s - [%(block_id)s] - %(message)s"
        )
    )
    file.setFormatter(
        logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - [%(block_id)s] - %(message)s"
        )
    )

    block_filter = BlockContextFilter()
    console.addFilter(block_filter)
    file.addFilter(block_filter)

    root = logging.getLogger()
    root.setLevel(numeric_level)
    root.handlers.clear()
    root.addHandler(console)
    root.addHandler(file)
