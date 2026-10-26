"""
共用字段校验器
"""
from django.core.exceptions import ValidationError


COOPERATION_TYPES = [
    "commercial_ad", "fashion_show", "documentary",
    "self_media", "space_rental", "other",
]
PERIOD_CHOICES = ["1month", "3months", "6months", "1year", "flexible"]
INQUIRY_STATUSES = ["pending_contact", "in_progress", "completed", "cancelled"]
CONTACT_STATUSES = ["pending", "contacted", "archived"]


def validate_inquiry_fields(data: dict) -> None:
    """校验合作咨询字段。"""
    if not data.get("name") or len(data["name"]) > 100:
        raise ValidationError("姓名必填且不超过 100 字")
    email = data.get("email", "")
    if not email or "@" not in email:
        raise ValidationError("邮箱格式不正确")
    if data.get("cooperation_type") not in COOPERATION_TYPES:
        raise ValidationError("合作类型不在允许值内")
    if data.get("expected_period") not in PERIOD_CHOICES:
        raise ValidationError("期望周期不在允许值内")
    if len(data.get("description", "")) > 5000:
        raise ValidationError("需求描述不超过 5000 字")
    if not data.get("consent_given"):
        raise ValidationError("请勾选联系授权")


def validate_contact_fields(data: dict) -> None:
    """校验联系方式字段：邮箱/电话/微信至少一项非空。"""
    if not data.get("name") or len(data["name"]) > 100:
        raise ValidationError("姓名必填且不超过 100 字")
    email = data.get("email", "")
    phone = data.get("phone", "")
    wechat = data.get("wechat", "")
    if not (email or phone or wechat):
        raise ValidationError("邮箱、电话、微信至少填写一项")
    if email and "@" not in email:
        raise ValidationError("邮箱格式不正确")
    preferred = data.get("preferred_channel", "email")
    if preferred == "email" and not email:
        raise ValidationError("首选联系方式与已填写渠道不对应")
    if preferred == "phone" and not phone:
        raise ValidationError("首选联系方式与已填写渠道不对应")
    if preferred == "wechat" and not wechat:
        raise ValidationError("首选联系方式与已填写渠道不对应")
    if len(data.get("message", "")) > 2000:
        raise ValidationError("留言不超过 2000 字")
    if not data.get("consent_given"):
        raise ValidationError("请勾选联系授权")


def validate_cover_publish(project, errors: list) -> None:
    """校验发布状态作品的封面条件。"""
    has_cover = bool(project.cover_image or project.cover_image_legacy_path)
    if not has_cover:
        errors.append("发布状态的作品必须具备封面")

    # 额外封面数量（通过中间表）
    from ..models import ProjectAssetRelation, MediaAsset
    extra_count = ProjectAssetRelation.objects.filter(
        project=project, role="extra_cover",
    ).count()
    if extra_count > 4:
        errors.append("额外封面最多 4 张")

    # 视频作品的素材状态
    if project.content_type == "video" and project.video_asset_id:
        video = MediaAsset.objects.filter(id=project.video_asset_id).first()
        if video:
            if video.asset_status != "ready":
                errors.append(f"视频素材（{video.asset_status}）未就绪")
            if (video.duration_seconds or 0) <= 0:
                errors.append("视频时长必须大于 0")
