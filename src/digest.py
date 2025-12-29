"""
Digest builder: creates structured digest from ready entries.

Output structure:
{
    "overview": "综合概述（100-150字）",
    "url_items": [  # URL_RESOURCE type with full summaries
        {"title": "...", "highlights": [...], "url": "...", "page_link": "..."}
    ],
    "note_items": [  # NOTE_CONTENT type, title + page_link only
        {"title": "...", "page_link": "..."}
    ],
    "empty_items": [  # EMPTY_INVALID type, title + page_link only
        {"title": "...", "page_link": "..."}
    ],
    "citations": ["page_id_1", ...]
}
"""
from typing import Dict, List

from src.llm import generate_overview, parse_highlights


def _build_url_item(item: Dict) -> Dict:
    """Build a structured summary for URL_RESOURCE item (with highlights)."""
    summary = item.get("summary") or item.get("tldr") or ""
    insights = item.get("insights") or summary
    highlights = parse_highlights(insights)
    
    # If no highlights parsed, use summary as single highlight
    if not highlights and summary:
        highlights = [summary[:30]]
    
    return {
        "title": item.get("title", "无标题"),
        "highlights": highlights,
        "url": item.get("url", ""),
        "page_link": item.get("page_link", ""),
    }


def _build_simple_item(item: Dict) -> Dict:
    """Build a simple item entry (title + page_link only, no summary)."""
    return {
        "title": item.get("title", "无标题"),
        "page_link": item.get("page_link", ""),
    }


def build_digest(entries: List[Dict]) -> Dict:
    """
    Build a structured digest payload from ready entries, grouped by ItemType.
    
    Each entry should include: id, title, url, item_type, page_link, summary/tldr.
    
    Returns:
        Dict with overview, url_items, note_items, empty_items, and citations
    """
    if not entries:
        return {
            "overview": "本批次无内容。",
            "url_items": [],
            "note_items": [],
            "empty_items": [],
            "citations": [],
        }
    
    # Separate entries by item_type
    url_entries: List[Dict] = []
    note_entries: List[Dict] = []
    empty_entries: List[Dict] = []
    
    for entry in entries:
        item_type = (entry.get("item_type") or "").upper()
        if item_type == "NOTE_CONTENT":
            note_entries.append(entry)
        elif item_type == "EMPTY_INVALID":
            empty_entries.append(entry)
        else:
            # Default to URL_RESOURCE or unclassified
            url_entries.append(entry)
    
    # 1. Generate comprehensive overview (based on URL entries primarily)
    if url_entries:
        overview = generate_overview(url_entries)
    elif note_entries:
        overview = f"本批次共{len(note_entries)}条笔记内容。"
    else:
        overview = "本批次无有效内容。"
    
    all_citations: List[str] = []
    
    # 2. Build URL items with full summaries
    url_items: List[Dict] = []
    for item in url_entries:
        url_items.append(_build_url_item(item))
        if item.get("id"):
            all_citations.append(item["id"])
    
    # 3. Build note items (simple: title + page_link)
    note_items: List[Dict] = []
    for item in note_entries:
        note_items.append(_build_simple_item(item))
        if item.get("id"):
            all_citations.append(item["id"])
    
    # 4. Build empty items (simple: title + page_link)
    empty_items: List[Dict] = []
    for item in empty_entries:
        empty_items.append(_build_simple_item(item))
        if item.get("id"):
            all_citations.append(item["id"])
    
    return {
        "overview": overview,
        "url_items": url_items,
        "note_items": note_items,
        "empty_items": empty_items,
        "citations": list(dict.fromkeys(all_citations)),  # Dedupe while preserving order
    }
