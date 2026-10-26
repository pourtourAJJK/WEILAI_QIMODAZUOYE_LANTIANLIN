<script setup>
import { ref, onMounted } from 'vue'
import { getSite } from '../api/public'

const site = ref(null)

onMounted(async () => {
  try {
    const { data } = await getSite()
    site.value = data
  } catch (e) { console.error(e) }
})
</script>

<template>
  <section class="hero">
    <div class="container">
      <h1 class="hero-title">{{ site?.home_title || '影羽·YINGYU STUDIO' }}</h1>
      <p class="hero-desc muted">{{ site?.home_description || '个人摄影作品集' }}</p>

      <!-- Showreel（演示用：用占位视频或 poster） -->
      <div class="showreel-wrap">
        <div class="showreel-placeholder">
          <span class="play-icon">▶</span>
          <p>33 秒个人 Showreel —— 服装走秀 / 商业广告 / 纪录片</p>
          <p class="muted">开发阶段暂用占位，生产环境接入真实视频素材</p>
        </div>
      </div>

      <!-- 快速入口 -->
      <div class="quick-links">
        <router-link to="/work" class="q-link">
          <h3>校内创作</h3>
          <span>查看作品 →</span>
        </router-link>
        <router-link to="/space" class="q-link">
          <h3>商业项目</h3>
          <span>查看作品 →</span>
        </router-link>
        <router-link to="/contact" class="q-link accent">
          <h3>合作咨询</h3>
          <span>联系我们 →</span>
        </router-link>
      </div>
    </div>
  </section>
</template>

<style scoped>
.hero { padding: 40px 0 60px; }
.hero-title {
  font-size: 42px;
  font-weight: 700;
  margin-bottom: 10px;
  background: linear-gradient(135deg, var(--accent), #f5e0b3);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}
.hero-desc { font-size: 16px; margin-bottom: 30px; }

.showreel-wrap {
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid var(--border);
  margin-bottom: 40px;
}
.showreel-placeholder {
  aspect-ratio: 16 / 9;
  background: linear-gradient(135deg, #1a1a20, #252530);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 12px;
  color: var(--text);
}
.play-icon {
  font-size: 48px;
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: rgba(232, 192, 125, 0.2);
  color: var(--accent);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.quick-links {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}
.q-link {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 28px 24px;
  color: var(--text);
  transition: border-color 0.2s, transform 0.2s;
}
.q-link:hover {
  border-color: var(--accent);
  transform: translateY(-2px);
  text-decoration: none;
}
.q-link h3 { font-size: 18px; margin-bottom: 16px; color: var(--accent); }
.q-link span { color: var(--text-muted); font-size: 13px; }
.q-link.accent { background: linear-gradient(135deg, #2a2210, #1f1a10); }
</style>
