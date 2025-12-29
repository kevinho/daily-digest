"""
Preprocessing module for Notion items.

Uses smart routing to classify items and apply appropriate processing:
- URL_RESOURCE: Detect ContentType, fetch title from URL, backfill if needed
- NOTE_CONTENT: Generate NOTE-YYYYMMDD-N name, mark ready
- EMPTY_INVALID: Mark as Error
"""
import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from src.browser import fetch_page_content, fetch_page_title
from src.content_type import ContentType, detect_content_type_sync
from src.routing import ItemType, classify_item
from src.utils import generate_note_name


def _first_non_empty_line(text: str) -> Optional[str]:
    for line in text.splitlines():
        cleaned = line.strip()
        if cleaned:
            return cleaned[:140]
    return None


def derive_title_from_content(content: Optional[str]) -> Optional[str]:
    if not content:
        return None
    return _first_non_empty_line(content)


def fetch_text_from_url(url: str, cdp_url: str) -> Optional[str]:
    try:
        return asyncio.run(fetch_page_content(url, cdp_url))
    except Exception as exc:
        logging.warning("Preprocess: fetch_page_content failed for %s: %s", url, exc)
        return None


def fetch_title_from_url(url: str, cdp_url: str) -> Optional[str]:
    try:
        return asyncio.run(fetch_page_title(url, cdp_url))
    except Exception as exc:
        logging.warning("Preprocess: fetch_page_title failed for %s: %s", url, exc)
        return None


def _domain_from_url(url: Optional[str]) -> Optional[str]:
    if not url:
        return None
    try:
        parsed = urlparse(url)
        return parsed.hostname
    except Exception:
        return None


def _is_meaningful_name(name: str, url: Optional[str]) -> bool:
    """Treat empty/placeholder/domain-like/auto-generated names as missing."""
    cleaned = (name or "").strip()
    if not cleaned:
        return False
    lowered = cleaned.lower()
    # Common placeholder names
    if lowered in {"untitled", "new page", "bookmark", "default", "image clip"}:
        return False
    # Auto-generated names that should be replaced with proper NOTE-xxx format
    if lowered.startswith("image-"):
        return False
    # names that are just the domain or url are not meaningful
    domain = _domain_from_url(url)
    if domain and (cleaned == domain or cleaned.startswith("http")):
        return False
    return True


def _process_url_resource(page: Dict[str, Any], notion: Any, cdp_url: str) -> Dict[str, Any]:
    """Process URL_RESOURCE: detect ContentType, backfill title if needed, set ItemType."""
    page_id = page.get("id", "")
    name = (page.get("title") or "").strip()
    url = page.get("url")
    raw_content = (page.get("raw_content") or "").strip()
    attachments: List[str] = page.get("attachments") or []

    # Always set ItemType
    notion.set_item_type(page_id, "url_resource")

    # Detect ContentType from URL
    content_type = ContentType.UNKNOWN
    content_type_reason = ""
    if url:
        try:
            content_type, content_type_reason = detect_content_type_sync(url)
            logging.debug(f"ContentType detected for {url}: {content_type.value} ({content_type_reason})")
        except Exception as e:
            logging.warning(f"ContentType detection failed for {url}: {e}")
            content_type = ContentType.UNKNOWN
            content_type_reason = f"Detection error: {e}"
    
    # Always set ContentType in Notion
    notion.set_content_type(page_id, content_type.value)

    # Check if ContentType is processable
    if not content_type.processable and content_type != ContentType.UNKNOWN:
        # Non-processable content (PDF, IMAGE, VIDEO, AUDIO, BINARY)
        reason = f"ContentType '{content_type.value}' not processable yet"
        if content_type.future_support:
            reason += " (future support planned)"
        notion.mark_unprocessed(page_id, reason)
        return {
            "action": "unprocessed",
            "reason": reason,
            "item_type": "url_resource",
            "content_type": content_type.value,
        }

    has_name = _is_meaningful_name(name, url)

    if has_name:
        # Already has meaningful name, skip title backfill
        return {"action": "skip", "item_type": "url_resource", "content_type": content_type.value}

    # Need to backfill title
    title = None
    if url:
        title = fetch_title_from_url(url, cdp_url)
        if not title:
            text = fetch_text_from_url(url, cdp_url) or ""
            title = derive_title_from_content(text)
    if not title and raw_content:
        title = derive_title_from_content(raw_content)
    if not title and attachments:
        title = attachments[0].split("/")[-1][:140]
    if not title and url:
        domain = _domain_from_url(url)
        if domain:
            title = f"Bookmark:{domain}"[:140]

    if title:
        notion.set_title(page_id, title, note="Backfilled Name from URL")
        return {"action": "backfilled", "title": title, "item_type": "url_resource", "content_type": content_type.value}

    notion.mark_as_error(page_id, "unable to backfill Name from URL")
    return {"action": "error", "reason": "backfill failed", "item_type": "url_resource", "content_type": content_type.value}


def _process_note_content(page: Dict[str, Any], notion: Any, sequence: int) -> Dict[str, Any]:
    """Process NOTE_CONTENT: generate name, set ItemType, and mark ready."""
    page_id = page.get("id", "")
    name = (page.get("title") or "").strip()

    # Always set ItemType
    notion.set_item_type(page_id, "note_content")

    has_name = _is_meaningful_name(name, None)

    if has_name:
        # Already has meaningful name, just mark ready
        notion.mark_as_done(page_id, "Content note", status=notion.status.ready)
        return {"action": "ready", "item_type": "note_content"}

    # Generate NOTE-YYYYMMDD-N name
    title = generate_note_name(sequence)
    notion.set_title(page_id, title, note="Auto-generated note name")
    notion.mark_as_done(page_id, "Content note", status=notion.status.ready)
    return {"action": "ready", "title": title, "item_type": "note_content"}


def _process_empty_invalid(page: Dict[str, Any], notion: Any, reason: str) -> Dict[str, Any]:
    """Process EMPTY_INVALID: set ItemType and mark as Error."""
    page_id = page.get("id", "")
    # Always set ItemType
    notion.set_item_type(page_id, "empty_invalid")
    notion.mark_as_error(page_id, reason)
    return {"action": "error", "reason": reason, "item_type": "empty_invalid"}


def preprocess_item(page: Dict[str, Any], notion: Any, cdp_url: str, note_sequence: int = 1) -> Dict[str, Any]:
    """
    Preprocess a single item using smart routing.
    
    Args:
        page: Simplified page data from NotionManager
        notion: NotionManager instance
        cdp_url: Chrome DevTools Protocol URL
        note_sequence: Sequence number for NOTE_CONTENT naming
        
    Returns:
        Dict with action, reason, item_type, and optionally title
    """
    item_type, reason = classify_item(page, notion)
    
    if item_type == ItemType.URL_RESOURCE:
        return _process_url_resource(page, notion, cdp_url)
    elif item_type == ItemType.NOTE_CONTENT:
        return _process_note_content(page, notion, note_sequence)
    else:  # EMPTY_INVALID
        return _process_empty_invalid(page, notion, reason)


def preprocess_batch(pages: List[Dict[str, Any]], notion: Any, cdp_url: str) -> Dict[str, int]:
    """
    Preprocess a batch of items.
    
    Returns counters for each action type.
    """
    counters = {"backfilled": 0, "error": 0, "skip": 0, "ready": 0, "unprocessed": 0}
    note_sequence = 1  # Track sequence for NOTE_CONTENT items today
    
    for page in pages:
        result = preprocess_item(page, notion, cdp_url, note_sequence)
        action = result.get("action", "skip")
        
        if action in counters:
            counters[action] += 1
        else:
            counters["skip"] += 1
        
        # Increment sequence for NOTE_CONTENT
        if result.get("item_type") == "note_content" and action == "ready":
            note_sequence += 1
    
    return counters
