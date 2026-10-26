"""
播放 Service —— 会话创建 + 进度上报 + 完播判定

开题报告迁移：RPC portfolio_create_play_session() + portfolio_record_progress() → 本 Service
核心业务规则（PRD §4.5）：
  - 会话去重：同一作品 + 同一会话 ID 不重复创建
  - 节点到达：自然播放跨过时记录，同一会话每节点最多一次
  - 完播判定：结束事件为真 AND 覆盖 ≥ 98% AND 尾部附近自然到达
  - 视频时长快照：创建时复制，后续换视频不影响统计口径
"""

from datetime import datetime

from ..models import PlaySession, MediaAsset


NODE_POSITIONS = [0.1, 0.25, 0.5, 0.75, 0.95]  # 百分比


def create_session(project_id: int, session_id: str,
                   video_asset_id: int = None,
                   video_duration: float = 0,
                   visitor_identity: str = "",
                   session_token_hash: str = "") -> PlaySession:
    """
    创建播放会话（去重）。视频时长从素材记录复制快照。

    开题报告 RPC portfolio_create_play_session() 迁移实现。
    """
    # 去重：同作品 + 同 session_id
    existing = PlaySession.objects.filter(
        project_id=project_id, session_id=session_id,
    ).first()
    if existing:
        return existing

    # 视频时长快照
    if not video_duration and video_asset_id:
        try:
            asset = MediaAsset.objects.get(id=video_asset_id)
            video_duration = asset.duration_seconds or 0
        except MediaAsset.DoesNotExist:
            video_duration = 0

    return PlaySession.objects.create(
        project_id=project_id,
        session_id=session_id,
        video_asset_id=video_asset_id,
        video_duration=video_duration,
        visitor_identity=visitor_identity[:100],
        session_token_hash=session_token_hash[:200],
    )


def report_progress(project_id: int, session_id: str,
                    natural_intervals: list[tuple[float, float]],
                    is_ended: bool = False,
                    video_duration: float = None) -> PlaySession:
    """
    合并自然播放区间、去重记录节点到达、检查完播条件。

    开题报告 RPC portfolio_record_progress() 迁移实现。

    Args:
        project_id: 作品 ID
        session_id: 会话 ID（同作品同会话唯一）
        natural_intervals: 自然播放区间列表 [(start_seconds, end_seconds), ...]
                          拖动产生的跳跃区间**不应**包含在内
        is_ended: 播放器是否触发了 ended 事件
        video_duration: 当前会话视频时长（不传则用会话快照）
    """
    session = PlaySession.objects.filter(
        project_id=project_id, session_id=session_id,
    ).first()
    if not session:
        return None

    duration = video_duration or session.video_duration or 0
    if duration <= 0:
        return session

    # 合并自然播放区间 → 观看覆盖（秒）
    covered_seconds = 0.0
    if natural_intervals:
        merged = _merge_intervals(natural_intervals)
        covered_seconds = sum(end - start for start, end in merged if end > start)

    # 记录节点到达
    node_reached = dict(session.node_reached_at or {})
    now_iso = datetime.now().isoformat()
    reached_positions = covered_seconds / duration if duration > 0 else 0
    for pct in NODE_POSITIONS:
        key = f"{int(pct * 100)}pct"
        if reached_positions >= pct and key not in node_reached:
            node_reached[key] = now_iso
    # 尾部（98% 以上）
    tail_key = "98pct"
    if reached_positions >= 0.98 and tail_key not in node_reached:
        node_reached[tail_key] = now_iso

    # 完播判定：三条件同时满足
    completed = is_ended and (covered_seconds / duration >= 0.98) and (reached_positions >= 0.98)

    session.last_event_at = datetime.now()
    session.node_reached_at = node_reached
    if completed and not session.is_completed:
        session.is_completed = True
        session.completed_at = datetime.now()
    session.save(update_fields=["last_event_at", "node_reached_at",
                                 "is_completed", "completed_at"])

    return session


def _merge_intervals(intervals: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """合并重叠或相邻的播放区间。"""
    if not intervals:
        return []
    intervals = sorted([(min(a, b), max(a, b)) for a, b in intervals])
    merged = [intervals[0]]
    for start, end in intervals[1:]:
        prev_start, prev_end = merged[-1]
        if start <= prev_end + 1.0:  # 1 秒容差
            merged[-1] = (prev_start, max(prev_end, end))
        else:
            merged.append((start, end))
    return merged
