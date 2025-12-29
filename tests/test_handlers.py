"""Tests for platform handlers."""
import pytest

from src.handlers.base import BaseHandler
from src.handlers.registry import get_handler, register_handler, get_all_handlers, clear_handlers
from src.handlers.twitter import TwitterHandler, extract_tweet_id_from_url
from src.handlers.generic import GenericHandler
from src.handlers.pdf import PDFHandler


class TestBaseHandler:
    """Test BaseHandler abstract class."""
    
    def test_matches_requires_url_and_patterns(self):
        """matches() should return False for empty URL or patterns."""
        class TestHandler(BaseHandler):
            name = "test"
            patterns = []
            
            async def extract(self, page, url):
                return (None, None)
        
        assert TestHandler.matches("") is False
        assert TestHandler.matches("http://example.com") is False  # Empty patterns
    
    def test_repr(self):
        """Handler should have a readable repr."""
        handler = TwitterHandler()
        assert "TwitterHandler" in repr(handler)
        assert "patterns" in repr(handler)


class TestTwitterHandler:
    """Test TwitterHandler."""
    
    def test_matches_twitter_com(self):
        assert TwitterHandler.matches("https://twitter.com/user/status/123")
        assert TwitterHandler.matches("https://www.twitter.com/user/status/123")
    
    def test_matches_x_com(self):
        assert TwitterHandler.matches("https://x.com/user/status/123")
        assert TwitterHandler.matches("https://www.x.com/user/status/123")
    
    def test_does_not_match_others(self):
        assert not TwitterHandler.matches("https://example.com")
        assert not TwitterHandler.matches("https://facebook.com")
        assert not TwitterHandler.matches("https://xcom.example.com")  # Not x.com
    
    def test_extract_tweet_id(self):
        assert extract_tweet_id_from_url("https://x.com/user/status/123456789") == "123456789"
        assert extract_tweet_id_from_url("https://twitter.com/user/status/987654321") == "987654321"
    
    def test_extract_tweet_id_with_query_params(self):
        url = "https://x.com/user/status/123456789?s=12&t=xyz"
        assert extract_tweet_id_from_url(url) == "123456789"
    
    def test_extract_tweet_id_empty_url(self):
        assert extract_tweet_id_from_url("") is None
        assert extract_tweet_id_from_url(None) is None
    
    def test_handler_name(self):
        handler = TwitterHandler()
        assert handler.name == "twitter"


class TestGenericHandler:
    """Test GenericHandler."""
    
    def test_matches_anything(self):
        """GenericHandler should match any URL (fallback)."""
        assert GenericHandler.matches("https://example.com")
        assert GenericHandler.matches("https://any-site.org/page")
        assert GenericHandler.matches("")  # Even empty (always True)
    
    def test_handler_name(self):
        handler = GenericHandler()
        assert handler.name == "generic"


class TestPDFHandler:
    """Test PDFHandler."""
    
    def test_matches_pdf_extension(self):
        assert PDFHandler.matches("https://example.com/doc.pdf")
        assert PDFHandler.matches("https://example.com/path/to/file.PDF")
    
    def test_matches_pdf_with_query(self):
        assert PDFHandler.matches("https://example.com/doc.pdf?token=abc")
    
    def test_does_not_match_non_pdf(self):
        assert not PDFHandler.matches("https://example.com/page.html")
        assert not PDFHandler.matches("https://example.com/image.jpg")
        assert not PDFHandler.matches("")
    
    def test_extract_filename_simple(self):
        assert PDFHandler.extract_filename("https://example.com/report.pdf") == "report.pdf"
    
    def test_extract_filename_with_path(self):
        assert PDFHandler.extract_filename("https://example.com/docs/2024/annual-report.pdf") == "annual-report.pdf"
    
    def test_extract_filename_with_query(self):
        assert PDFHandler.extract_filename("https://example.com/doc.pdf?token=xyz") == "doc.pdf"
    
    def test_extract_filename_url_encoded(self):
        result = PDFHandler.extract_filename("https://example.com/my%20document.pdf")
        assert result == "my document.pdf"
    
    def test_extract_filename_fallback(self):
        # No .pdf in path, should use domain fallback
        result = PDFHandler.extract_filename("https://example.com/download/12345")
        assert "example.com" in result
    
    def test_handler_name(self):
        handler = PDFHandler()
        assert handler.name == "pdf"


class TestHandlerRegistry:
    """Test handler registration and lookup."""
    
    def test_get_handler_returns_twitter_for_twitter_url(self):
        handler = get_handler("https://x.com/user/status/123")
        assert isinstance(handler, TwitterHandler)
    
    def test_get_handler_returns_generic_for_unknown_url(self):
        handler = get_handler("https://example.com/page")
        assert isinstance(handler, GenericHandler)
    
    def test_get_handler_returns_generic_for_empty_url(self):
        handler = get_handler("")
        assert isinstance(handler, GenericHandler)
    
    def test_get_all_handlers(self):
        """Should return list of registered handlers."""
        handlers = get_all_handlers()
        assert TwitterHandler in handlers
    
    def test_clear_and_register(self):
        """Test clearing and re-registering handlers."""
        # Save current state
        original_handlers = get_all_handlers().copy()
        
        # Clear
        clear_handlers()
        assert len(get_all_handlers()) == 0
        
        # Fallback should still work
        handler = get_handler("https://x.com/user/status/123")
        assert isinstance(handler, GenericHandler)  # Falls back
        
        # Re-register
        register_handler(TwitterHandler)
        assert TwitterHandler in get_all_handlers()
        
        # Now Twitter should match
        handler = get_handler("https://x.com/user/status/123")
        assert isinstance(handler, TwitterHandler)
        
        # Restore original handlers
        clear_handlers()
        for h in original_handlers:
            register_handler(h)

