"""Natural language date parsing for Memos MCP server."""
import re
from datetime import datetime, timedelta
from typing import Tuple


def parse_date_range(expression: str) -> Tuple[str, str]:
    """
    Parse natural language date expressions into ISO date strings.
    
    Args:
        expression: Natural language date expression (Chinese or English)
        
    Returns:
        Tuple of (start_date, end_date) in ISO format (YYYY-MM-DD)
        
    Raises:
        ValueError: If expression cannot be parsed
        
    Examples:
        >>> parse_date_range("今天")
        ('2026-01-13', '2026-01-13')
        >>> parse_date_range("过去一周")
        ('2026-01-06', '2026-01-13')
    """
    expression = expression.strip().lower()
    now = datetime.now()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Helper function to format date
    def fmt(dt: datetime) -> str:
        return dt.strftime("%Y-%m-%d")
    
    # 今天 / today
    if expression in ["今天", "today"]:
        return (fmt(today), fmt(today))
    
    # 昨天 / yesterday
    if expression in ["昨天", "yesterday"]:
        yesterday = today - timedelta(days=1)
        return (fmt(yesterday), fmt(yesterday))
    
    # 前天 / day before yesterday
    if expression in ["前天", "day before yesterday"]:
        day_before = today - timedelta(days=2)
        return (fmt(day_before), fmt(day_before))
    
    # 过去N天 / last N days / past N days
    match = re.match(r"过去(\d+)天", expression)
    if not match:
        match = re.match(r"(?:last|past)\s*(\d+)\s*days?", expression)
    if match:
        days = int(match.group(1))
        start = today - timedelta(days=days - 1)
        return (fmt(start), fmt(today))
    
    # 最近N天 / recent N days
    match = re.match(r"最近(\d+)天", expression)
    if not match:
        match = re.match(r"recent\s*(\d+)\s*days?", expression)
    if match:
        days = int(match.group(1))
        start = today - timedelta(days=days - 1)
        return (fmt(start), fmt(today))
    
    # 本周 / this week (周一到今天)
    if expression in ["本周", "this week"]:
        weekday = today.weekday()  # 0=Monday, 6=Sunday
        monday = today - timedelta(days=weekday)
        return (fmt(monday), fmt(today))
    
    # 上周 / last week (上周一到上周日)
    if expression in ["上周", "last week"]:
        weekday = today.weekday()
        last_monday = today - timedelta(days=weekday + 7)
        last_sunday = last_monday + timedelta(days=6)
        return (fmt(last_monday), fmt(last_sunday))
    
    # 这周一到周五 / this week monday to friday
    if expression in ["这周一到周五", "this week monday to friday"]:
        weekday = today.weekday()
        monday = today - timedelta(days=weekday)
        friday = monday + timedelta(days=4)
        # 如果今天是周末，返回本周一到周五
        # 如果今天是工作日，返回周一到今天
        end = min(friday, today)
        return (fmt(monday), fmt(end))
    
    # 本月 / this month
    if expression in ["本月", "this month"]:
        first_day = today.replace(day=1)
        return (fmt(first_day), fmt(today))
    
    # 上个月 / last month
    if expression in ["上个月", "上月", "last month"]:
        first_day_this_month = today.replace(day=1)
        last_day_last_month = first_day_this_month - timedelta(days=1)
        first_day_last_month = last_day_last_month.replace(day=1)
        return (fmt(first_day_last_month), fmt(last_day_last_month))
    
    # 今年 / this year
    if expression in ["今年", "this year"]:
        first_day = today.replace(month=1, day=1)
        return (fmt(first_day), fmt(today))
    
    # 去年 / last year
    if expression in ["去年", "last year"]:
        first_day = today.replace(year=today.year - 1, month=1, day=1)
        last_day = today.replace(year=today.year - 1, month=12, day=31)
        return (fmt(first_day), fmt(last_day))
    
    # If no pattern matches, raise error with suggestions
    supported = [
        "今天/today", "昨天/yesterday", "前天",
        "过去N天/last N days", "最近N天/recent N days",
        "本周/this week", "上周/last week", "这周一到周五",
        "本月/this month", "上个月/last month",
        "今年/this year", "去年/last year"
    ]
    raise ValueError(
        f"无法识别的日期表达: '{expression}'\n"
        f"支持的表达方式: {', '.join(supported)}"
    )


def parse_date_range_to_timestamp(expression: str) -> Tuple[int, int]:
    """
    Parse natural language date expressions into Unix timestamps.
    
    Args:
        expression: Natural language date expression
        
    Returns:
        Tuple of (start_timestamp, end_timestamp)
    """
    start_date, end_date = parse_date_range(expression)
    
    # Convert to datetime at start/end of day
    start_dt = datetime.strptime(start_date, "%Y-%m-%d").replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(
        hour=23, minute=59, second=59, microsecond=999999
    )
    
    return (int(start_dt.timestamp()), int(end_dt.timestamp()))
