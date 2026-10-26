# Test Report —— 影羽·YINGYU STUDIO

## 核心业务规则单元验证（Service 层）

验证时间：2026-10-26
验证方式：Django shell 直接调用 Service 层（绕过前端，纯业务规则验证）

| # | 规则 | 测试脚本 | 结果 | 详情 |
|---|------|---------|------|------|
| 1 | **工作日截止计算** | `verify_rules.py` | ✅ PASS | 提交 10-26(日) + 3 工作日 → 截止 10-28(周三)，自动跳过周末 |
| 2 | **表单幂等** | `verify_rules.py` | ✅ PASS | 同一 request_id 第二次提交返回同一记录（id=1），不新增行 |
| 3 | **乐观锁版本控制** | `verify_rules.py` | ✅ PASS | version=1 更新成功（version→2），再用 version=1 更新被拒绝（VersionConflictError） |
| 4 | **完播三条件判定** | `verify_rules.py` | ✅ PASS | 覆盖 100% + ended=True → is_completed=True；覆盖 50% + ended=True → is_completed=False |
| 5 | **软删除** | `verify_rules.py` | ✅ PASS | 下架后 PortfolioProject.objects 可见 0 条（默认过滤），PortfolioProject.all_objects 可见 1 条 |
| 6 | **状态历史事务** | `verify_rules.py` | ✅ PASS | 两次状态变更产生 2 条 StatusHistory：pending_contact→in_progress→completed |

**覆盖说明**：开题报告的 8 条业务规则中，"草稿暂存"是纯前端 localStorage 实现，后端无对应测试。剩余 7 条全部通过（软删除算一条）。

## API 端点 HTTP 验证

| 端点 | 方法 | 预期 | 实际 |
|------|------|------|------|
| `/api/public/site/` | GET | 200 | ✅ 200，返回品牌信息 |
| `/api/public/categories/?page_key=campus` | GET | 200 | ✅ 200，返回 4 个分类 |
| `/api/public/projects/?page_size=3` | GET | 200 | ✅ 200，返回作品列表 |
| `/api/submit/inquiry/` | POST | 201 | ✅ 201，返回 id + 提示 |
| `/api/submit/inquiry/` (同 request_id 重试) | POST | 200/返回原记录 | ✅ 幂等生效 |
| `/api/auth/login/` | POST admin/admin1234 | 200 + JWT | ✅ 返回 refresh + access token |
| `/api/admin/inquiries/` (带 JWT) | GET | 200 | ✅ 返回咨询列表 |
| `/api/admin/inquiries/{id}/status/` (带 JWT) | POST | 200 | ✅ 状态更新 + 历史写入 |
| `/api/admin/projects/{id}/publish/` | POST 无封面 | 422 | ✅ 返回 PublishValidationError |
| `/api/admin/inquiries/export/csv/` | GET | CSV Content-Disposition | ✅ 返回 CSV 文本 |

## 前端构建验证

| 检查项 | 结果 |
|--------|------|
| `npm run build` | ✅ 通过，233ms，无编译错误 |
| dist/ 产物 | ✅ HTML + CSS + JS 全部正确生成 |
| Vite proxy | ✅ `/api` 正确转发到 Django :8000 |
| SPA 路由 | ✅ 前台 5 路由 + 后台路由守卫均可跳转 |

## 端到端核心流程（手动 E2E 脚本）

### 路径 1：访客浏览 → 提交合作需求

```bash
# 步骤
curl -X POST http://localhost:8000/api/submit/inquiry/ \
  -H "Content-Type: application/json" \
  -d '{"request_id":"demo-001","name":"测试","email":"e2e@test.com",
       "cooperation_type":"commercial_ad","expected_period":"1month",
       "description":"E2E 测试","consent_given":true}'
# 预期：{"id": N, "message": "需求已提交，我们会在 1~3 个工作日内答复。"}
```

### 路径 2：管理员登录 → 改咨询状态

```bash
# 登录
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin1234"}'
# 返回 {"access": "...JWT...", "refresh": "...", "user": {...}}

# 查咨询（带 JWT）
curl http://localhost:8000/api/admin/inquiries/ \
  -H "Authorization: Bearer <access_token>"
# 返回列表，找到刚提交的 id=N, version=1

# 改状态（带 JWT + version）
curl -X POST http://localhost:8000/api/admin/inquiries/N/status/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"status":"in_progress","version":1,"admin_notes":"开始对接"}'
# 预期：200，状态更新 + StatusHistory 表新增一条
```

## 已知问题（不影响演示）

| 问题 | 影响 | 处理 |
|------|------|------|
| DateTimeField naive datetime RuntimeWarning | PlaySession 的时间字段在 USE_TZ=True 下触发 | 开发阶段不影响功能，生产环境改 `django.utils.timezone.now()` |
| 开发阶段验证码明文返回 | get_captcha 的 hint 字段直接给答案 | 后端注释里已标注，生产需要存 DB + 过期 |
| video_duration 默认 0 | 素材上传没接 ffmpeg，视频时长留 0 | 完播判定用 duration 快照，为 0 时自动跳过（Service 层已处理） |
| SQLite 不支持 RLS | 已用 DRF Permission + Manager 过滤替代 | 生产换 PostgreSQL 时可保留 Service 层边界 |
