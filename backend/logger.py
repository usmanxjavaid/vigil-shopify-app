import logging
import sys
from contextvars import ContextVar
from logging.handlers import RotatingFileHandler
from pathlib import Path

from config import settings

# Holds the current request's shop_id so every log line picks it up
# automatically — call sites just do logger.info("message"), they never
# need to pass shop_id manually. Set once per request, in a middleware,
# once real shop-scoped requests exist (Phase 3+). For now it stays "-".
shop_id_ctx: ContextVar[str] = ContextVar("shop_id", default="-")


class ShopIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.shop_id = shop_id_ctx.get()
        return True


def setup_logging() -> None:
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | shop=%(shop_id)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    shop_filter = ShopIdFilter()

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(settings.console_log_level)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(shop_filter)

    # Always DEBUG in the file, regardless of console level — same rule
    # as Velvora, so debugging never requires flipping env vars back and forth.
    # Rotating so a busy multi-tenant app doesn't grow one unbounded file.
    file_handler = RotatingFileHandler(
        log_dir / "vigil.log", maxBytes=5_000_000, backupCount=3, encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    file_handler.addFilter(shop_filter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # handlers filter, not the logger itself
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)