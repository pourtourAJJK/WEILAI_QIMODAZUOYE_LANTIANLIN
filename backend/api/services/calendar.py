"""
日历 Service —— 工作日截止时间计算

开题报告迁移：RPC 函数 portfolio_workday() → 本 Service 实现。
"""

from datetime import date, datetime, timedelta

from django.db.models import Max

from ..models import BusinessCalendar


def get_latest_strategy_version():
    """获取当前最新的工作日历策略版本号。"""
    result = BusinessCalendar.objects.aggregate(v=Max("strategy_version"))
    return result["v"] or 1


def is_workday(d: date, strategy_version: int = None) -> bool:
    """判断某日期是否为工作日。不在日历中的日期按工作日处理。"""
    if strategy_version is None:
        strategy_version = get_latest_strategy_version()
    try:
        cal = BusinessCalendar.objects.get(strategy_version=strategy_version, date=d)
        return cal.is_workday
    except BusinessCalendar.DoesNotExist:
        # 没有记录时默认工作日（兼容未初始化情况）
        return True


def calculate_sla_deadline(submitted_at: datetime, sla_days: int,
                           strategy_version: int = None) -> datetime:
    """
    从提交时间开始，跳过休息日，数满 sla_days 个工作日得到截止时间。

    与开题报告行为一致：截止时间精确到秒，休息日不计数。
    """
    if strategy_version is None:
        strategy_version = get_latest_strategy_version()

    current_date = submitted_at.date()
    workdays_counted = 0

    while workdays_counted < sla_days:
        if is_workday(current_date, strategy_version):
            workdays_counted += 1
        if workdays_counted >= sla_days:
            break
        current_date += timedelta(days=1)

    # 截止时间为第 N 个工作日的 23:59:59
    deadline = datetime.combine(current_date, datetime.max.time(),
                                tzinfo=submitted_at.tzinfo)
    return deadline


def activate_new_strategy(entries: list[dict]) -> int:
    """
    保存并启用新的工作日历策略版本。

    Args:
        entries: [{"date": "2026-10-27", "is_workday": True, "notes": ""}, ...]

    Returns:
        新版本号
    """
    new_version = get_latest_strategy_version() + 1
    new_entries = []
    for e in entries:
        d = datetime.strptime(e["date"], "%Y-%m-%d").date()
        new_entries.append(BusinessCalendar(
            strategy_version=new_version,
            date=d,
            is_workday=e.get("is_workday", True),
            notes=e.get("notes", ""),
        ))
    BusinessCalendar.objects.bulk_create(new_entries)
    return new_version
