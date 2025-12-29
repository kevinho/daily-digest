"""
Tests for weekly digest generation.
"""

from datetime import date
from unittest.mock import MagicMock

import pytest

from src.reporting.models import ReportType, ReportPeriod
from src.reporting.builder import WeeklyReportBuilder
from src.reporting.date_utils import get_weekly_range


class TestWeeklyReportBuilder:
    """Tests for WeeklyReportBuilder."""
    
    def test_build_empty_reports(self):
        """Builder handles empty daily reports list."""
        builder = WeeklyReportBuilder()
        period = ReportPeriod(
            type=ReportType.WEEKLY,
            start_date=date(2025, 1, 13),
            end_date=date(2025, 1, 19),
        )
        
        result = builder.build(daily_reports=[], period=period)
        
        assert result.overview == "本周无日报记录。"
        assert result.source_ids == []
    
    def test_build_extracts_daily_ids(self):
        """Builder collects daily report IDs as sources."""
        builder = WeeklyReportBuilder()
        period = ReportPeriod(
            type=ReportType.WEEKLY,
            start_date=date(2025, 1, 13),
            end_date=date(2025, 1, 19),
        )
        
        daily_reports = [
            {"id": "daily-1", "title": "Daily 1", "date": "2025-01-13", "summary": "Day 1"},
            {"id": "daily-2", "title": "Daily 2", "date": "2025-01-14", "summary": "Day 2"},
        ]
        
        result = builder.build(daily_reports=daily_reports, period=period)
        
        assert "daily-1" in result.source_ids
        assert "daily-2" in result.source_ids
    
    def test_build_generates_content_blocks(self):
        """Builder creates Notion blocks for weekly content."""
        builder = WeeklyReportBuilder()
        period = ReportPeriod(
            type=ReportType.WEEKLY,
            start_date=date(2025, 1, 13),
            end_date=date(2025, 1, 19),
        )
        
        daily_reports = [
            {"id": "d1", "title": "Daily Digest - 2025-01-13", "date": "2025-01-13"},
        ]
        
        result = builder.build(daily_reports=daily_reports, period=period)
        
        assert len(result.content_blocks) > 0
    
    def test_build_with_ai_overview(self):
        """Builder uses AI function when provided."""
        builder = WeeklyReportBuilder()
        period = ReportPeriod(
            type=ReportType.WEEKLY,
            start_date=date(2025, 1, 13),
            end_date=date(2025, 1, 19),
        )
        
        daily_reports = [{"id": "d1", "title": "Daily", "date": "2025-01-13"}]
        
        mock_overview_fn = MagicMock(return_value={
            "overview": "AI weekly overview",
            "trends": ["Trend 1", "Trend 2"],
            "emerging": ["New topic"],
            "fading": [],
        })
        
        result = builder.build(
            daily_reports=daily_reports,
            period=period,
            generate_overview_fn=mock_overview_fn,
        )
        
        assert result.overview == "AI weekly overview"
        assert "Trend 1" in result.highlights
        mock_overview_fn.assert_called_once()


class TestWeeklyDigestService:
    """Integration tests for weekly digest generation."""
    
    def test_service_skips_existing_report(self):
        """Service returns existing weekly report ID."""
        from src.reporting.service import DigestService
        
        mock_inbox = MagicMock()
        mock_reporting = MagicMock()
        mock_reporting.find_report.return_value = {"id": "existing-weekly"}
        
        service = DigestService(mock_inbox, mock_reporting)
        
        result = service.generate_weekly(date(2025, 1, 15))
        
        assert result == "existing-weekly"
    
    def test_service_queries_daily_reports_in_range(self):
        """Service queries daily reports for the week."""
        from src.reporting.service import DigestService
        
        mock_inbox = MagicMock()
        mock_reporting = MagicMock()
        mock_reporting.find_report.return_value = None
        mock_reporting.query_reports_in_range.return_value = [
            {"id": "d1", "title": "Daily 1", "date": "2025-01-13"},
            {"id": "d2", "title": "Daily 2", "date": "2025-01-14"},
        ]
        mock_reporting.create_report.return_value = "new-weekly-id"
        
        service = DigestService(mock_inbox, mock_reporting)
        
        result = service.generate_weekly(date(2025, 1, 15))
        
        # Should query for Daily reports in the week range
        mock_reporting.query_reports_in_range.assert_called_once()
        call_args = mock_reporting.query_reports_in_range.call_args
        assert call_args[1]["report_type"] == "Daily"
        assert result == "new-weekly-id"
    
    def test_service_returns_none_for_no_dailies(self):
        """Service returns None when no daily reports found."""
        from src.reporting.service import DigestService
        
        mock_inbox = MagicMock()
        mock_reporting = MagicMock()
        mock_reporting.find_report.return_value = None
        mock_reporting.query_reports_in_range.return_value = []
        
        service = DigestService(mock_inbox, mock_reporting)
        
        result = service.generate_weekly(date(2025, 1, 15))
        
        assert result is None
        mock_reporting.create_report.assert_not_called()
    
    def test_service_warns_about_missing_dailies(self):
        """Service logs warning when fewer than 7 dailies."""
        from src.reporting.service import DigestService
        
        mock_inbox = MagicMock()
        mock_reporting = MagicMock()
        mock_reporting.find_report.return_value = None
        mock_reporting.query_reports_in_range.return_value = [
            {"id": "d1", "title": "Daily 1", "date": "2025-01-13"},
            {"id": "d2", "title": "Daily 2", "date": "2025-01-14"},
        ]
        mock_reporting.create_report.return_value = "weekly-id"
        
        service = DigestService(mock_inbox, mock_reporting)
        
        # Should complete without exception, warning is logged internally
        result = service.generate_weekly(date(2025, 1, 15))
        assert result == "weekly-id"


class TestWeeklyDateRange:
    """Tests for weekly date range calculation."""
    
    def test_mid_week_wednesday(self):
        """Get week range from Wednesday."""
        start, end = get_weekly_range(date(2025, 1, 15))  # Wednesday
        assert start == date(2025, 1, 13)  # Monday
        assert end == date(2025, 1, 19)    # Sunday
    
    def test_week_start_monday(self):
        """Get week range when target is Monday."""
        start, end = get_weekly_range(date(2025, 1, 13))
        assert start == date(2025, 1, 13)
        assert end == date(2025, 1, 19)
    
    def test_week_end_sunday(self):
        """Get week range when target is Sunday."""
        start, end = get_weekly_range(date(2025, 1, 19))
        assert start == date(2025, 1, 13)
        assert end == date(2025, 1, 19)

