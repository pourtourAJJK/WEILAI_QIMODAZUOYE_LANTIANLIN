# Iteration 3 —— Vue 3 前端（前台 5 路由 + 后台登录 + 概览）

**日期**：2026-10-26
**分支**：`feature/frontend-public`
**对应 Epic**：Epic 4（全部前台）+ Epic 5 部分（后台登录 + 概览）

---

## 改动说明

完成了 Vue 3 + Vite 前端 SPA 的完整实现：

### 核心依赖
- Vue 3 + Vue Router 4 + Axios + ECharts
- Vite 8（dev server proxy `/api` → Django :8000）

### API 封装（`src/api/`）
- `request.js`：Axios 实例 + JWT Authorization interceptor + 401 自动跳转登录
- `public.js`：getSite / getCategories / listProjects / getProject
- `submit.js`：submitInquiry / submitContact / recordVisit / createPlaySession / reportPlaybackProgress + generateRequestId

### 前台 5 路由（全部可运行）
| 路由 | 视图 | 状态 |
|------|------|------|
| `/` | HomeView.vue | ✅ 品牌 + Showreel 占位 + 快速入口 |
| `/work` | WorkListView.vue | ✅ 校内创作列表（瀑布流 + 分类筛选） |
| `/space` | SpaceListView.vue | ✅ 商业项目列表（复用 WorkList，page_key=commercial） |
| `/works/:slug` | WorkDetail.vue | ✅ 作品详情（封面轮播 + 视频占位 + 项目档案 + 介绍 + 心得） |
| `/contact` | ContactView.vue | ✅ 合作需求表单 + 联系方式表单（幂等 + 授权勾选） |
| `/about` | AboutView.vue | ✅ 品牌介绍 + 联系方式 |

### 后台入口
- `/login` —— LoginView.vue：管理员登录 + 图片验证码（开发阶段答案直接返回）
- `/admin` —— AdminDashboard.vue：概览统计（作品数/咨询数/播放会话）+ 最近咨询列表 + 快速入口

### 组件 + 样式
- SiteNav / SiteFooter / App.vue + 全局 style.css（深色主题，`--accent: #e8c07d`）
- 瀑布流 grid：CSS columns，三种卡片比例（hero 16:9 / banner 16:10 / portrait 3:4）

---

## 技术决策

| 决策 | 原因 |
|------|------|
| **Vite 默认模板 → 纯 JS** | 删除 `tsconfig.json` + 把 `build` 命令从 `tsc && vite build` 改为 `vite build`；开题报告明确说"未将 TypeScript 作为主要语言" |
| **Showreel / 视频播放器用占位** | 真实视频播放器（HTML5 Video + 播放区间采集 + 进度上报）在 Epic 5 的素材上传就绪后再接入；当前组件结构为 `<div class="showreel-placeholder">` 和 `<div class="player-placeholder">`，替换成 `<video>` 即可 |
| **瀑布流用 CSS columns 而非 JS 库** | 开题报告要求"前台按移动端/平板/桌面调整布局"；CSS columns 零依赖、自动响应、断点只需 `@media (max-width: ...) { column-count: N }` |
| **ECharts 已安装但暂未接入** | Dashboard 里的图表（PV/UV 趋势、节点到达率、完播率、排行榜条形图）在 Epic 5 统计看板里统一接入 |
| **验证码开发阶段答案直接返回** | get_captcha 的 `hint` 字段直接返回答案，生产环境需要改成存 DB + 过期；当前已在 `# 简单实现：直接把答案放 session` 注释里标注 |

---

## 构建 / 验证结果

| 检查项 | 结果 |
|--------|------|
| `npm run build` | ✅ 通过，233ms 完成，无编译错误 |
| 后端 `GET /api/public/projects/` | ✅ 200，返回已发布作品 |
| 前端 proxy | ✅ `/api` 请求正确转发到 Django :8000 |
| Git branch | ✅ feature/frontend-public |

---

## 已知局限

1. **后台 CRUD 还没实现** —— AdminDashboard 只有概览 + 快速入口；作品管理、客户需求状态流转、CSV 导出、站点编辑、工作日历、统计趋势图、排行榜还没写（Epic 5 主体）
2. **真实视频播放器 + 进度上报** —— 当前是占位 div，Epic 5 接入 HTML5 Video + 事件监听 + 区间合并 + 后端 API 调用
3. **ECharts 图表未接入** —— 统计看板还没写，Epic 5 统一实现
4. **图片上传未实现** —— Admin API `admin_asset_upload` 已就绪，但前端没有上传组件（Epic 5 作品编辑器里实现）
5. **开发阶段验证码答案明文** —— get_captcha endpoint 返回 `hint: "忽略此提示：ABCD"`，生产环境需移除
