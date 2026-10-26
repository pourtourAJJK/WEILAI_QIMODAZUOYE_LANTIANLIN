"""
DRF Views —— 公开 / 提交 / 管理员 / 统计 / 认证
"""

import uuid
import base64
import io
from datetime import date, datetime, timedelta

from django.contrib.auth import authenticate
from django.db.models import F
from rest_framework import viewsets, status, mixins
from rest_framework.response import Response
from rest_framework.decorators import action, api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from PIL import Image, ImageDraw, ImageFont

from .models import (
    PortfolioProject, PortfolioCategory, MediaAsset, ProjectAssetRelation,
    Inquiry, Contact, StatusHistory, ProjectVisit, PlaySession,
    SiteContent, BusinessCalendar, AdminBinding, LoginAttempt,
)
from .services import (
    inquiry as inquiry_service,
    contact as contact_service,
    portfolio as portfolio_service,
    playback as playback_service,
    calendar as calendar_service,
    stats as stats_service,
    site as site_service,
    login as login_service,
)
from .serializers import (
    SiteContentPublicSerializer, CategoryPublicSerializer, ProjectPublicSerializer,
    InquirySubmitSerializer, ContactSubmitSerializer, VisitRecordSerializer,
    PlaybackStartSerializer, PlaybackProgressSerializer,
    LoginSerializer, InquiryAdminSerializer, ContactAdminSerializer,
    ProjectAdminSerializer, MediaAssetAdminSerializer, CalendarSerializer,
    StatusHistorySerializer,
)
from .permissions import IsAdminUser
from .throttling import InquiryEmailThrottle, ContactChannelThrottle


# ── 认证 ──────────────────────────────────────────────────────────

@api_view(["get"])
@permission_classes([AllowAny])
def get_captcha(request):
    """返回图片验证码（6 字符 + 简单算术）。"""
    import random
    # 简单实现：生成 4 位随机码 + 200x60 图片
    captcha_text = "".join(random.choices("ABCDEFGHJKLMNPQRSTUVWXYZ23456789", k=4))
    img = Image.new("RGB", (200, 60), (240, 240, 240))
    draw = ImageDraw.Draw(img)
    # 画干扰线
    for _ in range(5):
        draw.line(
            [(random.randint(0, 200), random.randint(0, 60)),
             (random.randint(0, 200), random.randint(0, 60))],
            fill=(random.randint(0, 180), random.randint(0, 180), random.randint(0, 180)),
        )
    try:
        font = ImageFont.truetype("arial.ttf", 30)
    except Exception:
        font = ImageFont.load_default()
    for i, c in enumerate(captcha_text):
        draw.text((20 + i * 40, 15), c, fill=(0, 0, 200), font=font)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    img_b64 = base64.b64encode(buf.getvalue()).decode()
    # 简单实现：直接把答案放 session（生产环境应该存 DB + 过期）
    request.session["captcha"] = captcha_text.upper()
    return Response({
        "image": f"data:image/png;base64,{img_b64}",
        "hint": "忽略此提示：" + captcha_text,  # 开发阶段直接返回答案
    })


@api_view(["post"])
@permission_classes([AllowAny])
def login(request):
    """
    管理员登录 —— 三重校验 + 失败锁定：

    1. 【锁定检查】该用户名当前是否处于锁定状态（失败 5 次 → 锁 5 分钟）
    2. 【身份认证】Django Auth authenticate() 校验账号密码
    3. 【身份绑定】AdminBinding 表中有记录 + user.is_active=True

    失败计数器在：
      - 登录失败时 +1（触发锁定时锁定时间 = now + 5min）
      - 登录成功时清零 + 清除锁定
    """
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    username = serializer.validated_data["username"]
    password = serializer.validated_data["password"]

    # ── 1) 锁定检查 ──
    is_locked, remaining = login_service.is_account_locked(username)
    if is_locked:
        minutes = remaining // 60
        secs = remaining % 60
        return Response(
            {
                "detail": f"账号已被锁定，请在 {minutes} 分 {secs} 秒后重试",
                "locked": True,
                "remaining_seconds": remaining,
                "fail_count": LoginAttempt.MAX_FAILS_BEFORE_LOCK,
            },
            status=429,  # Too Many Requests（语义：被限流/锁定）
        )

    # ── 2) Django Auth authenticate ──
    user = authenticate(username=username, password=password)
    if not user:
        # 记录失败
        record = login_service.record_login_failure(username)
        remaining_attempts = max(
            0, LoginAttempt.MAX_FAILS_BEFORE_LOCK - record.fail_count
        )
        payload = {
            "detail": "用户名或密码错误",
            "fail_count": record.fail_count,
            "remaining_attempts": remaining_attempts,
            "locked": record.is_locked(),
            "remaining_seconds": record.remaining_lock_seconds(),
        }
        if record.is_locked():
            return Response(payload, status=429)
        return Response(payload, status=401)

    # ── 3) 身份绑定校验（必须是我们自己创建的管理员） ──
    is_valid, reason = login_service.verify_admin_identity(user)
    if not is_valid:
        # 身份不合格也算"登录失败"——避免攻击者知道哪些用户名存在
        record = login_service.record_login_failure(username)
        return Response(
            {
                "detail": reason,
                "fail_count": record.fail_count,
                "locked": record.is_locked(),
            },
            status=403,
        )

    # ── 4) 登录成功 → 签发 JWT + 重置失败计数 ──
    login_service.reset_on_success(username)

    refresh = RefreshToken.for_user(user)
    request.session.pop("captcha", None)
    return Response(
        {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
            },
        },
        status=200,
    )


# ── 公开 API ──────────────────────────────────────────────────────

@api_view(["get"])
@permission_classes([AllowAny])
def public_site(request):
    site = site_service.get_site_content()
    return Response(SiteContentPublicSerializer(site).data)


@api_view(["get"])
@permission_classes([AllowAny])
def public_categories(request):
    page_key = request.query_params.get("page_key")
    cats = portfolio_service.list_categories(page_key=page_key)
    return Response(CategoryPublicSerializer(cats, many=True).data)


@api_view(["get"])
@permission_classes([AllowAny])
def public_projects(request):
    page_key = request.query_params.get("page_key")
    category_slug = request.query_params.get("category")
    limit = int(request.query_params.get("page_size", 12))
    offset = int(request.query_params.get("offset", 0))
    qs, total = portfolio_service.list_published_projects(
        page_key=page_key, category_slug=category_slug,
        limit=limit, offset=offset,
    )
    return Response({
        "count": total,
        "next": f"?offset={offset + limit}&page_size={limit}",
        "results": ProjectPublicSerializer(qs, many=True).data,
    })


@api_view(["get"])
@permission_classes([AllowAny])
def public_project_detail(request, slug):
    project = portfolio_service.get_published_project_by_slug(slug)
    if not project:
        return Response({"detail": "作品不存在或未发布"}, status=404)
    return Response(ProjectPublicSerializer(project).data)


# ── 匿名提交 API ──────────────────────────────────────────────────

@api_view(["post"])
@permission_classes([AllowAny])
@throttle_classes([InquiryEmailThrottle])
def submit_inquiry(request):
    serializer = InquirySubmitSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        inquiry = inquiry_service.submit_inquiry(serializer.validated_data)
    except inquiry_service.IdempotencyError as e:
        return Response({"detail": str(e)}, status=409)
    except Exception as e:
        return Response({"detail": str(e)}, status=400)
    return Response({
        "id": inquiry.id,
        "message": "需求已提交，我们会在 1~3 个工作日内答复。",
    }, status=201)


@api_view(["post"])
@permission_classes([AllowAny])
@throttle_classes([ContactChannelThrottle])
def submit_contact(request):
    serializer = ContactSubmitSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        contact = contact_service.submit_contact(serializer.validated_data)
    except contact_service.IdempotencyError as e:
        return Response({"detail": str(e)}, status=409)
    except Exception as e:
        return Response({"detail": str(e)}, status=400)
    return Response({
        "id": contact.id,
        "message": "联系方式已收到。",
    }, status=201)


@api_view(["post"])
@permission_classes([AllowAny])
def record_visit(request):
    """作品访问记录（去重：project + visit_id）。"""
    serializer = VisitRecordSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    d = serializer.validated_data
    ProjectVisit.objects.update_or_create(
        project_id=d["project_id"], visit_id=d["visit_id"],
        defaults={
            "visitor_identity": d.get("visitor_identity", ""),
            "identity_key": d.get("identity_key", ""),
        },
    )
    return Response({"ok": True}, status=201)


@api_view(["post"])
@permission_classes([AllowAny])
def playback_start(request):
    serializer = PlaybackStartSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    session = playback_service.create_session(**serializer.validated_data)
    return Response({
        "id": session.id,
        "session_id": session.session_id,
        "video_duration": session.video_duration,
    }, status=201)


@api_view(["post"])
@permission_classes([AllowAny])
def playback_progress(request):
    serializer = PlaybackProgressSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    d = serializer.validated_data
    session = playback_service.report_progress(
        project_id=d["project_id"],
        session_id=d["session_id"],
        natural_intervals=d["natural_intervals"],
        is_ended=d["is_ended"],
    )
    if not session:
        return Response({"detail": "会话不存在"}, status=404)
    return Response({
        "session_id": session.session_id,
        "node_reached_at": session.node_reached_at,
        "is_completed": session.is_completed,
    })


# ── 管理员 API ────────────────────────────────────────────────────

@api_view(["get"])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_inquiries(request):
    status_filter = request.query_params.get("status")
    qs = Inquiry.objects.all()
    if status_filter:
        qs = qs.filter(status=status_filter)
    return Response(InquiryAdminSerializer(qs, many=True).data)


@api_view(["get"])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_inquiry_detail(request, inquiry_id):
    inquiry = Inquiry.objects.get(id=inquiry_id)
    history = StatusHistory.objects.filter(
        inquiry=inquiry,
    ).order_by("-operated_at")
    return Response({
        "inquiry": InquiryAdminSerializer(inquiry).data,
        "history": StatusHistorySerializer(history, many=True).data,
    })


@api_view(["post"])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_inquiry_update_status(request, inquiry_id):
    new_status = request.data.get("status")
    version = int(request.data.get("version", 0))
    notes = request.data.get("admin_notes", "")
    try:
        inquiry = inquiry_service.update_inquiry_status(
            inquiry_id=inquiry_id,
            new_status=new_status,
            version=version,
            notes=notes,
            operated_by=request.user,
        )
    except inquiry_service.VersionConflictError as e:
        return Response({"detail": str(e)}, status=409)
    except Exception as e:
        return Response({"detail": str(e)}, status=400)
    return Response(InquiryAdminSerializer(inquiry).data)


@api_view(["post"])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_inquiry_update_notes(request, inquiry_id):
    admin_notes = request.data.get("admin_notes", "")
    version = int(request.data.get("version", 0))
    try:
        inquiry = inquiry_service.update_inquiry_notes(
            inquiry_id=inquiry_id,
            admin_notes=admin_notes,
            version=version,
            operated_by=request.user,
        )
    except inquiry_service.VersionConflictError as e:
        return Response({"detail": str(e)}, status=409)
    return Response(InquiryAdminSerializer(inquiry).data)


@api_view(["get"])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_contacts(request):
    qs = Contact.objects.all()
    status_filter = request.query_params.get("status")
    if status_filter:
        qs = qs.filter(status=status_filter)
    return Response(ContactAdminSerializer(qs, many=True).data)


@api_view(["get", "post", "put"])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_projects(request, project_id=None):
    if request.method == "GET":
        if project_id:
            p = PortfolioProject.all_objects.get(id=project_id)
            return Response(ProjectAdminSerializer(p).data)
        qs = PortfolioProject.all_objects.all().order_by("-updated_at")
        return Response(ProjectAdminSerializer(qs, many=True).data)

    if request.method == "POST":
        data = request.data.copy()
        data.pop("version", None)  # 创建时不接受 version
        try:
            project = portfolio_service.save_project(data)
        except Exception as e:
            return Response({"detail": str(e)}, status=400)
        return Response(ProjectAdminSerializer(project).data, status=201)

    if request.method == "PUT":
        project = PortfolioProject.all_objects.get(id=project_id)
        data = request.data.copy()
        version = data.pop("version", None)
        try:
            updated = portfolio_service.save_project(
                {**data, "slug": project.slug}, version=version,
            )
        except portfolio_service.VersionConflictError as e:
            return Response({"detail": str(e)}, status=409)
        except Exception as e:
            return Response({"detail": str(e)}, status=400)
        return Response(ProjectAdminSerializer(updated).data)


@api_view(["post"])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_project_publish(request, project_id):
    version = request.data.get("version")
    try:
        project = portfolio_service.publish_project(project_id, version=version)
    except portfolio_service.VersionConflictError as e:
        return Response({"detail": str(e)}, status=409)
    except portfolio_service.PublishValidationError as e:
        return Response({"detail": str(e)}, status=422)
    return Response(ProjectAdminSerializer(project).data)


@api_view(["post"])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_project_unpublish(request, project_id):
    version = request.data.get("version")
    try:
        project = portfolio_service.unpublish_project(project_id, version=version)
    except portfolio_service.VersionConflictError as e:
        return Response({"detail": str(e)}, status=409)
    return Response(ProjectAdminSerializer(project).data)


@api_view(["get"])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_assets(request):
    qs = MediaAsset.objects.all().order_by("-uploaded_at")
    return Response(MediaAssetAdminSerializer(qs, many=True).data)


@api_view(["post"])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_asset_upload(request):
    """素材上传：接收文件 → 保存到 media/ → 创建 MediaAsset 记录。"""
    file_obj = request.FILES.get("file")
    if not file_obj:
        return Response({"detail": "请上传文件"}, status=400)

    import os
    from django.conf import settings

    asset_type = request.data.get("asset_type", "image")
    mime_type = file_obj.content_type or ""
    is_video = "video" in mime_type or file_obj.name.lower().endswith(
        (".mp4", ".webm", ".mov")
    )
    detected_type = "video" if is_video else asset_type

    # 保存到 MEDIA_ROOT
    upload_dir = os.path.join(settings.MEDIA_ROOT, "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    dest_path = os.path.join(upload_dir, file_obj.name)
    with open(dest_path, "wb+") as f:
        for chunk in file_obj.chunks():
            f.write(chunk)

    width = height = None
    duration = None
    if detected_type == "image":
        try:
            with Image.open(dest_path) as im:
                width, height = im.size
        except Exception:
            pass
    elif detected_type == "video":
        duration = 0  # 简单实现：视频时长留 0

    asset = MediaAsset.objects.create(
        asset_type=detected_type,
        storage_bucket="local",
        object_key=os.path.relpath(dest_path, settings.MEDIA_ROOT).replace("\\", "/"),
        mime_type=mime_type,
        file_size=file_obj.size,
        width=width,
        height=height,
        duration_seconds=duration,
        asset_status="ready",
    )
    return Response(MediaAssetAdminSerializer(asset).data, status=201)


@api_view(["get", "put"])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_site(request):
    if request.method == "GET":
        return Response(SiteContentPublicSerializer(site_service.get_site_content()).data)
    data = request.data
    version = data.pop("version", None)
    try:
        site = site_service.save_site_content(data, version=version)
    except Exception as e:
        return Response({"detail": str(e)}, status=409)
    return Response({
        "brand_name": site.brand_name,
        "brand_name_en": site.brand_name_en,
        "version": site.version,
    })


@api_view(["get", "post"])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_calendar(request):
    if request.method == "GET":
        strategy_version = request.query_params.get("strategy_version")
        qs = BusinessCalendar.objects.all()
        if strategy_version:
            qs = qs.filter(strategy_version=strategy_version)
        return Response(CalendarSerializer(qs, many=True).data)

    entries = request.data.get("entries", [])
    if not entries:
        return Response({"detail": "请提供日历条目"}, status=400)
    new_version = calendar_service.activate_new_strategy(entries)
    return Response({"strategy_version": new_version}, status=201)


@api_view(["get"])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_stats_summary(request):
    """概览统计。"""
    project_count = PortfolioProject.objects.count()
    published_count = PortfolioProject.objects.filter(is_published=True).count()
    inquiry_count = Inquiry.objects.count()
    contact_count = Contact.objects.count()
    play_stats = stats_service.get_completion_stats()
    return Response({
        "projects": {"total": project_count, "published": published_count},
        "inquiries": {
            "total": inquiry_count,
            "by_status": dict(
                Inquiry.objects.values_list("status").annotate(c=Count("id")).values_list("status", "c")
            ),
        },
        "contacts": {"total": contact_count},
        "playback": play_stats,
    })


@api_view(["get"])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_stats_playback(request):
    project_id = request.query_params.get("project_id")
    pv_uv = stats_service.get_pv_uv(project_id=project_id)
    completions = stats_service.get_completion_stats(project_id=project_id)
    return Response({**pv_uv, **completions})


@api_view(["get"])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_stats_trend(request):
    days = int(request.query_params.get("days", 7))
    project_id = request.query_params.get("project_id")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days - 1)
    trend = stats_service.get_daily_trend(start_date, end_date)
    return Response(trend)


@api_view(["get"])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_stats_rankings(request):
    limit = int(request.query_params.get("limit", 10))
    return Response(stats_service.get_rankings(limit=limit))


@api_view(["get"])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_inquiries_export_csv(request):
    """返回 CSV 文本，前端触发下载。"""
    csv_content = site_service.export_inquiries_csv()
    from django.http import HttpResponse
    response = HttpResponse(csv_content, content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = "attachment; filename=inquiries.csv"
    return response
