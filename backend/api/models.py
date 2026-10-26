"""
影羽·YINGYU STUDIO —— 数据模型（13 张业务表）

对照开题报告 §3.1 数据模型设计 + PRD §3 数据模型。
"""

from django.db import models
from django.contrib.auth.models import User


# ── 自定义 Manager（软删除支持） ──────────────────────────────────────

class SoftDeleteManager(models.Manager):
    """默认过滤 deleted_at 非空的记录。"""

    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class SoftDeleteAllManager(models.Manager):
    """不过滤，返回全部记录（含已软删除）。"""
    pass


# ═══════════════════════════════════════════════════════════════════════
# 作品域（4 张）
# ═══════════════════════════════════════════════════════════════════════


class PortfolioCategory(models.Model):
    """作品分类。按 page_key 区分校内创作 / 商业项目。"""

    PAGE_KEY_CHOICES = (
        ("campus", "校内创作"),
        ("commercial", "商业项目"),
    )

    slug = models.SlugField(max_length=50, unique=True, db_index=True)
    name = models.CharField(max_length=100, verbose_name="中文名")
    name_en = models.CharField(max_length=100, verbose_name="英文名", blank=True)
    page_key = models.CharField(max_length=20, choices=PAGE_KEY_CHOICES, db_index=True)
    sort_order = models.IntegerField(default=0, verbose_name="排序")
    is_enabled = models.BooleanField(default=True, verbose_name="启用")
    is_fixed = models.BooleanField(default=False, verbose_name="固定标记")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "portfolio_categories"
        ordering = ["page_key", "sort_order"]

    def __str__(self):
        return f"{self.name} ({self.get_page_key_display()})"


class MediaAsset(models.Model):
    """媒体素材（图片 / 视频）。"""

    ASSET_TYPE_CHOICES = (
        ("image", "图片"),
        ("video", "视频"),
    )
    ASSET_STATUS_CHOICES = (
        ("pending", "待处理"),
        ("ready", "就绪"),
        ("failed", "失败"),
        ("archived", "归档"),
    )

    asset_type = models.CharField(max_length=10, choices=ASSET_TYPE_CHOICES, db_index=True)
    file = models.FileField(upload_to="assets/%Y/%m/", null=True, blank=True)
    # 开发阶段用本地文件；生产可选对象存储，以下字段备用
    storage_bucket = models.CharField(max_length=100, blank=True, default="local")
    object_key = models.CharField(max_length=500, blank=True, default="")
    mime_type = models.CharField(max_length=100, blank=True)
    file_size = models.BigIntegerField(default=0, verbose_name="文件大小（字节）")
    width = models.IntegerField(null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)
    duration_seconds = models.FloatField(null=True, blank=True, verbose_name="视频时长（秒）")
    asset_status = models.CharField(max_length=10, choices=ASSET_STATUS_CHOICES, default="pending", db_index=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "portfolio_media_assets"

    def __str__(self):
        return f"#{self.id} {self.asset_type} ({self.asset_status})"


class PortfolioProject(models.Model):
    """作品主表。"""

    CONTENT_TYPE_CHOICES = (
        ("photo", "摄影"),
        ("video", "视频"),
        ("mixed", "混合"),
    )
    CARD_LAYOUT_CHOICES = (
        ("banner", "横幅叙事"),
        ("portrait", "竖幅展映"),
        ("hero", "全宽主视觉"),
    )

    # 软删除
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)
    objects = SoftDeleteManager()          # 默认只返回未删除
    all_objects = SoftDeleteAllManager()   # 返回全部

    # 基本信息
    slug = models.SlugField(max_length=60, unique=True, db_index=True)
    title = models.CharField(max_length=200, verbose_name="作品标题")
    category = models.ForeignKey(
        PortfolioCategory, on_delete=models.PROTECT,
        related_name="projects", db_index=True,
    )
    content_type = models.CharField(max_length=10, choices=CONTENT_TYPE_CHOICES)
    card_layout = models.CharField(max_length=10, choices=CARD_LAYOUT_CHOICES, default="banner")

    # 文本内容
    summary = models.TextField(blank=True, verbose_name="概述")
    background = models.TextField(blank=True, verbose_name="项目背景 / 介绍")
    notes = models.TextField(blank=True, verbose_name="制作心得 / 创作思路")
    credits = models.JSONField(default=list, blank=True, verbose_name="项目档案（标签-值对）")
    content_blocks = models.JSONField(default=list, blank=True, verbose_name="内容段落")

    # 素材关联（允许兼容旧数据的本地封面路径）
    cover_image = models.ForeignKey(
        MediaAsset, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="cover_of_projects",
    )
    cover_image_legacy_path = models.CharField(max_length=500, blank=True, default="", verbose_name="兼容旧数据的本地封面路径")
    video_asset = models.ForeignKey(
        MediaAsset, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="video_of_projects",
    )
    # 额外封面与素材库通过 ProjectAssetRelation 中间表按 role 过滤
    # 不在模型上声明 M2M，避免 Django E003 报错

    # 状态与乐观锁
    is_published = models.BooleanField(default=False, db_index=True)
    version = models.IntegerField(default=1, verbose_name="乐观锁版本号")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "portfolio_projects"
        ordering = ["-is_published", "-updated_at"]

    def __str__(self):
        return f"[{self.slug}] {self.title}"

    @property
    def is_deleted(self):
        return self.deleted_at is not None


class ProjectAssetRelation(models.Model):
    """作品与素材的关联表（封面、额外封面、素材库）。"""

    ROLE_CHOICES = (
        ("cover", "主封面"),
        ("extra_cover", "额外封面"),
        ("gallery", "素材库"),
    )
    ASSET_SOURCE_CHOICES = (
        ("real", "实拍"),
        ("concept", "概念"),
        ("placeholder", "占位"),
    )

    project = models.ForeignKey(PortfolioProject, on_delete=models.CASCADE, db_index=True)
    asset = models.ForeignKey(MediaAsset, on_delete=models.CASCADE, db_index=True)
    role = models.CharField(max_length=15, choices=ROLE_CHOICES, db_index=True)
    caption = models.CharField(max_length=300, blank=True, default="")
    asset_source = models.CharField(max_length=15, choices=ASSET_SOURCE_CHOICES, default="real")
    sort_order = models.IntegerField(default=0)

    class Meta:
        db_table = "project_asset_relations"
        ordering = ["sort_order"]

    def __str__(self):
        return f"project#{self.project_id} asset#{self.asset_id} {self.role}"


# ═══════════════════════════════════════════════════════════════════════
# 客户需求域（3 张）
# ═══════════════════════════════════════════════════════════════════════


class Inquiry(models.Model):
    """合作咨询。"""

    COOPERATION_TYPE_CHOICES = (
        ("commercial_ad", "商业广告"),
        ("fashion_show", "服装走秀"),
        ("documentary", "纪录片"),
        ("self_media", "自媒体"),
        ("space_rental", "空间预约"),
        ("other", "其他"),
    )
    PERIOD_CHOICES = (
        ("1month", "1 个月内"),
        ("3months", "3 个月内"),
        ("6months", "半年内"),
        ("1year", "1 年内"),
        ("flexible", "时间灵活"),
    )
    STATUS_CHOICES = (
        ("pending_contact", "待联系"),
        ("in_progress", "处理中"),
        ("completed", "已完成"),
        ("cancelled", "已取消"),
    )

    # 幂等
    request_id = models.CharField(max_length=100, unique=True, db_index=True)

    name = models.CharField(max_length=100)
    email = models.EmailField(db_index=True)
    cooperation_type = models.CharField(max_length=20, choices=COOPERATION_TYPE_CHOICES)
    expected_period = models.CharField(max_length=20, choices=PERIOD_CHOICES)
    description = models.TextField(max_length=5000, blank=True, default="")
    consent_given = models.BooleanField(default=False, verbose_name="授权标记")

    # 状态
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending_contact", db_index=True)
    admin_notes = models.TextField(blank=True, default="")

    # SLA
    sla_started_at = models.DateTimeField(null=True, blank=True)
    sla_deadline_at = models.DateTimeField(null=True, blank=True, db_index=True)
    sla_strategy_version = models.IntegerField(default=1)

    # 乐观锁
    version = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "portfolio_inquiries"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Inquiry#{self.id} from {self.name} ({self.email})"


class Contact(models.Model):
    """联系方式。"""

    PREFERRED_CHANNEL_CHOICES = (
        ("email", "邮箱"),
        ("phone", "电话"),
        ("wechat", "微信"),
    )
    STATUS_CHOICES = (
        ("pending", "待联系"),
        ("contacted", "已联系"),
        ("archived", "已归档"),
    )

    # 幂等
    request_id = models.CharField(max_length=100, unique=True, db_index=True)

    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, default="", db_index=True)
    phone = models.CharField(max_length=30, blank=True, default="")
    wechat = models.CharField(max_length=100, blank=True, default="")
    company = models.CharField(max_length=200, blank=True, default="")
    preferred_channel = models.CharField(max_length=10, choices=PREFERRED_CHANNEL_CHOICES, default="email")
    message = models.TextField(max_length=2000, blank=True, default="")
    consent_given = models.BooleanField(default=False)

    # 状态
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default="pending", db_index=True)
    admin_notes = models.TextField(blank=True, default="")

    # 乐观锁
    version = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "portfolio_contacts"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Contact#{self.id} {self.name}"


class StatusHistory(models.Model):
    """状态历史。通过两个可空外键区分 Inquiry / Contact 来源（两者只能一个非空）。"""

    inquiry = models.ForeignKey(Inquiry, on_delete=models.CASCADE, null=True, blank=True, db_index=True)
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, null=True, blank=True, db_index=True)
    old_status = models.CharField(max_length=20)
    new_status = models.CharField(max_length=20)
    notes = models.CharField(max_length=500, blank=True, default="")
    operated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    operated_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "portfolio_status_history"
        ordering = ["-operated_at"]
        indexes = [
            models.Index(fields=["inquiry", "contact"]),
        ]

    def __str__(self):
        return f"History#{self.id}: {self.old_status} → {self.new_status}"


# ═══════════════════════════════════════════════════════════════════════
# 统计与日历域（4 张）
# ═══════════════════════════════════════════════════════════════════════


class ProjectVisit(models.Model):
    """作品访问记录。"""

    project = models.ForeignKey(PortfolioProject, on_delete=models.CASCADE, db_index=True)
    visit_id = models.CharField(max_length=100, db_index=True)
    visitor_identity = models.CharField(max_length=100, blank=True, default="")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    identity_key = models.CharField(max_length=100, db_index=True, blank=True, default="")
    visited_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "portfolio_project_visits"
        unique_together = [("project", "visit_id")]

    def __str__(self):
        return f"Visit {self.project_id}::{self.visit_id[:8]}"


class PlaySession(models.Model):
    """视频播放会话。"""

    project = models.ForeignKey(PortfolioProject, on_delete=models.CASCADE, db_index=True)
    session_id = models.CharField(max_length=100, db_index=True)
    video_asset = models.ForeignKey(MediaAsset, on_delete=models.SET_NULL, null=True, blank=True)
    video_duration = models.FloatField(default=0, verbose_name="视频时长（秒，创建时快照）")
    visitor_identity = models.CharField(max_length=100, blank=True, default="")
    session_token_hash = models.CharField(max_length=200, blank=True, default="")

    started_at = models.DateTimeField(auto_now_add=True, db_index=True)
    last_event_at = models.DateTimeField(null=True, blank=True)
    node_reached_at = models.JSONField(default=dict, blank=True, verbose_name="节点到达时间")
    completed_at = models.DateTimeField(null=True, blank=True)
    is_completed = models.BooleanField(default=False, db_index=True)

    class Meta:
        db_table = "portfolio_play_sessions"
        unique_together = [("project", "session_id")]
        ordering = ["-started_at"]

    def __str__(self):
        return f"Play {self.project_id}::{self.session_id[:8]}"


class ExportRecord(models.Model):
    """导出记录（当前 CSV 导出不写入此表，保留用于未来增强）。"""

    EXPORT_TYPE_CHOICES = (
        ("inquiries_csv", "合作咨询 CSV"),
        ("contacts_csv", "联系方式 CSV"),
        ("all_csv", "全部客户 CSV"),
    )

    admin = models.ForeignKey(User, on_delete=models.CASCADE)
    export_type = models.CharField(max_length=20, choices=EXPORT_TYPE_CHOICES)
    filter_snapshot = models.JSONField(default=dict, blank=True)
    file_path = models.CharField(max_length=500, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "portfolio_export_records"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Export#{self.id} {self.export_type}"


class BusinessCalendar(models.Model):
    """工作日历。策略版本 + 日期联合主键。"""

    strategy_version = models.IntegerField(default=1, db_index=True)
    date = models.DateField(db_index=True)
    is_workday = models.BooleanField(default=True)
    notes = models.CharField(max_length=200, blank=True, default="")

    class Meta:
        db_table = "portfolio_business_calendar"
        unique_together = [("strategy_version", "date")]
        ordering = ["strategy_version", "date"]

    def __str__(self):
        return f"v{self.strategy_version} {self.date}={'工作日' if self.is_workday else '休息日'}"


# ═══════════════════════════════════════════════════════════════════════
# 站点与权限域（2 张）
# ═══════════════════════════════════════════════════════════════════════


class SiteContent(models.Model):
    """站点内容（单例）。"""

    # 单例保证
    _instance = None

    brand_name = models.CharField(max_length=100, default="影羽")
    brand_name_en = models.CharField(max_length=100, default="YINGYU STUDIO")
    home_title = models.CharField(max_length=200, default="影羽·YINGYU STUDIO")
    home_description = models.TextField(
        default="个人摄影作品集 —— 用镜头讲述故事，用影像传递温度。"
    )
    about_text = models.TextField(
        default="这里是关于页面的默认文案，请在后台修改。"
    )
    home_showreel = models.ForeignKey(
        MediaAsset, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="showreel_of_site",
    )
    contact_email = models.EmailField(default="hello@example.com")
    contact_phone = models.CharField(max_length=30, blank=True, default="")
    social_links = models.JSONField(default=list, blank=True)
    space_page_content = models.TextField(blank=True, default="")
    sla_days = models.IntegerField(default=3, verbose_name="工作日答复天数")
    version = models.IntegerField(default=1)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "portfolio_site_content"
        verbose_name = "站点内容"
        verbose_name_plural = "站点内容（单例，请只保留一条）"

    def __str__(self):
        return f"Site: {self.brand_name} · {self.brand_name_en}"

    def save(self, *args, **kwargs):
        """单例：确保数据库中只存在一条 SiteContent 记录。"""
        if SiteContent.objects.exists() and not self.pk:
            existing = SiteContent.objects.first()
            self.pk = existing.pk
        super().save(*args, **kwargs)


class AdminBinding(models.Model):
    """管理员绑定（单例）。"""

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bound_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "portfolio_admin_binding"
        verbose_name = "管理员绑定"
        verbose_name_plural = "管理员绑定（单例）"

    def __str__(self):
        return f"Admin: {self.user.username}"


class LoginAttempt(models.Model):
    """
    登录失败追踪：同一用户名累计失败 5 次后自动锁定 5 分钟。

    - fail_count: 连续失败次数（成功登录后重置）
    - locked_until: 锁定到期时间；null 表示当前未锁定
    - last_failed_at: 最近一次失败时间（清理用）
    """

    MAX_FAILS_BEFORE_LOCK = 5
    LOCK_DURATION_SECONDS = 300  # 5 分钟

    username = models.CharField(max_length=150, unique=True, db_index=True)
    fail_count = models.IntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True, db_index=True)
    last_failed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "portfolio_login_attempts"
        verbose_name = "登录失败追踪"

    def __str__(self):
        status = "🔒锁定" if self.is_locked() else "🟢正常"
        return f"{self.username}: {self.fail_count} 次失败 {status}"

    def is_locked(self) -> bool:
        """当前是否处于锁定状态。"""
        from django.utils import timezone
        if not self.locked_until:
            return False
        return self.locked_until > timezone.now()

    def remaining_lock_seconds(self) -> int:
        """剩余锁定秒数（已解锁返回 0）。"""
        from django.utils import timezone
        if not self.locked_until:
            return 0
        delta = self.locked_until - timezone.now()
        return max(0, int(delta.total_seconds()))
