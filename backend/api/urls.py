"""
API 路由 —— 按公开 / 提交 / 管理员分组
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views


urlpatterns = [
    # ── 认证 ──
    path("auth/captcha/", views.get_captcha, name="captcha"),
    path("auth/login/", views.login, name="login"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token-refresh"),

    # ── 公开 ──
    path("public/site/", views.public_site, name="public-site"),
    path("public/categories/", views.public_categories, name="public-categories"),
    path("public/projects/", views.public_projects, name="public-projects"),
    path("public/projects/<slug:slug>/", views.public_project_detail, name="public-project-detail"),

    # ── 匿名提交 ──
    path("submit/inquiry/", views.submit_inquiry, name="submit-inquiry"),
    path("submit/contact/", views.submit_contact, name="submit-contact"),
    path("submit/visit/", views.record_visit, name="submit-visit"),
    path("submit/playback/start/", views.playback_start, name="playback-start"),
    path("submit/playback/progress/", views.playback_progress, name="playback-progress"),

    # ── 管理员 ──
    path("admin/inquiries/", views.admin_inquiries, name="admin-inquiries"),
    path("admin/inquiries/export/csv/", views.admin_inquiries_export_csv, name="admin-inquiries-export"),
    path("admin/inquiries/<int:inquiry_id>/", views.admin_inquiry_detail, name="admin-inquiry-detail"),
    path("admin/inquiries/<int:inquiry_id>/status/", views.admin_inquiry_update_status, name="admin-inquiry-status"),
    path("admin/inquiries/<int:inquiry_id>/notes/", views.admin_inquiry_update_notes, name="admin-inquiry-notes"),
    path("admin/contacts/", views.admin_contacts, name="admin-contacts"),
    path("admin/projects/", views.admin_projects, name="admin-projects-list"),
    path("admin/projects/<int:project_id>/", views.admin_projects, name="admin-project-detail"),
    path("admin/projects/<int:project_id>/publish/", views.admin_project_publish, name="admin-project-publish"),
    path("admin/projects/<int:project_id>/unpublish/", views.admin_project_unpublish, name="admin-project-unpublish"),
    path("admin/assets/", views.admin_assets, name="admin-assets"),
    path("admin/assets/upload/", views.admin_asset_upload, name="admin-asset-upload"),
    path("admin/site/", views.admin_site, name="admin-site"),
    path("admin/calendar/", views.admin_calendar, name="admin-calendar"),
    # 统计
    path("admin/stats/summary/", views.admin_stats_summary, name="admin-stats-summary"),
    path("admin/stats/playback/", views.admin_stats_playback, name="admin-stats-playback"),
    path("admin/stats/trend/", views.admin_stats_trend, name="admin-stats-trend"),
    path("admin/stats/rankings/", views.admin_stats_rankings, name="admin-stats-rankings"),
]
