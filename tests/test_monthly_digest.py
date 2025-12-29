"""
Tests for monthly digest generation.
"""

from datetime import date
from unittest.mock import MagicMock

import pytest

from src.reporting.models import ReportType, ReportPeriod
from src.reporting.builder import MonthlyReportBuilder
from src.reporting.date_utils import get_monthly_range


class TestMonthlyReportBuilder:
    """Tests for MonthlyReportBuilder."""
    
    def test_build_empty_reports(self):
        """Builder handles empty weekly reports list."""
        builder = MonthlyReportBuilder()
        period = ReportPeriod(
            type=ReportType.MONTHLY,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 31),
        )
        
        result = builder.build(weekly_reports=[], period=period)
        
        assert result.overview == "本月无周报记录。"
        assert result.source_ids == []
    
    def test_build_extracts_weekly_ids(self):
        """Builder collects weekly report IDs as sources."""
        builder = MonthlyReportBuilder()
        period = ReportPeriod(
            type=ReportType.MONTHLY,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 31),
        )
        
        weekly_reports = [
            {"id": "weekly-1", "title": "Weekly W01", "highlights": ["AI"]},
            {"id": "weekly-2", "title": "Weekly W02", "highlights": ["Tech"]},
        ]
        
        result = builder.build(weekly_reports=weekly_reports, period=period)
        
        assert "weekly-1" in result.source_ids
        assert "weekly-2" in result.source_ids
    
    def test_build_generates_content_blocks(self):
        """Builder creates Notion blocks for monthly content."""
        builder = MonthlyReportBuilder()
        period = ReportPeriod(
            type=ReportType.MONTHLY,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 31),
        )
        
        weekly_reports = [
            {"id": "w1", "title": "Weekly Digest - W01 2025"},
        ]
        
        result = builder.build(weekly_reports=weekly_reports, period=period)
        
        assert len(result.content_blocks) > 0
    
    def test_build_with_ai_overview(self):
        """Builder uses AI function when provided."""
        builder = MonthlyReportBuilder()
        period = ReportPeriod(
            type=ReportType.MONTHLY,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 31),
        )
        
        weekly_reports = [{"id": "w1", "title": "Weekly", "highlights": []}]
        
        mock_overview_fn = MagicMock(return_value={
            "overview": "AI monthly overview",
            "dominant_themes": ["Theme 1", "Theme 2"],
            "evolution": "Topics evolved from X to Y",
        })
        
        result = builder.build(
            weekly_reports=weekly_reports,
            period=period,
            generate_overview_fn=mock_overview_fn,
        )
        
        assert result.overview == "AI monthly overview"
        assert "Theme 1" in result.highlights
        mock_overview_fn.assert_called_once()


class TestMonthlyDigestService:
    """Integration tests for monthly digest generation."""
    
    def test_service_skips_existing_report(self):
        """Service returns existing monthly report ID."""
        from src.reporting.service import DigestService
        
        mock_inbox = MagicMock()
        mock_reporting = MagicMock()
        mock_reporting.find_report.return_value = {"id": "existing-monthly"}
        
        service = DigestService(mock_inbox, mock_reporting)
        
        result = service.generate_monthly(date(2025, 1, 15))
        
        assert result == "existing-monthly"
    
    def test_service_queries_weekly_reports_in_range(self):
        """Service queries weekly reports for the month."""
        from src.reporting.service import DigestService
        
        mock_inbox = MagicMock()
        mock_reporting = MagicMock()
        mock_reporting.find_report.return_value = None
        mock_reporting.query_reports_in_range.return_value = [
            {"id": "w1", "title": "Weekly W01", "highlights": []},
            {"id": "w2", "title": "Weekly W02", "highlights": []},
        ]
        mock_reporting.create_report.return_value = "new-monthly-id"
        
        service = DigestService(mock_inbox, mock_reporting)
        
        result = service.generate_monthly(date(2025, 1, 15))
        
        # Should query for Weekly reports in the month range
        mock_reporting.query_reports_in_range.assert_called_once()
        call_args = mock_reporting.query_reports_in_range.call_args
        assert call_args[1]["report_type"] == "Weekly"
        assert result == "new-monthly-id"
    
    def test_service_returns_none_for_no_weeklies(self):
        """Service returns None when no weekly reports found."""
        from src.reporting.service import DigestService
        
        mock_inbox = MagicMock()
        mock_reporting = MagicMock()
        mock_reporting.find_report.return_value = None
        mock_reporting.query_reports_in_range.return_value = []
        
        service = DigestService(mock_inbox, mock_reporting)
        
        result = service.generate_monthly(date(2025, 1, 15))
        
        assert result is None
        mock_reporting.create_report.assert_not_called()


class TestMonthlyDateRange:
    """Tests for monthly date range calculation."""
    
    def test_january_31_days(self):
        """January has 31 days."""
        start, end = get_monthly_range(date(2025, 1, 15))
        assert start == date(2025, 1, 1)
        assert end == date(2025, 1, 31)
    
    def test_february_non_leap(self):
        """February 2025 has 28 days (not leap year)."""
        start, end = get_monthly_range(date(2025, 2, 15))
        assert start == date(2025, 2, 1)
        assert end == date(2025, 2, 28)
    
    def test_february_leap_year(self):
        """February 2024 has 29 days (leap year)."""
        start, end = get_monthly_range(date(2024, 2, 15))
        assert start == date(2024, 2, 1)
        assert end == date(2024, 2, 29)
    
    def test_december_year_boundary(self):
        """December handles year boundary correctly."""
        start, end = get_monthly_range(date(2025, 12, 15))
        assert start == date(2025, 12, 1)
        assert end == date(2025, 12, 31)
    
    def test_april_30_days(self):
        """April has 30 days."""
        start, end = get_monthly_range(date(2025, 4, 15))
        assert start == date(2025, 4, 1)
        assert end == date(2025, 4, 30)

