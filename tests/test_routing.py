"""Tests for smart item routing."""
import pytest
from unittest.mock import MagicMock

from src.routing import ItemType, classify_item
from src.utils import generate_note_name


class TestItemType:
    """Test ItemType enum."""

    def test_enum_values(self):
        assert ItemType.URL_RESOURCE.value == "url_resource"
        assert ItemType.NOTE_CONTENT.value == "note_content"
        assert ItemType.EMPTY_INVALID.value == "empty_invalid"

    def test_enum_members(self):
        members = list(ItemType)
        assert len(members) == 3
        assert ItemType.URL_RESOURCE in members
        assert ItemType.NOTE_CONTENT in members
        assert ItemType.EMPTY_INVALID in members


class TestClassifyItem:
    """Test classify_item function."""

    @pytest.fixture
    def mock_notion(self):
        """Create a mock NotionManager."""
        notion = MagicMock()
        notion.has_page_blocks = MagicMock(return_value=False)
        return notion

    def test_url_resource_with_url(self, mock_notion):
        """Item with URL should be classified as URL_RESOURCE."""
        item = {"id": "page-123", "url": "https://example.com/article"}
        
        item_type, reason = classify_item(item, mock_notion)
        
        assert item_type == ItemType.URL_RESOURCE
        assert "URL" in reason
        # Should not call has_page_blocks (fast path)
        mock_notion.has_page_blocks.assert_not_called()

    def test_url_resource_with_whitespace_url(self, mock_notion):
        """URL with whitespace should still be URL_RESOURCE."""
        item = {"id": "page-123", "url": "  https://example.com  "}
        
        item_type, reason = classify_item(item, mock_notion)
        
        assert item_type == ItemType.URL_RESOURCE

    def test_note_content_with_blocks(self, mock_notion):
        """Item without URL but with content blocks should be NOTE_CONTENT."""
        mock_notion.has_page_blocks.return_value = True
        item = {"id": "page-123", "url": None}
        
        item_type, reason = classify_item(item, mock_notion)
        
        assert item_type == ItemType.NOTE_CONTENT
        assert "content blocks" in reason.lower()
        mock_notion.has_page_blocks.assert_called_once_with("page-123")

    def test_note_content_empty_url(self, mock_notion):
        """Empty string URL should check content blocks."""
        mock_notion.has_page_blocks.return_value = True
        item = {"id": "page-123", "url": ""}
        
        item_type, reason = classify_item(item, mock_notion)
        
        assert item_type == ItemType.NOTE_CONTENT

    def test_note_content_whitespace_url(self, mock_notion):
        """Whitespace-only URL should check content blocks."""
        mock_notion.has_page_blocks.return_value = True
        item = {"id": "page-123", "url": "   "}
        
        item_type, reason = classify_item(item, mock_notion)
        
        assert item_type == ItemType.NOTE_CONTENT

    def test_empty_invalid_no_url_no_blocks(self, mock_notion):
        """Item without URL and no content blocks should be EMPTY_INVALID."""
        mock_notion.has_page_blocks.return_value = False
        item = {"id": "page-123", "url": None}
        
        item_type, reason = classify_item(item, mock_notion)
        
        assert item_type == ItemType.EMPTY_INVALID
        assert "no url" in reason.lower() or "no content" in reason.lower()

    def test_empty_invalid_missing_url_key(self, mock_notion):
        """Item without URL key should check content blocks."""
        mock_notion.has_page_blocks.return_value = False
        item = {"id": "page-123"}
        
        item_type, reason = classify_item(item, mock_notion)
        
        assert item_type == ItemType.EMPTY_INVALID


class TestGenerateNoteName:
    """Test generate_note_name function."""

    def test_default_sequence(self):
        """Default sequence should be 1."""
        name = generate_note_name()
        
        assert name.startswith("NOTE-")
        assert name.endswith("-1")
        # Check date format YYYYMMDD
        parts = name.split("-")
        assert len(parts) == 3
        assert len(parts[1]) == 8
        assert parts[1].isdigit()

    def test_custom_sequence(self):
        """Custom sequence should be reflected."""
        name = generate_note_name(sequence=5)
        
        assert name.endswith("-5")

    def test_sequence_increment(self):
        """Sequential calls should produce different names."""
        names = [generate_note_name(seq) for seq in range(1, 4)]
        
        assert names[0].endswith("-1")
        assert names[1].endswith("-2")
        assert names[2].endswith("-3")

    def test_format_consistency(self):
        """Format should always be NOTE-YYYYMMDD-N."""
        import re
        pattern = r"^NOTE-\d{8}-\d+$"
        
        for seq in [1, 10, 100]:
            name = generate_note_name(seq)
            assert re.match(pattern, name), f"Name '{name}' doesn't match pattern"

