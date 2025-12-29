"""
Reporting module for recursive summarization system.

This module provides hierarchical digest generation:
- Daily: Summarizes individual items from Inbox
- Weekly: Summarizes daily digests
- Monthly: Summarizes weekly digests
"""

from src.reporting.models import ReportType, ReportPeriod, ReportData
from src.reporting.date_utils import (
    get_daily_range,
    get_weekly_range,
    get_monthly_range,
)

__all__ = [
    "ReportType",
    "ReportPeriod",
    "ReportData",
    "get_daily_range",
    "get_weekly_range",
    "get_monthly_range",
]

