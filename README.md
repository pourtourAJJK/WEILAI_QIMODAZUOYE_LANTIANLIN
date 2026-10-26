# 影羽·YINGYU STUDIO —— 个人摄影作品集网站

> 《未来技术》课程大作业 —— BMAD-Method 工作流 + Git 分支合并实践

## 项目简介

**可视化个人简历 + 可视化商业展示窗口**。面向摄影与视频创作者，将传统文字简历转化为有真实作品支撑的项目案例集合，同时面向潜在客户提供从作品浏览到合作提交的完整路径。

- 前端：Vue 3 + Vite + Vue Router + Axios
- 后端：Django REST Framework（替代开题报告原 CloudBase RPC 架构）
- 数据库：SQLite（开发）/ PostgreSQL（生产）
- 部署：前后台分离，开发阶段 `localhost:5173`（前端）+ `localhost:8000`（后端）

## 目录结构

```
WEILAI_BYSJ_L/
├── _bmad-output/                      BMAD 工作流产物
│   ├── planning-artifacts/            阶段一、二（需求/架构/任务拆分）
│   │   ├── product-brief.md           产品简报
│   │   ├── prd.md                     需求规格
│   │   ├── architecture.md            技术架构（Django 如何承载开题报告业务规则）
│   │   └── epics-and-stories.md       开发任务拆分
│   └── implementation-artifacts/       阶段三、四（迭代记录/构建/测试）
│       ├── iteration-1.md             Django 骨架 + 13 张表
│       ├── iteration-2.md             Service 层 8 条业务规则 + DRF API
│       ├── iteration-3.md             Vue 3 前端（前台 5 路由 + 后台登录 + 概览）
│       ├── build-report.md            构建报告（API 清单 + build 输出）
│       └── test-report.md             测试报告
├── backend/                            Django 后端
│   ├── manage.py
│   ├── requirements.txt
│   ├── portfolio/                     Django project package
│   ├── api/                           业务 app（models/services/views）
│   │   ├── models.py                  13 张业务表
│   │   ├── services/                  8 条核心业务规则
│   │   ├── views.py                   DRF API endpoints
│   │   ├── serializers.py
│   │   ├── permissions.py
│   │   ├── throttling.py
│   │   └── fixtures/initial_data.json 初始数据
│   └── db.sqlite3                      SQLite 开发数据库（自动生成）
├── frontend/                           Vue 3 前端
│   ├── package.json
│   ├── vite.config.js                 含 proxy /api → :8000
│   └── src/
│       ├── api/                       Axios API 封装
│       ├── router/index.js            Vue Router
│       ├── views/                     前台 + 后台页面
│       ├── components/                SiteNav / SiteFooter
│       └── main.js
├── AGENTS.md                           大作业规则（BMAD + Git 规范）
├── .gitignore
└── README.md                          ← 本文件
```

## 快速启动

### 1. 启动后端（端口 8000）

```bash
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py loaddata api/fixtures/initial_data.json  # 可选：灌入初始数据
python manage.py runserver 0.0.0.0:8000
```

- 管理员账号：`admin` / `admin1234`
- Django Admin：`http://localhost:8000/admin/`

### 2. 启动前端（端口 5173）

```bash
cd frontend
npm install          # 首次运行
npm run dev
```

- 前台页面：`http://localhost:5173/`
- 后台入口：`http://localhost:5173/login`（管理员登录）

Vite dev server 已配置 proxy：
- `/api/*` → `http://localhost:8000/api/*`
- `/media/*` → `http://localhost:8000/media/*`

### 3. 生产构建

```bash
# 前端
cd frontend && npm run build      # 输出到 frontend/dist/

# 后端（使用 PostgreSQL）
# 修改 portfolio/settings.py DATABASES 配置
# 安装 psycopg2-binary
```

## 核心演示路径

> 课程大作业评分核心：至少一条完整核心流程能当场演示。

### 路径 1：访客浏览 + 提交合作需求（~1 分钟）

1. 打开 `http://localhost:5173/`
2. 首页 Showreel 区域 → 向下滚动
3. 点"校内创作"或"商业项目"进入作品列表 → 切换分类筛选 → 点击一张作品 → 详情弹窗（封面轮播 + 项目档案）
4. 点顶部导航"联系我们" → 填写合作需求表单（姓名/邮箱/合作类型/勾选授权）→ **提交** → 看到提示"需求已提交，我们会在 1~3 个工作日内答复。"

### 路径 2：管理员登录 + 查看咨询 + 改状态（~1 分钟）

1. 打开 `http://localhost:5173/login`
2. 输入 `admin` / `admin1234` → **登录**
3. 跳转后台概览 → 看到作品数 / 咨询数 / 播放会话统计
4. 打开"客户需求"API（`/api/admin/inquiries/`）→ 找到刚才的提交
5. 用 curl 或直接用快速入口的状态流转功能改状态 → 查看状态历史自动写入

### 技术亮点演示

| 亮点 | 验证方法 |
|------|---------|
| **乐观锁版本控制** | 两个窗口同时编辑同一作品 → 后保存的看到"请刷新后重试"（API 层返回 409） |
| **表单幂等** | 合作需求提交后按 F5 刷新（同一 request_id）→ 后台只有一条记录 |
| **工作日截止时间** | 周一提交咨询 → 截止时间 = 周四；周五提交 → 截止时间 = 下周三（自动跳过周末） |
| **软删除** | 作品下架（置 `is_published=False` + `deleted_at=now()`）→ 前台隐藏，后台 all_objects 可查 |

## 技术亮点（与开题报告对比）

开题报告后端采用 CloudBase PostgreSQL + RPC 函数（无独立业务服务器）。本次实现改用 **Django REST Framework**，核心业务规则一一迁移：

| 开题报告 RPC | Django 实现 | 文件 |
|-------------|------------|------|
| `portfolio_submit_inquiry()` | `inquiry_service.submit_inquiry()` + 幂等 + SLA 计算 | `backend/api/services/inquiry.py` |
| `portfolio_update_inquiry()` | `inquiry_service.update_inquiry_status()` + `transaction.atomic()` | 同上 |
| `portfolio_workday()` | `calendar_service.calculate_sla_deadline()` | `backend/api/services/calendar.py` |
| 作品发布触发器 | `portfolio_service.publish_project()` + `publish_validations` | `backend/api/services/portfolio.py` |
| `portfolio_create_play_session()` + `portfolio_record_progress()` | `playback_service.create_session()` / `report_progress()` | `backend/api/services/playback.py` |
| 行级安全策略 (RLS) | DRF Permission 类 + Manager 过滤 | `backend/api/permissions.py` + `backend/api/models.py` |
| 乐观锁版本控制 | `version` 字段 + `filter(version=expected).update(version=F('version')+1)` | Service 层 |
| 软删除 | `SoftDeleteManager` 默认过滤 + `all_objects` 全部可见 | `backend/api/models.py` |

## Git 历史

```
fc5834f Merge branch 'feature/frontend-public' into main
6a3bd95 feat: 完成 Vue 3 前端 SPA（前台 5 路由 + 后台登录 + 概览 Dashboard）
b78316e Merge branch 'feature/service-layer' into main
95da1c5 feat: 完成 Service 层 8 条业务规则 + DRF 全部 API 端点（Epic 3）
f25152f Merge branch 'feature/init-and-models' into main
f06ad19 feat: 完成 Django 后端骨架、13 张业务表与初始数据（Epic 1-2）
2d6558a docs: 完成架构设计与任务拆分
b24d235 docs: 完成产品简报
ced3f73 docs: 初始化仓库结构与规则文件
ecc1031 first commit
```

**硬约束满足**：
- ✅ 3 个 feature 分支 + merge commit 痕迹（AGENTS.md §2.1）
- ✅ 四阶段独立 commit（docs: 初始化 → docs: 产品简报 → docs: 架构设计 + 3 个 feat: 功能）
- ✅ Conventional commit 格式（feat / docs / merge）
- ✅ 无伪造历史（无 --amend、无 rebase、无倒填日期）
- ✅ BMAD 产物全部在 `_bmad-output/` 下

## 已知局限（本期范围外）

- 多角色审批体系（仅一名管理员，无多级审批）
- 付费观看 / 访客会员体系
- 跨设备实时推送（依赖手动刷新）
- 高并发压力测试（以功能正确性为主）
- 视频加密防盗链（开发阶段简化）
- 真实视频播放器接入（当前 Showreel 为占位 div）
- 前端作品编辑器、状态流转 UI、CSV 导出按钮、素材上传组件、统计看板 ECharts 图表、工作日历 UI（后端 API 已就绪，前端待接入）
- PostgreSQL 生产部署（开发阶段用 SQLite）
