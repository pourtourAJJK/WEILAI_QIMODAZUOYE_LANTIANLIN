---
title: "影羽·YINGYU STUDIO 技术架构"
status: draft
created: 2026-10-26
updated: 2026-10-26
---

# 技术架构：影羽·YINGYU STUDIO

## 1. 总体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        浏览器 / 访客                            │
│                                                                 │
│  ┌──────────────────┐     ┌──────────────────┐                  │
│  │  前台展示端 SPA   │     │  后台管理端 SPA   │                 │
│  │  (Vue 3 + Vite)  │     │  (Vue 3 + Vite)  │                 │
│  │  5 路由 + 组件库  │     │  6 模块 + 编辑面板│                 │
│  └────────┬─────────┘     └────────┬─────────┘                 │
│           │  Axios / Fetch + JWT   │                            │
└───────────┼────────────────────────┼────────────────────────────┘
            │                        │
            ▼                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Django REST Framework 后端                     │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    URL Router                             │    │
│  │  /api/public/*   → 公开读取（已发布作品）                 │    │
│  │  /api/submit/*   → 匿名提交（幂等 + 限流）               │    │
│  │  /api/admin/*    → 管理员接口（IsAdminUser Permission）  │    │
│  │  /api/auth/*     → 登录认证（Django Auth + JWT）         │    │
│  └──────────────────┬──────────────────────────────────────┘    │
│                     ▼                                           │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                  Permission & Throttling                  │    │
│  │  IsAuthenticated / IsAdminUser / AllowAny                │    │
│  │  InquiryThrottle / ContactThrottle（邮箱级+全局限流）     │    │
│  │  PublicSnapshotViewSet → 自动过滤 is_published=True      │    │
│  └──────────────────┬──────────────────────────────────────┘    │
│                     ▼                                           │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                  Service Layer（核心业务规则）            │    │
│  │                                                           │    │
│  │  PortfolioService   → 作品 CRUD + 发布校验 + 乐观锁      │    │
│  │  InquiryService     → 咨询提交 + 幂等 + 状态流转 + 历史  │    │
│  │  ContactService     → 联系方式提交 + 幂等                 │    │
│  │  PlaybackService    → 播放会话 + 进度 + 完播判定          │    │
│  │  CalendarService    → 工作日截止计算 + 策略版本管理      │    │
│  │  StatsService       → PV/UV/节点率/完播率统计查询         │    │
│  │  SiteService        → 站点内容读取/保存                  │    │
│  │  ExportService      → CSV 数据导出                        │    │
│  └──────────────────┬──────────────────────────────────────┘    │
│                     ▼                                           │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                  Django ORM + Models                       │    │
│  │  13 张业务表（见 PRD §3） + signals + constraints         │    │
│  │  SQLite（开发）/ PostgreSQL（生产）                        │    │
│  └──────────────────┬──────────────────────────────────────┘    │
│                     ▼                                           │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                  文件存储                                  │    │
│  │  Django media/（开发，本地文件系统）                       │    │
│  │  腾讯云 COS / 阿里云 OSS（生产，django-storages）          │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

## 2. 开题报告 → Django 架构映射

这是本项目架构设计的核心。开题报告后端采用 **CloudBase PostgreSQL + RPC 函数**（无独立业务服务器，业务逻辑全在数据库层），本期改用 **Django REST Framework**。下表逐项说明迁移方式：

| 开题报告机制 | 原实现 | Django 替代实现 | 文件位置 |
|-------------|--------|----------------|---------|
| **RPC 函数**（~20 个） | PostgreSQL PL/pgSQL 存储函数 | DRF ViewSet + Service 方法 | `backend/api/views.py` + `backend/api/services/*.py` |
| **行级安全策略（RLS）** | PostgreSQL RLS 对每张表定义访问规则 | DRF Permission 类 + Service 层过滤 | `backend/api/permissions.py` + Service 方法内的 `filter()` |
| **管理员校验** `portfolio_is_admin()` | RPC 函数内查询 `site_admin_binding` | `IsAdminUser` Permission 类检查 `AdminBinding` 表 | `backend/api/permissions.py` |
| **乐观锁版本控制** | RPC 函数内比较 `version` 字段 | Service 层 `filter(version=expected).update(version=F('version')+1)` | `backend/api/services/portfolio.py` |
| **触发器：作品发布校验** | PostgreSQL trigger 在 insert/update 时校验 | Service 层 `PortfolioService.publish()` 方法 | `backend/api/services/portfolio.py` |
| **软删除** | `portfolio_projects.deleted_at` + 查询条件过滤 | 自定义 Model Manager：默认 `objects` 过滤 `deleted_at__isnull=True`，`all_objects` 全部可见 | `backend/api/managers.py` |
| **幂等（requestId）** | RPC 函数先查重后写入 | Service 层先 `filter(request_id=...).first()` | `backend/api/services/inquiry.py` |
| **频率限制** | RPC 函数内查询计数表判断 | DRF `ScopedRateThrottle` + 自定义 ScopeThrottle | `backend/api/throttling.py` |
| **工作日截止计算** | RPC 函数 `portfolio_workday()` | Service 层逐日期判断 + 跳过休息日 | `backend/api/services/calendar.py` |
| **完播判定** | RPC 函数内校验结束事件 + 覆盖比例 + 尾部到达 | Service 层 `PlaybackService.report_progress()` 内逻辑 | `backend/api/services/playback.py` |
| **状态历史事务** | RPC 函数 `portfolio_update_inquiry()` 内 BEGIN/COMMIT | Django `transaction.atomic()` 上下文管理器 | `backend/api/services/inquiry.py` |
| **公开快照读取** `portfolio_public_snapshot()` | 单个 RPC 返回品牌 + 作品列表 + 分类 | 拆分为多个公开 GET endpoint | `backend/api/views.py` PublicAPIViewSet |
| **CSV 导出** | 前端浏览器端生成（开题报告方式不变） | 前端生成，后端提供筛选范围内的 JSON API | `backend/api/services/export.py` |
| **文件存储**（桶/对象路径/签名地址） | CloudBase 对象存储 + 15 分钟签名 URL | Django media/ + 开发阶段直接访问，生产用 `django-storages` | `backend/settings.py` MEDIA_ROOT/MEDIA_URL |
| **身份认证** | CloudBase 身份认证服务 + 自建表单 | Django Auth + REST Framework SimpleJWT + 图片验证码 | `backend/api/views.py` AuthAPIView |
| **草稿暂存** | 前端 localStorage（开题报告方式不变） | 前端 localStorage | 前端实现 |

## 3. Django 项目结构

```
backend/
├── manage.py                        ← Django 管理入口
├── requirements.txt                 ← 依赖清单
├── .env.example                     ← 环境变量模板
├── portfolio/                       ← Django project package
│   ├── __init__.py
│   ├── settings.py                  ← 配置（DRF、CORS、JWT、media）
│   ├── urls.py                      ← 根 URL 路由
│   ├── wsgi.py
│   └── asgi.py
│
└── api/                             ← 核心业务 app
    ├── __init__.py
    ├── apps.py
    ├── migrations/                  ← 数据库迁移
    ├── models.py                    ← 13 张业务表（Django ORM）
    ├── managers.py                  ← 自定义 Manager（软删除等）
    ├── serializers.py               ← DRF Serializers
    ├── views.py                     ← DRF ViewSets
    ├── urls.py                      ← API 路由
    ├── permissions.py               ← DRF Permission 类
    ├── throttling.py                ← DRF Throttling 类
    ├── pagination.py                ← DRF Pagination
    ├── filters.py                   ← 筛选后端
    ├── services/                    ← 业务逻辑层
    │   ├── __init__.py
    │   ├── portfolio.py             ← 作品 + 分类 + 素材
    │   ├── inquiry.py               ← 咨询 + 状态 + 历史
    │   ├── contact.py               ← 联系方式
    │   ├── playback.py              ← 播放会话 + 进度 + 完播
    │   ├── calendar.py              ← 工作日 + SLA 计算
    │   ├── stats.py                 ← 统计查询
    │   ├── site.py                  ← 站点内容
    │   └── export.py                ← CSV 导出
    ├── utils/                       ← 工具函数
    │   ├── captcha.py               ← 图片验证码
    │   └── validators.py            ← 字段校验器
    └── tests/                       ← Django TestCase
        ├── test_inquiry_idempotency.py
        ├── test_optimistic_lock.py
        ├── test_sla_deadline.py
        └── test_playback_completion.py
```

## 4. 前端项目结构

```
frontend/
├── package.json
├── vite.config.js                   ← Vite 配置 + proxy /api → Django :8000
├── index.html
├── .env.example
│
├── src/
│   ├── main.js
│   ├── App.vue
│   ├── router/index.js              ← Vue Router（前台 5 路由 + 后台 6 路由）
│   ├── api/                         ← API 封装（Axios）
│   │   ├── request.js               ← Axios 实例 + JWT interceptor
│   │   ├── public.js                ← 公开接口（作品、分类、站点）
│   │   ├── submit.js                ← 提交接口（咨询、联系方式）
│   │   ├── admin/                   ← 管理接口
│   │   │   ├── auth.js
│   │   │   ├── portfolio.js
│   │   │   ├── inquiry.js
│   │   │   └── stats.js
│   │   └── playback.js              ← 播放会话 + 进度上报
│   │
│   ├── stores/                      ← Pinia（可选，简单状态用 ref 即可）
│   │
│   ├── utils/
│   │   ├── draft.js                 ← 本地草稿暂存
│   │   ├── idempotency.js           ← requestId 生成
│   │   └── formatters.js
│   │
│   ├── components/                  ← 共享组件
│   │   ├── VideoPlayer.vue          ← HTML5 Video + 事件监听 + 进度上报
│   │   ├── ImageCarousel.vue        ← 封面轮播
│   │   ├── WaterfallGrid.vue        ← 瀑布流布局（三种卡片比例）
│   │   ├── SiteNav.vue
│   │   ├── SiteFooter.vue
│   │   └── CodeShowcase.vue
│   │
│   ├── views/
│   │   ├── public/                  ← 前台页面
│   │   │   ├── HomeView.vue         ← 首页 + Showreel
│   │   │   ├── WorkListView.vue     ← 作品目录（校内）
│   │   │   ├── SpaceListView.vue    ← 商业项目目录
│   │   │   ├── WorkDetail.vue       ← 作品详情弹窗
│   │   │   ├── ContactView.vue
│   │   │   └── AboutView.vue
│   │   └── admin/                   ← 后台页面
│   │       ├── LoginView.vue
│   │       ├── DashboardView.vue    ← 概览
│   │       ├── PortfolioEdit.vue    ← 作品编辑器
│   │       ├── InquiryListView.vue  ← 客户需求 + 状态流转 + CSV
│   │       ├── SiteEdit.vue
│   │       ├── CalendarView.vue
│   │       └── StatsView.vue        ← 统计看板 + ECharts
│   │
│   └── assets/
│       └── styles/                   ← Tailwind CSS 或纯 CSS
│
└── public/
```

## 5. 依赖清单

### 5.1 后端（requirements.txt）

```
Django>=5.0,<5.2
djangorestframework>=3.15
djangorestframework-simplejwt>=5.3
django-cors-headers>=4.4
django-filter>=24.2
Pillow>=10.0           # 图片验证码 + 图片处理
python-dotenv>=1.0     # .env 加载
# 生产可选
# django-storages[boto3]>=1.14
# psycopg2-binary>=2.9
```

### 5.2 前端（package.json）

```json
{
  "dependencies": {
    "vue": "^3.5",
    "vue-router": "^4.5",
    "axios": "^1.7",
    "echarts": "^5.5"
  },
  "devDependencies": {
    "vite": "^5.4",
    "@vitejs/plugin-vue": "^5.1"
  }
}
```

## 6. API 路由设计

### 6.1 公开接口（无需认证）

| Method | Path | 说明 |
|--------|------|------|
| GET | `/api/public/site/` | 站点内容快照（品牌/介绍/Showreel/联系方式） |
| GET | `/api/public/categories/?page_key=campus/commercial` | 分类列表 |
| GET | `/api/public/projects/?category=...&page_key=...` | 已发布作品列表（分页） |
| GET | `/api/public/projects/{slug}/` | 单个作品详情 |

### 6.2 提交接口（匿名，幂等 + 限流）

| Method | Path | 说明 |
|--------|------|------|
| POST | `/api/submit/inquiry/` | 合作咨询提交（request_id + 60s 限流） |
| POST | `/api/submit/contact/` | 联系方式提交（request_id + 60s 限流） |
| POST | `/api/submit/visit/` | 作品访问记录 |
| POST | `/api/submit/playback/start/` | 播放会话创建 |
| POST | `/api/submit/playback/progress/` | 播放进度上报 |
| GET | `/api/captcha/` | 图片验证码（登录用） |

### 6.3 管理员接口（需 JWT + AdminBinding 校验）

| Method | Path | 说明 |
|--------|------|------|
| POST | `/api/auth/login/` | 登录（用户名 + 密码 + 验证码） |
| POST | `/api/auth/refresh/` | JWT 刷新 |
| GET/PUT | `/api/admin/projects/` | 作品列表 + CRUD |
| POST | `/api/admin/projects/{id}/publish/` | 发布（校验封面/素材/版本） |
| POST | `/api/admin/projects/{id}/unpublish/` | 下架（软删除） |
| GET/PUT | `/api/admin/categories/` | 分类 CRUD |
| POST | `/api/admin/assets/upload/` | 素材上传 |
| GET/PUT | `/api/admin/inquiries/` | 合作咨询列表 + 筛选 |
| POST | `/api/admin/inquiries/{id}/status/` | 状态更新 + 历史写入（事务） |
| GET/PUT | `/api/admin/contacts/` | 联系方式管理 |
| POST | `/api/admin/inquiries/export/` | CSV 导出（筛选范围） |
| GET/PUT | `/api/admin/site/` | 站点内容 |
| GET/PUT | `/api/admin/calendar/` | 工作日历 |
| POST | `/api/admin/calendar/activate/` | 启用新策略版本 |
| GET | `/api/admin/stats/summary/` | 概览统计 |
| GET | `/api/admin/stats/playback/?project=&range=...&granularity=...` | 播放统计 |
| GET | `/api/admin/stats/rankings/?range=...` | 作品排行榜 |

## 7. 开发运行

| 组件 | 命令 | 端口 |
|------|------|------|
| 后端 | `cd backend && python manage.py runserver` | `http://localhost:8000` |
| 前端 | `cd frontend && npm run dev` | `http://localhost:5173`（Vite proxy `/api` → `:8000`） |
| 数据库 | SQLite（默认，`backend/db.sqlite3`） | — |

**首次启动**：
```bash
# 后端
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser     # 管理员账号
python manage.py runserver

# 前端（新终端）
cd frontend
npm install
npm run dev
```
