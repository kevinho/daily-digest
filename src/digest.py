"""
Digest builder: creates structured digest from ready entries.

Output structure:
{
    "overview": "综合概述（100-150字）",
    "tag_groups": [
        {
            "tag": "标签名",
            "items": [
                {"title": "...", "highlights": [...], "url": "..."}
            ]
        }
    ],
    "citations": ["page_id_1", ...]
}
"""
from typing import Dict, List

from src.llm import generate_overview, parse_highlights


def group_by_tag(entries: List[Dict]) -> Dict[str, List[Dict]]:
    """Group entries by tag. Items with multiple tags appear in each group."""
    grouped: Dict[str, List[Dict]] = {}
    for e in entries:
        tags = e.get("tags") or ["未分类"]
        for t in tags:
            grouped.setdefault(t, []).append(e)
    return grouped


def build_digest(entries: List[Dict]) -> Dict:
    """
    Build a structured digest payload from ready entries.
    
    Each entry should include: id, tags, summary/tldr, title, url.
    
    Returns:
        Dict with overview, tag_groups, and citations
    """
    if not entries:
        return {
            "overview": "本批次无内容。",
            "tag_groups": [],
            "citations": [],
        }
    
    # 1. Generate comprehensive overview
    overview = generate_overview(entries)
    
    # 2. Group by tag and build item summaries
    grouped = group_by_tag(entries)
    tag_groups: List[Dict] = []
    all_citations: List[str] = []
    
    for tag, items in grouped.items():
        group_items: List[Dict] = []
        for item in items:
            # Extract highlights from summary/insights
            summary = item.get("summary") or item.get("tldr") or ""
            insights = item.get("insights") or summary
            highlights = parse_highlights(insights)
            
            # If no highlights parsed, use summary as single highlight
            if not highlights and summary:
                highlights = [summary[:30]]
            
            group_items.append({
                "title": item.get("title", "无标题"),
                "highlights": highlights,
                "url": item.get("url", ""),
            })
            
            # Collect citation
            item_id = item.get("id")
            if item_id:
                all_citations.append(item_id)
        
        tag_groups.append({
            "tag": tag,
            "items": group_items,
        })
    
    return {
        "overview": overview,
        "tag_groups": tag_groups,
        "citations": list(dict.fromkeys(all_citations)),  # Dedupe while preserving order
    }
