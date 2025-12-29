"""
Tests for date utility functions.
"""

from datetime import date

import pytest

from src.reporting.date_utils import (
    get_daily_range,
    get_weekly_range,
    get_monthly_range,
    get_period_range,
    format_date_range,
)


class TestGetDailyRange:
    """Tests for get_daily_range function."""
    
    def test_normal_date(self):
        """Daily range returns same date for start and end."""
        target = date(2025, 1, 15)
        start, end = get_daily_range(target)
        assert start == target
        assert end == target
    
    def test_month_boundary(self):
        """Daily range works at month boundary."""
        target = date(2025, 1, 31)
        start, end = get_daily_range(target)
        assert start == target
        assert end == target
    
    def test_year_boundary(self):
        """Daily range works at year boundary."""
        target = date(2024, 12, 31)
        start, end = get_daily_range(target)
        assert start == target
        assert end == target


class TestGetWeeklyRange:
    """Tests for get_weekly_range function."""
    
    def test_mid_week(self):
        """Weekly range from mid-week date."""
        # Wednesday Jan 15, 2025
        target = date(2025, 1, 15)
        start, end = get_weekly_range(target)
        assert start == date(2025, 1, 13)  # Monday
        assert end == date(2025, 1, 19)    # Sunday
    
    def test_monday(self):
        """Weekly range when target is Monday."""
        target = date(2025, 1, 13)  # Monday
        start, end = get_weekly_range(target)
        assert start == date(2025, 1, 13)
        assert end == date(2025, 1, 19)
    
    def test_sunday(self):
        """Weekly range when target is Sunday."""
        target = date(2025, 1, 19)  # Sunday
        start, end = get_weekly_range(target)
        assert start == date(2025, 1, 13)
        assert end == date(2025, 1, 19)
    
    def test_week_spanning_months(self):
        """Weekly range when week spans two months."""
        # Feb 1, 2025 is Saturday - week spans Jan/Feb
        target = date(2025, 2, 1)
        start, end = get_weekly_range(target)
        assert start == date(2025, 1, 27)  # Monday in Jan
        assert end == date(2025, 2, 2)     # Sunday in Feb
    
    def test_week_spanning_years(self):
        """Weekly range when week spans two years."""
        # Dec 31, 2024 is Tuesday
        target = date(2024, 12, 31)
        start, end = get_weekly_range(target)
        assert start == date(2024, 12, 30)  # Monday
        assert end == date(2025, 1, 5)      # Sunday in next year


class TestGetMonthlyRange:
    """Tests for get_monthly_range function."""
    
    def test_january(self):
        """Monthly range for January (31 days)."""
        target = date(2025, 1, 15)
        start, end = get_monthly_range(target)
        assert start == date(2025, 1, 1)
        assert end == date(2025, 1, 31)
    
    def test_february_normal(self):
        """Monthly range for February non-leap year (28 days)."""
        target = date(2025, 2, 15)
        start, end = get_monthly_range(target)
        assert start == date(2025, 2, 1)
        assert end == date(2025, 2, 28)
    
    def test_february_leap_year(self):
        """Monthly range for February leap year (29 days)."""
        target = date(2024, 2, 15)  # 2024 is a leap year
        start, end = get_monthly_range(target)
        assert start == date(2024, 2, 1)
        assert end == date(2024, 2, 29)
    
    def test_april(self):
        """Monthly range for April (30 days)."""
        target = date(2025, 4, 15)
        start, end = get_monthly_range(target)
        assert start == date(2025, 4, 1)
        assert end == date(2025, 4, 30)
    
    def test_december(self):
        """Monthly range for December (year boundary)."""
        target = date(2025, 12, 15)
        start, end = get_monthly_range(target)
        assert start == date(2025, 12, 1)
        assert end == date(2025, 12, 31)
    
    def test_first_day_of_month(self):
        """Monthly range when target is first day."""
        target = date(2025, 3, 1)
        start, end = get_monthly_range(target)
        assert start == date(2025, 3, 1)
        assert end == date(2025, 3, 31)
    
    def test_last_day_of_month(self):
        """Monthly range when target is last day."""
        target = date(2025, 3, 31)
        start, end = get_monthly_range(target)
        assert start == date(2025, 3, 1)
        assert end == date(2025, 3, 31)


class TestGetPeriodRange:
    """Tests for get_period_range helper function."""
    
    def test_daily(self):
        """Period range for daily type."""
        target = date(2025, 1, 15)
        start, end = get_period_range("daily", target)
        assert start == target
        assert end == target
    
    def test_weekly(self):
        """Period range for weekly type."""
        target = date(2025, 1, 15)
        start, end = get_period_range("weekly", target)
        assert start == date(2025, 1, 13)
        assert end == date(2025, 1, 19)
    
    def test_monthly(self):
        """Period range for monthly type."""
        target = date(2025, 1, 15)
        start, end = get_period_range("monthly", target)
        assert start == date(2025, 1, 1)
        assert end == date(2025, 1, 31)
    
    def test_case_insensitive(self):
        """Period range type is case-insensitive."""
        target = date(2025, 1, 15)
        
        start1, end1 = get_period_range("DAILY", target)
        start2, end2 = get_period_range("Daily", target)
        start3, end3 = get_period_range("daily", target)
        
        assert start1 == start2 == start3
        assert end1 == end2 == end3
    
    def test_invalid_type(self):
        """Period range raises error for invalid type."""
        target = date(2025, 1, 15)
        with pytest.raises(ValueError, match="Unknown report type"):
            get_period_range("yearly", target)


class TestFormatDateRange:
    """Tests for format_date_range helper function."""
    
    def test_same_date(self):
        """Format single date when start equals end."""
        start = end = date(2025, 1, 15)
        result = format_date_range(start, end)
        assert result == "2025-01-15"
    
    def test_different_dates(self):
        """Format date range when dates differ."""
        start = date(2025, 1, 13)
        end = date(2025, 1, 19)
        result = format_date_range(start, end)
        assert result == "2025-01-13 ~ 2025-01-19"

