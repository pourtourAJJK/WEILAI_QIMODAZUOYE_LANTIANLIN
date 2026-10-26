<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
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
const lockedUntil = ref(0)        // Unix 秒级时间戳；> 0 表示锁定中
const remainingSeconds = ref(0)   // 当前剩余秒数
let countdownTimer = null

async function loadCaptcha() {
  try {
    const { data } = await request.get('/auth/captcha/')
    captchaImg.value = data.image
    captchaText.value = data.hint.split('：').pop() || ''
  } catch (e) { console.error(e) }
}

function startCountdown() {
  // 每秒刷新 remainingSeconds
  stopCountdown()
  countdownTimer = setInterval(() => {
    const now = Math.floor(Date.now() / 1000)
    const left = Math.max(0, lockedUntil.value - now)
    remainingSeconds.value = left
    if (left <= 0) {
      stopCountdown()
      lockedUntil.value = 0
    }
  }, 1000)
}

function stopCountdown() {
  if (countdownTimer) {
    clearInterval(countdownTimer)
    countdownTimer = null
  }
}

onUnmounted(stopCountdown)

const isLocked = () => remainingSeconds.value > 0

function formatRemaining(secs) {
  const m = Math.floor(secs / 60)
  const s = secs % 60
  return `${m} 分 ${s} 秒`
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
    // 成功
    localStorage.setItem('access_token', data.access)
    localStorage.setItem('refresh_token', data.refresh)
    stopCountdown()
    const next = route.query.next || '/admin'
    router.push(next)
  } catch (e) {
    const body = e.response?.data || {}
    error.value = body.detail || '登录失败'

    if (body.locked && body.remaining_seconds > 0) {
      // 账号被锁定
      remainingSeconds.value = body.remaining_seconds
      lockedUntil.value = Math.floor(Date.now() / 1000) + body.remaining_seconds
      startCountdown()
    } else if (body.remaining_attempts !== undefined) {
      // 未锁定但还有几次机会
      error.value = `${body.detail}（还能尝试 ${body.remaining_attempts} 次）`
    }

    // 密码错了 → 刷新验证码
    loadCaptcha()
  }
  loading.value = false
}

onMounted(loadCaptcha)
</script>

<template>
  <div class="login-page">
    <div class="login-card">
      <h1>后台登录</h1>
      <p class="muted">影羽·YINGYU STUDIO —— 管理员入口</p>

      <!-- 锁定警告条 -->
      <div v-if="isLocked()" class="lock-banner">
        <strong>🔒 账号已锁定</strong>
        <span>请在 {{ formatRemaining(remainingSeconds) }} 后重试</span>
      </div>

      <div class="field">
        <label>用户名</label>
        <input v-model="username" placeholder="admin" :disabled="isLocked()" />
      </div>
      <div class="field">
        <label>密码</label>
        <input
          v-model="password"
          type="password"
          placeholder="admin1234"
          :disabled="isLocked()"
          @keyup.enter="login"
        />
      </div>
      <div class="field">
        <label>验证码</label>
        <div class="captcha-row">
          <input v-model="captchaText" placeholder="输入验证码" :disabled="isLocked()" @keyup.enter="login" />
          <img :src="captchaImg" class="captcha-img" :class="{ dim: isLocked() }" @click="loadCaptcha" title="点击刷新" />
        </div>
      </div>

      <p v-if="error" class="error-text">{{ error }}</p>
      <button
        @click="login"
        :disabled="loading || isLocked()"
        style="width: 100%"
      >
        <template v-if="loading">登录中…</template>
        <template v-else-if="isLocked()">锁定中 {{ formatRemaining(remainingSeconds) }}</template>
        <template v-else>登录</template>
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

/* 锁定警告 */
.lock-banner {
  background: #3a1a1a;
  border: 1px solid #e06a6a;
  border-radius: 8px;
  padding: 12px 16px;
  margin-bottom: 16px;
  color: #e06a6a;
  font-size: 14px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.lock-banner span { font-size: 13px; color: var(--text-muted); }

.field { margin-bottom: 16px; }
.field label { display: block; font-size: 13px; color: var(--text-muted); margin-bottom: 6px; }
.captcha-row { display: flex; gap: 10px; }
.captcha-row input { flex: 1; }
.captcha-img { height: 40px; border-radius: 6px; cursor: pointer; border: 1px solid var(--border); }
.captcha-img.dim { opacity: 0.4; cursor: not-allowed; }

button:disabled {
  opacity: 0.5;
  background: #3a1a1a;
  color: #e06a6a;
  cursor: not-allowed;
}

.hint { text-align: center; margin-top: 16px; font-size: 11px; }
</style>
