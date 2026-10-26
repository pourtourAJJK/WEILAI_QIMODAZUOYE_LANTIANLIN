<script setup>
import { ref } from 'vue'
import { submitInquiry, submitContact, generateRequestId } from '../api/submit'

// ── 合作需求表单 ──
const inquiry = ref({
  request_id: generateRequestId(),
  name: '',
  email: '',
  cooperation_type: 'commercial_ad',
  expected_period: 'flexible',
  description: '',
  consent_given: false,
})
const inquiryMsg = ref('')
const inquiryError = ref('')
const inquiryLoading = ref(false)

async function submitInq() {
  inquiryError.value = ''; inquiryMsg.value = ''
  if (!inquiry.value.consent_given) { inquiryError.value = '请勾选联系授权'; return }
  inquiryLoading.value = true
  try {
    const { data } = await submitInquiry(inquiry.value)
    inquiryMsg.value = data.message
    inquiry.value = { ...inquiry.value, request_id: generateRequestId(), name: '', email: '', description: '' }
  } catch (e) {
    inquiryError.value = e.response?.data?.detail || '提交失败，请稍后再试'
  }
  inquiryLoading.value = false
}

// ── 联系方式表单 ──
const contact = ref({
  request_id: generateRequestId(),
  name: '',
  email: '',
  phone: '',
  wechat: '',
  company: '',
  preferred_channel: 'email',
  message: '',
  consent_given: false,
})
const contactMsg = ref('')
const contactError = ref('')
const contactLoading = ref(false)

async function submitCtc() {
  contactError.value = ''; contactMsg.value = ''
  if (!contact.value.consent_given) { contactError.value = '请勾选联系授权'; return }
  if (!contact.value.email && !contact.value.phone && !contact.value.wechat) {
    contactError.value = '邮箱、电话、微信至少填写一项'; return
  }
  contactLoading.value = true
  try {
    const { data } = await submitContact(contact.value)
    contactMsg.value = data.message
    contact.value = { ...contact.value, request_id: generateRequestId(), name: '', message: '' }
  } catch (e) {
    contactError.value = e.response?.data?.detail || '提交失败'
  }
  contactLoading.value = false
}
</script>

<template>
  <section class="contact-page">
    <div class="container">
      <h1>联系我们</h1>
      <p class="muted">留下你的合作需求或联系方式，我们会在工作日内答复。</p>

      <div class="form-grid">
        <!-- 合作需求 -->
        <div class="form-card">
          <h3>合作需求</h3>
          <div class="field">
            <label>姓名 *</label>
            <input v-model="inquiry.name" placeholder="你的名字" />
          </div>
          <div class="field">
            <label>邮箱 *</label>
            <input v-model="inquiry.email" type="email" placeholder="用于接收答复" />
          </div>
          <div class="row">
            <div class="field">
              <label>合作类型 *</label>
              <select v-model="inquiry.cooperation_type">
                <option value="commercial_ad">商业广告</option>
                <option value="fashion_show">服装走秀</option>
                <option value="documentary">纪录片</option>
                <option value="self_media">自媒体</option>
                <option value="space_rental">空间预约</option>
                <option value="other">其他</option>
              </select>
            </div>
            <div class="field">
              <label>期望周期</label>
              <select v-model="inquiry.expected_period">
                <option value="1month">1 个月内</option>
                <option value="3months">3 个月内</option>
                <option value="6months">半年内</option>
                <option value="1year">1 年内</option>
                <option value="flexible">时间灵活</option>
              </select>
            </div>
          </div>
          <div class="field">
            <label>需求描述</label>
            <textarea v-model="inquiry.description" placeholder="简要描述你的项目需求、风格偏好、时间节点等…"></textarea>
          </div>
          <div class="consent">
            <label><input type="checkbox" v-model="inquiry.consent_given" /> 我同意以上信息用于合作沟通</label>
          </div>
          <p v-if="inquiryMsg" class="success-text">{{ inquiryMsg }}</p>
          <p v-if="inquiryError" class="error-text">{{ inquiryError }}</p>
          <button @click="submitInq" :disabled="inquiryLoading">
            {{ inquiryLoading ? '提交中…' : '提交需求' }}
          </button>
        </div>

        <!-- 联系方式 -->
        <div class="form-card">
          <h3>留下联系方式</h3>
          <div class="field">
            <label>姓名 *</label>
            <input v-model="contact.name" placeholder="你的名字" />
          </div>
          <div class="row">
            <div class="field">
              <label>邮箱</label>
              <input v-model="contact.email" type="email" placeholder="hello@example.com" />
            </div>
            <div class="field">
              <label>电话</label>
              <input v-model="contact.phone" placeholder="138-xxxx-xxxx" />
            </div>
          </div>
          <div class="field">
            <label>微信</label>
            <input v-model="contact.wechat" placeholder="wechat_id" />
          </div>
          <div class="field">
            <label>公司 / 品牌</label>
            <input v-model="contact.company" placeholder="（可选）" />
          </div>
          <div class="field">
            <label>首选联系方式</label>
            <select v-model="contact.preferred_channel">
              <option value="email">邮箱</option>
              <option value="phone">电话</option>
              <option value="wechat">微信</option>
            </select>
          </div>
          <div class="field">
            <label>留言</label>
            <textarea v-model="contact.message" placeholder="简单说一下你好…"></textarea>
          </div>
          <div class="consent">
            <label><input type="checkbox" v-model="contact.consent_given" /> 我同意以上信息用于联系</label>
          </div>
          <p v-if="contactMsg" class="success-text">{{ contactMsg }}</p>
          <p v-if="contactError" class="error-text">{{ contactError }}</p>
          <button @click="submitCtc" :disabled="contactLoading">
            {{ contactLoading ? '提交中…' : '提交联系方式' }}
          </button>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.contact-page { padding: 40px 0 80px; }
.contact-page h1 { font-size: 28px; margin-bottom: 6px; }
.contact-page .muted { margin-bottom: 32px; }

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}
@media (max-width: 800px) { .form-grid { grid-template-columns: 1fr; } }

.form-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 28px;
}
.form-card h3 { font-size: 18px; margin-bottom: 20px; color: var(--accent); }

.field { margin-bottom: 16px; }
.field label {
  display: block;
  font-size: 13px;
  color: var(--text-muted);
  margin-bottom: 6px;
}
.row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.consent { margin-bottom: 12px; font-size: 13px; color: var(--text-muted); }
button { width: 100%; margin-top: 8px; }
</style>
