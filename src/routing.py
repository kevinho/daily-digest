"""
Smart item routing: classify items by type for appropriate processing.

ItemType determines the processing flow:
- URL_RESOURCE: Has URL -> fetch content + summarize
- NOTE_CONTENT: No URL but has content blocks -> mark ready directly
- EMPTY_INVALID: No URL and no content -> mark as Error
"""
from enum import Enum
from typing import TYPE_CHECKING, Tuple

if TYPE_CHECKING:
    from src.notion import NotionManager


class ItemType(Enum):
    """Item classification for processing routing."""
    URL_RESOURCE = "url_resource"      # Has valid URL
    NOTE_CONTENT = "note_content"      # No URL but has content blocks
    EMPTY_INVALID = "empty_invalid"    # No URL and no content


def classify_item(item_data: dict, notion: "NotionManager") -> Tuple[ItemType, str]:
    """
    Classify an item based on URL presence and content blocks.
    
    Fast path: Check URL field first (no API call).
    Slow path: If no URL, call Notion API to check for content blocks.
    
    Args:
        item_data: Simplified page data (must have 'id' and optionally 'url')
        notion: NotionManager instance for API calls
        
    Returns:
        Tuple of (ItemType, reason_string)
    """
    url = (item_data.get("url") or "").strip()
    page_id = item_data.get("id", "")
    
    # Fast path: URL present -> URL_RESOURCE
    if url:
        return ItemType.URL_RESOURCE, "Has URL"
    
    # Slow path: Check content blocks via Notion API
    has_blocks = notion.has_page_blocks(page_id)
    if has_blocks:
        return ItemType.NOTE_CONTENT, "Has content blocks but no URL"
    
    return ItemType.EMPTY_INVALID, "No URL and no content blocks"

