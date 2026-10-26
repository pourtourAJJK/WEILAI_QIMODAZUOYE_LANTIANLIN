"""
站点 Service + CSV 导出 Service
"""

from ..models import SiteContent, Inquiry, Contact


def get_site_content() -> SiteContent:
    """返回站点内容单例（不存在则创建默认）。"""
    site, _ = SiteContent.objects.get_or_create()
    return site


def save_site_content(data: dict, version: int = None) -> SiteContent:
    """保存站点内容（单例 + 乐观锁）。"""
    site = get_site_content()
    if version is not None and site.version != version:
        from .inquiry import VersionConflictError
        raise VersionConflictError(
            f"站点内容版本不匹配，当前 {site.version}。"
        )
    for k, v in data.items():
        if hasattr(site, k) and k not in ("id", "version", "updated_at"):
            setattr(site, k, v)
    site.version = (version or site.version) + 1
    site.save()
    return site


def export_inquiries_csv(filters: dict = None) -> str:
    """
    导出合作咨询数据为 CSV 字符串。前端在浏览器端生成下载，
    后端仅返回数据（导出记录暂不写入 ExportRecord）。
    """
    qs = Inquiry.objects.all()
    if filters:
        if filters.get("status"):
            qs = qs.filter(status=filters["status"])
        if filters.get("page_key"):
            pass  # 咨询无 page_key
    qs = qs.order_by("-created_at")

    rows = ["姓名,邮箱,合作类型,期望周期,需求描述,状态,备注,提交时间,截止时间,版本号"]
    type_names = {
        "commercial_ad": "商业广告", "fashion_show": "服装走秀",
        "documentary": "纪录片", "self_media": "自媒体",
        "space_rental": "空间预约", "other": "其他",
    }
    status_names = {
        "pending_contact": "待联系", "in_progress": "处理中",
        "completed": "已完成", "cancelled": "已取消",
    }
    for q in qs:
        row = ",".join([
            q.name.replace(",", "，"),
            q.email,
            type_names.get(q.cooperation_type, q.cooperation_type),
            q.expected_period,
            (q.description or "").replace(",", "，").replace("\n", " "),
            status_names.get(q.status, q.status),
            (q.admin_notes or "").replace(",", "，").replace("\n", " "),
            q.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            q.sla_deadline_at.strftime("%Y-%m-%d %H:%M:%S") if q.sla_deadline_at else "",
            str(q.version),
        ])
        rows.append(row)
    return "\n".join(rows)
