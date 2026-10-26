<script setup>
import { ref, onMounted } from 'vue'
import request from '../api/request'
import { useRouter } from 'vue-router'

const router = useRouter()
const stats = ref(null)
const inquiries = ref([])
const loading = ref(true)

async function load() {
  loading.value = true
  try {
    const [summary, inquiriesRes] = await Promise.all([
      request.get('/admin/stats/summary/'),
      request.get('/admin/inquiries/'),
    ])
    stats.value = summary.data
    inquiries.value = inquiriesRes.data
  } catch (e) {
    if (e.response?.status === 403 || e.response?.status === 401) {
      alert('需要管理员权限，请重新登录')
      router.push('/login')
    }
  }
  loading.value = false
}

function logout() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  router.push('/login')
}

onMounted(load)
</script>

<template>
  <section class="admin">
    <div class="container">
      <header class="admin-header">
        <h1>管理后台</h1>
        <button class="logout-btn" @click="logout">退出登录</button>
      </header>

      <!-- 概览统计 -->
      <div v-if="stats" class="stats-grid">
        <div class="stat-card">
          <span class="label">作品总数</span>
          <strong>{{ stats.projects?.total || 0 }}</strong>
          <span class="sub muted">已发布 {{ stats.projects?.published || 0 }}</span>
        </div>
        <div class="stat-card">
          <span class="label">合作咨询</span>
          <strong>{{ stats.inquiries?.total || 0 }}</strong>
          <span class="sub muted">待联系 {{ (stats.inquiries?.by_status || {}).pending_contact || 0 }}</span>
        </div>
        <div class="stat-card">
          <span class="label">联系方式</span>
          <strong>{{ stats.contacts?.total || 0 }}</strong>
        </div>
        <div class="stat-card">
          <span class="label">有效播放会话</span>
          <strong>{{ stats.playback?.total_sessions || 0 }}</strong>
          <span class="sub muted">完播率 {{ stats.playback?.completion_rate || 0 }}%</span>
        </div>
      </div>

      <!-- 快速入口 -->
      <div class="quick-actions">
        <router-link to="/admin/projects" class="action-card">
          <h3>作品管理</h3><span>新增 / 编辑 / 发布 →</span>
        </router-link>
        <router-link to="/admin/inquiries" class="action-card">
          <h3>客户需求</h3><span>状态流转 / CSV 导出 →</span>
        </router-link>
        <router-link to="/admin/stats" class="action-card">
          <h3>观看统计</h3><span>PV·UV 趋势 / 排行榜 →</span>
        </router-link>
        <router-link to="/admin/calendar" class="action-card">
          <h3>工作日历</h3><span>设置工作日 / 休息日 →</span>
        </router-link>
      </div>

      <!-- 最近咨询 -->
      <h2 class="section-title">最近合作咨询</h2>
      <table class="inquiry-table">
        <thead>
          <tr><th>姓名</th><th>邮箱</th><th>类型</th><th>状态</th><th>截止时间</th><th>提交时间</th></tr>
        </thead>
        <tbody>
          <tr v-for="inq in inquiries.slice(0, 8)" :key="inq.id">
            <td>{{ inq.name }}</td>
            <td>{{ inq.email }}</td>
            <td>{{ inq.cooperation_type }}</td>
            <td><span :class="['status-badge', inq.status]">{{ inq.status }}</span></td>
            <td class="muted">{{ inq.sla_deadline_at?.slice(0, 16) }}</td>
            <td class="muted">{{ inq.created_at?.slice(0, 16) }}</td>
          </tr>
          <tr v-if="!inquiries.length && !loading">
            <td colspan="6" class="empty">暂无咨询记录</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<style scoped>
.admin { padding: 30px 0 80px; }
.admin-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }
.admin-header h1 { font-size: 24px; color: var(--accent); }
.logout-btn { background: transparent; border: 1px solid var(--danger); color: var(--danger); }

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 32px;
}
@media (max-width: 800px) { .stats-grid { grid-template-columns: repeat(2, 1fr); } }
.stat-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.stat-card .label { font-size: 12px; color: var(--text-muted); }
.stat-card strong { font-size: 28px; color: var(--accent); }
.stat-card .sub { font-size: 12px; }

.quick-actions {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 40px;
}
@media (max-width: 800px) { .quick-actions { grid-template-columns: repeat(2, 1fr); } }
.action-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 20px;
  color: var(--text);
}
.action-card:hover { border-color: var(--accent); text-decoration: none; }
.action-card h3 { font-size: 15px; margin-bottom: 8px; color: var(--accent); }
.action-card span { font-size: 12px; color: var(--text-muted); }

.section-title { font-size: 18px; margin-bottom: 16px; }

.inquiry-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.inquiry-table th, .inquiry-table td {
  text-align: left;
  padding: 10px 12px;
  border-bottom: 1px solid var(--border);
}
.inquiry-table th { color: var(--text-muted); font-weight: 500; }
.status-badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 11px;
}
.status-badge.pending_contact { background: #3a2a10; color: var(--accent); }
.status-badge.in_progress { background: #1a3a2a; color: var(--success); }
.status-badge.completed { background: #202028; color: var(--text-muted); }
.status-badge.cancelled { background: #3a1a1a; color: var(--danger); }
.empty { text-align: center; color: var(--text-muted); padding: 30px; }
</style>
