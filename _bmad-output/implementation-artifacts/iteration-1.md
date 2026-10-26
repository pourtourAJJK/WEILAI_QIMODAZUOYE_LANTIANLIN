# Iteration 1 —— Django 后端骨架 + 13 张业务表

**日期**：2026-10-26
**分支**：`feature/init-and-models`
**对应 Epic**：Epic 1（项目初始化）+ Epic 2（数据模型 + Fixtures）

---

## 改动说明

完成了 Django 后端的基础骨架搭建，包括：

1. **Django 项目初始化**（`portfolio/` package）
   - Django 5.2 + DRF + SimpleJWT + CORS Headers + django-filter
   - settings.py 完整配置：REST_FRAMEWORK、JWT 2h access token、CORS 白名单 localhost:5173
   - 自定义分页类 `api/pagination.py`

2. **13 张业务表全部定义**（`api/models.py`）
   - 作品域：PortfolioProject（软删除 Manager）、PortfolioCategory、MediaAsset、ProjectAssetRelation
   - 客户域：Inquiry、Contact、StatusHistory（可空外键区分来源）
   - 统计日历域：ProjectVisit（unique_together 去重）、PlaySession、ExportRecord、BusinessCalendar（联合主键）
   - 站点权限域：SiteContent（单例 save 方法）、AdminBinding（OneToOne 到 User）

3. **迁移 + 初始数据灌入**
   - `makemigrations` → `migrate` 全部成功
   - 初始数据：8 分类（campus 4 + commercial 4）、5 已发布作品、站点内容、14 天工作日历、3 模拟 MediaAsset
   - 管理员：admin / admin1234（已绑定 AdminBinding）

---

## 技术决策

| 决策 | 原因 |
|------|------|
| **去掉 PortfolioProject.extra_covers/gallery 的 M2M 声明** | Django E003：两个 M2M 共享同一个 through 模型不允许。改为在 Service/Serializer 层通过 `ProjectAssetRelation.objects.filter(role="extra_cover")` 查询 |
| **软删除用 Manager 而非 QuerySet filter** | 开题报告原设计需要前台过滤 deleted_at 非空 + 后台 all_objects 全部可见；自定义 SoftDeleteManager / SoftDeleteAllManager 是 Django 社区推荐方式 |
| **BusinessCalendar 用 strategy_version + date 联合主键** | 开题报告要求"修改日历后新增策略版本，不改变历史截止时间"；联合主键天然保证同一版本下日期唯一 |
| **SQLite 作为开发数据库** | Windows 开发阶段 SQLite 开箱即用；PRD 明确 PostgreSQL 为生产数据库 |
| **request_id 唯一约束直接加在模型字段上** | 开题报告的幂等设计：相同 request_id 不新增行；Django 模型层 unique 约束比 Service 层先执行，更不容易绕过 |

---

## 构建 / 验证结果

| 检查项 | 结果 |
|--------|------|
| `python manage.py check` | ✅ System check 通过（0 errors） |
| `makemigrations` | ✅ 生成 `api/migrations/0001_initial.py`，13 张模型 |
| `migrate` | ✅ 13 张表全部创建 |
| `runserver` | ✅ 启动成功（admin/ 页面 200） |
| Fixtures 灌入 | ✅ 分类 8 / 作品 5 / 站点 1 / 日历 14 条目 / MediaAsset 3 |
| 管理员创建 | ✅ admin / admin1234 + AdminBinding |

---

## 已知局限

1. **API Endpoints 尚未实现**——views.py 和 urls.py 还没写，runserver 返回 404（预期内，Epic 3+ 实现）
2. **前端尚未搭建**——Vue 3 + Vite 骨架还没初始化（Epic 4 实现）
3. **Service 层尚未实现**——8 条核心业务规则（乐观锁、幂等、工作日截止等）还没写（Epic 3 实现）
4. **图片验证码未实现**——当前登录接口还没写，验证码逻辑留在 Service 层实现
5. **MediaAsset 真实文件上传**——当前 fixtures 用模拟数据（storage_bucket + object_key），真实上传 API 在 Epic 5 实现
