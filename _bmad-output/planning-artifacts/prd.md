---
title: "影羽·YINGYU STUDIO 需求规格（PRD）"
status: draft
created: 2026-10-26
updated: 2026-10-26
source: "开题报告 V1C1（肖信羽 2435102090646）+ Django 架构适配"
---

# PRD：影羽·YINGYU STUDIO

## 1. 概述

### 1.1 项目背景

摄影与视频创作者的作品集长期分散在短视频平台、社交媒体和网盘中，传统文字简历无法充分展示视觉类岗位的实际能力。本项目"影羽·YINGYU STUDIO"旨在将个人介绍、代表作品、项目经历和商业合作入口整合在同一网站中，形成从作品展示到合作洽谈的完整浏览路径。

### 1.2 设计理念

- **可视化个人简历 + 可视化商业展示** —— 作品优先于文字
- **前台简洁浏览，后台集中管理** —— 两端共用同一数据链路和业务规则
- **展示内容与管理规则分离** —— 页面负责呈现，后端负责校验，规则下沉

### 1.3 范围

**本期纳入**：前台展示端（5 路由）+ 后台管理端（6 模块）+ 核心业务规则（幂等、乐观锁、工作日截止、完播判定、软删除、状态历史、草稿暂存）。

**本期不纳入**：多角色审批、付费观看、访客会员、跨设备实时推送、高并发压力测试、正式域名绑定、视频加密。

---

## 2. 功能需求

### 2.1 前台展示端（面向访客，无需登录）

| 路由 | 功能 | 关键交互 |
|------|------|---------|
| `/` | 首页品牌展示 | 品牌名称 + 导航 + 33 秒 Showreel 视频（自动加载，播放结束后可自然向下滚动）；Showreel 下方个人介绍模块 |
| `/work` | 校内创作作品目录 | 两级分类（大类：校内创作）→ 具体方向筛选（网页设计、AIGC、学院宣传、微电影等）；瀑布流错落布局，三种卡片比例（横幅叙事/竖幅展映/全宽主视觉） |
| `/space` | 商业项目作品目录 | 同上，大类为商业项目（商业广告、服装走秀、纪录片、自媒体等） |
| `/works/:id` | 作品详情弹窗 | 封面轮播（左右箭头切换多封面）+ 视频/图片素材 + 项目档案（标签-值对：项目名称/类型/时间/本人职责）+ 项目介绍 + 制作心得；视频作品显示"播放作品"按钮；上下作品切换 + 返回列表 |
| `/contact` | 联系我们 | 两个独立表单：合作需求（姓名/邮箱/合作类型/期望周期/需求描述/授权勾选）+ 联系方式（姓名 + 邮箱/电话/微信至少一项 + 首选联系方式 + 留言） |
| `/about` | 关于 / 商业空间 | 品牌介绍 + 公开联系方式 + 社交链接 + 空间页内容 |

**非功能要求**：响应式（手机/平板/桌面三档）、表单校验、前台只读已发布作品、视频播放统计采集。

### 2.2 后台管理端（面向管理员，需登录）

| 模块 | 功能 | 关键规则 |
|------|------|---------|
| 登录 | 管理员身份认证 | Django Auth 自建登录表单 + 图片验证码；未绑定管理员身份的登录用户无法读取客户数据或写入业务表 |
| 概览 | 统计摘要 | 作品总数/已发布/草稿、客户咨询数/状态分布、作品访问趋势、视频播放统计摘要 |
| 作品管理 | CRUD + 素材关联 | 新增/编辑作品（标识/标题/分类/类型/卡片布局/封面/额外封面/视频/素材库/项目档案/内容段落）；乐观锁版本校验；发布时校验封面存在 + 素材状态就绪 + 视频时长 > 0；软删除（前台隐藏，后台保留）；本地草稿暂存 |
| 客户需求 | 咨询/联系方式管理 | 状态筛选（待联系/处理中/已完成/已取消）；状态流转 + 状态历史（同一事务）；时效截止时间显示；CSV 数据导出（浏览器端生成） |
| 站点内容 | 品牌配置 | 品牌名称/英文名称/首页标题描述/关于文案/Showreel 素材/公开联系方式/社交链接/空间页内容/答复时效策略 |
| 工作日历 | 日历配置 | 日期设置为工作日或休息日；保存并启用新策略版本；已用旧策略计算的需求保留原截止时间 |
| 统计看板 | 观看数据 | PV/UV 双折线图（时间范围 + 作品筛选 + 日/周/月粒度）；节点到达率（10%/25%/50%/75%/95%/尾部）；完播率；作品排行榜（播放量 → 完播率 → 作品标识稳定排序） |

---

## 3. 数据模型（13 张业务表）

按开题报告的数据模型迁移到 Django，使用 Django ORM 定义。分组如下：

### 3.1 作品域（4 张）

| 表（Django Model） | 关键字段 |
|------|---------|
| `PortfolioProject` | id, slug, title, category(FK), content_type, card_layout, summary, background, notes, credits(JSONB), content_blocks(JSONB), cover_image(FK→MediaAsset), extra_covers(M2M→MediaAsset), video_asset(FK→MediaAsset), gallery(M2M→MediaAsset), is_published, version(IntegerField, optimistic lock), created_at, updated_at, deleted_at(soft delete) |
| `PortfolioCategory` | id, slug, name_en, page_key(campus/commercial), sort_order, is_enabled, is_fixed |
| `MediaAsset` | id, asset_type(image/video), storage_bucket, object_key, mime_type, file_size, width, height, duration_seconds, asset_status(pending/ready/failed/archived), uploaded_at |
| `ProjectAssetRelation` | id, project(FK), asset(FK), role(cover/extra_cover/video/gallery), caption, asset_source(real/concept/placeholder), sort_order |

### 3.2 客户需求域（3 张）

| 表 | 关键字段 |
|------|---------|
| `Inquiry` | id, request_id(unique, idempotency), name, email, cooperation_type, expected_period, description, consent_given, status(pending_contact/in_progress/completed/cancelled), admin_notes, sla_started_at, sla_deadline_at, version, created_at, updated_at |
| `Contact` | id, request_id(unique), name, email, phone, wechat, company, preferred_channel, message, consent_given, status, admin_notes, version, created_at, updated_at |
| `StatusHistory` | id, inquiry(FK, nullable), contact(FK, nullable), old_status, new_status, notes, operated_by(FK→User), operated_at |

### 3.3 统计与日历域（4 张）

| 表 | 关键字段 |
|------|---------|
| `ProjectVisit` | id, project(FK), visit_id(unique together with project), visitor_identity, user(FK→User, nullable), identity_key, visited_at |
| `PlaySession` | id, project(FK), session_id(unique together with project), video_asset(FK), video_duration, visitor_identity, session_token_hash, started_at, last_event_at, node_reached_at(JSONB, 每个节点的到达时间), completed_at |
| `ExportRecord` | id, admin(FK→User), export_type, filter_snapshot(JSONB), file_path, created_at |
| `BusinessCalendar` | id, strategy_version, date, is_workday, notes |

### 3.4 站点与权限域（2 张）

| 表 | 关键字段 |
|------|---------|
| `SiteContent` | id, brand_name, brand_name_en, home_title, home_description, about_text, home_showreel(FK→MediaAsset), contact_email, contact_phone, social_links(JSONB), space_page_content, sla_days, version |
| `AdminBinding` | id, user(FK→User, OneToOne) |

---

## 4. 核心业务规则（必须从开题报告迁移）

### 4.1 表单幂等 + 频率限制

- 合作咨询和联系方式提交均使用前端生成的 `request_id` 实现幂等
- 相同 request_id 重试 → 返回原有记录；相同 request_id 但内容不同 → 拒绝写入
- 合作咨询：邮箱级 60 秒 1 次、24 小时 10 次；全局 1 分钟 20 次、24 小时 1000 次
- 联系方式：同一联系方式 60 秒 1 次；全局同上

**Django 迁移方案**：
- 幂等：Service 层先 `filter(request_id=...).first()`，存在则返回，不存在才创建
- 限流：DRF Throttling 类（自定义 `InquiryThrottle` 和 `ContactThrottle`，结合 `ScopedRateThrottle` 实现邮箱级 + 全局两级限流）

### 4.2 乐观锁版本控制

- 作品保存和客户状态更新时，前端携带读取到的 `version` 值
- 后端在更新时 `filter(id=...).filter(version=前端值)` 才执行，更新成功后 `version += 1`
- 版本不一致 → 拒绝覆盖，返回错误提示"请刷新后重试"

**Django 迁移方案**：
- 在 Model 的 `save()` 或 Service 层实现，使用 `update(version=F('version')+1, ...)` + `filter(version=expected_version)`；返回受影响行数，若为 0 则抛出 `VersionConflict` 异常

### 4.3 作品发布校验

- 发布状态的作品必须有封面（已登记图片素材或兼容旧数据的本地路径）
- 额外封面最多 4 张且不能与主封面重复
- 视频作品引用的视频素材必须处于 `ready` 状态且 `duration_seconds > 0`

**Django 迁移方案**：
- 在 `PortfolioProject.clean()` 或 Service 层的 `publish()` 方法中校验；校验失败抛出 `ValidationError`

### 4.4 工作日截止时间计算

- 合作咨询提交时，从提交时间开始，跳过 `BusinessCalendar` 中标记为休息日的日期，数满 `sla_days` 个工作日得到截止时间
- 已使用旧策略计算的需求保留原截止时间；修改日历后新增策略版本，不改变历史

**Django 迁移方案**：
- Service 层 `calculate_sla_deadline(submitted_at, strategy_version)` 方法；查询该版本下的日历条目，逐个日期判断

### 4.5 视频播放统计

- **会话创建**：访客点击播放 → 创建 `PlaySession`；同一作品 + 同一会话 ID 去重（网络重试不放大播放量）
- **进度上报**：播放器约 15 秒或累计 80 个区间时提交；暂停/拖动/结束/离开页面时立即发送；拖动产生的跳跃区间不计为观看内容
- **节点到达**：自然播放跨过节点时记录，同一会话每个节点最多一次
- **完播判定**：结束事件为真 **AND** 观看覆盖 ≥ 视频时长 98% **AND** 自然播放到达尾部附近
- **PV/UV 计算**：播放 PV = 有效播放会话数；节点到达率 = 命中该节点的会话数 / 有效会话数；完播率 = 完播会话数 / 有效会话数；UV = 选定范围内 `identity_key` 去重

**Django 迁移方案**：
- Service 层 `create_session()` 先查重再创建；`report_progress()` 合并自然播放区间、校验 token、去重节点；`calculate_completion()` 在结束事件触发时检查三个条件；统计查询用 ORM `annotate` + `Count` + `Distinct`

### 4.6 客户状态历史

- 合作咨询与联系方式共用 `StatusHistory` 表，通过可空外键区分来源（两者只能有一个非空）
- 状态变更与历史写入在**同一事务**中完成
- 主记录更新失败 → 历史不写入

**Django 迁移方案**：
- Service 层用 `transaction.atomic()` 包裹主记录更新 + `StatusHistory.create()`；任何一步异常则整体回滚

### 4.7 软删除

- 作品下架：设置 `deleted_at = now()` + `is_published = False`
- 前台公开查询自动过滤 `deleted_at IS NULL AND is_published = True`
- 后台保留数据和历史统计

**Django 迁移方案**：
- 自定义 Manager：`objects.filter(deleted_at__isnull=True)` 默认过滤；`all_objects` 访问全部
- 前台只读公开快照的 Service 方法自动加过滤条件

### 4.8 草稿暂存

- 作品编辑器关闭时若有改动 → 提示"是否保存为草稿" → 写入浏览器 localStorage
- 下次打开同一作品 → 自动回填草稿并提示"已恢复上次未完成的草稿"
- 作品保存成功 → 清除对应草稿

**Django 迁移方案**：
- 纯前端 localStorage 实现，后端不需要任何改动
- 草稿仅在本地，不经过后端校验

---

## 5. 非功能需求

| 类别 | 要求 |
|------|------|
| 响应式 | 前台/后台均适配手机（<768px）、平板（768-1024px）、桌面（>1024px） |
| 表单校验 | 必填项、邮箱格式、字段长度、允许值（合作类型、期望周期、状态） |
| 安全边界 | 客户数据、私密素材仅管理员可读取；公开素材短时签名或直接读取（开发阶段简化） |
| 统计口径一致 | 空数据时显示"暂无数据"而非示例数值；UV 为去重身份数，不宣称准确自然人数 |
| 视觉简洁 | 前台作品优先，后台清晰表格 + 状态标识 + 编辑面板 |
| 异常反馈 | 保存失败、版本冲突、网络中断、空数据均有明确提示 |

---

## 6. 数据库权限（Django 迁移方案）

开题报告原方案：所有业务表启用 RLS + RPC 函数写入。

**Django 迁移方案**：
- 不再依赖 PostgreSQL RLS（SQLite 不支持，PostgreSQL 虽支持但 Django Auth 体系可覆盖）
- 公开读取：前台匿名访问只读 `is_published=True AND deleted_at IS NULL` 的 `PortfolioProject` 和 `PortfolioCategory`
- 提交接口：合作咨询和联系方式提交走公开 API，但校验 `request_id` 幂等 + 限流
- 管理接口：所有写操作和私密读取（客户数据、统计看板、素材管理）需管理员身份 → DRF `IsAuthenticated` + 自定义 `IsAdminUser`（检查 `AdminBinding` 表）
- Django 模型本身不提供行级安全，通过 Service 层过滤 + DRF Permission 类实现同等边界
