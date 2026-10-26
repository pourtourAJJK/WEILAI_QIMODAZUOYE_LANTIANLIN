"""
合作咨询 Service —— 提交、幂等、状态流转、历史事务

开题报告迁移：RPC portfolio_submit_inquiry() + portfolio_update_inquiry() → 本 Service
核心业务规则（PRD §4.1/§4.2/§4.6）：
  - 幂等：相同 request_id 重试返回原有记录
  - 乐观锁：status update 携带 version，冲突拒绝覆盖
  - 状态历史：状态变更 + 历史写入在同一事务
  - 工作日截止：提交时计算 sla_deadline_at 并冻结
"""

from django.db import transaction

from ..models import Inquiry, StatusHistory
from . import calendar
from ..utils.validators import (
    INQUIRY_STATUSES,
    validate_inquiry_fields,
)


class VersionConflictError(Exception):
    """乐观锁版本不匹配。"""
    pass


class IdempotencyError(Exception):
    """幂等冲突：相同 request_id 但内容不同。"""
    pass


def submit_inquiry(data: dict) -> Inquiry:
    """
    匿名提交合作咨询（带幂等 + 工作日截止）。

    开题报告 RPC portfolio_submit_inquiry() 的迁移实现。
    """
    from django.db.models import F

    # 1) 幂等检查
    request_id = data.get("request_id", "")
    existing = Inquiry.objects.filter(request_id=request_id).first()
    if existing:
        # 同一 request_id 但核心字段变了 → 拒绝
        if existing.email != data.get("email"):
            raise IdempotencyError("相同请求标识但内容不同，提交被拒绝")
        return existing

    # 2) 字段校验
    validate_inquiry_fields(data)

    # 3) 工作日截止时间
    sla_days = calendar.get_latest_strategy_version() and 3  # 默认 3 个工作日
    # 从 SiteContent 读取 sla_days
    try:
        from ..models import SiteContent
        site = SiteContent.objects.first()
        if site:
            sla_days = site.sla_days
    except Exception:
        pass

    now = data.get("submitted_at") or __import__("django.utils.timezone",
                                                 fromlist=["now"]).now()
    deadline = calendar.calculate_sla_deadline(now, sla_days)
    strategy_version = calendar.get_latest_strategy_version()

    # 4) 创建记录
    inquiry = Inquiry.objects.create(
        request_id=request_id,
        name=data["name"].strip(),
        email=data["email"].strip().lower(),
        cooperation_type=data["cooperation_type"],
        expected_period=data.get("expected_period", "flexible"),
        description=data.get("description", ""),
        consent_given=data.get("consent_given", False),
        status="pending_contact",
        sla_started_at=now,
        sla_deadline_at=deadline,
        sla_strategy_version=strategy_version,
        version=1,
    )
    return inquiry


@transaction.atomic
def update_inquiry_status(inquiry_id: int, new_status: str,
                          version: int, notes: str = "",
                          operated_by=None) -> Inquiry:
    """
    后台更新咨询状态：乐观锁 + 同一事务内写入状态历史。

    开题报告 RPC portfolio_update_inquiry() 的迁移实现。
    """
    if new_status not in INQUIRY_STATUSES:
        from django.core.exceptions import ValidationError
        raise ValidationError(f"状态不在允许值内: {new_status}")

    inquiry = Inquiry.objects.select_for_update().get(id=inquiry_id)
    old_status = inquiry.status

    # 乐观锁检查
    if inquiry.version != version:
        raise VersionConflictError(
            f"版本号不匹配，当前版本 {inquiry.version}，提交版本 {version}。请刷新后重试。"
        )

    # 执行更新 + 版本递增
    updated = Inquiry.objects.filter(
        id=inquiry_id, version=version,
    ).update(
        status=new_status,
        admin_notes=notes or inquiry.admin_notes,
        version=F("version") + 1,
    )
    if updated == 0:
        raise VersionConflictError("乐观锁更新失败")

    # 刷新获取最新数据
    inquiry.refresh_from_db()

    # 同一事务内写入状态历史
    StatusHistory.objects.create(
        inquiry=inquiry,
        old_status=old_status,
        new_status=new_status,
        notes=notes,
        operated_by=operated_by,
    )
    return inquiry


def update_inquiry_notes(inquiry_id: int, admin_notes: str,
                         version: int, operated_by=None) -> Inquiry:
    """更新备注（不改变状态，不影响原始 sla_deadline）。"""
    inquiry = Inquiry.objects.select_for_update().get(id=inquiry_id)
    if inquiry.version != version:
        raise VersionConflictError(
            f"版本号不匹配，当前版本 {inquiry.version}，提交版本 {version}。"
        )

    updated = Inquiry.objects.filter(
        id=inquiry_id, version=version,
    ).update(
        admin_notes=admin_notes,
        version=F("version") + 1,
    )
    if updated == 0:
        raise VersionConflictError("乐观锁更新失败")

    inquiry.refresh_from_db()
    return inquiry
