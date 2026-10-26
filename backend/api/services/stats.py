"""
统计查询 Service —— PV / UV / 节点到达率 / 完播率 / 排行榜

开题报告迁移：RPC portfolio_stats_*() → 本 Service
"""

from datetime import datetime, timedelta

from django.db.models import Count, Q, Sum, Avg
from django.db.models.functions import TruncDate

from ..models import ProjectVisit, PlaySession, PortfolioProject


def get_pv_uv(project_id=None, start_date=None, end_date=None):
    """
    PV = 有效播放会话数
    UV = 选定范围内 identity_key 去重数

    开题报告口径不变：播放 PV 是有效会话数，不是访问记录数。
    """
    sessions = PlaySession.objects.all()
    if project_id:
        sessions = sessions.filter(project_id=project_id)
    if start_date:
        sessions = sessions.filter(started_at__date__gte=start_date)
    if end_date:
        sessions = sessions.filter(started_at__date__lte=end_date)

    pv = sessions.count()
    uv = ProjectVisit.objects.all()
    if project_id:
        uv = uv.filter(project_id=project_id)
    if start_date:
        uv = uv.filter(visited_at__date__gte=start_date)
    if end_date:
        uv = uv.filter(visited_at__date__lte=end_date)
    uv = uv.values("identity_key").distinct().count()

    return {"pv": pv, "uv": uv}


def get_daily_trend(start_date: datetime, end_date: datetime,
                    granularity="day"):
    """按日 / 周 / 月粒度返回 PV / UV 趋势。"""
    sessions = PlaySession.objects.filter(
        started_at__date__gte=start_date.date(),
        started_at__date__lte=end_date.date(),
    )
    visits = ProjectVisit.objects.filter(
        visited_at__date__gte=start_date.date(),
        visited_at__date__lte=end_date.date(),
    )

    pv_by_date = dict(
        sessions.annotate(d=TruncDate("started_at"))
        .values("d")
        .annotate(c=Count("id"))
        .values_list("d", "c")
    )
    uv_by_date = dict(
        visits.annotate(d=TruncDate("visited_at"))
        .values("d")
        .annotate(c=Count("identity_key", distinct=True))
        .values_list("d", "c")
    )

    days = []
    current = start_date.date()
    while current <= end_date.date():
        days.append({
            "date": current.isoformat(),
            "pv": pv_by_date.get(current, 0),
            "uv": uv_by_date.get(current, 0),
        })
        current += timedelta(days=1)
    return days


def get_completion_stats(project_id=None):
    """节点到达率 + 完播率。"""
    sessions = PlaySession.objects.all()
    if project_id:
        sessions = sessions.filter(project_id=project_id)
    total = sessions.count()
    if total == 0:
        return {"total_sessions": 0, "node_rates": {}, "completion_rate": 0}

    completed = sessions.filter(is_completed=True).count()
    node_rates = {}
    for pct in [10, 25, 50, 75, 95, 98]:
        key = f"{pct}pct"
        reached = sessions.filter(node_reached_at__has_key=key).count()
        node_rates[key] = round(reached / total * 100, 1)

    return {
        "total_sessions": total,
        "node_rates": node_rates,
        "completion_rate": round(completed / total * 100, 1),
    }


def get_rankings(limit=10):
    """
    作品排行榜：先按播放量降序，再按完播率降序，再按作品标识升序稳定排序。

    开题报告排序逻辑保持不变。
    """
    # 聚合：每个作品的播放会话数 + 完播会话数
    from django.db.models.functions import Coalesce
    stats = (
        PlaySession.objects.values("project_id")
        .annotate(
            play_count=Count("id"),
            completed_count=Count("id", filter=Q(is_completed=True)),
        )
        .order_by("-play_count", "-completed_count", "project_id")
        [:limit]
    )

    project_ids = [s["project_id"] for s in stats]
    projects = {
        p.id: p for p in PortfolioProject.objects.filter(id__in=project_ids)
    }

    rankings = []
    for s in stats:
        project = projects.get(s["project_id"])
        if not project:
            continue
        completion_rate = round(
            s["completed_count"] / s["play_count"] * 100, 1
        ) if s["play_count"] else 0
        rankings.append({
            "project_id": project.id,
            "title": project.title,
            "slug": project.slug,
            "play_count": s["play_count"],
            "completion_rate": completion_rate,
        })
    return rankings
