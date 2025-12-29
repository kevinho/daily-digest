"""Tests for llm.py overview and highlight functions."""
import pytest
from unittest.mock import patch, MagicMock

from src.llm import (
    generate_overview,
    generate_overview_fallback,
    parse_highlights,
)


class TestGenerateOverviewFallback:
    """Tests for generate_overview_fallback (no-AI)."""

    def test_empty_items(self):
        result = generate_overview_fallback([])
        assert result == "本批次无内容。"

    def test_single_item(self):
        items = [{"title": "Test Article", "tags": ["AI"]}]
        result = generate_overview_fallback(items)
        assert "1条内容" in result
        assert "AI" in result

    def test_multiple_tags(self):
        items = [
            {"title": "A", "tags": ["AI"]},
            {"title": "B", "tags": ["Tech"]},
            {"title": "C", "tags": ["AI", "News"]},
        ]
        result = generate_overview_fallback(items)
        assert "3条内容" in result
        # AI appears twice
        assert "AI" in result

    def test_includes_highlights(self):
        items = [
            {"title": "Important Article", "tags": ["News"]},
            {"title": "Another One", "tags": ["Tech"]},
        ]
        result = generate_overview_fallback(items)
        assert "重点内容包括" in result

    def test_length_limit(self):
        items = [{"title": "A" * 100, "tags": [f"Tag{i}"]} for i in range(20)]
        result = generate_overview_fallback(items)
        assert len(result) <= 200


class TestGenerateOverview:
    """Tests for generate_overview (with AI)."""

    def test_empty_items_no_api_call(self):
        result = generate_overview([])
        assert result == "本批次无内容。"

    @patch("src.llm._get_openai_client")
    def test_fallback_when_no_client(self, mock_get_client):
        mock_get_client.return_value = None
        items = [{"title": "Test", "tags": ["AI"]}]
        result = generate_overview(items)
        # Should fall back to simple version
        assert "1条内容" in result

    @patch("src.llm._get_openai_client")
    def test_uses_ai_when_available(self, mock_get_client):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="AI生成的综合概述内容"))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        items = [{"title": "Test Article", "tags": ["AI"], "summary": "Test summary"}]
        result = generate_overview(items)

        assert result == "AI生成的综合概述内容"
        mock_client.chat.completions.create.assert_called_once()


class TestParseHighlights:
    """Tests for parse_highlights function."""

    def test_empty_input(self):
        assert parse_highlights("") == []
        assert parse_highlights(None) == []

    def test_bullet_list(self):
        insights = "- First point\n- Second point\n- Third point"
        result = parse_highlights(insights)
        assert len(result) == 3
        assert "First point" in result
        assert "Second point" in result
        assert "Third point" in result

    def test_dash_bullet_list(self):
        insights = "• Point one\n• Point two"
        result = parse_highlights(insights)
        assert len(result) == 2

    def test_numbered_list(self):
        insights = "1. First\n2. Second\n3. Third"
        result = parse_highlights(insights)
        assert len(result) == 3
        assert "First" in result

    def test_chinese_numbered_list(self):
        insights = "1、要点一\n2、要点二"
        result = parse_highlights(insights)
        assert len(result) == 2

    def test_truncates_long_items(self):
        long_text = "A" * 50
        insights = f"- {long_text}\n- Short"
        result = parse_highlights(insights)
        assert len(result[0]) == 30  # Truncated
        assert result[1] == "Short"

    def test_max_five_items(self):
        insights = "\n".join([f"- Item {i}" for i in range(10)])
        result = parse_highlights(insights)
        assert len(result) == 5

    def test_removes_prefix_labels(self):
        insights = "Insights: This is a point\n要点: Another point"
        result = parse_highlights(insights)
        # Should remove "Insights:" and "要点:" prefixes
        assert "Insights" not in str(result)
        assert "要点" not in str(result)

    def test_skips_empty_lines(self):
        insights = "- Point one\n\n- Point two\n\n\n- Point three"
        result = parse_highlights(insights)
        assert len(result) == 3

    def test_handles_mixed_formats(self):
        insights = """Insights:
- First bullet
• Second bullet
1. Third numbered
Normal line"""
        result = parse_highlights(insights)
        assert len(result) >= 3

