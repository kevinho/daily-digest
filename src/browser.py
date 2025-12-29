import asyncio
from typing import Callable, Dict, Optional, TypeVar

try:
    from tenacity import retry, stop_after_attempt, wait_exponential
except ImportError:
    # Fallback no-op decorators if tenacity is not installed (e.g., in lightweight test env)
    T = TypeVar("T")

    def _identity(x: T) -> T:
        return x

    def retry(*args, **kwargs):  # type: ignore
        def wrapper(fn: Callable[..., T]) -> Callable[..., T]:
            return fn

        return wrapper

    def stop_after_attempt(*args, **kwargs):  # type: ignore
        return None

    def wait_exponential(*args, **kwargs):  # type: ignore
        return None


from src.utils import get_antibot_settings


def _page_options(override: Optional[Dict] = None) -> Dict:
    base = get_antibot_settings()
    if override:
        base.update(override)
    return base


BLOCK_MARKERS = [
    "javascript is disabled",
    "enable javascript",
    "continue using x.com",
    "登录后查看",
    "sign in to x",
]


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, min=1, max=4))
async def fetch_page_content(
    url: str,
    cdp_url: str = "http://localhost:9222",
    timeout_ms: int = 15000,
    anti_bot: Optional[bool] = None,
    page_options: Optional[Dict] = None,
) -> Optional[str]:
    # Lazy import to avoid hard dependency at module import time (helps tests without playwright installed)
    try:
        from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
    except ImportError as exc:
        raise RuntimeError("playwright is required to fetch page content") from exc

    try:
        import trafilatura
    except ImportError as exc:
        raise RuntimeError("trafilatura is required to extract text") from exc

    opts = _page_options(page_options)
    anti_bot_enabled = opts.get("enable") if anti_bot is None else anti_bot

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(cdp_url)
        context = await browser.new_context(
            user_agent=opts.get("user_agent"),
            viewport=opts.get("viewport"),
            device_scale_factor=opts.get("device_scale_factor"),
            has_touch=opts.get("has_touch"),
            is_mobile=opts.get("is_mobile"),
            locale=opts.get("locale"),
            timezone_id=opts.get("timezone_id"),
        )
        page = await context.new_page()
        if anti_bot_enabled and opts.get("init_script"):
            await context.add_init_script(opts["init_script"])
        try:
            await page.goto(url, wait_until="load", timeout=timeout_ms)
            html = await page.content()
            if any(marker in html.lower() for marker in BLOCK_MARKERS):
                raise RuntimeError("blocked: login/JS wall detected")
            text = trafilatura.extract(html)
            return text
        except PlaywrightTimeoutError:
            return None
        finally:
            await page.close()
            await context.close()
            await browser.close()


def fetch_page_content_sync(url: str, cdp_url: str = "http://localhost:9222", timeout_ms: int = 15000) -> Optional[str]:
    return asyncio.get_event_loop().run_until_complete(fetch_page_content(url, cdp_url, timeout_ms))
