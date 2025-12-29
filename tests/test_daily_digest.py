"""
Tests for daily digest generation.
"""

from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from src.reporting.models import ReportType, ReportPeriod, ReportData
from src.reporting.builder import DailyReportBuilder


class TestDailyReportBuilder:
    """Tests for DailyReportBuilder."""
    
    def test_build_empty_items(self):
        """Builder handles empty item list."""
        builder = DailyReportBuilder()
        period = ReportPeriod(
            type=ReportType.DAILY,
            start_date=date(2025, 1, 15),
            end_date=date(2025, 1, 15),
        )
        
        result = builder.build(items=[], period=period)
        
        assert result.overview == "今日无新增内容。"
        assert result.source_ids == []
        assert result.highlights == []
    
    def test_build_groups_by_tags(self):
        """Builder correctly groups items by tags."""
        builder = DailyReportBuilder()
        period = ReportPeriod(
            type=ReportType.DAILY,
            start_date=date(2025, 1, 15),
            end_date=date(2025, 1, 15),
        )
        
        items = [
            {"id": "1", "title": "Article 1", "tags": ["tech"], "summary": "Tech content"},
            {"id": "2", "title": "Article 2", "tags": ["tech"], "summary": "More tech"},
            {"id": "3", "title": "Article 3", "tags": ["news"], "summary": "News content"},
        ]
        
        result = builder.build(items=items, period=period)
        
        assert "tech" in result.categories
        assert "news" in result.categories
        assert len(result.categories["tech"]) == 2
        assert len(result.categories["news"]) == 1
    
    def test_build_extracts_source_ids(self):
        """Builder collects all source IDs."""
        builder = DailyReportBuilder()
        period = ReportPeriod(
            type=ReportType.DAILY,
            start_date=date(2025, 1, 15),
            end_date=date(2025, 1, 15),
        )
        
        items = [
            {"id": "id-1", "title": "A", "tags": ["x"]},
            {"id": "id-2", "title": "B", "tags": ["y"]},
        ]
        
        result = builder.build(items=items, period=period)
        
        assert "id-1" in result.source_ids
        assert "id-2" in result.source_ids
    
    def test_build_generates_content_blocks(self):
        """Builder creates Notion blocks for content."""
        builder = DailyReportBuilder()
        period = ReportPeriod(
            type=ReportType.DAILY,
            start_date=date(2025, 1, 15),
            end_date=date(2025, 1, 15),
        )
        
        items = [
            {"id": "1", "title": "Test Article", "tags": ["tech"], "summary": "Test summary"},
        ]
        
        result = builder.build(items=items, period=period)
        
        # Should have content blocks
        assert len(result.content_blocks) > 0
        # Check for expected block types
        block_types = [b.get("type") for b in result.content_blocks]
        assert "heading_2" in block_types
        assert "bulleted_list_item" in block_types
    
    def test_build_with_ai_overview(self):
        """Builder uses AI function when provided."""
        builder = DailyReportBuilder()
        period = ReportPeriod(
            type=ReportType.DAILY,
            start_date=date(2025, 1, 15),
            end_date=date(2025, 1, 15),
        )
        
        items = [{"id": "1", "title": "Test", "tags": ["tech"]}]
        
        mock_overview_fn = MagicMock(return_value={
            "overview": "AI generated overview",
            "highlights": ["Point 1", "Point 2"],
        })
        
        result = builder.build(
            items=items,
            period=period,
            generate_overview_fn=mock_overview_fn,
        )
        
        assert result.overview == "AI generated overview"
        assert result.highlights == ["Point 1", "Point 2"]
        mock_overview_fn.assert_called_once()
    
    def test_build_handles_items_without_tags(self):
        """Builder handles items with no tags (uses '未分类')."""
        builder = DailyReportBuilder()
        period = ReportPeriod(
            type=ReportType.DAILY,
            start_date=date(2025, 1, 15),
            end_date=date(2025, 1, 15),
        )
        
        items = [
            {"id": "1", "title": "No Tags", "tags": []},
            {"id": "2", "title": "Null Tags", "tags": None},
        ]
        
        result = builder.build(items=items, period=period)
        
        # Items without tags go to "未分类"
        assert "未分类" in result.categories
        assert len(result.categories["未分类"]) == 2


class TestDailyDigestService:
    """Integration tests for daily digest generation."""
    
    def test_service_skips_existing_report(self):
        """Service returns existing report ID if found."""
        from src.reporting.service import DigestService
        
        # Mock managers
        mock_inbox = MagicMock()
        mock_reporting = MagicMock()
        mock_reporting.find_report.return_value = {"id": "existing-id"}
        
        service = DigestService(mock_inbox, mock_reporting)
        
        result = service.generate_daily(date(2025, 1, 15), force=False)
        
        assert result == "existing-id"
        mock_inbox.fetch_ready_for_digest.assert_not_called()
    
    def test_service_generates_new_report(self):
        """Service creates new report when none exists."""
        from src.reporting.service import DigestService
        
        mock_inbox = MagicMock()
        mock_inbox.fetch_ready_for_digest.return_value = [
            {"id": "item-1", "title": "Test", "tags": ["tech"], "summary": "Test summary"},
        ]
        
        mock_reporting = MagicMock()
        mock_reporting.find_report.return_value = None
        mock_reporting.create_report.return_value = "new-page-id"
        
        service = DigestService(mock_inbox, mock_reporting)
        
        result = service.generate_daily(date(2025, 1, 15))
        
        assert result == "new-page-id"
        mock_reporting.create_report.assert_called_once()
    
    def test_service_force_regenerates(self):
        """Service regenerates when force=True."""
        from src.reporting.service import DigestService
        
        mock_inbox = MagicMock()
        mock_inbox.fetch_ready_for_digest.return_value = [
            {"id": "item-1", "title": "Test", "tags": ["tech"]},
        ]
        
        mock_reporting = MagicMock()
        mock_reporting.create_report.return_value = "new-page-id"
        
        service = DigestService(mock_inbox, mock_reporting)
        
        result = service.generate_daily(date(2025, 1, 15), force=True)
        
        # Should not check for existing report
        mock_reporting.find_report.assert_not_called()
        assert result == "new-page-id"
    
    def test_service_returns_none_for_empty_items(self):
        """Service returns None when no items found."""
        from src.reporting.service import DigestService
        
        mock_inbox = MagicMock()
        mock_inbox.fetch_ready_for_digest.return_value = []
        
        mock_reporting = MagicMock()
        mock_reporting.find_report.return_value = None
        
        service = DigestService(mock_inbox, mock_reporting)
        
        result = service.generate_daily(date(2025, 1, 15))
        
        assert result is None
        mock_reporting.create_report.assert_not_called()

