---
title: "影羽·YINGYU STUDIO Epics & Stories"
status: draft
created: 2026-10-26
updated: 2026-10-26
---

# Epics & Stories

按开发依赖顺序排列。每个 Epic 内的 Story 按先后顺序实现，前一个 Story 的产出是后一个的依赖。

---

## Epic 1：项目初始化与基础架构

**目标**：Django 后端骨架可 runserver，Vue 前端骨架可 npm run dev，两端通过 Vite proxy 联通 `/api`。

| Story | 描述 | 交付物 | 验收标准 |
|-------|------|--------|---------|
| 1.1 | Django 项目骨架初始化 | `backend/manage.py`, `backend/portfolio/`（settings/urls/wsgi/asgi）, `backend/api/`（apps/models/views/urls） | `python manage.py runserver` 返回 200 |
| 1.2 | DRF + CORS + JWT 配置 | `settings.py` INSTALLED_APPS、REST_FRAMEWORK、CORS_ALLOWED_ORIGINS 配置 | 前端 `axios` 调用 `/api/public/` 返回 JSON |
| 1.3 | Vue 3 + Vite 骨架 | `frontend/package.json`, `vite.config.js`（含 proxy `/api` → `:8000`）, `src/main.js`, `src/App.vue`, `src/router/index.js` | `npm run dev` 在 localhost:5173 可访问 |
| 1.4 | Axios 封装 + 路由守卫 | `src/api/request.js`, `src/router/index.js` 路由定义（前台 5 + 后台 6） | 前台路由可切换，后台路由未登录跳转登录页 |

---

## Epic 2：数据模型 + 迁移 + Fixtures

**目标**：13 张业务表全部定义，迁移通过，有测试数据可跑通前台展示。

| Story | 描述 | 交付物 | 验收标准 |
|-------|------|--------|---------|
| 2.1 | 作品域 4 张表模型 | `models.py` PortfolioProject, PortfolioCategory, MediaAsset, ProjectAssetRelation + 自定义 Manager（软删除） | `makemigrations` 生成迁移文件 |
| 2.2 | 客户域 3 张表模型 | Inquiry, Contact, StatusHistory | 同上 |
| 2.3 | 统计日历域 4 张表模型 | ProjectVisit, PlaySession, ExportRecord, BusinessCalendar | 同上 |
| 2.4 | 站点权限域 2 张表模型 | SiteContent, AdminBinding | 同上 |
| 2.5 | 执行迁移 + 创建管理员 | `migrate` 成功；`createsuperuser` 创建管理员账号 | 数据库中 13 张表 + Django Auth 表均存在 |
| 2.6 | 测试数据 Fixture | 分类（校内 4 个方向 + 商业 4 个方向）、作品（5 条已发布，含封面素材）、站点内容（品牌/介绍/联系方式）、工作日历（当前月 2 周） | `loaddata` 成功；前台可看到作品列表 |

---

## Epic 3：核心业务规则 Service 层

**目标**：开题报告的 8 条核心业务规则（见 PRD §4）全部在 Service 层实现并可单元测试。

| Story | 描述 | 交付物 | 验收标准 |
|-------|------|--------|---------|
| 3.1 | 乐观锁版本控制 | `services/portfolio.py` save_project() + 版本检查 + VersionConflict 异常 | 两次并发保存，第二次返回冲突错误 |
| 3.2 | 表单幂等 + 限流 | `services/inquiry.py` submit() 先查重；`throttling.py` InquiryThrottle / ContactThrottle | 相同 request_id 重试不新增记录；超限时返回 429 |
| 3.3 | 作品发布校验 | `services/portfolio.py` publish() 校验封面/素材状态/视频时长 | 无封面作品发布失败；未就绪素材关联发布失败 |
| 3.4 | 工作日截止计算 | `services/calendar.py` calculate_sla_deadline() | 给定提交时间 + 策略版本，跳过休息日得出截止时间 |
| 3.5 | 状态历史事务 | `services/inquiry.py` update_status() 用 `transaction.atomic()` | 主记录更新失败时历史不写入 |
| 3.6 | 播放会话 + 去重 | `services/playback.py` create_session() 同作品+同会话查重 | 网络重试不新增播放 PV |
| 3.7 | 进度合并 + 完播判定 | `services/playback.py` report_progress() 自然区间合并 + 完播三条件检查 | 拖动区间不计观看；结束+覆盖≥98%+尾部到达才算完播 |
| 3.8 | 软删除 Manager | `managers.py` Default manager 过滤 deleted_at，all_objects 全部可见 | 前台查询不含下架作品；后台 all_objects 可查 |

---

## Epic 4：公开 API + 前台展示端

**目标**：前台 5 路由全部跑通，有真实瀑布流布局、视频播放、表单提交。

| Story | 描述 | 交付物 | 验收标准 |
|-------|------|--------|---------|
| 4.1 | 公开 API Endpoints | `views.py` PublicAPIViewSet：site snapshot + categories + projects list/detail | curl 调用返回正确 JSON |
| 4.2 | 提交 API Endpoints | SubmitAPIViewSet：inquiry submit + contact submit + visit record + playback start/progress + captcha | curl 提交咨询返回 success |
| 4.3 | 首页 + Showreel | `HomeView.vue`：品牌 + 导航 + Showreel Video 组件 + 个人介绍 | 打开首页自动加载 Showreel，可播放 |
| 4.4 | 作品目录 + 分类筛选 | `WorkListView.vue` + `SpaceListView.vue`：两级分类切换 + 瀑布流组件（三种卡片比例） | 切换大类 → 具体方向筛选 → 滚动浏览 |
| 4.5 | 作品详情弹窗 | `WorkDetail.vue`：封面轮播 + 视频播放组件 + 项目档案 + 上下切换 + 返回 | 点卡片 → 打开详情；视频可播放；上/下一个切换 |
| 4.6 | 视频播放统计采集 | `VideoPlayer.vue`：事件监听 + 自然播放区间 + 15s 上报 + 拖动跳过 | 真实播放后后台 PlaySession 有记录 |
| 4.7 | 合作需求 + 联系方式表单 | `ContactView.vue`：两个独立表单 + 校验 + request_id 生成 + 成功提示 | 填写提交 → 显示"需求已提交，我们会在 1~3 个工作日内答复。" |
| 4.8 | 关于 + 商业空间页 | `AboutView.vue` | 品牌介绍 + 联系方式展示 |
| 4.9 | 响应式适配 | 所有前台组件 CSS 媒体查询 | 手机 / 平板 / 桌面三档均可操作 |

---

## Epic 5：管理员 API + 后台管理端

**目标**：后台 6 模块全部跑通，管理员登录后可进行完整 CRUD + 状态流转 + CSV 导出。

| Story | 描述 | 交付物 | 验收标准 |
|-------|------|--------|---------|
| 5.1 | 管理员 Permission + JWT + 验证码 | `permissions.py` IsAdminUser；`views.py` AuthAPIView 登录 + captcha | 登录 → 返回 JWT；非管理员访问 /api/admin/* 返回 403 |
| 5.2 | 管理员 API Endpoints | AdminAPIViewSet：projects CRUD + categories + assets upload + inquiries + contacts + site + calendar + stats | curl 用 JWT 可调用 |
| 5.3 | 登录页 | `LoginView.vue`：用户名 + 密码 + 图片验证码 + 登录按钮 | 管理员账号登录 → 跳转到概览 |
| 5.4 | 概览统计 | `DashboardView.vue`：作品数/咨询数/趋势摘要 | 页面加载显示统计数字 |
| 5.5 | 作品管理 + 编辑器 | `PortfolioEdit.vue`：作品 CRUD + 素材上传 + 项目档案编辑 + 发布/下架 + 乐观锁冲突提示 + 本地草稿暂存 | 编辑作品 → 保存 → 前台可见；下架 → 前台隐藏 |
| 5.6 | 客户需求管理 + 状态流转 | `InquiryListView.vue`：咨询列表 + 状态筛选 + 详情弹窗 + 状态变更 + 状态历史显示 | 改状态 → 历史记录自动写入；状态历史事务可验证 |
| 5.7 | CSV 导出 | `services/export.py` + 前端导出按钮 | 点击导出 → 浏览器下载 CSV → Excel/WPS 可打开 |
| 5.8 | 站点内容编辑 | `SiteEdit.vue` | 修改品牌名 → 前台刷新可见 |
| 5.9 | 工作日历 + SLA | `CalendarView.vue`：日期点击编辑工作日/休息日 + 启用新策略 | 设置休息日 → 新提交需求的截止时间跳过该日 |
| 5.10 | 统计看板 + PV/UV 趋势图 | `StatsView.vue`：ECharts 双折线图 + 时间范围筛选 + 节点到达率 + 完播率 | 真实播放数据可在看板上看到 |
| 5.11 | 作品排行榜 | 排行榜区域（先播放量后完播率排序） | 有真实播放数据时排行榜有内容 |

---

## Epic 6：构建验证 + 核心流程 E2E

**目标**：前后端 build 通过，核心演示流程可端到端跑通，核心业务规则各有单元测试。

| Story | 描述 | 交付物 | 验收标准 |
|-------|------|--------|---------|
| 6.1 | 后端单元测试 | `tests/`：幂等测试、乐观锁冲突测试、工作日截止测试、完播判定测试 | `pytest` 或 `python manage.py test` 全部 PASS |
| 6.2 | 前端 build 验证 | `npm run build` | 无编译错误，输出 dist/ 目录 |
| 6.3 | 核心流程手动 E2E | ① 打开前台 → 浏览作品 → 提交合作需求（request_id 幂等验证）② 管理员登录 → 作品编辑发布 → 前台可见 → 视频播放 → 后台统计看到 ③ 状态流转 → 历史写入 → CSV 导出打开正常 | 三条链路各自跑通并有截图记录 |
| 6.4 | 响应式 E2E | 手机尺寸查看前台导航、作品卡片、表单是否可操作；后台表格是否可读 | 三个断点（768px / 1024px）各截图验证 |

---

## Epic 7：文档 + 最终交付

**目标**：README 写清楚启动方法，BMAD 四阶段产物齐全，Git 历史完整。

| Story | 描述 | 交付物 | 验收标准 |
|-------|------|--------|---------|
| 7.1 | BMAD 迭代记录 | `_bmad-output/implementation-artifacts/iteration-1.md`（后端骨架 + 数据模型完成） + `iteration-2.md`（前台 + 后台完成） | 每次迭代独立文件，内容含改动说明 + 技术决策 + 验证结果 |
| 7.2 | Build 报告 | `build-report.md` | 后端 `manage.py runserver` 启动日志 + 前端 `npm run build` 输出 |
| 7.3 | Test 报告 | `test-report.md` | 单元测试通过情况 + E2E 截图记录 |
| 7.4 | README | 项目介绍 + 技术栈 + 启动步骤（后端端口、前端端口、proxy 配置）+ 目录结构 + 核心演示流程指引 | 新人按 README 能在 10 分钟内跑通 |
| 7.5 | 最终 commit | `test: 核心流程 E2E 验证通过` 或类似信息 | Git log 完整显示四阶段 + feature 分支合并痕迹 |

---

## 分支策略

| Epic | 分支名 | 合并到 main |
|------|--------|------------|
| Epic 1-2（基础设施） | `feature/init-and-models` | ✅ |
| Epic 3（业务规则） | `feature/service-layer` | ✅ |
| Epic 4（前台） | `feature/frontend-public` | ✅ |
| Epic 5（后台） | `feature/admin-dashboard` | ✅ |
| Epic 6-7（验证 + 文档） | `feature/test-and-docs` | ✅ |

每个 Epic 完成后 merge 回 main，产生 merge commit 痕迹。**Git log 必须能看到形如 `Merge branch 'feature/xxx' into main` 的记录**（AGENTS.md §2.1 硬约束）。

---

## 演示路径（核心流程）

> 这是课程大作业评分的核心——至少一条完整核心流程能当场演示。

**演示脚本**（≤ 3 分钟）：

1. **启动后端**（如果需要）：`cd backend && python manage.py runserver`
2. **启动前端**（如果需要）：`cd frontend && npm run dev`
3. **打开前台** `http://localhost:5173`
4. 首页 Showreel 自动播放 → 向下滚动看到瀑布流作品网格 → 点一张作品卡片 → 详情弹窗 + 视频播放 → 关闭
5. 点"联系我们" → 填写合作需求表单 → 提交 → 看到"需求已提交，我们会在 1~3 个工作日内答复。"
6. （切换到后台）管理员登录 → 客户需求列表看到刚才提交的记录 → 打开详情 → 改状态为"处理中" → 保存 → 状态历史自动写入
7. 打开统计看板 → 看到刚才的播放 PV 有记录（如果视频播放过）

**技术亮点演示**（时间允许时）：
- 乐观锁：两个窗口同时编辑同一作品，后保存的那个会看到"请刷新后重试"
- 幂等：合作需求提交后，按 F5 刷新（用同一 request_id），后台只有一条记录
- 工作日截止：提交咨询后，后台看到的截止时间自动跳过周末
