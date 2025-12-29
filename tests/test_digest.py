"""Tests for src/digest.py"""
import pytest
from unittest.mock import patch

from src.digest import build_digest, _build_url_item, _build_simple_item


class TestBuildUrlItem:
    """Tests for _build_url_item function."""

    def test_full_item(self):
        item = {
            "title": "Test Article",
            "summary": "This is a test summary.",
            "url": "https://example.com",
            "page_link": "https://notion.so/abc123",
        }
        result = _build_url_item(item)
        assert result["title"] == "Test Article"
        assert result["url"] == "https://example.com"
        assert result["page_link"] == "https://notion.so/abc123"
        assert isinstance(result["highlights"], list)

    def test_with_insights(self):
        item = {
            "title": "Article",
            "insights": "- Point one\n- Point two",
            "url": "",
            "page_link": "",
        }
        result = _build_url_item(item)
        assert len(result["highlights"]) >= 1

    def test_missing_fields(self):
        item = {}
        result = _build_url_item(item)
        assert result["title"] == "无标题"
        assert result["url"] == ""
        assert result["page_link"] == ""


class TestBuildSimpleItem:
    """Tests for _build_simple_item function."""

    def test_with_values(self):
        item = {"title": "Note Title", "page_link": "https://notion.so/xyz"}
        result = _build_simple_item(item)
        assert result["title"] == "Note Title"
        assert result["page_link"] == "https://notion.so/xyz"
        assert "highlights" not in result
        assert "url" not in result

    def test_missing_fields(self):
        result = _build_simple_item({})
        assert result["title"] == "无标题"
        assert result["page_link"] == ""


class TestBuildDigest:
    """Tests for build_digest function."""

    @patch("src.digest.generate_overview")
    def test_empty_entries(self, mock_overview):
        result = build_digest([])
        assert result["overview"] == "本批次无内容。"
        assert result["url_items"] == []
        assert result["note_items"] == []
        assert result["empty_items"] == []
        assert result["citations"] == []
        mock_overview.assert_not_called()

    @patch("src.digest.generate_overview")
    def test_url_resource_entries(self, mock_overview):
        mock_overview.return_value = "Test overview"
        entries = [
            {
                "id": "page1",
                "title": "Web Article",
                "item_type": "URL_RESOURCE",
                "summary": "Summary text",
                "url": "https://example.com",
                "page_link": "https://notion.so/page1",
            }
        ]
        result = build_digest(entries)

        assert result["overview"] == "Test overview"
        assert len(result["url_items"]) == 1
        assert result["url_items"][0]["title"] == "Web Article"
        assert result["url_items"][0]["page_link"] == "https://notion.so/page1"
        assert len(result["note_items"]) == 0
        assert result["citations"] == ["page1"]

    @patch("src.digest.generate_overview")
    def test_note_content_entries(self, mock_overview):
        entries = [
            {
                "id": "page2",
                "title": "My Note",
                "item_type": "NOTE_CONTENT",
                "page_link": "https://notion.so/page2",
            }
        ]
        result = build_digest(entries)

        # No URL entries, so overview is simple
        assert "笔记" in result["overview"]
        assert len(result["url_items"]) == 0
        assert len(result["note_items"]) == 1
        assert result["note_items"][0]["title"] == "My Note"
        assert result["note_items"][0]["page_link"] == "https://notion.so/page2"
        assert "highlights" not in result["note_items"][0]

    @patch("src.digest.generate_overview")
    def test_empty_invalid_entries(self, mock_overview):
        entries = [
            {
                "id": "page3",
                "title": "Empty Item",
                "item_type": "EMPTY_INVALID",
                "page_link": "https://notion.so/page3",
            }
        ]
        result = build_digest(entries)

        assert len(result["empty_items"]) == 1
        assert result["empty_items"][0]["title"] == "Empty Item"

    @patch("src.digest.generate_overview")
    def test_mixed_item_types(self, mock_overview):
        mock_overview.return_value = "Mixed content overview"
        entries = [
            {"id": "p1", "title": "URL 1", "item_type": "URL_RESOURCE", "summary": "S1", "url": "https://a.com", "page_link": ""},
            {"id": "p2", "title": "Note 1", "item_type": "NOTE_CONTENT", "page_link": ""},
            {"id": "p3", "title": "URL 2", "item_type": "url_resource", "summary": "S2", "url": "https://b.com", "page_link": ""},
            {"id": "p4", "title": "Empty 1", "item_type": "EMPTY_INVALID", "page_link": ""},
        ]
        result = build_digest(entries)

        assert len(result["url_items"]) == 2
        assert len(result["note_items"]) == 1
        assert len(result["empty_items"]) == 1
        assert len(result["citations"]) == 4

    @patch("src.digest.generate_overview")
    def test_unclassified_defaults_to_url(self, mock_overview):
        """Items without item_type should be treated as URL_RESOURCE."""
        mock_overview.return_value = "Overview"
        entries = [
            {"id": "p1", "title": "Unknown", "summary": "S", "url": "https://x.com", "page_link": ""}
        ]
        result = build_digest(entries)
        
        assert len(result["url_items"]) == 1
        assert len(result["note_items"]) == 0

    @patch("src.digest.generate_overview")
    def test_citations_deduped(self, mock_overview):
        mock_overview.return_value = "Overview"
        entries = [
            {"id": "same_id", "title": "A", "item_type": "URL_RESOURCE", "summary": "", "url": "", "page_link": ""},
        ]
        result = build_digest(entries)
        assert result["citations"] == ["same_id"]
