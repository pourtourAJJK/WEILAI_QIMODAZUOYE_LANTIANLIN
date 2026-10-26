# Iteration 2 —— Service 层 + DRF 全部 API 端点

**日期**：2026-10-26
**分支**：`feature/service-layer`
**对应 Epic**：Epic 3（全部 8 条核心业务规则）+ Epic 4/5 的 API 端点层

---

## 改动说明

完成了 Django REST Framework 后端 API 的完整实现，包括：

### Service 层（8 个业务规则）

| 文件 | 对应开题报告 RPC | 核心规则 |
|------|----------------|---------|
| `services/calendar.py` | `portfolio_workday()` | 工作日 SLA 截止计算（跳过休息日，策略版本冻结） |
| `services/inquiry.py` | `portfolio_submit_inquiry()` + `portfolio_update_inquiry()` | 幂等提交 + 乐观锁状态更新 + 状态历史事务 |
| `services/contact.py` | `portfolio_submit_contact()` | 联系方式幂等提交 |
| `services/portfolio.py` | `portfolio_admin_save_project()` + 触发器 | 作品 CRUD + 乐观锁版本校验 + publish 封面/素材校验 + 软删除 |
| `services/playback.py` | `portfolio_create_play_session()` + `portfolio_record_progress()` | 播放会话去重 + 节点到达记录 + 完播三条件判定 |
| `services/stats.py` | `portfolio_stats_*()` | PV/UV 聚合 + 节点到达率 + 完播率 + 排行榜排序 |
| `services/site.py` | `portfolio_public_snapshot()` | 站点内容单例 + CSV 导出 |

### API 端点（全部实现）

| 分组 | 端点 | 权限 |
|------|------|------|
| **认证** | `/api/auth/captcha/`, `/api/auth/login/`, `/api/auth/refresh/` | AllowAny |
| **公开** | `/api/public/site/`, `/api/public/categories/`, `/api/public/projects/`, `/api/public/projects/{slug}/` | AllowAny |
| **匿名提交** | `/api/submit/inquiry/`, `/api/submit/contact/`, `/api/submit/visit/`, `/api/submit/playback/start/`, `/api/submit/playback/progress/` | AllowAny + Throttle |
| **管理员** | `/api/admin/inquiries/`（含 CSV 导出）、`/api/admin/contacts/`、`/api/admin/projects/`（CRUD + publish/unpublish）、`/api/admin/assets/` + 上传、`/api/admin/site/`、`/api/admin/calendar/`、`/api/admin/stats/*`（概览 + 播放 + 趋势 + 排行榜） | IsAuthenticated + IsAdminUser |

### 其他

- `permissions.py`：`IsAdminUser`（检查 AdminBinding 表，替代开题报告的 `portfolio_is_admin()` RPC）
- `throttling.py`：`InquiryEmailThrottle`（邮箱级 60s 一次）+ `ContactChannelThrottle`（联系方式 60s 一次）
- `serializers.py`：公开 / 提交 / 管理员三套 Serializer
- `api/urls.py` + `portfolio/urls.py`：全部路由挂载

---

## 技术决策

| 决策 | 原因 |
|------|------|
| **RPC → Service 方法 + DRF View** | 开题报告后端无业务服务器（RPC 全在 PostgreSQL 里）；Django 作为 Web 框架有明确的 Service → View → URL 分层，自然迁移 |
| **触发器 → Service.publish()** | PostgreSQL trigger 改为 Django Service 层校验（封面存在 + 素材 ready + 视频时长 > 0）；好处：Python 可测试 + 不依赖 SQL 客户端查看 |
| **RLS → Permission + Manager 过滤** | SQLite 不支持 RLS；Django 用 DRF Permission 类控制谁能访问哪些接口，用 SoftDeleteManager 过滤已下架作品 |
| **完播三条件原样保留** | 开题报告定义的"结束事件 + 覆盖 ≥ 98% + 尾部附近自然到达"三个条件全部保留，不因迁移架构而简化 |
| **CSV 导出仍由前端触发下载** | 开题报告设计：后端返回 CSV 文本，前端在浏览器端生成下载。后端额外提供 `Content-Disposition: attachment` 头简化前端 |

---

## 构建 / 验证结果

| 检查项 | 结果 |
|--------|------|
| `python manage.py check` | ✅ 0 errors |
| 所有模块 import | ✅ `from api import urls, views, serializers, services, permissions, throttling` 全部 OK |
| `runserver` | ✅ 启动成功 |
| `/api/public/site/` | ✅ 200，返回品牌信息 |
| `/api/public/categories/?page_key=campus` | ✅ 200，返回 4 个分类 |
| `/api/public/projects/?page_size=3` | ✅ 200，返回作品列表 |
| Fixtures 灌入 | ✅ 分类 8 + 作品 5 + 站点 1 + 日历 14 条目 |

---

## 已知局限

1. **前端尚未搭建** —— Vue 3 + Vite 还没初始化（Epic 4），API 端点还没真实调用链验证
2. **管理员端到端未验证** —— login → JWT → `/api/admin/*` 这条链路还没跑通（前端 axios + JWT header 还没加）
3. **限流 / 节流实际效果未验证** —— throttle 类已定义，但 Django 默认缓存是本地内存，多进程下可能不共享
4. **单元测试未写** —— Epic 计划里有单元测试（幂等、乐观锁、完播判定），当前还没实现（可在迭代后补）
5. **视频时长自动提取** —— 当前素材上传的 duration_seconds 留 0，需要 ffmpeg 或专门库（Epic 5 可补）
