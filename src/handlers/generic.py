"""
Generic HTML handler - fallback for unrecognized domains.

Uses trafilatura for text extraction.
"""
import logging
from typing import Optional, Tuple

from src.handlers.base import BaseHandler

logger = logging.getLogger(__name__)


class GenericHandler(BaseHandler):
    """
    Generic handler for standard HTML pages.
    
    Uses trafilatura for text extraction.
    Matches any URL (fallback handler).
    """
    
    name: str = "generic"
    patterns: list = [".*"]  # Match anything (fallback)
    
    @classmethod
    def matches(cls, url: str) -> bool:
        """Always returns True - this is the fallback handler."""
        return True
    
    async def extract(self, page, url: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract title and content using trafilatura.
        
        Args:
            page: Playwright Page object
            url: URL being processed
            
        Returns:
            Tuple of (title, content)
        """
        try:
            import trafilatura
        except ImportError:
            logger.warning("trafilatura not installed, cannot extract content")
            return (None, None)
        
        try:
            html = await page.content()
            
            # Extract title from meta/title tags
            title = await self._extract_title(page)
            
            # Extract text content using trafilatura
            content = trafilatura.extract(html)
            
            return (title, content)
            
        except Exception as e:
            logger.warning(f"GenericHandler extraction failed for {url}: {e}")
            return (None, None)
    
    async def _extract_title(self, page) -> Optional[str]:
        """Extract title from page meta tags or title element."""
        try:
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
            
            generic_markers = {"something went wrong", "error", "loading"}
            for t in candidates:
                low = t.lower()
                if any(g in low for g in generic_markers):
                    continue
                return t
            
            return candidates[0] if candidates else None
            
        except Exception:
            return None
    
    async def wait_for_content(self, page) -> bool:
        """Wait for generic page content to load."""
        try:
            await page.wait_for_timeout(1500)
            return True
        except Exception:
            return False


# Note: GenericHandler is NOT registered via @register_handler
# It should be returned as fallback by registry.get_handler()

