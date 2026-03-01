<script setup>
import { computed, ref, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Bell, Search, Settings, FileText, Activity, ClipboardList, LayoutDashboard, HeartPulse, ShieldCheck, User } from 'lucide-vue-next'
import api from '@/api'

const route = useRoute()
const router = useRouter()

const pageTitle = computed(() => route.meta.title || 'HealthAI')

// ==================== 搜索 ====================
const searchQuery = ref('')
const showResults = ref(false)
const searchBoxRef = ref(null)

// 静态页面导航条目
const NAV_ITEMS = [
  { type: 'nav', title: '首页', subtitle: '健康总览', path: '/', icon: 'LayoutDashboard' },
  { type: 'nav', title: '智能问诊', subtitle: 'AI 健康助手对话', path: '/consultation', icon: 'HeartPulse' },
  { type: 'nav', title: '健康数据', subtitle: '指标趋势与图表', path: '/health-data', icon: 'Activity' },
  { type: 'nav', title: '风险评估', subtitle: '心血管/糖尿病风险分析', path: '/risk-assessment', icon: 'ShieldCheck' },
  { type: 'nav', title: '健康档案', subtitle: '个人健康信息', path: '/profile', icon: 'User' },
  { type: 'nav', title: '体检报告', subtitle: '上传与查看体检报告', path: '/exam-report', icon: 'ClipboardList' },
]

const healthReports = ref([])
const examReports = ref([])

onMounted(async () => {
  try {
    const [rRes, eRes] = await Promise.all([
      api.get('/user/reports'),
      api.get('/exam/reports?limit=20'),
    ])
    healthReports.value = (rRes.data.reports || []).map(r => ({
      type: 'report',
      title: r.title || r.report_type,
      subtitle: r.created_at?.slice(0, 10) || '',
      path: r.link_to || '/profile',
      icon: 'FileText',
    }))
    examReports.value = (eRes.data.reports || []).map(r => ({
      type: 'exam',
      title: r.filename || '体检报告',
      subtitle: r.report_date || r.uploaded_at?.slice(0, 10) || '',
      path: `/exam-report?id=${r.id}`,
      icon: 'ClipboardList',
    }))
  } catch {}
})

const allItems = computed(() => [
  ...NAV_ITEMS,
  ...healthReports.value,
  ...examReports.value,
])

const searchResults = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return []
  return allItems.value
    .filter(item =>
      item.title.toLowerCase().includes(q) ||
      item.subtitle.toLowerCase().includes(q)
    )
    .slice(0, 8)
})

const groupedResults = computed(() => {
  const groups = {}
  const labelMap = { nav: '页面导航', report: '健康报告', exam: '体检报告' }
  for (const item of searchResults.value) {
    if (!groups[item.type]) groups[item.type] = { label: labelMap[item.type], items: [] }
    groups[item.type].items.push(item)
  }
  return Object.values(groups)
})

function onFocus() {
  if (searchQuery.value.trim()) showResults.value = true
}

function onInput() {
  showResults.value = searchQuery.value.trim().length > 0
}

function selectItem(item) {
  router.push(item.path)
  searchQuery.value = ''
  showResults.value = false
}

function handleClickOutside(e) {
  if (searchBoxRef.value && !searchBoxRef.value.contains(e.target)) {
    showResults.value = false
  }
}

onMounted(() => document.addEventListener('mousedown', handleClickOutside))
onBeforeUnmount(() => document.removeEventListener('mousedown', handleClickOutside))

const iconMap = { FileText, Activity, ClipboardList, LayoutDashboard, HeartPulse, ShieldCheck, User }
</script>

<template>
  <header class="header">
    <div class="header-left">
      <h1 class="page-title">{{ pageTitle }}</h1>
    </div>

    <div class="header-center">
      <div class="search-box" ref="searchBoxRef">
        <Search :size="18" class="search-icon" />
        <input
          type="text"
          class="search-input"
          placeholder="搜索页面、报告、指标..."
          v-model="searchQuery"
          @focus="onFocus"
          @input="onInput"
          autocomplete="off"
        />
        <!-- 搜索结果下拉 -->
        <div v-if="showResults && searchResults.length > 0" class="search-dropdown">
          <template v-for="group in groupedResults" :key="group.label">
            <div class="search-group-label">{{ group.label }}</div>
            <button
              v-for="item in group.items"
              :key="item.path + item.title"
              class="search-result-item"
              @mousedown.prevent="selectItem(item)"
            >
              <component :is="iconMap[item.icon]" :size="15" class="result-icon" />
              <div class="result-text">
                <span class="result-title">{{ item.title }}</span>
                <span class="result-subtitle">{{ item.subtitle }}</span>
              </div>
            </button>
          </template>
        </div>
        <div v-else-if="showResults && searchQuery.trim() && searchResults.length === 0" class="search-dropdown search-empty">
          未找到与「{{ searchQuery }}」相关的内容
        </div>
      </div>
    </div>

    <div class="header-right">
      <button class="btn btn-icon">
        <Bell :size="20" />
      </button>
      <button class="btn btn-icon">
        <Settings :size="20" />
      </button>
      <div class="user-avatar">
        <img src="https://api.dicebear.com/7.x/avataaars/svg?seed=health" alt="用户头像" />
      </div>
    </div>
  </header>
</template>

<style scoped>
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-md) var(--spacing-lg);
  background-color: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
  position: sticky;
  top: 0;
  z-index: 50;
}

.header-left {
  flex: 1;
}

.page-title {
  font-size: var(--font-size-xl);
  font-weight: 600;
}

.header-center {
  flex: 2;
  max-width: 480px;
  margin: 0 var(--spacing-lg);
}

.search-box {
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 16px;
  color: var(--color-text-tertiary);
}

.search-input {
  width: 100%;
  padding: 10px 16px 10px 44px;
  font-size: var(--font-size-sm);
  background-color: var(--color-bg);
  border: none;
  border-radius: var(--radius-full);
  outline: none;
  transition: all var(--transition-fast);
}

.search-input:focus {
  background-color: var(--color-surface);
  box-shadow: 0 0 0 2px var(--color-primary);
}

.search-input::placeholder {
  color: var(--color-text-tertiary);
}

.header-right {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: var(--spacing-sm);
}

.user-avatar {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-full);
  overflow: hidden;
  margin-left: var(--spacing-sm);
  cursor: pointer;
}

.user-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* ==================== 搜索下拉 ==================== */
.search-dropdown {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  right: 0;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  z-index: 200;
  overflow: hidden;
  padding: 6px 0;
}

.search-group-label {
  padding: 6px 16px 4px;
  font-size: 11px;
  font-weight: 600;
  color: var(--color-text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.search-result-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 8px 16px;
  background: none;
  border: none;
  cursor: pointer;
  text-align: left;
  transition: background var(--transition-fast);
}

.search-result-item:hover {
  background: var(--color-bg);
}

.result-icon {
  color: var(--color-primary);
  flex-shrink: 0;
}

.result-text {
  display: flex;
  flex-direction: column;
  gap: 1px;
  min-width: 0;
}

.result-title {
  font-size: var(--font-size-sm);
  font-weight: 500;
  color: var(--color-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.result-subtitle {
  font-size: 12px;
  color: var(--color-text-tertiary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.search-empty {
  padding: 14px 16px;
  font-size: var(--font-size-sm);
  color: var(--color-text-tertiary);
  text-align: center;
}
</style>
