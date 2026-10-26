"""
自定义 DRF 限流类

开题报告迁移：邮箱级 + 全局级频率限制 → DRF Throttling
"""

from rest_framework.throttling import ScopedRateThrottle, SimpleRateThrottle


class InquiryEmailThrottle(ScopedRateThrottle):
    """合作咨询：邮箱级 60s 1 次 + 24h 10 次。"""
    scope = "inquiry_email"

    def get_cache_key(self, request, view):
        if request.method != "POST":
            return None
        email = request.data.get("email", "anonymous").lower()
        return f"inquiry_email_{email}"


class ContactChannelThrottle(ScopedRateThrottle):
    """联系方式：60s 1 次。"""
    scope = "contact_channel"

    def get_cache_key(self, request, view):
        if request.method != "POST":
            return None
        contact = request.data.get("email") or request.data.get("phone") or request.data.get("wechat") or "anon"
        return f"contact_channel_{contact}"
