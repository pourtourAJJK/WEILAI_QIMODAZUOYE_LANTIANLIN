"""
自定义 DRF 权限类
"""

from rest_framework.permissions import BasePermission

from .models import AdminBinding


class IsAdminUser(BasePermission):
    """
    必须是 Django Auth 已认证用户，且在 AdminBinding 表中有记录。

    开题报告迁移：RPC portfolio_is_admin() → 本 Permission
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return AdminBinding.objects.filter(user=request.user).exists()
