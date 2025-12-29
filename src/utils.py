import logging
import os
from datetime import timezone
from typing import Optional

from dotenv import load_dotenv

# Gracefully ignore missing/permission-denied .env during tests
try:
    load_dotenv()
except PermissionError:
    pass


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


def _parse_bool(val: Optional[str], default: bool) -> bool:
    if val is None:
        return default
    return val.lower() in ("1", "true", "yes", "on")


def get_int(key: str, default: int) -> int:
    try:
        return int(os.getenv(key, default))
    except Exception:
        return default

def _parse_viewport(val: Optional[str]) -> Optional[dict]:
    if not val:
        return None
    parts = val.lower().replace("x", " ").split()
    if len(parts) != 2:
        return None
    try:
        w, h = int(parts[0]), int(parts[1])
        return {"width": w, "height": h}
    except Exception:
        return None


def get_antibot_settings() -> dict:
    """Load anti-bot/UA/viewport settings from env."""
    ua_default = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
    viewport_default = {"width": 1280, "height": 720}
    init_script_default = """
// Remove webdriver
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
// Fake plugins
Object.defineProperty(navigator, 'plugins', { get: () => [1,2,3,4,5] });
"""
    args_env = os.getenv("ANTI_BOT_ARGS")
    args_list = args_env.split() if args_env else [
        "--disable-blink-features=AutomationControlled",
        "--no-sandbox",
    ]
    viewport_env = _parse_viewport(os.getenv("ANTI_BOT_VIEWPORT"))
    return {
        "enable": _parse_bool(os.getenv("ANTI_BOT_ENABLE"), True),
        "args": args_list,
        "init_script": os.getenv("ANTI_BOT_INIT_SCRIPT", init_script_default),
        "user_agent": os.getenv("ANTI_BOT_USER_AGENT", ua_default),
        "viewport": viewport_env or viewport_default,
        "device_scale_factor": float(os.getenv("ANTI_BOT_DEVICE_SCALE", "2")),
        "has_touch": _parse_bool(os.getenv("ANTI_BOT_HAS_TOUCH"), False),
        "is_mobile": _parse_bool(os.getenv("ANTI_BOT_IS_MOBILE"), False),
        "locale": os.getenv("ANTI_BOT_LOCALE", "en-US"),
        "timezone_id": os.getenv("ANTI_BOT_TIMEZONE", "America/Los_Angeles"),
    }

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
