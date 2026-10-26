<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getCategories, listProjects } from '../api/public'

const props = defineProps({
  pageKey: { type: String, required: true },  // "campus" | "commercial"
  pageTitle: { type: String, required: true },
})

const route = useRoute()
const router = useRouter()
const categories = ref([])
const projects = ref([])
const selectedCat = ref(route.query.category || '')

async function load() {
  try {
    const cats = await getCategories(props.pageKey)
    categories.value = cats.data
    const res = await listProjects({
      pageKey: props.pageKey,
      category: selectedCat.value,
      page_size: 20,
    })
    projects.value = res.data.results || []
  } catch (e) { console.error(e) }
}

function selectCat(slug) {
  selectedCat.value = selectedCat.value === slug ? '' : slug
  router.replace({ query: { category: selectedCat.value } })
  load()
}

onMounted(load)
</script>

<template>
  <section class="list-page">
    <div class="container">
      <h1 class="page-title">{{ pageTitle }}</h1>

      <!-- 分类筛选 -->
      <div class="filters">
        <button
          class="filter-btn"
          :class="{ active: !selectedCat }"
          @click="selectCat('')"
        >全部</button>
        <button
          v-for="c in categories"
          :key="c.slug"
          class="filter-btn"
          :class="{ active: selectedCat === c.slug }"
          @click="selectCat(c.slug)"
        >{{ c.name }}</button>
      </div>

      <!-- 瀑布流作品网格 -->
      <div v-if="projects.length" class="waterfall">
        <div
          v-for="p in projects"
          :key="p.id"
          class="card"
          :class="p.card_layout"
          @click="router.push(`/works/${p.slug}`)"
        >
          <div class="card-cover">
            <img
              v-if="p.cover?.object_key"
              :src="`/media/${p.cover.object_key}`"
              :alt="p.title"
              loading="lazy"
            />
            <div v-else class="cover-fallback"></div>
            <div class="card-overlay">
              <h3>{{ p.title }}</h3>
              <span class="card-type">{{ p.category?.name }}</span>
            </div>
          </div>
        </div>
      </div>
      <div v-else class="empty-state">暂无已发布作品</div>
    </div>
  </section>
</template>

<style scoped>
.list-page { padding: 40px 0 80px; }
.page-title { font-size: 28px; margin-bottom: 24px; color: var(--text); }

.filters {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 32px;
}
.filter-btn {
  background: transparent;
  color: var(--text-muted);
  border: 1px solid var(--border);
  padding: 8px 16px;
  font-size: 13px;
  border-radius: 20px;
}
.filter-btn.active {
  background: var(--accent);
  color: var(--bg);
  border-color: var(--accent);
}

.waterfall {
  column-count: 3;
  column-gap: 16px;
}
.card {
  break-inside: avoid;
  margin-bottom: 16px;
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid var(--border);
  cursor: pointer;
  transition: border-color 0.2s;
  position: relative;
}
.card:hover { border-color: var(--accent); }
.card.hero { aspect-ratio: 16 / 9; }
.card.banner { aspect-ratio: 16 / 10; }
.card.portrait { aspect-ratio: 3 / 4; }

.card-cover {
  width: 100%;
  height: 100%;
  position: relative;
}
.card-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.cover-fallback {
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #252530, #1a1a20);
}
.card-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(to top, rgba(0,0,0,0.85) 0%, transparent 60%);
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  padding: 16px;
}
.card-overlay h3 { font-size: 15px; margin-bottom: 4px; color: var(--text); }
.card-type { font-size: 12px; color: var(--accent); }

@media (max-width: 1024px) { .waterfall { column-count: 2; } }
@media (max-width: 640px) {
  .waterfall { column-count: 1; }
  .page-title { font-size: 22px; }
}
</style>
