"""Tests for src/digest.py"""
import pytest
from unittest.mock import patch

from src.digest import group_by_tag, build_digest


class TestGroupByTag:
    """Tests for group_by_tag function."""

    def test_groups_single_tag(self):
        entries = [
            {"id": "1", "title": "A", "tags": ["AI"]},
            {"id": "2", "title": "B", "tags": ["AI"]},
        ]
        result = group_by_tag(entries)
        assert "AI" in result
        assert len(result["AI"]) == 2

    def test_groups_multiple_tags(self):
        entries = [
            {"id": "1", "title": "A", "tags": ["AI", "Tech"]},
            {"id": "2", "title": "B", "tags": ["News"]},
        ]
        result = group_by_tag(entries)
        assert "AI" in result
        assert "Tech" in result
        assert "News" in result
        # Item with multiple tags appears in each group
        assert len(result["AI"]) == 1
        assert len(result["Tech"]) == 1

    def test_untagged_items(self):
        entries = [
            {"id": "1", "title": "A", "tags": []},
            {"id": "2", "title": "B", "tags": None},
        ]
        result = group_by_tag(entries)
        assert "未分类" in result
        assert len(result["未分类"]) == 2


class TestBuildDigest:
    """Tests for build_digest function."""

    @patch("src.digest.generate_overview")
    def test_empty_entries(self, mock_overview):
        result = build_digest([])
        assert result["overview"] == "本批次无内容。"
        assert result["tag_groups"] == []
        assert result["citations"] == []
        mock_overview.assert_not_called()

    @patch("src.digest.generate_overview")
    def test_structure_with_entries(self, mock_overview):
        mock_overview.return_value = "Test overview"
        entries = [
            {
                "id": "page1",
                "title": "Test Article",
                "tags": ["AI"],
                "summary": "This is a test summary.",
                "url": "https://example.com",
            }
        ]
        result = build_digest(entries)

        # Check overview
        assert result["overview"] == "Test overview"
        mock_overview.assert_called_once_with(entries)

        # Check tag_groups structure
        assert len(result["tag_groups"]) == 1
        group = result["tag_groups"][0]
        assert group["tag"] == "AI"
        assert len(group["items"]) == 1

        # Check item structure
        item = group["items"][0]
        assert item["title"] == "Test Article"
        assert isinstance(item["highlights"], list)
        assert item["url"] == "https://example.com"

        # Check citations
        assert result["citations"] == ["page1"]

    @patch("src.digest.generate_overview")
    def test_multi_tag_entries(self, mock_overview):
        mock_overview.return_value = "Overview"
        entries = [
            {
                "id": "page1",
                "title": "Multi-tag Article",
                "tags": ["AI", "Tech"],
                "summary": "Summary",
                "url": "https://example.com",
            }
        ]
        result = build_digest(entries)

        # Should have 2 tag groups
        assert len(result["tag_groups"]) == 2
        tags = [g["tag"] for g in result["tag_groups"]]
        assert "AI" in tags
        assert "Tech" in tags

        # Citations should be deduped
        assert result["citations"] == ["page1"]

    @patch("src.digest.generate_overview")
    def test_missing_url(self, mock_overview):
        mock_overview.return_value = "Overview"
        entries = [
            {
                "id": "page1",
                "title": "No URL Article",
                "tags": ["News"],
                "summary": "Summary",
            }
        ]
        result = build_digest(entries)

        item = result["tag_groups"][0]["items"][0]
        assert item["url"] == ""

    @patch("src.digest.generate_overview")
    def test_highlights_from_insights(self, mock_overview):
        mock_overview.return_value = "Overview"
        entries = [
            {
                "id": "page1",
                "title": "Article",
                "tags": ["AI"],
                "insights": "- Point one\n- Point two\n- Point three",
                "summary": "Fallback summary",
                "url": "",
            }
        ]
        result = build_digest(entries)

        item = result["tag_groups"][0]["items"][0]
        # Should parse insights into highlights
        assert len(item["highlights"]) >= 1
