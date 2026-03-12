<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Heart, Microscope, Activity, Stethoscope, ArrowRight } from 'lucide-vue-next'
import api from '../api'

const router = useRouter()
const departments = ref([])
const loading = ref(true)

const iconMap = {
  general: Stethoscope,
  cardiology: Heart,
  endocrinology: Activity,
  dermatology: Microscope,
}

const colorMap = {
  general:       { bg: '#EFF6FF', color: '#2563EB', border: '#BFDBFE' },
  cardiology:    { bg: '#FFF1F2', color: '#E11D48', border: '#FECDD3' },
  endocrinology: { bg: '#F0FDF4', color: '#16A34A', border: '#BBF7D0' },
  dermatology:   { bg: '#FFF7ED', color: '#EA580C', border: '#FED7AA' },
}

onMounted(async () => {
  try {
    const res = await api.getDepartments()
    if (res.success) departments.value = res.data
  } catch (e) {
    console.error('Failed to load departments:', e)
  } finally {
    loading.value = false
  }
})

const selectDepartment = (dept) => {
  router.push({ name: 'Consultation', query: { department: dept.id } })
}
</script>

<template>
  <div class="dept-page">
    <div class="dept-container">
      <div class="dept-header">
        <h2 class="dept-title">选择门诊科室</h2>
        <p class="dept-subtitle">请根据您的健康需求选择对应科室，AI 将为您提供专项智能问诊服务</p>
      </div>

      <div v-if="loading" class="dept-loading">
        <div class="loading-spin"></div>
      </div>

      <div v-else class="dept-grid">
        <button
          v-for="dept in departments"
          :key="dept.id"
          class="dept-card"
          :style="{
            '--dept-bg': colorMap[dept.id]?.bg || '#F8FAFC',
            '--dept-color': colorMap[dept.id]?.color || '#475569',
            '--dept-border': colorMap[dept.id]?.border || '#E2E8F0',
          }"
          @click="selectDepartment(dept)"
        >
          <div class="dept-card-icon">
            <component :is="iconMap[dept.id] || Stethoscope" :size="28" />
          </div>
          <div class="dept-card-body">
            <div class="dept-card-top">
              <span class="dept-name">{{ dept.icon }} {{ dept.name }}</span>
              <ArrowRight :size="16" class="dept-arrow" />
            </div>
            <p class="dept-desc">{{ dept.desc }}</p>
          </div>
        </button>
      </div>

      <p class="dept-note">
        所有门诊均由 AI 提供辅助分析，建议仅供参考，不构成医疗诊断
      </p>
    </div>
  </div>
</template>

<style scoped>
.dept-page {
  min-height: 100%;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: 48px 24px;
}

.dept-container {
  width: 100%;
  max-width: 720px;
}

.dept-header {
  text-align: center;
  margin-bottom: 36px;
}

.dept-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--color-text-primary);
  margin: 0 0 8px;
}

.dept-subtitle {
  font-size: 14px;
  color: var(--color-text-secondary);
  margin: 0;
}

.dept-loading {
  display: flex;
  justify-content: center;
  padding: 60px 0;
}

.loading-spin {
  width: 28px;
  height: 28px;
  border: 3px solid var(--color-border);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.dept-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.dept-card {
  background: var(--dept-bg);
  border: 1.5px solid var(--dept-border);
  border-radius: 14px;
  padding: 20px;
  display: flex;
  align-items: flex-start;
  gap: 16px;
  cursor: pointer;
  text-align: left;
  transition: transform 0.15s, box-shadow 0.15s;
}

.dept-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.08);
}

.dept-card:active {
  transform: translateY(0);
}

.dept-card-icon {
  width: 52px;
  height: 52px;
  border-radius: 12px;
  background: white;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--dept-color);
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.dept-card-body {
  flex: 1;
  min-width: 0;
}

.dept-card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}

.dept-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.dept-arrow {
  color: var(--dept-color);
  flex-shrink: 0;
}

.dept-desc {
  font-size: 13px;
  color: var(--color-text-secondary);
  margin: 0;
  line-height: 1.5;
}

.dept-note {
  text-align: center;
  font-size: 12px;
  color: var(--color-text-tertiary);
  margin-top: 28px;
}

@media (max-width: 560px) {
  .dept-grid {
    grid-template-columns: 1fr;
  }
}
</style>
