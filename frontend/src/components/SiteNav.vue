<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const isAdmin = computed(() => localStorage.getItem('access_token'))

const links = [
  { to: '/', label: '首页' },
  { to: '/work', label: '校内创作' },
  { to: '/space', label: '商业项目' },
  { to: '/contact', label: '联系我们' },
  { to: '/about', label: '关于' },
]

function logout() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  router.push('/login')
}
</script>

<template>
  <header class="nav">
    <div class="container nav-inner">
      <router-link to="/" class="brand">
        <strong>影羽</strong>
        <span class="brand-en">YINGYU STUDIO</span>
      </router-link>

      <nav class="nav-links">
        <router-link
          v-for="l in links"
          :key="l.to"
          :to="l.to"
          :class="{ active: route.path === l.to }"
        >{{ l.label }}</router-link>
        <template v-if="isAdmin">
          <router-link to="/admin" class="admin-link">后台</router-link>
          <button @click="logout" class="logout-btn">退出</button>
        </template>
        <router-link v-else to="/login" class="login-link">登录</router-link>
      </nav>
    </div>
  </header>
</template>

<style scoped>
.nav {
  position: sticky;
  top: 0;
  z-index: 100;
  background: rgba(15, 15, 17, 0.9);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--border);
}
.nav-inner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
}
.brand {
  display: flex;
  flex-direction: column;
  color: var(--text);
  text-decoration: none;
  line-height: 1.2;
}
.brand strong { font-size: 18px; color: var(--accent); }
.brand-en { font-size: 10px; letter-spacing: 2px; color: var(--text-muted); }

.nav-links { display: flex; gap: 24px; align-items: center; }
.nav-links a { color: var(--text-muted); font-size: 14px; }
.nav-links a.active, .nav-links a:hover { color: var(--text); }
.admin-link { color: var(--accent); }
.login-link { color: var(--accent); }
.logout-btn {
  padding: 6px 12px;
  font-size: 12px;
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text-muted);
}
.logout-btn:hover { border-color: var(--danger); color: var(--danger); }
</style>
