import logging
import os
from datetime import timezone
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


def get_env(key: str, default: Optional[str] = None, required: bool = False) -> str:
    value = os.getenv(key, default)
    if required and (value is None or value == ""):
        raise ValueError(f"Missing required env var: {key}")
    return value


def configure_logging() -> None:
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(name)s %(message)s")


def get_timezone() -> timezone:
    """
    Resolve timezone from env TIMEZONE (e.g., Asia/Shanghai), fallback to UTC.
    """
    tz_name = os.getenv("TIMEZONE")
    if tz_name:
        try:
            from zoneinfo import ZoneInfo

            return ZoneInfo(tz_name)
        except Exception:
            pass
    return timezone.utc
