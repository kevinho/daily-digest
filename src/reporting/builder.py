"""
Report builders for different digest levels.

Each builder takes input from the level below and generates a ReportData.
"""

import logging
from typing import Any, Dict, List

from src.reporting.models import ReportData, ReportPeriod, ReportType

logger = logging.getLogger(__name__)


class DailyReportBuilder:
    """
    Build daily digest from Inbox items.
    
    Input: List of items with summaries from Inbox DB
    Output: ReportData with grouped content and AI overview
    """
    
    def build(
        self,
        items: List[Dict[str, Any]],
        period: ReportPeriod,
        generate_overview_fn=None,
    ) -> ReportData:
        """
        Build a daily report from inbox items.
        
        Args:
            items: List of item dicts with keys: id, title, summary, tags, url
            period: The report period
            generate_overview_fn: Optional function to generate AI overview
            
        Returns:
            ReportData with overview, highlights, and content blocks
        """
        if not items:
            return ReportData(
                period=period,
                overview="今日无新增内容。",
                highlights=[],
                source_ids=[],
                content_blocks=[],
                categories={},
            )
        
        # Group items by tags
        categories = self._group_by_tags(items)
        
        # Extract source IDs
        source_ids = [item.get("id") for item in items if item.get("id")]
        
        # Extract page links from items for linking
        item_links = self._extract_highlights(items)  # Contains page_link info
        
        # Generate overview using AI if available
        if generate_overview_fn:
            overview_data = generate_overview_fn(items)
            overview = overview_data.get("overview", "")
            ai_highlights = overview_data.get("highlights", [])
            
            # Combine AI text with source item links
            # AI text is more concise, but we want it clickable
            highlights_with_links = self._merge_ai_highlights_with_links(ai_highlights, item_links)
            highlights = ai_highlights  # For metadata
        else:
            # Fallback: use item titles with links
            overview = self._fallback_overview(items, categories)
            highlights_with_links = item_links
            highlights = [h.get("text", "") for h in highlights_with_links]
        
        # Build Notion content blocks with linked highlights
        content_blocks = self._build_content_blocks(items, categories, highlights_with_links)
        
        return ReportData(
            period=period,
            overview=overview,
            highlights=highlights,
            source_ids=source_ids,
            content_blocks=content_blocks,
            categories=categories,
        )
    
    def _group_by_tags(self, items: List[Dict]) -> Dict[str, Dict[str, List[Dict]]]:
        """Group items into two-level hierarchy using AI categorization."""
        from src.llm import categorize_items
        
        # Use AI two-level categorization
        ai_categories = categorize_items(items)
        
        # Convert index-based categories to item-based (two-level)
        categories: Dict[str, Dict[str, List[Dict]]] = {}
        assigned_indices = set()
        
        for main_cat, sub_cats in ai_categories.items():
            if not isinstance(sub_cats, dict):
                # Handle flat structure (fallback compatibility)
                sub_cats = {"默认": sub_cats if isinstance(sub_cats, list) else []}
            
            categories[main_cat] = {}
            for sub_cat, indices in sub_cats.items():
                if not isinstance(indices, list):
                    continue
                categories[main_cat][sub_cat] = []
                for idx in indices:
                    if isinstance(idx, int) and 0 <= idx < len(items):
                        categories[main_cat][sub_cat].append(items[idx])
                        assigned_indices.add(idx)
        
        # Add any unassigned items to "其他" category
        unassigned = [items[i] for i in range(len(items)) if i not in assigned_indices]
        if unassigned:
            if "其他" not in categories:
                categories["其他"] = {}
            categories["其他"]["未分类"] = unassigned
        
        return categories
    
    def _fallback_overview(self, items: List[Dict], categories: Dict) -> str:
        """Generate a simple overview without AI."""
        count = len(items)
        cat_count = len(categories)
        cat_names = "、".join(list(categories.keys())[:5])
        return f"今日收集{count}条内容，涵盖{cat_count}个类别：{cat_names}。"
    
    def _extract_highlights(self, items: List[Dict], max_count: int = 5) -> List[Dict]:
        """Extract top highlights from items with page link info."""
        highlights = []
        for item in items[:max_count]:
            title = item.get("title", "")
            if title:
                highlights.append({
                    "text": title[:80],
                    "page_link": item.get("page_link", ""),
                    "url": item.get("url", ""),
                })
        return highlights
    
    def _merge_ai_highlights_with_links(
        self,
        ai_highlights: List[str],
        item_links: List[Dict],
    ) -> List[Dict]:
        """
        Merge AI-generated highlight text with source item links.
        
        AI provides concise summaries, item_links provide page URLs.
        Combine them by index order (AI highlight i -> item i's link).
        """
        merged = []
        for i, ai_text in enumerate(ai_highlights):
            if i < len(item_links):
                # Use AI text with item's page link
                merged.append({
                    "text": ai_text,
                    "page_link": item_links[i].get("page_link", ""),
                    "url": item_links[i].get("url", ""),
                })
            else:
                # No matching item, just use AI text without link
                merged.append({
                    "text": ai_text,
                    "page_link": "",
                    "url": "",
                })
        return merged
    
    def _build_content_blocks(
        self,
        items: List[Dict],
        categories: Dict[str, Dict[str, List[Dict]]],  # Two-level categories
        highlights: List,  # Can be List[str] or List[Dict]
    ) -> List[Dict]:
        """Build Notion blocks for the report content with two-level categories."""
        blocks: List[Dict] = []
        
        # Statistics section - show main categories with subcategory counts
        blocks.append(_heading2(f"📊 统计 ({len(items)}条)"))
        for main_cat, sub_cats in categories.items():
            if isinstance(sub_cats, dict):
                total = sum(len(items) for items in sub_cats.values())
                sub_names = "、".join(sub_cats.keys())
                blocks.append(_bullet(f"{main_cat}: {total}条 ({sub_names})"))
            else:
                blocks.append(_bullet(f"{main_cat}: {len(sub_cats)}条"))
        blocks.append(_divider())
        
        # Highlights section with clickable links
        if highlights:
            blocks.append(_heading2("⭐ 今日要点"))
            for h in highlights:
                if isinstance(h, dict):
                    text = h.get("text", "")
                    page_link = h.get("page_link", "")
                    if page_link:
                        blocks.append(_bullet_with_link(text, page_link))
                    else:
                        blocks.append(_bullet(text))
                else:
                    blocks.append(_bullet(h))
            blocks.append(_divider())
        
        # Two-level category display
        for main_cat, sub_cats in categories.items():
            if not isinstance(sub_cats, dict):
                continue
            
            # Count total items in main category
            total_in_main = sum(len(sub_items) for sub_items in sub_cats.values())
            blocks.append(_heading2(f"📁 {main_cat} ({total_in_main}条)"))
            
            for sub_cat, sub_items in sub_cats.items():
                if not sub_items:
                    continue
                
                # Subcategory header (heading3 style)
                blocks.append(_heading3(f"▸ {sub_cat} ({len(sub_items)}条)"))
                
                for item in sub_items:
                    title = item.get("title", "无标题")
                    summary = item.get("summary", "")
                    url = item.get("url", "")
                    page_link = item.get("page_link", "")
                    
                    # Clean summary: remove TLDR/Insights labels and get first line only
                    display_text = _clean_summary(summary) if summary else title[:80]
                    
                    # Prefer page_link for Notion internal linking, fall back to external URL
                    link = page_link or url
                    if link:
                        blocks.append(_bullet_with_link(f"📌 {display_text}", link))
                    else:
                        blocks.append(_bullet(f"📌 {display_text}"))
            
            blocks.append(_divider())
        
        return blocks


class WeeklyReportBuilder:
    """
    Build weekly digest from Daily reports.
    
    Input: List of daily reports from Reporting DB
    Output: ReportData with trend analysis and AI synthesis
    """
    
    def build(
        self,
        daily_reports: List[Dict[str, Any]],
        period: ReportPeriod,
        generate_overview_fn=None,
    ) -> ReportData:
        """
        Build a weekly report from daily reports.
        
        Args:
            daily_reports: List of daily report dicts
            period: The report period
            generate_overview_fn: Optional function to generate AI overview
            
        Returns:
            ReportData with weekly synthesis
        """
        if not daily_reports:
            return ReportData(
                period=period,
                overview="本周无日报记录。",
                highlights=[],
                source_ids=[],
                content_blocks=[],
            )
        
        source_ids = [r.get("id") for r in daily_reports if r.get("id")]
        
        # Always extract trends with page links from daily reports
        trends_with_links = self._extract_trends(daily_reports)
        
        # Generate overview text using AI if available
        if generate_overview_fn:
            overview_data = generate_overview_fn(daily_reports)
            overview = overview_data.get("overview", "")
            # Use AI trends as highlights for metadata, but use linked trends for display
            highlights = overview_data.get("trends", [h.get("text", "") for h in trends_with_links])
        else:
            overview = self._fallback_overview(daily_reports)
            highlights = [h.get("text", "") for h in trends_with_links]
        
        # Use trends_with_links for content blocks (has page_link info)
        content_blocks = self._build_content_blocks(daily_reports, trends_with_links)
        
        return ReportData(
            period=period,
            overview=overview,
            highlights=highlights,
            source_ids=source_ids,
            content_blocks=content_blocks,
        )
    
    def _fallback_overview(self, daily_reports: List[Dict]) -> str:
        """Generate a simple weekly overview without AI."""
        count = len(daily_reports)
        return f"本周共{count}天有内容记录。"
    
    def _extract_trends(self, daily_reports: List[Dict]) -> List[Dict]:
        """Extract trends from daily reports with source info."""
        # Aggregate highlights with source tracking
        all_trends = []
        for report in daily_reports:
            highlights = report.get("highlights") or []
            report_url = report.get("url", "")
            report_date = report.get("date", "")
            for h in highlights:
                all_trends.append({
                    "text": h,
                    "page_link": report_url,
                    "date": report_date,
                })
        return all_trends[:5]
    
    def _build_content_blocks(
        self,
        daily_reports: List[Dict],
        highlights: List,  # Can be List[str] or List[Dict]
    ) -> List[Dict]:
        """Build Notion blocks for weekly report."""
        blocks: List[Dict] = []
        
        # Daily reports section with clickable links and summaries
        blocks.append(_heading2(f"📅 本周概览 ({len(daily_reports)}天)"))
        for report in daily_reports:
            title = report.get("title", "")
            date_str = report.get("date", "")
            summary = report.get("summary", "")[:200]  # ~200 chars
            page_url = report.get("url", "")
            
            # Daily report title as callout with link
            blocks.append(_callout(f"{date_str}: {title}", "📋", page_url))
            
            # Summary paragraph (indented feeling)
            if summary:
                blocks.append(_paragraph(f"  {summary}"))
            
            # Add spacing
            blocks.append(_paragraph(""))
        
        blocks.append(_divider())
        
        # Trends section with page links
        if highlights:
            blocks.append(_heading2("📈 本周趋势"))
            for h in highlights:
                if isinstance(h, dict):
                    # New format with source info
                    text = h.get("text", "")
                    page_link = h.get("page_link", "")
                    date_str = h.get("date", "")
                    if page_link:
                        blocks.append(_bullet_with_link(f"{text} ({date_str})", page_link))
                    else:
                        blocks.append(_bullet(f"{text} ({date_str})"))
                else:
                    # Old format: just string
                    blocks.append(_bullet(h))
            blocks.append(_divider())
        
        return blocks


class MonthlyReportBuilder:
    """
    Build monthly digest from Weekly reports.
    
    Input: List of weekly reports from Reporting DB
    Output: ReportData with monthly review and theme evolution
    """
    
    def build(
        self,
        weekly_reports: List[Dict[str, Any]],
        period: ReportPeriod,
        generate_overview_fn=None,
    ) -> ReportData:
        """
        Build a monthly report from weekly reports.
        
        Args:
            weekly_reports: List of weekly report dicts
            period: The report period
            generate_overview_fn: Optional function to generate AI overview
            
        Returns:
            ReportData with monthly review
        """
        if not weekly_reports:
            return ReportData(
                period=period,
                overview="本月无周报记录。",
                highlights=[],
                source_ids=[],
                content_blocks=[],
            )
        
        source_ids = [r.get("id") for r in weekly_reports if r.get("id")]
        
        # Always extract themes with page links from weekly reports
        themes_with_links = self._extract_themes(weekly_reports)
        
        if generate_overview_fn:
            overview_data = generate_overview_fn(weekly_reports)
            overview = overview_data.get("overview", "")
            highlights = overview_data.get("dominant_themes", [h.get("text", "") for h in themes_with_links])
        else:
            overview = self._fallback_overview(weekly_reports)
            highlights = [h.get("text", "") for h in themes_with_links]
        
        # Use themes_with_links for content blocks (has page_link info)
        content_blocks = self._build_content_blocks(weekly_reports, themes_with_links)
        
        return ReportData(
            period=period,
            overview=overview,
            highlights=highlights,
            source_ids=source_ids,
            content_blocks=content_blocks,
        )
    
    def _fallback_overview(self, weekly_reports: List[Dict]) -> str:
        """Generate a simple monthly overview without AI."""
        count = len(weekly_reports)
        return f"本月共{count}周有内容记录。"
    
    def _extract_themes(self, weekly_reports: List[Dict]) -> List[Dict]:
        """Extract themes from weekly reports with source info."""
        all_themes = []
        for report in weekly_reports:
            highlights = report.get("highlights") or []
            report_url = report.get("url", "")
            report_title = report.get("title", "")
            for h in highlights:
                all_themes.append({
                    "text": h,
                    "page_link": report_url,
                    "source": report_title,
                })
        return all_themes[:5]
    
    def _build_content_blocks(
        self,
        weekly_reports: List[Dict],
        themes: List,  # Can be List[str] or List[Dict]
    ) -> List[Dict]:
        """Build Notion blocks for monthly report."""
        blocks: List[Dict] = []
        
        # Weekly reports section with clickable links and summaries
        blocks.append(_heading2(f"📆 本月概览 ({len(weekly_reports)}周)"))
        for report in weekly_reports:
            title = report.get("title", "")
            summary = report.get("summary", "")[:200]  # ~200 chars
            page_url = report.get("url", "")
            
            # Weekly report title as callout with link
            blocks.append(_callout(title, "📅", page_url))
            
            # Summary paragraph
            if summary:
                blocks.append(_paragraph(f"  {summary}"))
            
            # Add spacing
            blocks.append(_paragraph(""))
        
        blocks.append(_divider())
        
        # Themes section with page links
        if themes:
            blocks.append(_heading2("🎯 本月主题"))
            for t in themes:
                if isinstance(t, dict):
                    # New format with source info
                    text = t.get("text", "")
                    page_link = t.get("page_link", "")
                    source = t.get("source", "")
                    if page_link:
                        blocks.append(_bullet_with_link(f"{text} ({source})", page_link))
                    else:
                        blocks.append(_bullet(text))
                else:
                    # Old format: just string
                    blocks.append(_bullet(t))
            blocks.append(_divider())
        
        return blocks


# ============================================================
# Notion Block Helpers
# ============================================================

def _heading2(text: str) -> Dict:
    """Create a heading_2 block."""
    return {
        "object": "block",
        "type": "heading_2",
        "heading_2": {
            "rich_text": [{"type": "text", "text": {"content": text[:100]}}]
        },
    }


def _heading3(text: str) -> Dict:
    """Create a heading_3 block."""
    return {
        "object": "block",
        "type": "heading_3",
        "heading_3": {
            "rich_text": [{"type": "text", "text": {"content": text[:100]}}]
        },
    }


def _paragraph(text: str) -> Dict:
    """Create a paragraph block."""
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": [{"type": "text", "text": {"content": text[:2000]}}]
        },
    }


def _paragraph_link(text: str, url: str) -> Dict:
    """Create a paragraph block with a link."""
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": [
                {"type": "text", "text": {"content": text[:2000], "link": {"url": url}}}
            ]
        },
    }


def _bullet(text: str) -> Dict:
    """Create a bulleted list item block."""
    return {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {
            "rich_text": [{"type": "text", "text": {"content": text[:2000]}}]
        },
    }


def _divider() -> Dict:
    """Create a divider block."""
    return {"object": "block", "type": "divider", "divider": {}}


def _clean_summary(summary: str) -> str:
    """
    Clean summary text: remove all labels and get clean content only.
    
    Input might be:
        "**TLDR:** Some text.\n**Insights:**\n1. Point one\n2. Point two"
    Output:
        "Some text."
    """
    import re
    
    if not summary:
        return ""
    
    text = summary.strip()
    
    # Remove all markdown bold markers
    text = text.replace('**', '')
    
    # Remove TLDR label (various formats)
    text = re.sub(r'^TLDR:?\s*', '', text, flags=re.IGNORECASE)
    
    # Split at Insights or numbered list or newline
    # Stop at: "Insights:", numbered items "1.", or newlines
    parts = re.split(r'\n|Insights:?|\d+\.', text, maxsplit=1, flags=re.IGNORECASE)
    first_part = parts[0].strip() if parts else text
    
    # Clean up any remaining artifacts
    first_part = first_part.strip('.:;,\n ')
    
    # Truncate to reasonable length
    return first_part[:100] if first_part else ""


def _callout(text: str, icon: str = "📌", url: str = None) -> Dict:
    """Create a callout block with optional link."""
    rich_text = [
        {
            "type": "text",
            "text": {"content": text[:2000], "link": {"url": url} if url else None},
            "annotations": {"bold": True},
        }
    ]
    return {
        "object": "block",
        "type": "callout",
        "callout": {
            "rich_text": rich_text,
            "icon": {"type": "emoji", "emoji": icon},
            "color": "gray_background",
        },
    }


def _bullet_with_link(text: str, url: str) -> Dict:
    """Create a bulleted list item with clickable link."""
    return {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {
            "rich_text": [
                {"type": "text", "text": {"content": text[:2000], "link": {"url": url}}}
            ]
        },
    }

