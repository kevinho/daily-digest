import asyncio
from typing import Callable, Dict, Optional, TypeVar
from urllib.parse import urlparse

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

_PAGE_CACHE: Dict[str, Dict[str, str]] = {}


def _host(url: str) -> str:
    try:
        return urlparse(url).hostname or ""
    except Exception:
        return ""


async def _extract_twitter_text(page) -> Optional[str]:
    """Best-effort extractor for X/Twitter."""
    tweet_locator = page.locator('div[data-testid="tweetText"]')
    tweet_count = await tweet_locator.count()
    if tweet_count > 0:
        parts = []
        for i in range(tweet_count):
            parts.append((await tweet_locator.nth(i).inner_text()).strip())
        joined = "\n".join(p for p in parts if p)
        if joined:
            return joined
    # Fallback to main role text
    try:
        main_loc = page.locator('main[role="main"]')
        if await main_loc.count() > 0:
            main_text = (await main_loc.inner_text()).strip()
            if main_text:
                return main_text
    except Exception:
        pass
    return None


async def _extract_text_by_host(page, html: str, url: str) -> Optional[str]:
    host = _host(url).lower()
    if "x.com" in host or "twitter.com" in host:
        text = await _extract_twitter_text(page)
        if text:
            return text
    return None


def _cache_get(url: str, key: str) -> Optional[str]:
    entry = _PAGE_CACHE.get(url)
    if entry:
        return entry.get(key)
    return None


def _cache_set(url: str, key: str, value: Optional[str]) -> None:
    if value is None:
        return
    if url not in _PAGE_CACHE:
        _PAGE_CACHE[url] = {}
    _PAGE_CACHE[url][key] = value


def _wait_delay_ms(url: str) -> int:
    """Return extra wait (ms) after navigation for dynamic pages."""
    host = (url or "").lower()
    if "x.com" in host or "twitter.com" in host:
        return 10000
    return 1500


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
    "we've detected that javascript is disabled",
    "something went wrong",
]


def _retry_kwargs(kind: str) -> Dict:
    """Unified retry config from env with sensible defaults."""
    attempts = get_int("PAGE_FETCH_RETRIES", 1)
    if kind == "title":
        attempts = get_int("PAGE_TITLE_RETRIES", attempts)
    return {
        "stop": stop_after_attempt(max(1, attempts)),
        "wait": wait_exponential(multiplier=0.5, min=1, max=4),
    }


async def fetch_page_content(
    url: str,
    cdp_url: str = "http://localhost:9222",
    timeout_ms: int = 15000,
    anti_bot: Optional[bool] = None,
    page_options: Optional[Dict] = None,
) -> Optional[str]:
    # Serve from cache if available
    cached_text = _cache_get(url, "text")
    if cached_text:
        return cached_text

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

    retry_kwargs = _retry_kwargs("content")

    @retry(**retry_kwargs)
    async def _run() -> Optional[str]:
        async with async_playwright() as p:
            browser = await p.chromium.connect_over_cdp(cdp_url)
            contexts = browser.contexts
            created_context = False
            if contexts:
                context = contexts[0]
            else:
                context = await browser.new_context(
                    user_agent=opts.get("user_agent"),
                    viewport=opts.get("viewport"),
                    device_scale_factor=opts.get("device_scale_factor"),
                    has_touch=opts.get("has_touch"),
                    is_mobile=opts.get("is_mobile"),
                    locale=opts.get("locale"),
                    timezone_id=opts.get("timezone_id"),
                )
                created_context = True
            page = await context.new_page()
            if anti_bot_enabled and opts.get("init_script"):
                await context.add_init_script(opts["init_script"])
            try:
                await page.goto(url, wait_until="load", timeout=timeout_ms)
                await page.wait_for_timeout(_wait_delay_ms(url))
                html = await page.content()
                if any(marker in html.lower() for marker in BLOCK_MARKERS):
                    raise RuntimeError("blocked: login/JS wall detected")
                # Host-specific extractor (e.g., Twitter)
                host_text = await _extract_text_by_host(page, html, url)
                if host_text:
                    _cache_set(url, "text", host_text)
                    return host_text

                text = trafilatura.extract(html)
                if text:
                    _cache_set(url, "text", text)
                return text
            except PlaywrightTimeoutError:
                return None
            finally:
                await page.close()
                if created_context:
                    await context.close()

    return await _run()


async def fetch_page_title(
    url: str,
    cdp_url: str = "http://localhost:9222",
    timeout_ms: int = 15000,
    anti_bot: Optional[bool] = None,
    page_options: Optional[Dict] = None,
) -> Optional[str]:
    """Fetch page <title> via CDP, honoring anti-bot settings."""
    cached_title = _cache_get(url, "title")
    if cached_title:
        return cached_title

    retry_kwargs = _retry_kwargs("title")

    async def _run() -> Optional[str]:
        try:
            from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
        except ImportError as exc:
            raise RuntimeError("playwright is required to fetch page title") from exc

        opts = _page_options(page_options)
        anti_bot_enabled = opts.get("enable") if anti_bot is None else anti_bot

        async with async_playwright() as p:
            browser = await p.chromium.connect_over_cdp(cdp_url)
            contexts = browser.contexts
            created_context = False
            if contexts:
                context = contexts[0]
            else:
                context = await browser.new_context(
                    user_agent=opts.get("user_agent"),
                    viewport=opts.get("viewport"),
                    device_scale_factor=opts.get("device_scale_factor"),
                    has_touch=opts.get("has_touch"),
                    is_mobile=opts.get("is_mobile"),
                    locale=opts.get("locale"),
                    timezone_id=opts.get("timezone_id"),
                )
                created_context = True
            page = await context.new_page()
            if anti_bot_enabled and opts.get("init_script"):
                await context.add_init_script(opts["init_script"])
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
                # Allow dynamic head/meta to settle (slow pages like X may need longer)
                await page.wait_for_timeout(_wait_delay_ms(url))
                candidates = await page.evaluate(
                    """() => {
                        const vals = [];
                        const push = (v) => { if (v && typeof v === 'string' && v.trim()) vals.push(v.trim()); };
                        const pickMeta = (key) => {
                            const el = document.querySelector(`meta[property="${key}"]`) || document.querySelector(`meta[name="${key}"]`);
                            return el ? (el.content || el.getAttribute('content') || '') : '';
                        };
                        push(pickMeta('og:title'));
                        push(pickMeta('twitter:title'));
                        push(pickMeta('title'));
                        push(document.title || '');
                        return vals;
                    }"""
                )
                generic = {"something went wrong", "x.com", "javascript is disabled"}
                chosen = None
                for t in candidates:
                    low = t.lower()
                    if any(g in low for g in generic):
                        continue
                    chosen = t
                    break
                title = chosen or (await page.title())

                # Best-effort: also extract text and cache it, to avoid re-open in content fetch
                html = await page.content()
                extracted_text = await _extract_text_by_host(page, html, url)
                if extracted_text:
                    _cache_set(url, "text", extracted_text)

                if title:
                    _cache_set(url, "title", title)
                return title
            except PlaywrightTimeoutError:
                return None
            finally:
                await page.close()
                if created_context:
                    await context.close()

    # Apply retry wrapper explicitly for title fetch
    wrapped = retry(**retry_kwargs)(_run)
    return await wrapped()


def fetch_page_content_sync(url: str, cdp_url: str = "http://localhost:9222", timeout_ms: int = 15000) -> Optional[str]:
    return asyncio.get_event_loop().run_until_complete(fetch_page_content(url, cdp_url, timeout_ms))
