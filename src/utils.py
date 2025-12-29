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


def normalize_tweet_url(url: str) -> Optional[str]:
    """Return normalized tweet URL if valid, else None."""
    from urllib.parse import urlparse

    if not url:
        return None
    parsed = urlparse(url)
    host = (parsed.netloc or "").lower()
    if "twitter.com" not in host and "x.com" not in host:
        return None
    parts = [p for p in parsed.path.split("/") if p]
    # Expect .../<user>/status/<id>
    if len(parts) < 3 or parts[-2] != "status":
        # try find numeric id at end
        tweet_id = next((p for p in reversed(parts) if p.isdigit()), None)
    else:
        tweet_id = parts[-1] if parts[-1].isdigit() else None
    if not tweet_id:
        return None
    # Prefer x.com canonical
    return f"https://x.com/i/web/status/{tweet_id}"
