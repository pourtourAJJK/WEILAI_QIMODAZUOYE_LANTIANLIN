# Build Report

## 后端

| 项目 | 值 |
|------|------|
| Django | 5.2.6 |
| 数据库 | SQLite (`backend/db.sqlite3`) |
| 启动 | `cd backend && python manage.py runserver 0.0.0.0:8000` |
| migrate | ✅ 全部 OK |
| system check | ✅ 0 errors |
| API 测试 | ✅ `/api/public/site/`, `/api/public/categories/`, `/api/public/projects/` 全部 200 |
| Fixtures | ✅ 分类 8 / 作品 5 / 站点 1 / 日历 14 条目 / 管理员 admin:admin1234 |

### API 端点清单

```
/auth/captcha/            GET    图片验证码（开发阶段答案明文）
/auth/login/              POST   管理员登录 → JWT
/auth/refresh/            POST   JWT 刷新

/public/site/             GET    站点内容快照
/public/categories/       GET    分类（?page_key=campus/commercial）
/public/projects/        GET    作品列表（?page_key=&category=&page_size=&offset=）
/public/projects/{slug}/  GET    作品详情

/submit/inquiry/          POST   合作咨询（幂等 + 邮箱限流）
/submit/contact/          POST   联系方式（幂等 + 联系方式限流）
/submit/visit/            POST   作品访问记录
/submit/playback/start/   POST   播放会话创建（去重）
/submit/playback/progress/ POST   播放进度上报（区间合并 + 节点到达 + 完播判定）

/admin/inquiries/         GET    合作咨询列表（?status=）
/admin/inquiries/export/csv/ GET CSV 导出（Content-Disposition attachment）
/admin/inquiries/{id}/     GET    咨询详情 + 状态历史
/admin/inquiries/{id}/status/ POST 状态更新（乐观锁 + 同一事务写历史）
/admin/inquiries/{id}/notes/ POST 备注更新（乐观锁）
/admin/contacts/          GET    联系方式列表
/admin/projects/          GET/POST 作品列表 + 创建
/admin/projects/{id}/     GET/PUT 作品详情 + 更新（乐观锁）
/admin/projects/{id}/publish/  POST 发布（封面/素材校验）
/admin/projects/{id}/unpublish/ POST 下架（软删除）
/admin/assets/            GET    素材列表
/admin/assets/upload/     POST   素材上传（multipart/form-data）
/admin/site/              GET/PUT 站点内容
/admin/calendar/          GET/POST 日历 + 启用新策略版本
/admin/stats/summary/     GET    概览统计
/admin/stats/playback/    GET    播放统计（PV/UV/节点率/完播率）
/admin/stats/trend/       GET    PV/UV 趋势（?days=7）
/admin/stats/rankings/    GET    作品排行榜（?limit=10）
```

---

## 前端

| 项目 | 值 |
|------|------|
| Vue | 3 + Vite 8 |
| Router | vue-router 4 |
| HTTP | axios 1 |
| 图表 | echarts 6（已安装，Epic 5 接入） |
| dev server | `cd frontend && npm run dev` → `http://localhost:5173` |
| build | `cd frontend && npm run build` → 233ms，无错误 |
| proxy | Vite dev server `/api` + `/media` → `http://localhost:8000` |

### Build 输出（节选）

```
✓ built in 233ms
dist/assets/index-n75VTtzU.css             2.78 kB │ gzip:  1.03 kB
dist/assets/index-YsuVlVxe.js            104.03 kB │ gzip: 40.28 kB
dist/assets/request-Dc9bNIk2.js           50.36 kB │ gzip: 18.88 kB
dist/assets/ContactView-aUkOqvie.js        6.15 kB │ gzip:  2.23 kB
dist/assets/AdminDashboard--T860gqm.js     3.38 kB │ gzip:  1.60 kB
dist/assets/WorkDetail-FULkQ-iy.js         2.73 kB │ gzip:  1.32 kB
dist/assets/LoginView-CeAXsZJa.js          2.05 kB │ gzip:  1.15 kB
dist/assets/WorkListView-CyqDkQBi.js       1.73 kB │ gzip:  0.96 kB
dist/assets/HomeView-BqPSGG9r.js           1.37 kB │ gzip:  0.84 kB
dist/assets/AboutView-CjEvSeT-.js          0.91 kB │ gzip:  0.60 kB
dist/assets/SpaceListView-K7ggF1WN.js      0.27 kB │ gzip:  0.24 kB
```

---

## 启动指南

```bash
# 终端 1：后端
cd backend
python manage.py migrate          # 数据库迁移
python manage.py loaddata api/fixtures/initial_data.json  # 初始数据（如果需要重新灌入）
python manage.py runserver 0.0.0.0:8000

# 终端 2：前端
cd frontend
npm run dev                        # http://localhost:5173

# 管理员账号
admin / admin1234
```
