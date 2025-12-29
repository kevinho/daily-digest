"""
Tests for reporting models.
"""

from datetime import date

import pytest

from src.reporting.models import ReportType, ReportPeriod, ReportData


class TestReportType:
    """Tests for ReportType enum."""
    
    def test_values(self):
        """Check enum values."""
        assert ReportType.DAILY.value == "Daily"
        assert ReportType.WEEKLY.value == "Weekly"
        assert ReportType.MONTHLY.value == "Monthly"
    
    def test_from_string(self):
        """Create enum from string value."""
        assert ReportType("Daily") == ReportType.DAILY
        assert ReportType("Weekly") == ReportType.WEEKLY
        assert ReportType("Monthly") == ReportType.MONTHLY


class TestReportPeriod:
    """Tests for ReportPeriod dataclass."""
    
    def test_daily_title(self):
        """Daily report title format."""
        period = ReportPeriod(
            type=ReportType.DAILY,
            start_date=date(2025, 1, 15),
            end_date=date(2025, 1, 15),
        )
        assert period.title == "Daily Digest - 2025-01-15"
    
    def test_weekly_title(self):
        """Weekly report title format with week number."""
        period = ReportPeriod(
            type=ReportType.WEEKLY,
            start_date=date(2025, 1, 13),
            end_date=date(2025, 1, 19),
        )
        assert period.title == "Weekly Digest - W03 2025"
    
    def test_monthly_title(self):
        """Monthly report title format."""
        period = ReportPeriod(
            type=ReportType.MONTHLY,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 31),
        )
        assert period.title == "Monthly Digest - January 2025"
    
    def test_daily_title_cn(self):
        """Daily report Chinese title."""
        period = ReportPeriod(
            type=ReportType.DAILY,
            start_date=date(2025, 1, 15),
            end_date=date(2025, 1, 15),
        )
        assert period.title_cn == "日报 - 2025-01-15"
    
    def test_weekly_title_cn(self):
        """Weekly report Chinese title."""
        period = ReportPeriod(
            type=ReportType.WEEKLY,
            start_date=date(2025, 1, 13),
            end_date=date(2025, 1, 19),
        )
        assert period.title_cn == "周报 - 2025年第03周"
    
    def test_monthly_title_cn(self):
        """Monthly report Chinese title."""
        period = ReportPeriod(
            type=ReportType.MONTHLY,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 31),
        )
        assert period.title_cn == "月报 - 2025年01月"


class TestReportData:
    """Tests for ReportData dataclass."""
    
    def test_default_values(self):
        """ReportData has correct default values."""
        period = ReportPeriod(
            type=ReportType.DAILY,
            start_date=date(2025, 1, 15),
            end_date=date(2025, 1, 15),
        )
        data = ReportData(period=period, overview="Test overview")
        
        assert data.highlights == []
        assert data.source_ids == []
        assert data.content_blocks == []
        assert data.categories == {}
    
    def test_source_count(self):
        """ReportData source_count property."""
        period = ReportPeriod(
            type=ReportType.DAILY,
            start_date=date(2025, 1, 15),
            end_date=date(2025, 1, 15),
        )
        data = ReportData(
            period=period,
            overview="Test",
            source_ids=["id1", "id2", "id3"],
        )
        assert data.source_count == 3
    
    def test_is_empty_with_no_content(self):
        """ReportData is_empty when no sources and no overview."""
        period = ReportPeriod(
            type=ReportType.DAILY,
            start_date=date(2025, 1, 15),
            end_date=date(2025, 1, 15),
        )
        data = ReportData(period=period, overview="")
        assert data.is_empty is True
    
    def test_is_empty_with_overview(self):
        """ReportData is not empty when has overview."""
        period = ReportPeriod(
            type=ReportType.DAILY,
            start_date=date(2025, 1, 15),
            end_date=date(2025, 1, 15),
        )
        data = ReportData(period=period, overview="Some content")
        assert data.is_empty is False
    
    def test_is_empty_with_sources(self):
        """ReportData is not empty when has sources."""
        period = ReportPeriod(
            type=ReportType.DAILY,
            start_date=date(2025, 1, 15),
            end_date=date(2025, 1, 15),
        )
        data = ReportData(period=period, overview="", source_ids=["id1"])
        assert data.is_empty is False

