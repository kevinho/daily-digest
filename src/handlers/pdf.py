"""
PDF handler for PDF files.

Extracts filename from URL and marks as ready.
No content extraction (future OCR support planned).
"""
import logging
import re
from typing import Optional, Tuple
from urllib.parse import urlparse, unquote

from src.handlers.base import BaseHandler
from src.handlers.registry import register_handler

logger = logging.getLogger(__name__)


@register_handler
class PDFHandler(BaseHandler):
    """
    Handler for PDF files.
    
    Extracts title from URL filename.
    Does not extract content (future OCR support).
    """
    
    name: str = "pdf"
    patterns: list = []  # Selected by ContentType, not URL pattern
    
    @classmethod
    def matches(cls, url: str) -> bool:
        """Check if URL points to a PDF file."""
        if not url:
            return False
        try:
            parsed = urlparse(url.lower())
            path = parsed.path
            # Check if URL path ends with .pdf
            if path.endswith(".pdf"):
                return True
            # Check query params for pdf
            if "pdf" in parsed.query.lower():
                return True
            return False
        except Exception:
            return False
    
    async def extract(self, page, url: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract title from PDF URL.
        
        Returns:
            Tuple of (title from filename, None for content)
        """
        title = self.extract_filename(url)
        logger.debug(f"PDFHandler: extracted title '{title}' from {url}")
        return (title, None)
    
    @staticmethod
    def extract_filename(url: str) -> Optional[str]:
        """
        Extract filename from PDF URL.
        
        Handles various URL patterns:
        - Direct: /path/to/file.pdf
        - Google Docs: /export?format=pdf&id=xxx
        - With query params: /file.pdf?token=xxx
        """
        if not url:
            return None
        
        try:
            parsed = urlparse(url)
            path = unquote(parsed.path)  # URL decode
            
            # Get last path segment
            segments = [s for s in path.split("/") if s]
            if not segments:
                return None
            
            filename = segments[-1]
            
            # Remove query string if it leaked through
            if "?" in filename:
                filename = filename.split("?")[0]
            
            # If filename ends with .pdf, use it
            if filename.lower().endswith(".pdf"):
                return filename[:140]
            
            # Try to find .pdf anywhere in the path
            for seg in reversed(segments):
                if seg.lower().endswith(".pdf"):
                    return seg[:140]
            
            # Check query params for filename
            query = parsed.query
            if query:
                # Look for filename= or name= params
                for pattern in [r'filename=([^&]+\.pdf)', r'name=([^&]+\.pdf)', r'file=([^&]+\.pdf)']:
                    match = re.search(pattern, query, re.IGNORECASE)
                    if match:
                        return unquote(match.group(1))[:140]
            
            # Fallback: use domain + pdf
            hostname = parsed.hostname or ""
            return f"PDF from {hostname}"[:140] if hostname else None
            
        except Exception as e:
            logger.debug(f"Failed to extract PDF filename: {e}")
            return None
    
    async def wait_for_content(self, page) -> bool:
        """No waiting needed for PDF handler."""
        return True

