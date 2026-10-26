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
  <section class="about-page">
    <div class="container">
      <h1>关于 {{ site?.brand_name_en || 'YINGYU STUDIO' }}</h1>
      <p class="brand-cn">{{ site?.brand_name }}</p>
      <p class="intro">{{ site?.about_text || '个人摄影作品集网站。' }}</p>

      <div class="contact-box">
        <h3>联系方式</h3>
        <p><strong>邮箱：</strong>{{ site?.contact_email }}</p>
        <p v-if="site?.contact_phone"><strong>电话：</strong>{{ site.contact_phone }}</p>
      </div>
    </div>
  </section>
</template>

<style scoped>
.about-page { padding: 60px 0; }
.about-page h1 { font-size: 32px; margin-bottom: 6px; }
.brand-cn { color: var(--accent); margin-bottom: 30px; }
.intro { max-width: 600px; font-size: 16px; color: var(--text-muted); margin-bottom: 40px; line-height: 1.8; }

.contact-box {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 24px 28px;
}
.contact-box h3 { font-size: 16px; margin-bottom: 14px; color: var(--accent); }
.contact-box p { font-size: 14px; margin-bottom: 6px; }
</style>
