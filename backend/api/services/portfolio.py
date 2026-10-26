"""
作品 Service —— CRUD + 乐观锁 + 发布校验 + 素材关联

开题报告迁移：RPC portfolio_admin_save_project() + 触发器 → 本 Service
核心业务规则（PRD §4.2/§4.3）：
  - 乐观锁：保存时携带 version，冲突拒绝覆盖
  - 发布校验：封面存在 + 额外封面 ≤ 4 + 视频素材 ready + 时长 > 0
  - 软删除：下架置 deleted_at + is_published=False，前台隐藏后台保留
"""

from datetime import datetime

from django.db.models import F

from ..models import (
    PortfolioProject,
    PortfolioCategory,
    MediaAsset,
    ProjectAssetRelation,
)
from ..utils.validators import validate_cover_publish


class VersionConflictError(Exception):
    pass


class PublishValidationError(Exception):
    pass


def save_project(data: dict, version: int = None,
                 user=None) -> PortfolioProject:
    """
    保存/更新作品（乐观锁）。

    开题报告 RPC portfolio_admin_save_project() 的迁移实现。
    """
    slug = data.get("slug")
    is_create = not slug or not PortfolioProject.all_objects.filter(slug=slug).exists()

    # 创建
    if is_create:
        category = _resolve_category(data.get("category_id"), data.get("category_slug"))
        project = PortfolioProject.objects.create(
            slug=slug or _generate_slug(data.get("title")),
            title=data["title"],
            category=category,
            content_type=data.get("content_type", "photo"),
            card_layout=data.get("card_layout", "banner"),
            summary=data.get("summary", ""),
            background=data.get("background", ""),
            notes=data.get("notes", ""),
            credits=data.get("credits", []),
            content_blocks=data.get("content_blocks", []),
            cover_image_id=data.get("cover_image_id"),
            cover_image_legacy_path=data.get("cover_image_legacy_path", ""),
            video_asset_id=data.get("video_asset_id"),
            version=1,
        )
    else:
        project = PortfolioProject.all_objects.get(slug=slug)
        if version is not None and project.version != version:
            raise VersionConflictError(
                f"版本号不匹配，当前 {project.version}，提交 {version}。"
            )
        category = _resolve_category(data.get("category_id"), data.get("category_slug"))
        updated = PortfolioProject.all_objects.filter(
            id=project.id,
            version=version if version is not None else project.version,
        ).update(
            title=data.get("title", project.title),
            category=category,
            content_type=data.get("content_type", project.content_type),
            card_layout=data.get("card_layout", project.card_layout),
            summary=data.get("summary", project.summary),
            background=data.get("background", project.background),
            notes=data.get("notes", project.notes),
            credits=data.get("credits", project.credits),
            content_blocks=data.get("content_blocks", project.content_blocks),
            cover_image_id=data.get("cover_image_id", project.cover_image_id),
            cover_image_legacy_path=data.get("cover_image_legacy_path",
                                             project.cover_image_legacy_path),
            video_asset_id=data.get("video_asset_id", project.video_asset_id),
            version=F("version") + 1,
        )
        if version is not None and updated == 0:
            raise VersionConflictError("乐观锁更新失败")
        project.refresh_from_db()

    # 素材关联
    _sync_asset_relations(project, data.get("extra_covers", []), role="extra_cover")
    _sync_asset_relations(project, data.get("gallery", []), role="gallery")

    return project


def publish_project(project_id: int, version: int = None) -> PortfolioProject:
    """
    发布作品：先校验封面/素材条件，再置 is_published=True。

    开题报告触发器的迁移实现——触发器改为 Service 层校验。
    """
    project = PortfolioProject.all_objects.get(id=project_id)

    # 校验
    errors = []
    validate_cover_publish(project, errors)
    if errors:
        raise PublishValidationError("；".join(errors))

    # 乐观锁
    current_version = project.version
    if version is not None and version != current_version:
        raise VersionConflictError(f"版本号不匹配。")

    updated = PortfolioProject.all_objects.filter(
        id=project_id,
        version=version if version is not None else current_version,
    ).update(
        is_published=True,
        deleted_at=None,
        version=F("version") + 1,
    )
    if updated == 0:
        raise VersionConflictError("乐观锁发布失败")

    project.refresh_from_db()
    return project


def unpublish_project(project_id: int, version: int = None) -> PortfolioProject:
    """下架作品（软删除）：deleted_at = now() + is_published=False。"""
    project = PortfolioProject.all_objects.get(id=project_id)
    current_version = project.version
    if version is not None and version != current_version:
        raise VersionConflictError(f"版本号不匹配。")

    updated = PortfolioProject.all_objects.filter(
        id=project_id,
        version=version if version is not None else current_version,
    ).update(
        is_published=False,
        deleted_at=datetime.now(),
        version=F("version") + 1,
    )
    if updated == 0:
        raise VersionConflictError("乐观锁下架失败")

    project.refresh_from_db()
    return project


# ── 内部辅助 ──────────────────────────────────────────────────────

def _resolve_category(cat_id=None, cat_slug=None):
    if cat_id:
        return PortfolioCategory.objects.get(id=cat_id)
    if cat_slug:
        return PortfolioCategory.objects.get(slug=cat_slug)
    raise ValueError("作品必须关联分类")


def _sync_asset_relations(project, asset_ids: list[int], role: str) -> None:
    """按 role 同步作品的素材关联。"""
    ProjectAssetRelation.objects.filter(project=project, role=role).delete()
    if asset_ids:
        rels = [
            ProjectAssetRelation(
                project=project, asset_id=aid, role=role, sort_order=i,
            )
            for i, aid in enumerate(asset_ids)
        ]
        ProjectAssetRelation.objects.bulk_create(rels)


def _generate_slug(title: str) -> str:
    import re
    base = re.sub(r"[^\w\s-]", "", title.lower()).strip().replace(" ", "-")
    if not base:
        base = f"project-{PortfolioProject.objects.count() + 1}"
    slug = base[:50]
    i = 1
    while PortfolioProject.objects.filter(slug=slug).exists():
        slug = f"{base[:45]}-{i}"
        i += 1
    return slug


# ── 公开快照读取（前台匿名） ──────────────────────────────────────

def list_published_projects(page_key=None, category_slug=None,
                            limit=None, offset=0):
    """读取已发布作品列表（前台匿名）。"""
    qs = PortfolioProject.objects.filter(is_published=True)
    if page_key:
        qs = qs.filter(category__page_key=page_key, category__is_enabled=True)
    if category_slug:
        qs = qs.filter(category__slug=category_slug)

    total = qs.count()
    if limit:
        qs = qs[offset:offset + limit]
    return list(qs), total


def get_published_project_by_slug(slug: str) -> PortfolioProject | None:
    return PortfolioProject.objects.filter(slug=slug, is_published=True).first()


def list_categories(page_key=None):
    qs = PortfolioCategory.objects.filter(is_enabled=True)
    if page_key:
        qs = qs.filter(page_key=page_key)
    return list(qs)


def get_project_assets(project: PortfolioProject):
    """返回作品的素材字典：extra_covers + gallery。"""
    from django.db.models import Prefetch

    extra = ProjectAssetRelation.objects.filter(
        project=project, role="extra_cover",
    ).select_related("asset").order_by("sort_order")
    gallery = ProjectAssetRelation.objects.filter(
        project=project, role="gallery",
    ).select_related("asset").order_by("sort_order")
    return {
        "extra_covers": [r.asset for r in extra],
        "gallery": [r.asset for r in gallery],
    }
