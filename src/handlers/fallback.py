"""
Fallback handler for non-processable content types.

For content types that cannot be extracted (PDF, IMAGE, VIDEO, AUDIO, BINARY),
this handler simply marks them as ready without actual content extraction.
"""
import logging
from typing import Optional, Tuple

from src.handlers.base import BaseHandler

logger = logging.getLogger(__name__)


class FallbackHandler(BaseHandler):
    """
    Fallback handler for non-processable content.
    
    Does not extract content, just marks item as ready.
    Used for: PDF, IMAGE, VIDEO, AUDIO, BINARY
    """
    
    name: str = "fallback"
    patterns: list = []  # No URL patterns - selected explicitly by ContentType
    
    @classmethod
    def matches(cls, url: str) -> bool:
        """Fallback handler is selected explicitly, not by URL pattern."""
        return False
    
    async def extract(self, page, url: str) -> Tuple[Optional[str], Optional[str]]:
        """
        No-op extraction for non-processable content.
        
        Returns:
            Tuple of (None, None) - no content extracted
        """
        logger.debug(f"FallbackHandler: No extraction for {url}")
        return (None, None)
    
    async def wait_for_content(self, page) -> bool:
        """No waiting needed for fallback handler."""
        return True

