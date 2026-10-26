<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import request from '../api/request'

const router = useRouter()
const route = useRoute()

const username = ref('admin')
const password = ref('admin1234')
const captchaText = ref('')
const captchaImg = ref('')
const loading = ref(false)
const error = ref('')

async function loadCaptcha() {
  try {
    const { data } = await request.get('/auth/captcha/')
    captchaImg.value = data.image
    // 开发阶段 captcha 答案直接返回（见后端 get_captcha hint）
    captchaText.value = data.hint.split('：').pop() || ''
  } catch (e) { console.error(e) }
}

async function login() {
  error.value = ''
  loading.value = true
  try {
    const { data } = await request.post('/auth/login/', {
      username: username.value,
      password: password.value,
      captcha_text: captchaText.value,
    })
    localStorage.setItem('access_token', data.access)
    localStorage.setItem('refresh_token', data.refresh)
    const next = route.query.next || '/admin'
    router.push(next)
  } catch (e) {
    error.value = e.response?.data?.detail || '登录失败'
  }
  loading.value = false
}

import { onMounted } from 'vue'
onMounted(loadCaptcha)
</script>

<template>
  <div class="login-page">
    <div class="login-card">
      <h1>后台登录</h1>
      <p class="muted">影羽·YINGYU STUDIO —— 管理员入口</p>

      <div class="field">
        <label>用户名</label>
        <input v-model="username" placeholder="admin" />
      </div>
      <div class="field">
        <label>密码</label>
        <input v-model="password" type="password" placeholder="admin1234" @keyup.enter="login" />
      </div>
      <div class="field">
        <label>验证码</label>
        <div class="captcha-row">
          <input v-model="captchaText" placeholder="输入验证码" @keyup.enter="login" />
          <img :src="captchaImg" class="captcha-img" @click="loadCaptcha" title="点击刷新" />
        </div>
      </div>

      <p v-if="error" class="error-text">{{ error }}</p>
      <button @click="login" :disabled="loading" style="width: 100%">
        {{ loading ? '登录中…' : '登录' }}
      </button>

      <p class="muted hint">开发阶段：admin / admin1234（验证码见图片下方）</p>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 60vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
}
.login-card {
  width: 100%;
  max-width: 380px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 32px;
}
.login-card h1 { font-size: 22px; margin-bottom: 4px; color: var(--accent); }
.login-card .muted { margin-bottom: 24px; font-size: 13px; }

.field { margin-bottom: 16px; }
.field label { display: block; font-size: 13px; color: var(--text-muted); margin-bottom: 6px; }
.captcha-row { display: flex; gap: 10px; }
.captcha-row input { flex: 1; }
.captcha-img { height: 40px; border-radius: 6px; cursor: pointer; border: 1px solid var(--border); }
.hint { text-align: center; margin-top: 16px; font-size: 11px; }
</style>
