"""
Date utility functions for calculating report periods.
"""

from datetime import date, timedelta
from typing import Tuple


def get_daily_range(target_date: date) -> Tuple[date, date]:
    """
    Get the date range for a daily report.
    
    Args:
        target_date: The target date
        
    Returns:
        Tuple of (start_date, end_date), both are the same date
        
    Example:
        >>> get_daily_range(date(2025, 1, 15))
        (date(2025, 1, 15), date(2025, 1, 15))
    """
    return (target_date, target_date)


def get_weekly_range(target_date: date) -> Tuple[date, date]:
    """
    Get the date range for a weekly report (Monday to Sunday, ISO week).
    
    Args:
        target_date: Any date within the target week
        
    Returns:
        Tuple of (monday, sunday) for the week containing target_date
        
    Example:
        >>> get_weekly_range(date(2025, 1, 15))  # Wednesday
        (date(2025, 1, 13), date(2025, 1, 19))  # Mon-Sun
    """
    # Monday is weekday 0 in Python
    monday = target_date - timedelta(days=target_date.weekday())
    sunday = monday + timedelta(days=6)
    return (monday, sunday)


def get_monthly_range(target_date: date) -> Tuple[date, date]:
    """
    Get the date range for a monthly report.
    
    Args:
        target_date: Any date within the target month
        
    Returns:
        Tuple of (first_day, last_day) of the month
        
    Example:
        >>> get_monthly_range(date(2025, 1, 15))
        (date(2025, 1, 1), date(2025, 1, 31))
        
        >>> get_monthly_range(date(2025, 2, 15))  # Feb 2025 (not leap year)
        (date(2025, 2, 1), date(2025, 2, 28))
        
        >>> get_monthly_range(date(2024, 2, 15))  # Feb 2024 (leap year)
        (date(2024, 2, 1), date(2024, 2, 29))
    """
    first_day = target_date.replace(day=1)
    
    # Calculate last day by going to next month and subtracting 1 day
    if target_date.month == 12:
        # December -> January of next year
        next_month_first = target_date.replace(year=target_date.year + 1, month=1, day=1)
    else:
        next_month_first = target_date.replace(month=target_date.month + 1, day=1)
    
    last_day = next_month_first - timedelta(days=1)
    return (first_day, last_day)


def get_period_range(report_type: str, target_date: date) -> Tuple[date, date]:
    """
    Get date range based on report type string.
    
    Args:
        report_type: One of "daily", "weekly", "monthly" (case-insensitive)
        target_date: Target date for the period
        
    Returns:
        Tuple of (start_date, end_date)
        
    Raises:
        ValueError: If report_type is not recognized
    """
    report_type_lower = report_type.lower()
    
    if report_type_lower == "daily":
        return get_daily_range(target_date)
    elif report_type_lower == "weekly":
        return get_weekly_range(target_date)
    elif report_type_lower == "monthly":
        return get_monthly_range(target_date)
    else:
        raise ValueError(f"Unknown report type: {report_type}")


def format_date_range(start: date, end: date) -> str:
    """
    Format a date range for display.
    
    Args:
        start: Start date
        end: End date
        
    Returns:
        Formatted string like "2025-01-13 ~ 2025-01-19" or "2025-01-15" if same
    """
    if start == end:
        return start.isoformat()
    return f"{start.isoformat()} ~ {end.isoformat()}"

