"""
DRF Serializers
"""

from rest_framework import serializers
from django.contrib.auth.models import User

from .models import (
    PortfolioCategory, PortfolioProject, MediaAsset, ProjectAssetRelation,
    Inquiry, Contact, StatusHistory, ProjectVisit, PlaySession,
    BusinessCalendar, SiteContent, AdminBinding,
)


# ── 公开 ──────────────────────────────────────────────────────────

class MediaAssetPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediaAsset
        fields = ["id", "asset_type", "object_key", "mime_type",
                  "width", "height", "duration_seconds"]


class CategoryPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortfolioCategory
        fields = ["id", "slug", "name", "name_en", "page_key", "sort_order"]


class ProjectAssetRelationSerializer(serializers.ModelSerializer):
    asset = MediaAssetPublicSerializer()

    class Meta:
        model = ProjectAssetRelation
        fields = ["asset", "role", "caption", "asset_source", "sort_order"]


class ProjectPublicSerializer(serializers.ModelSerializer):
    category = CategoryPublicSerializer()
    cover = serializers.SerializerMethodField()
    video = serializers.SerializerMethodField()
    extra_covers = serializers.SerializerMethodField()
    gallery = serializers.SerializerMethodField()

    class Meta:
        model = PortfolioProject
        fields = [
            "id", "slug", "title", "category", "content_type", "card_layout",
            "summary", "background", "notes", "credits", "content_blocks",
            "cover", "video", "extra_covers", "gallery",
        ]

    def get_cover(self, obj):
        if obj.cover_image_id:
            return MediaAssetPublicSerializer(obj.cover_image).data
        if obj.cover_image_legacy_path:
            return {"object_key": obj.cover_image_legacy_path, "asset_type": "image"}
        return None

    def get_video(self, obj):
        if obj.video_asset_id:
            return MediaAssetPublicSerializer(obj.video_asset).data
        return None

    def _assets_by_role(self, obj, role):
        rels = ProjectAssetRelation.objects.filter(
            project=obj, role=role,
        ).select_related("asset").order_by("sort_order")
        return [MediaAssetPublicSerializer(r.asset).data for r in rels]

    def get_extra_covers(self, obj):
        return self._assets_by_role(obj, "extra_cover")

    def get_gallery(self, obj):
        return self._assets_by_role(obj, "gallery")


class SiteContentPublicSerializer(serializers.ModelSerializer):
    home_showreel = MediaAssetPublicSerializer()

    class Meta:
        model = SiteContent
        fields = [
            "brand_name", "brand_name_en", "home_title", "home_description",
            "about_text", "home_showreel", "contact_email", "contact_phone",
            "social_links", "space_page_content",
        ]


# ── 提交 ──────────────────────────────────────────────────────────

class InquirySubmitSerializer(serializers.Serializer):
    request_id = serializers.CharField(max_length=100)
    name = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    cooperation_type = serializers.ChoiceField(
        choices=["commercial_ad", "fashion_show", "documentary",
                 "self_media", "space_rental", "other"],
    )
    expected_period = serializers.ChoiceField(
        choices=["1month", "3months", "6months", "1year", "flexible"],
        default="flexible",
    )
    description = serializers.CharField(max_length=5000, required=False, default="")
    consent_given = serializers.BooleanField()


class ContactSubmitSerializer(serializers.Serializer):
    request_id = serializers.CharField(max_length=100)
    name = serializers.CharField(max_length=100)
    email = serializers.EmailField(required=False, allow_blank=True, default="")
    phone = serializers.CharField(max_length=30, required=False, allow_blank=True, default="")
    wechat = serializers.CharField(max_length=100, required=False, allow_blank=True, default="")
    company = serializers.CharField(max_length=200, required=False, allow_blank=True, default="")
    preferred_channel = serializers.ChoiceField(
        choices=["email", "phone", "wechat"], default="email",
    )
    message = serializers.CharField(max_length=2000, required=False, default="")
    consent_given = serializers.BooleanField()


class PlaybackStartSerializer(serializers.Serializer):
    project_id = serializers.IntegerField()
    session_id = serializers.CharField(max_length=100)
    video_asset_id = serializers.IntegerField(required=False, default=None)
    video_duration = serializers.FloatField(required=False, default=0)
    visitor_identity = serializers.CharField(max_length=100, required=False, default="")
    session_token_hash = serializers.CharField(max_length=200, required=False, default="")


class PlaybackProgressSerializer(serializers.Serializer):
    project_id = serializers.IntegerField()
    session_id = serializers.CharField(max_length=100)
    natural_intervals = serializers.ListField(child=serializers.ListField(child=serializers.FloatField()))
    is_ended = serializers.BooleanField(default=False)


class VisitRecordSerializer(serializers.Serializer):
    project_id = serializers.IntegerField()
    visit_id = serializers.CharField(max_length=100)
    visitor_identity = serializers.CharField(max_length=100, required=False, default="")
    identity_key = serializers.CharField(max_length=100, required=False, default="")


# ── 管理员 ─────────────────────────────────────────────────────────

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    captcha_text = serializers.CharField(required=False, default="")
    captcha_token = serializers.CharField(required=False, default="")


class InquiryAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Inquiry
        fields = [
            "id", "request_id", "name", "email", "cooperation_type",
            "expected_period", "description", "consent_given",
            "status", "admin_notes", "sla_started_at", "sla_deadline_at",
            "version", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "request_id", "sla_*", "created_at", "updated_at"]


class ContactAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = "__all__"


class StatusHistorySerializer(serializers.ModelSerializer):
    operated_by = UserSerializer()

    class Meta:
        model = StatusHistory
        fields = "__all__"


class ProjectAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortfolioProject
        fields = [
            "id", "slug", "title", "category", "content_type", "card_layout",
            "summary", "background", "notes", "credits", "content_blocks",
            "cover_image", "cover_image_legacy_path", "video_asset",
            "is_published", "version", "created_at", "updated_at", "deleted_at",
        ]
        read_only_fields = ["id", "version", "created_at", "updated_at", "deleted_at"]


class MediaAssetAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediaAsset
        fields = [
            "id", "asset_type", "storage_bucket", "object_key", "mime_type",
            "file_size", "width", "height", "duration_seconds",
            "asset_status", "uploaded_at",
        ]
        read_only_fields = ["id", "uploaded_at"]


class CalendarSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessCalendar
        fields = ["strategy_version", "date", "is_workday", "notes"]
