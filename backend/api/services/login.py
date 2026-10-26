"""
登录锁定 Service —— 失败 5 次自动锁定 5 分钟

规则：
  - 按 username 追踪（不记录 IP / 设备指纹；开发阶段简化）
  - MAX_FAILS_BEFORE_LOCK = 5
  - LOCK_DURATION_SECONDS = 300（5 分钟）
  - 锁定到期后自动解锁；成功登录后立即重置 fail_count + 清除锁定
  - 身份校验：Django Auth authenticate() 成功后 + 检查 AdminBinding + is_active + is_staff
"""

from datetime import timedelta

from django.utils import timezone

from ..models import LoginAttempt, AdminBinding


def get_or_create_record(username: str) -> LoginAttempt:
    """按 username 获取或创建 LoginAttempt 记录。"""
    record, _ = LoginAttempt.objects.get_or_create(username=username)
    return record


def is_account_locked(username: str) -> tuple[bool, int]:
    """
    检查账号当前是否被锁定。

    Returns:
        (is_locked: bool, remaining_seconds: int)
    """
    record = get_or_create_record(username)
    remaining = record.remaining_lock_seconds()
    return (remaining > 0, remaining)


def record_login_failure(username: str) -> LoginAttempt:
    """
    记录一次登录失败。如果累计失败次数达到阈值，设置锁定到期时间。
    """
    now = timezone.now()
    record = get_or_create_record(username)

    # 已锁定但到期了 → 清除锁定，开始新一轮计数
    if record.locked_until and record.locked_until <= now:
        record.locked_until = None
        record.fail_count = 0

    record.fail_count += 1
    record.last_failed_at = now

    if record.fail_count >= LoginAttempt.MAX_FAILS_BEFORE_LOCK:
        record.locked_until = now + timedelta(seconds=LoginAttempt.LOCK_DURATION_SECONDS)

    record.save()
    return record


def reset_on_success(username: str) -> None:
    """登录成功 → 重置失败计数 + 清除锁定。"""
    LoginAttempt.objects.filter(username=username).update(
        fail_count=0,
        locked_until=None,
        last_failed_at=None,
    )


def verify_admin_identity(user) -> tuple[bool, str]:
    """
    验证 Django User 是否是"我们自己创建的管理员账号"。

    条件：
      1. user.is_active == True（账号未被禁用）
      2. AdminBinding 表中有记录（明确绑定管理员身份）

    Returns:
        (is_valid: bool, reason: str)
    """
    if not user.is_active:
        return False, "该账号已被禁用"
    if not AdminBinding.objects.filter(user=user).exists():
        return False, "该账号未绑定管理员权限"
    return True, ""
