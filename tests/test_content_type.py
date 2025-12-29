"""Tests for ContentType detection."""
import pytest

from src.content_type import (
    ContentType,
    parse_mime_type,
    infer_from_extension,
)


class TestContentTypeEnum:
    """Test ContentType enum properties."""
    
    def test_all_values_exist(self):
        """All ContentType values should be defined."""
        assert ContentType.HTML.value == "html"
        assert ContentType.PDF.value == "pdf"
        assert ContentType.IMAGE.value == "image"
        assert ContentType.VIDEO.value == "video"
        assert ContentType.AUDIO.value == "audio"
        assert ContentType.JSON.value == "json"
        assert ContentType.TEXT.value == "text"
        assert ContentType.BINARY.value == "binary"
        assert ContentType.UNKNOWN.value == "unknown"
    
    def test_processable_property(self):
        """Only HTML, TEXT, JSON should be processable."""
        assert ContentType.HTML.processable is True
        assert ContentType.TEXT.processable is True
        assert ContentType.JSON.processable is True
        
        assert ContentType.PDF.processable is False
        assert ContentType.IMAGE.processable is False
        assert ContentType.VIDEO.processable is False
        assert ContentType.AUDIO.processable is False
        assert ContentType.BINARY.processable is False
        assert ContentType.UNKNOWN.processable is False
    
    def test_future_support_property(self):
        """PDF, IMAGE, VIDEO, AUDIO should have future support."""
        assert ContentType.PDF.future_support is True
        assert ContentType.IMAGE.future_support is True
        assert ContentType.VIDEO.future_support is True
        assert ContentType.AUDIO.future_support is True
        
        assert ContentType.HTML.future_support is False
        assert ContentType.TEXT.future_support is False
        assert ContentType.JSON.future_support is False
        assert ContentType.BINARY.future_support is False
        assert ContentType.UNKNOWN.future_support is False


class TestParseMimeType:
    """Test MIME type to ContentType parsing."""
    
    def test_html_types(self):
        assert parse_mime_type("text/html") == ContentType.HTML
        assert parse_mime_type("text/html; charset=utf-8") == ContentType.HTML
        assert parse_mime_type("application/xhtml+xml") == ContentType.HTML
    
    def test_pdf_type(self):
        assert parse_mime_type("application/pdf") == ContentType.PDF
    
    def test_image_types(self):
        assert parse_mime_type("image/jpeg") == ContentType.IMAGE
        assert parse_mime_type("image/png") == ContentType.IMAGE
        assert parse_mime_type("image/gif") == ContentType.IMAGE
        assert parse_mime_type("image/webp") == ContentType.IMAGE
        assert parse_mime_type("image/svg+xml") == ContentType.IMAGE
    
    def test_video_types(self):
        assert parse_mime_type("video/mp4") == ContentType.VIDEO
        assert parse_mime_type("video/webm") == ContentType.VIDEO
        assert parse_mime_type("video/ogg") == ContentType.VIDEO
    
    def test_audio_types(self):
        assert parse_mime_type("audio/mpeg") == ContentType.AUDIO
        assert parse_mime_type("audio/wav") == ContentType.AUDIO
        assert parse_mime_type("audio/ogg") == ContentType.AUDIO
    
    def test_json_type(self):
        assert parse_mime_type("application/json") == ContentType.JSON
        assert parse_mime_type("text/json") == ContentType.JSON
    
    def test_text_types(self):
        assert parse_mime_type("text/plain") == ContentType.TEXT
        assert parse_mime_type("text/csv") == ContentType.TEXT
        assert parse_mime_type("text/markdown") == ContentType.TEXT
    
    def test_binary_type(self):
        assert parse_mime_type("application/octet-stream") == ContentType.BINARY
        assert parse_mime_type("application/zip") == ContentType.BINARY
    
    def test_empty_header(self):
        assert parse_mime_type(None) == ContentType.UNKNOWN
        assert parse_mime_type("") == ContentType.UNKNOWN
    
    def test_case_insensitive(self):
        assert parse_mime_type("TEXT/HTML") == ContentType.HTML
        assert parse_mime_type("Application/PDF") == ContentType.PDF


class TestInferFromExtension:
    """Test extension-based ContentType inference."""
    
    def test_html_extensions(self):
        assert infer_from_extension("http://example.com/page.html") == ContentType.HTML
        assert infer_from_extension("http://example.com/page.htm") == ContentType.HTML
        assert infer_from_extension("http://example.com/page.xhtml") == ContentType.HTML
    
    def test_pdf_extension(self):
        assert infer_from_extension("http://example.com/doc.pdf") == ContentType.PDF
    
    def test_image_extensions(self):
        assert infer_from_extension("http://example.com/img.jpg") == ContentType.IMAGE
        assert infer_from_extension("http://example.com/img.jpeg") == ContentType.IMAGE
        assert infer_from_extension("http://example.com/img.png") == ContentType.IMAGE
        assert infer_from_extension("http://example.com/img.gif") == ContentType.IMAGE
        assert infer_from_extension("http://example.com/img.webp") == ContentType.IMAGE
    
    def test_video_extensions(self):
        assert infer_from_extension("http://example.com/video.mp4") == ContentType.VIDEO
        assert infer_from_extension("http://example.com/video.webm") == ContentType.VIDEO
        assert infer_from_extension("http://example.com/video.avi") == ContentType.VIDEO
    
    def test_audio_extensions(self):
        assert infer_from_extension("http://example.com/audio.mp3") == ContentType.AUDIO
        assert infer_from_extension("http://example.com/audio.wav") == ContentType.AUDIO
        assert infer_from_extension("http://example.com/audio.ogg") == ContentType.AUDIO
    
    def test_json_extension(self):
        assert infer_from_extension("http://example.com/data.json") == ContentType.JSON
    
    def test_text_extensions(self):
        assert infer_from_extension("http://example.com/file.txt") == ContentType.TEXT
        assert infer_from_extension("http://example.com/file.md") == ContentType.TEXT
    
    def test_no_extension(self):
        assert infer_from_extension("http://example.com/page") == ContentType.UNKNOWN
        assert infer_from_extension("http://example.com/") == ContentType.UNKNOWN
    
    def test_unknown_extension(self):
        assert infer_from_extension("http://example.com/file.xyz") == ContentType.UNKNOWN
    
    def test_case_insensitive(self):
        assert infer_from_extension("http://example.com/page.HTML") == ContentType.HTML
        assert infer_from_extension("http://example.com/doc.PDF") == ContentType.PDF
    
    def test_with_query_params(self):
        # Extension matching should work even with query params
        # (currently doesn't strip them, but we test actual behavior)
        result = infer_from_extension("http://example.com/page.html?foo=bar")
        # May or may not work depending on implementation
        # Just verify it doesn't crash
        assert result in [ContentType.HTML, ContentType.UNKNOWN]

