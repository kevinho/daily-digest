import pytest
from src.browser import _extract_twitter_meta, _host, _cache_get, _cache_set, _PAGE_CACHE


class TestExtractTwitterMeta:
    """Test _extract_twitter_meta for extracting content from HTML meta tags."""

    def test_extract_from_oembed_title(self):
        """Should extract title and text from oembed link title attribute."""
        html = '''
        <html><head>
        <link href="https://publish.x.com/oembed?url=..." rel="alternate" 
              title="Demis Hassabis on X: &quot;Amazing work from the incredibly talented Director&quot; / X" 
              type="application/json+oembed">
        </head></html>
        '''
        result = _extract_twitter_meta(html)
        assert result["title"] == 'Demis Hassabis on X: "Amazing work from the incredibly talented Director" / X'
        assert result["text"] == "Amazing work from the incredibly talented Director"

    def test_extract_from_oembed_alternate_order(self):
        """Should extract even when attributes are in different order."""
        html = '''
        <html><head>
        <link title="Author on X: &quot;Hello world&quot; / X" 
              type="application/json+oembed"
              href="https://publish.x.com/oembed">
        </head></html>
        '''
        result = _extract_twitter_meta(html)
        assert result["title"] == 'Author on X: "Hello world" / X'
        assert result["text"] == "Hello world"

    def test_extract_from_og_title(self):
        """Should fallback to og:title if oembed not found."""
        html = '''
        <html><head>
        <meta property="og:title" content="User on X: &quot;Test tweet&quot; / X">
        </head></html>
        '''
        result = _extract_twitter_meta(html)
        assert result["title"] == 'User on X: "Test tweet" / X'
        assert result["text"] == "Test tweet"

    def test_extract_complex_tweet(self):
        """Should handle complex tweet with emojis and special chars."""
        html = '''
        <html><head>
        <link type="application/json+oembed" 
              title="Demis Hassabis on X: &quot;&#39;The Thinking Game&#39; documentary has just passed 200M views! 🤯 https://t.co/test&quot; / X"
              href="https://publish.x.com/oembed">
        </head></html>
        '''
        result = _extract_twitter_meta(html)
        assert "200M views" in result["text"]
        assert "🤯" in result["text"]

    def test_no_meta_tags(self):
        """Should return None values when no meta tags found."""
        html = '<html><head></head><body>Hello</body></html>'
        result = _extract_twitter_meta(html)
        assert result["title"] is None
        assert result["text"] is None

    def test_html_entity_decoding(self):
        """Should decode HTML entities properly."""
        html = '''
        <html><head>
        <link type="application/json+oembed" 
              title="User on X: &quot;&lt;150ms time-to-first-sound&quot; / X"
              href="test">
        </head></html>
        '''
        result = _extract_twitter_meta(html)
        assert "<150ms" in result["text"]


class TestHost:
    """Test _host helper function."""

    def test_extract_hostname(self):
        assert _host("https://x.com/user/status/123") == "x.com"
        assert _host("https://twitter.com/user") == "twitter.com"
        assert _host("https://example.com/page") == "example.com"

    def test_empty_url(self):
        assert _host("") == ""
        assert _host(None) == ""

    def test_invalid_url(self):
        assert _host("not a url") == ""


class TestPageCache:
    """Test page cache functions."""

    def setup_method(self):
        _PAGE_CACHE.clear()

    def test_cache_set_and_get(self):
        _cache_set("https://example.com", "title", "Test Title")
        assert _cache_get("https://example.com", "title") == "Test Title"

    def test_cache_get_missing(self):
        assert _cache_get("https://notcached.com", "title") is None

    def test_cache_multiple_keys(self):
        _cache_set("https://test.com", "title", "My Title")
        _cache_set("https://test.com", "text", "My Text")
        assert _cache_get("https://test.com", "title") == "My Title"
        assert _cache_get("https://test.com", "text") == "My Text"

    def test_cache_set_none_value_ignored(self):
        _cache_set("https://test.com", "title", None)
        assert _cache_get("https://test.com", "title") is None


@pytest.mark.asyncio
async def test_placeholder_browser_fetch():
    # Placeholder: ensure module imports
    assert True
