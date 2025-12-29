"""
Twitter/X handler with Smart Waiters.

Specialized extraction for Twitter/X.com with:
- Smart wait for content with fast failure detection
- Meta tag extraction (instant, no DOM wait)
- DOM-based fallback extraction
"""
import asyncio
import logging
import re
from enum import Enum
from typing import Optional, Tuple
import html as html_module

from src.handlers.base import BaseHandler
from src.handlers.registry import register_handler

logger = logging.getLogger(__name__)


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


# Element selectors
CONTENT_SELECTOR = 'div[data-testid="tweetText"], article[data-testid="tweet"]'
LOGIN_SELECTOR = '[data-testid="login"]'
ERROR_SELECTOR = 'span:has-text("Something went wrong")'


@register_handler
class TwitterHandler(BaseHandler):
    """
    Handler for Twitter/X content extraction.
    
    Features:
    - Smart Waiters for fast content detection / error detection
    - Hybrid extraction: meta tags first, DOM fallback
    - Handles login walls and server errors gracefully
    """
    
    name: str = "twitter"
    patterns: list = [r"twitter\.com", r"x\.com"]
    
    async def extract(self, page, url: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract title and content from Twitter page.
        
        Uses hybrid strategy:
        1. Try meta tag extraction (instant)
        2. Fall back to DOM extraction if needed
        
        Args:
            page: Playwright Page object
            url: URL being processed
            
        Returns:
            Tuple of (title, content)
            
        Raises:
            TwitterLoginWallError: If login wall detected
            TwitterServerError: If server error detected
        """
        # Smart wait with fast failure detection
        wait_result, wait_message = await self._smart_wait(page)
        
        if wait_result == TwitterWaitResult.LOGIN_WALL:
            raise TwitterLoginWallError(wait_message)
        elif wait_result == TwitterWaitResult.SERVER_ERROR:
            raise TwitterServerError(wait_message)
        
        # Get page HTML for meta extraction
        html = await page.content()
        
        # Hybrid extraction
        title, content = await self._extract_hybrid(page, html)
        
        # If smart wait timed out and no content, treat as error
        if wait_result == TwitterWaitResult.TIMEOUT and not content:
            logger.warning(f"Twitter content not found: {wait_message}")
            # Still return what we have (may have meta content)
        
        return (title, content)
    
    async def wait_for_content(self, page) -> bool:
        """Smart wait for Twitter content."""
        result, _ = await self._smart_wait(page)
        return result == TwitterWaitResult.SUCCESS
    
    async def _smart_wait(
        self,
        page,
        content_timeout_ms: int = 15000,
        login_timeout_ms: int = 2000,
        error_timeout_ms: int = 3000,
    ) -> Tuple[TwitterWaitResult, str]:
        """
        Smart wait with parallel detection of content/errors.
        
        Returns first detected state:
        - Content found → SUCCESS
        - Login wall → LOGIN_WALL
        - Server error → SERVER_ERROR
        - Timeout → TIMEOUT
        """
        try:
            # Create parallel detection tasks
            content_task = asyncio.create_task(
                page.wait_for_selector(CONTENT_SELECTOR, timeout=content_timeout_ms)
            )
            login_task = asyncio.create_task(
                page.wait_for_selector(LOGIN_SELECTOR, timeout=login_timeout_ms)
            )
            error_task = asyncio.create_task(
                page.wait_for_selector(ERROR_SELECTOR, timeout=error_timeout_ms)
            )
            
            # Wait for first completion
            done, pending = await asyncio.wait(
                [content_task, login_task, error_task],
                return_when=asyncio.FIRST_COMPLETED,
            )
            
            # Cancel pending tasks
            for task in pending:
                task.cancel()
                try:
                    await task
                except (asyncio.CancelledError, Exception):
                    pass
            
            # Check which completed first
            completed_task = done.pop()
            try:
                completed_task.result()  # Check if successful
                
                if completed_task is content_task:
                    return (TwitterWaitResult.SUCCESS, "Content loaded")
                elif completed_task is login_task:
                    return (TwitterWaitResult.LOGIN_WALL, "Login Wall Detected")
                elif completed_task is error_task:
                    return (TwitterWaitResult.SERVER_ERROR, "Twitter Server Error")
            except Exception:
                pass
            
            # First task had error - try content with shorter timeout
            try:
                await page.wait_for_selector(CONTENT_SELECTOR, timeout=5000)
                return (TwitterWaitResult.SUCCESS, "Content loaded (delayed)")
            except Exception:
                return (TwitterWaitResult.TIMEOUT, "Content Not Found (timeout)")
                
        except Exception as e:
            return (TwitterWaitResult.TIMEOUT, f"Smart wait failed: {e}")
    
    async def _extract_hybrid(self, page, html: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Hybrid extraction: meta tags first, DOM fallback.
        
        Returns:
            Tuple of (title, content)
        """
        # Step 1: Try instant meta tag extraction
        meta = self._extract_meta(html)
        title = meta.get("title")
        content = meta.get("text")
        
        # Step 2: If content missing or too short, try DOM
        if not content or len(content) < 10:
            dom_text = await self._extract_dom(page)
            if dom_text:
                content = dom_text
        
        return (title, content)
    
    def _extract_meta(self, html: str) -> dict:
        """
        Extract content from meta tags (instant, no wait needed).
        
        Tries:
        1. oembed link title attribute (contains full tweet)
        2. og:title meta tag (fallback)
        """
        result = {"title": None, "text": None}
        
        # Priority 1: oembed link title
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
            decoded = html_module.unescape(raw_title)
            result["title"] = decoded
            
            # Extract tweet body: after ": " and before " / X"
            body_match = re.search(r':\s*["\']?(.+?)["\']?\s*/\s*X$', decoded)
            if body_match:
                result["text"] = body_match.group(1).strip().strip('"\'')
        
        # Priority 2: og:title (fallback for title)
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
                result["title"] = html_module.unescape(og_match.group(1))
                # Try extract body from og:title too
                if not result["text"]:
                    body_match = re.search(r':\s*["\']?(.+?)["\']?\s*/\s*X$', result["title"])
                    if body_match:
                        result["text"] = body_match.group(1).strip().strip('"\'')
        
        return result
    
    async def _extract_dom(self, page) -> Optional[str]:
        """DOM-based extraction (requires page wait)."""
        try:
            tweet_locator = page.locator('div[data-testid="tweetText"]')
            tweet_count = await tweet_locator.count()
            
            if tweet_count > 0:
                parts = []
                for i in range(tweet_count):
                    text = (await tweet_locator.nth(i).inner_text()).strip()
                    if text:
                        parts.append(text)
                if parts:
                    return "\n".join(parts)
            
            # Fallback to main role text
            main_loc = page.locator('main[role="main"]')
            if await main_loc.count() > 0:
                main_text = (await main_loc.inner_text()).strip()
                if main_text:
                    return main_text
                    
        except Exception as e:
            logger.debug(f"DOM extraction failed: {e}")
        
        return None


def extract_tweet_id_from_url(url: str) -> Optional[str]:
    """Extract tweet ID from Twitter/X URL."""
    if not url:
        return None
    parts = url.split("/")
    # Look for numeric ID after 'status'
    for i, part in enumerate(parts):
        if part == "status" and i + 1 < len(parts):
            candidate = parts[i + 1].split("?")[0]
            if candidate.isdigit():
                return candidate
    # Fallback: last numeric segment
    for part in reversed(parts):
        cleaned = part.split("?")[0]
        if cleaned.isdigit():
            return cleaned
    return None

