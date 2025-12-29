"""
Digest service - orchestrates recursive summarization.
"""

import logging
from datetime import date
from typing import Optional

from src.reporting.models import ReportData, ReportPeriod, ReportType
from src.reporting.date_utils import (
    get_daily_range,
    get_weekly_range,
    get_monthly_range,
)
from src.reporting.builder import (
    DailyReportBuilder,
    WeeklyReportBuilder,
    MonthlyReportBuilder,
)

logger = logging.getLogger(__name__)


class DigestService:
    """
    Orchestrates the recursive summarization system.
    
    Responsibilities:
    - Coordinate report generation at each level
    - Check for existing reports (prevent duplicates)
    - Query source data from appropriate databases
    - Create reports in Reporting DB
    """
    
    def __init__(self, inbox_manager, reporting_manager):
        """
        Initialize the digest service.
        
        Args:
            inbox_manager: NotionManager for the Inbox database
            reporting_manager: ReportingDBManager for the Reporting database
        """
        self.inbox = inbox_manager
        self.reporting = reporting_manager
        
        # Builders for each level
        self.daily_builder = DailyReportBuilder()
        self.weekly_builder = WeeklyReportBuilder()
        self.monthly_builder = MonthlyReportBuilder()
    
    def generate_daily(
        self,
        target_date: date,
        force: bool = False,
    ) -> Optional[str]:
        """
        Generate a daily digest for the target date.
        
        Args:
            target_date: Date to generate digest for
            force: If True, regenerate even if exists
            
        Returns:
            Page ID of the created/existing report, or None on failure
        """
        start_date, end_date = get_daily_range(target_date)
        period = ReportPeriod(
            type=ReportType.DAILY,
            start_date=start_date,
            end_date=end_date,
        )
        
        # Check for existing report
        if not force:
            existing = self.reporting.find_report(ReportType.DAILY.value, start_date)
            if existing:
                logger.info(f"Daily report already exists for {start_date}: {existing.get('id')}")
                return existing.get("id")
        
        # Query items from Inbox
        items = self.inbox.fetch_items_for_date(start_date)
        logger.info(f"Found {len(items)} items for {start_date}")
        
        if not items:
            logger.warning(f"No items found for {start_date}, skipping digest")
            return None
        
        # Build report
        report_data = self.daily_builder.build(
            items=items,
            period=period,
            generate_overview_fn=self._get_daily_overview_fn(),
        )
        
        # Create in Reporting DB
        page_id = self.reporting.create_report(
            report_data=report_data,
            source_item_ids=report_data.source_ids,
        )
        
        logger.info(f"Created daily digest for {start_date}: {page_id}")
        return page_id
    
    def generate_weekly(
        self,
        target_date: date,
        force: bool = False,
    ) -> Optional[str]:
        """
        Generate a weekly digest for the week containing target_date.
        
        Args:
            target_date: Any date within the target week
            force: If True, regenerate even if exists
            
        Returns:
            Page ID of the created/existing report, or None on failure
        """
        start_date, end_date = get_weekly_range(target_date)
        period = ReportPeriod(
            type=ReportType.WEEKLY,
            start_date=start_date,
            end_date=end_date,
        )
        
        # Check for existing report
        if not force:
            existing = self.reporting.find_report(ReportType.WEEKLY.value, start_date)
            if existing:
                logger.info(f"Weekly report already exists for week of {start_date}: {existing.get('id')}")
                return existing.get("id")
        
        # Query daily reports for the week
        daily_reports = self.reporting.query_reports_in_range(
            report_type=ReportType.DAILY.value,
            start_date=start_date,
            end_date=end_date,
        )
        
        # Warn about missing dailies
        expected_days = 7
        if len(daily_reports) < expected_days:
            missing = expected_days - len(daily_reports)
            logger.warning(f"Weekly digest: {missing} daily reports missing for week of {start_date}")
        
        if not daily_reports:
            logger.warning(f"No daily reports found for week of {start_date}, skipping weekly digest")
            return None
        
        # Build report
        report_data = self.weekly_builder.build(
            daily_reports=daily_reports,
            period=period,
            generate_overview_fn=self._get_weekly_overview_fn(),
        )
        
        # Create in Reporting DB
        page_id = self.reporting.create_report(
            report_data=report_data,
            source_report_ids=report_data.source_ids,
        )
        
        logger.info(f"Created weekly digest for week of {start_date}: {page_id}")
        return page_id
    
    def generate_monthly(
        self,
        target_date: date,
        force: bool = False,
    ) -> Optional[str]:
        """
        Generate a monthly digest for the month containing target_date.
        
        Args:
            target_date: Any date within the target month
            force: If True, regenerate even if exists
            
        Returns:
            Page ID of the created/existing report, or None on failure
        """
        start_date, end_date = get_monthly_range(target_date)
        period = ReportPeriod(
            type=ReportType.MONTHLY,
            start_date=start_date,
            end_date=end_date,
        )
        
        # Check for existing report
        if not force:
            existing = self.reporting.find_report(ReportType.MONTHLY.value, start_date)
            if existing:
                logger.info(f"Monthly report already exists for {start_date.strftime('%Y-%m')}: {existing.get('id')}")
                return existing.get("id")
        
        # Query weekly reports for the month
        weekly_reports = self.reporting.query_reports_in_range(
            report_type=ReportType.WEEKLY.value,
            start_date=start_date,
            end_date=end_date,
        )
        
        # Warn about missing weeklies
        # Rough estimate: 4-5 weeks per month
        if len(weekly_reports) < 4:
            logger.warning(f"Monthly digest: Only {len(weekly_reports)} weekly reports for {start_date.strftime('%Y-%m')}")
        
        if not weekly_reports:
            logger.warning(f"No weekly reports found for {start_date.strftime('%Y-%m')}, skipping monthly digest")
            return None
        
        # Build report
        report_data = self.monthly_builder.build(
            weekly_reports=weekly_reports,
            period=period,
            generate_overview_fn=self._get_monthly_overview_fn(),
        )
        
        # Create in Reporting DB
        page_id = self.reporting.create_report(
            report_data=report_data,
            source_report_ids=report_data.source_ids,
        )
        
        logger.info(f"Created monthly digest for {start_date.strftime('%Y-%m')}: {page_id}")
        return page_id
    
    def _get_daily_overview_fn(self):
        """Get the AI overview function for daily digests."""
        try:
            from src.llm import generate_daily_digest
            return generate_daily_digest
        except ImportError:
            return None
    
    def _get_weekly_overview_fn(self):
        """Get the AI overview function for weekly digests."""
        try:
            from src.llm import generate_weekly_digest
            return generate_weekly_digest
        except ImportError:
            return None
    
    def _get_monthly_overview_fn(self):
        """Get the AI overview function for monthly digests."""
        try:
            from src.llm import generate_monthly_digest
            return generate_monthly_digest
        except ImportError:
            return None

