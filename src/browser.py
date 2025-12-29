import asyncio
from enum import Enum
from typing import Callable, Dict, Optional, Tuple, TypeVar
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


from src.utils import get_antibot_settings, get_int


# ================================================================
# Twitter Smart Wait - Result Types and Exceptions
# ================================================================

class TwitterWaitResult(Enum):
    """Result types for Twitter smart wait operation."""
    SUCCESS = "success"
    LOGIN_WALL = "login_wall"
    SERVER_ERROR = "server_error"
    TIMEOUT = "timeout"


class TwitterFetchError(Exception):
    """Base error for Twitter fetching."""
    pass


class TwitterLoginWallError(TwitterFetchError):
    """Twitter login wall detected."""
    pass


class TwitterServerError(TwitterFetchError):
    """Twitter server error detected."""
    pass


# Twitter element selectors
TWITTER_CONTENT_SELECTOR = 'div[data-testid="tweetText"], article[data-testid="tweet"]'
TWITTER_LOGIN_SELECTOR = '[data-testid="login"]'
TWITTER_ERROR_SELECTOR = 'span:has-text("Something went wrong")'

_PAGE_CACHE: Dict[str, Dict[str, str]] = {}


def _host(url: str) -> str:
    try:
        return urlparse(url).hostname or ""
    except Exception:
        return ""


def _extract_twitter_meta(html: str) -> dict:
    """
    Extract Twitter content from meta tags (instant, no DOM wait needed).
    
    Returns dict with:
      - title: from og:title or oembed title attribute
      - text: tweet body extracted from oembed title (content after ": " and before "/ X")
    """
    import re
    result = {"title": None, "text": None}
    
    # Priority 1: oembed link title attribute (contains full content)
    # Format: <link type="application/json+oembed" title="Author on X: &quot;content&quot; / X" ...>
    oembed_match = re.search(
        r'<link[^>]+type=["\']application/json\+oembed["\'][^>]+title=["\']([^"\']+)["\']',
        html,
        re.IGNORECASE
    )
    if not oembed_match:
        # Try alternate attribute order
        oembed_match = re.search(
            r'<link[^>]+title=["\']([^"\']+)["\'][^>]+type=["\']application/json\+oembed["\']',
            html,
            re.IGNORECASE
        )
    
    if oembed_match:
        raw_title = oembed_match.group(1)
        # Decode HTML entities
        import html as html_module
        decoded = html_module.unescape(raw_title)
        result["title"] = decoded
        
        # Extract tweet body: after first ": " or ": \"" and before " / X" or "\" / X"
        # Pattern: "Author on X: "content here" / X"
        body_match = re.search(r':\s*["\']?(.+?)["\']?\s*/\s*X$', decoded)
        if body_match:
            result["text"] = body_match.group(1).strip().strip('"\'')
    
    # Priority 2: og:title meta tag (fallback for title)
    if not result["title"]:
        og_match = re.search(
            r'<meta[^>]+(?:property|name)=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']',
            html,
            re.IGNORECASE
        )
        if not og_match:
            og_match = re.search(
                r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\']og:title["\']',
                html,
                re.IGNORECASE
            )
        if og_match:
            import html as html_module
            result["title"] = html_module.unescape(og_match.group(1))
            # Try extract body from og:title too
            if not result["text"]:
                body_match = re.search(r':\s*["\']?(.+?)["\']?\s*/\s*X$', result["title"])
                if body_match:
                    result["text"] = body_match.group(1).strip().strip('"\'')
    
    return result


async def _extract_twitter_dom(page) -> Optional[str]:
    """DOM-based extractor for X/Twitter (requires page wait)."""
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


async def _extract_twitter_hybrid(page, html: str) -> dict:
    """
    Hybrid Twitter extraction: Meta tags first, DOM fallback.
    
    Returns dict with 'title' and 'text' keys.
    """
    result = {"title": None, "text": None}
    
    # Step 1: Try instant meta tag extraction
    meta = _extract_twitter_meta(html)
    result["title"] = meta.get("title")
    result["text"] = meta.get("text")
    
    # Step 2: If text is missing or too short, try DOM extraction
    if not result["text"] or len(result["text"]) < 10:
        dom_text = await _extract_twitter_dom(page)
        if dom_text:
            result["text"] = dom_text
    
    return result


async def _extract_text_by_host(page, html: str, url: str) -> Optional[str]:
    """Extract text using host-specific strategies."""
    host = _host(url).lower()
    if "x.com" in host or "twitter.com" in host:
        hybrid = await _extract_twitter_hybrid(page, html)
        return hybrid.get("text")
    return None


def _get_twitter_wait_ms() -> int:
    """
    Get Twitter-specific wait time from env, default 10000ms.
    
    DEPRECATED: Use _twitter_smart_wait() instead for deterministic waiting.
    This function is kept for backward compatibility but returns 0 when
    smart wait is enabled.
    """
    return 0  # Smart wait handles timing now


async def _twitter_smart_wait(
    page,
    content_timeout_ms: int = 15000,
    login_timeout_ms: int = 2000,
    error_timeout_ms: int = 3000,
) -> Tuple[TwitterWaitResult, str]:
    """
    Smart wait for Twitter content with fast failure detection.
    
    Uses parallel waiting to detect:
    - Tweet content (success case)
    - Login wall (fast failure)
    - Server error (fast failure)
    
    Args:
        page: Playwright page object
        content_timeout_ms: Max wait for content (default 15s)
        login_timeout_ms: Max wait for login wall detection (default 2s)
        error_timeout_ms: Max wait for error detection (default 3s)
        
    Returns:
        Tuple of (TwitterWaitResult, message)
    """
    try:
        # Create tasks for parallel detection
        content_task = asyncio.create_task(
            page.wait_for_selector(TWITTER_CONTENT_SELECTOR, timeout=content_timeout_ms)
        )
        login_task = asyncio.create_task(
            page.wait_for_selector(TWITTER_LOGIN_SELECTOR, timeout=login_timeout_ms)
        )
        error_task = asyncio.create_task(
            page.wait_for_selector(TWITTER_ERROR_SELECTOR, timeout=error_timeout_ms)
        )
        
        # Wait for first to complete (success or fast failure)
        done, pending = await asyncio.wait(
            [content_task, login_task, error_task],
            return_when=asyncio.FIRST_COMPLETED,
        )
        
        # Cancel pending tasks to avoid warnings
        for task in pending:
            task.cancel()
            try:
                await task
            except (asyncio.CancelledError, Exception):
                pass
        
        # Check which task completed first
        completed_task = done.pop()
        try:
            result = completed_task.result()
            # Task completed successfully (found element)
            if completed_task is content_task:
                return (TwitterWaitResult.SUCCESS, "Content loaded")
            elif completed_task is login_task:
                return (TwitterWaitResult.LOGIN_WALL, "Login Wall Detected")
            elif completed_task is error_task:
                return (TwitterWaitResult.SERVER_ERROR, "Twitter Server Error: Something went wrong")
        except Exception:
            # Task raised exception (timeout or other)
            pass
        
        # If we get here, first completed task had an error
        # Wait a bit more for content as fallback
        try:
            await page.wait_for_selector(TWITTER_CONTENT_SELECTOR, timeout=5000)
            return (TwitterWaitResult.SUCCESS, "Content loaded (delayed)")
        except Exception:
            return (TwitterWaitResult.TIMEOUT, "Content Not Found (timeout)")
            
    except Exception as e:
        return (TwitterWaitResult.TIMEOUT, f"Smart wait failed: {e}")


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
    """
    Return extra wait (ms) after navigation for dynamic pages.
    
    For Twitter: returns 0 because _twitter_smart_wait() handles timing.
    For other sites: returns 1500ms default delay.
    """
    host = (url or "").lower()
    if "x.com" in host or "twitter.com" in host:
        return 0  # Smart wait handles Twitter timing
    return 1500


def _page_options(override: Optional[Dict] = None) -> Dict:
    base = get_antibot_settings()
    if override:
        base.update(override)
    return base


def extract_tweet_id_from_url(url: str) -> Optional[str]:
    """Extract tweet ID from Twitter/X URL."""
    if not url:
        return None
    parts = url.split("/")
    # Look for numeric ID after 'status'
    for i, part in enumerate(parts):
        if part == "status" and i + 1 < len(parts):
            candidate = parts[i + 1].split("?")[0]  # Remove query params
            if candidate.isdigit():
                return candidate
    # Fallback: last numeric segment
    for part in reversed(parts):
        cleaned = part.split("?")[0]
        if cleaned.isdigit():
            return cleaned
    return None


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
                
                # Host-specific extractor (e.g., Twitter) with hybrid strategy
                host = _host(url).lower()
                is_twitter = "x.com" in host or "twitter.com" in host
                
                if is_twitter:
                    # Smart wait for Twitter content with fast failure detection
                    wait_result, wait_message = await _twitter_smart_wait(page)
                    
                    if wait_result == TwitterWaitResult.LOGIN_WALL:
                        raise TwitterLoginWallError(wait_message)
                    elif wait_result == TwitterWaitResult.SERVER_ERROR:
                        raise TwitterServerError(wait_message)
                    # For SUCCESS or TIMEOUT, continue to try meta extraction
                    
                    html = await page.content()
                    
                    # Try Meta extraction (works even after timeout as fallback)
                    hybrid = await _extract_twitter_hybrid(page, html)
                    if hybrid.get("text"):
                        _cache_set(url, "text", hybrid["text"])
                    if hybrid.get("title"):
                        _cache_set(url, "title", hybrid["title"])
                    if hybrid.get("text"):
                        return hybrid["text"]
                    
                    # If smart wait timed out and no meta content, report error
                    if wait_result == TwitterWaitResult.TIMEOUT:
                        raise RuntimeError(f"Twitter content not found: {wait_message}")
                    
                    # Only check block markers if Meta extraction failed
                    if any(marker in html.lower() for marker in BLOCK_MARKERS):
                        raise RuntimeError("blocked: login/JS wall detected (no Meta content)")
                else:
                    # For non-Twitter: use simple delay then extract
                    await page.wait_for_timeout(_wait_delay_ms(url))
                    html = await page.content()
                    
                    # Check block markers first
                    if any(marker in html.lower() for marker in BLOCK_MARKERS):
                        raise RuntimeError("blocked: login/JS wall detected")
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
                host = _host(url).lower()
                if "x.com" in host or "twitter.com" in host:
                    # Use hybrid extraction for Twitter
                    hybrid = await _extract_twitter_hybrid(page, html)
                    if hybrid.get("text"):
                        _cache_set(url, "text", hybrid["text"])
                    # Prefer hybrid title over generic meta extraction
                    if hybrid.get("title") and not title:
                        title = hybrid["title"]
                else:
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
