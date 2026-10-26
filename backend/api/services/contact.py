"""
联系方式 Service —— 提交 + 幂等

开题报告迁移：RPC portfolio_submit_contact() → 本 Service
"""

from ..models import Contact
from ..utils.validators import validate_contact_fields


class IdempotencyError(Exception):
    pass


def submit_contact(data: dict) -> Contact:
    """匿名提交联系方式（带幂等）。"""
    request_id = data.get("request_id", "")
    existing = Contact.objects.filter(request_id=request_id).first()
    if existing:
        if existing.email != data.get("email"):
            raise IdempotencyError("相同请求标识但内容不同，提交被拒绝")
        return existing

    validate_contact_fields(data)

    contact = Contact.objects.create(
        request_id=request_id,
        name=data["name"].strip(),
        email=data.get("email", "").strip().lower(),
        phone=data.get("phone", "").strip(),
        wechat=data.get("wechat", "").strip(),
        company=data.get("company", "").strip(),
        preferred_channel=data.get("preferred_channel", "email"),
        message=data.get("message", ""),
        consent_given=data.get("consent_given", False),
        status="pending",
        version=1,
    )
    return contact
