<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getProject } from '../api/public'

const route = useRoute()
const router = useRouter()
const project = ref(null)
const loading = ref(true)
const activeCover = ref(0)

async function load() {
  loading.value = true
  try {
    const { data } = await getProject(route.params.slug)
    project.value = data
    activeCover.value = 0
  } catch (e) {
    if (e.response?.status === 404) {
      alert('作品不存在')
      router.push('/work')
    }
  }
  loading.value = false
}

function prevCover() {
  const covers = project.value?.extra_covers?.length || 0
  if (covers) activeCover.value = (activeCover.value - 1 + covers) % covers
}
function nextCover() {
  const covers = project.value?.extra_covers?.length || 0
  if (covers) activeCover.value = (activeCover.value + 1) % covers
}

onMounted(load)
watch(() => route.params.slug, load)
</script>

<template>
  <section class="detail-page">
    <div class="container" v-if="!loading && project">
      <button class="back-btn" @click="router.back()">← 返回作品列表</button>

      <div class="detail-grid">
        <!-- 左侧：视觉内容 -->
        <div class="media">
          <!-- 封面 / 额外封面轮播 -->
          <div class="carousel" v-if="project.extra_covers?.length">
            <img
              v-if="project.cover?.object_key"
              :src="`/media/${project.cover.object_key}`"
              alt="主封面"
              :class="{ active: activeCover === 0 }"
            />
            <img
              v-for="(c, i) in project.extra_covers"
              :key="c.id"
              v-show="activeCover === i + 1"
              :src="`/media/${c.object_key}`"
              alt=""
            />
            <button class="carousel-nav left" @click="prevCover">‹</button>
            <button class="carousel-nav right" @click="nextCover">›</button>
          </div>
          <div v-else class="single-cover">
            <img
              v-if="project.cover?.object_key"
              :src="`/media/${project.cover.object_key}`"
              alt="主封面"
            />
            <div v-else class="cover-fallback"></div>
          </div>

          <!-- 视频播放（占位） -->
          <div v-if="project.video" class="video-player">
            <div class="player-placeholder">
              <span class="play-big">▶</span>
              <p>真实视频播放器 + 进度上报（开发阶段暂用占位）</p>
            </div>
          </div>
        </div>

        <!-- 右侧：项目信息 -->
        <div class="info">
          <h1 class="title">{{ project.title }}</h1>
          <p class="category-tag">{{ project.category?.name }}</p>

          <!-- 项目档案（标签-值对） -->
          <div v-if="project.credits?.length" class="credits">
            <div v-for="(c, i) in project.credits" :key="i" class="credit-row">
              <span class="credit-label">{{ c.label }}</span>
              <span class="credit-value">{{ c.value }}</span>
            </div>
          </div>

          <div v-if="project.background" class="section">
            <h3>项目介绍</h3>
            <p>{{ project.background }}</p>
          </div>

          <div v-if="project.notes" class="section">
            <h3>制作心得</h3>
            <p>{{ project.notes }}</p>
          </div>
        </div>
      </div>
    </div>
    <div v-if="loading" class="empty-state">加载中…</div>
  </section>
</template>

<style scoped>
.detail-page { padding: 30px 0 60px; }
.back-btn {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text-muted);
  margin-bottom: 24px;
}
.back-btn:hover { color: var(--text); }

.detail-grid {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 40px;
}
@media (max-width: 900px) {
  .detail-grid { grid-template-columns: 1fr; }
}

.carousel {
  position: relative;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid var(--border);
}
.carousel img { width: 100%; aspect-ratio: 16/10; object-fit: cover; display: block; }
.carousel-nav {
  position: absolute;
  top: 50%; transform: translateY(-50%);
  background: rgba(0,0,0,0.6);
  border: none; color: white;
  width: 40px; height: 40px;
  border-radius: 50%;
  font-size: 24px;
  cursor: pointer;
}
.carousel-nav.left { left: 12px; }
.carousel-nav.right { right: 12px; }

.single-cover { border-radius: 12px; overflow: hidden; border: 1px solid var(--border); }
.single-cover img { width: 100%; aspect-ratio: 16/10; object-fit: cover; }
.cover-fallback { aspect-ratio: 16/10; background: linear-gradient(135deg, #252530, #1a1a20); }

.video-player {
  margin-top: 16px;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid var(--border);
}
.player-placeholder {
  aspect-ratio: 16 / 9;
  background: #1a1a20;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
}
.play-big { font-size: 48px; color: var(--accent); }

.title { font-size: 32px; margin-bottom: 8px; }
.category-tag { color: var(--accent); font-size: 14px; margin-bottom: 24px; }

.credits {
  background: var(--surface);
  border-radius: 10px;
  padding: 16px 20px;
  margin-bottom: 24px;
}
.credit-row {
  display: flex;
  padding: 8px 0;
  border-bottom: 1px dashed var(--border);
}
.credit-row:last-child { border-bottom: none; }
.credit-label { width: 100px; color: var(--text-muted); font-size: 13px; }
.credit-value { flex: 1; color: var(--text); font-size: 14px; }

.section { margin-bottom: 24px; }
.section h3 { font-size: 16px; color: var(--accent); margin-bottom: 10px; }
.section p { color: var(--text-muted); font-size: 14px; line-height: 1.8; }
</style>
