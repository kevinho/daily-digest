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
        
        # Generate overview using AI if available
        if generate_overview_fn:
            overview_data = generate_overview_fn(items)
            overview = overview_data.get("overview", "")
            highlights = overview_data.get("highlights", [])
        else:
            # Fallback: simple count-based overview
            overview = self._fallback_overview(items, categories)
            highlights = self._extract_highlights(items)
        
        # Build Notion content blocks
        content_blocks = self._build_content_blocks(items, categories, highlights)
        
        return ReportData(
            period=period,
            overview=overview,
            highlights=highlights,
            source_ids=source_ids,
            content_blocks=content_blocks,
            categories=categories,
        )
    
    def _group_by_tags(self, items: List[Dict]) -> Dict[str, List[Dict]]:
        """Group items by their tags."""
        categories: Dict[str, List[Dict]] = {}
        
        for item in items:
            tags = item.get("tags") or []
            if not tags:
                tags = ["未分类"]
            
            for tag in tags:
                if tag not in categories:
                    categories[tag] = []
                categories[tag].append(item)
        
        return categories
    
    def _fallback_overview(self, items: List[Dict], categories: Dict) -> str:
        """Generate a simple overview without AI."""
        count = len(items)
        cat_count = len(categories)
        cat_names = "、".join(list(categories.keys())[:5])
        return f"今日收集{count}条内容，涵盖{cat_count}个类别：{cat_names}。"
    
    def _extract_highlights(self, items: List[Dict], max_count: int = 5) -> List[str]:
        """Extract top highlights from items."""
        highlights = []
        for item in items[:max_count]:
            title = item.get("title", "")
            if title:
                highlights.append(title[:50])  # Truncate long titles
        return highlights
    
    def _build_content_blocks(
        self,
        items: List[Dict],
        categories: Dict[str, List[Dict]],
        highlights: List[str],
    ) -> List[Dict]:
        """Build Notion blocks for the report content."""
        blocks: List[Dict] = []
        
        # Statistics section
        blocks.append(_heading2(f"📊 统计 ({len(items)}条)"))
        for cat, cat_items in categories.items():
            blocks.append(_bullet(f"{cat}: {len(cat_items)}条"))
        blocks.append(_divider())
        
        # Highlights section
        if highlights:
            blocks.append(_heading2("⭐ 今日要点"))
            for h in highlights:
                blocks.append(_bullet(h))
            blocks.append(_divider())
        
        # Items by category
        for cat, cat_items in categories.items():
            blocks.append(_heading2(f"📁 {cat} ({len(cat_items)}条)"))
            for item in cat_items:
                title = item.get("title", "无标题")
                summary = item.get("summary", "")[:100]
                url = item.get("url", "")
                
                if url:
                    blocks.append(_paragraph_link(f"📌 {title}", url))
                else:
                    blocks.append(_paragraph(f"📌 {title}"))
                
                if summary:
                    blocks.append(_paragraph(f"  {summary}"))
            
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
        
        if generate_overview_fn:
            overview_data = generate_overview_fn(weekly_reports)
            overview = overview_data.get("overview", "")
            highlights = overview_data.get("dominant_themes", [])
        else:
            overview = self._fallback_overview(weekly_reports)
            highlights = self._extract_themes(weekly_reports)
        
        content_blocks = self._build_content_blocks(weekly_reports, highlights)
        
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
    
    def _extract_themes(self, weekly_reports: List[Dict]) -> List[str]:
        """Extract themes from weekly reports."""
        all_themes = []
        for report in weekly_reports:
            highlights = report.get("highlights") or []
            all_themes.extend(highlights)
        return all_themes[:5]
    
    def _build_content_blocks(
        self,
        weekly_reports: List[Dict],
        highlights: List[str],
    ) -> List[Dict]:
        """Build Notion blocks for monthly report."""
        blocks: List[Dict] = []
        
        # Weekly summary section
        blocks.append(_heading2(f"📆 本月概览 ({len(weekly_reports)}周)"))
        for report in weekly_reports:
            title = report.get("title", "")
            blocks.append(_bullet(title))
        blocks.append(_divider())
        
        # Themes section
        if highlights:
            blocks.append(_heading2("🎯 本月主题"))
            for h in highlights:
                blocks.append(_bullet(h))
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

