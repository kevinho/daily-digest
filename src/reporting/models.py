"""
Data models for the reporting system.
"""

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Any, Dict, List


class ReportType(Enum):
    """Type of report in the recursive summarization hierarchy."""
    
    DAILY = "Daily"
    WEEKLY = "Weekly"
    MONTHLY = "Monthly"


@dataclass
class ReportPeriod:
    """
    Represents a time period for a report.
    
    Attributes:
        type: The report type (Daily, Weekly, Monthly)
        start_date: Period start date (inclusive)
        end_date: Period end date (inclusive)
    """
    
    type: ReportType
    start_date: date
    end_date: date
    
    @property
    def title(self) -> str:
        """
        Generate a human-readable title for the report.
        
        Examples:
            - Daily: "Daily Digest - 2025-01-15"
            - Weekly: "Weekly Digest - W03 2025"
            - Monthly: "Monthly Digest - January 2025"
        """
        if self.type == ReportType.DAILY:
            return f"Daily Digest - {self.start_date.isoformat()}"
        elif self.type == ReportType.WEEKLY:
            week_num = self.start_date.isocalendar()[1]
            return f"Weekly Digest - W{week_num:02d} {self.start_date.year}"
        else:  # MONTHLY
            return f"Monthly Digest - {self.start_date.strftime('%B %Y')}"
    
    @property
    def title_cn(self) -> str:
        """
        Generate a Chinese title for the report.
        
        Examples:
            - Daily: "日报 - 2025-01-15"
            - Weekly: "周报 - 2025年第03周"
            - Monthly: "月报 - 2025年01月"
        """
        if self.type == ReportType.DAILY:
            return f"日报 - {self.start_date.isoformat()}"
        elif self.type == ReportType.WEEKLY:
            week_num = self.start_date.isocalendar()[1]
            return f"周报 - {self.start_date.year}年第{week_num:02d}周"
        else:  # MONTHLY
            return f"月报 - {self.start_date.strftime('%Y年%m月')}"


@dataclass
class ReportData:
    """
    Data structure for report content.
    
    Attributes:
        period: The report period
        overview: AI-generated overview/summary text
        highlights: List of key highlights/trends
        source_ids: IDs of source reports or items
        content_blocks: Notion block content for the page body
        categories: Optional categorization of items (for daily reports)
    """
    
    period: ReportPeriod
    overview: str
    highlights: List[str] = field(default_factory=list)
    source_ids: List[str] = field(default_factory=list)
    content_blocks: List[Dict[str, Any]] = field(default_factory=list)
    categories: Dict[str, List[Dict]] = field(default_factory=dict)
    
    @property
    def source_count(self) -> int:
        """Number of source items/reports."""
        return len(self.source_ids)
    
    @property
    def is_empty(self) -> bool:
        """Check if report has no content."""
        return self.source_count == 0 and not self.overview

