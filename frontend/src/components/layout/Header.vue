<script setup>
import { computed, ref, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Bell, Search, Settings, FileText, Activity, ClipboardList, LayoutDashboard, HeartPulse, ShieldCheck, User, AlertTriangle, CheckCircle, TrendingUp } from 'lucide-vue-next'
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
      api.getUserReports(),
      api.getExamReports(20),
    ])
    healthReports.value = (rRes.data || []).map(r => ({
      type: 'report',
      title: r.title || r.report_type,
      subtitle: r.created_at?.slice(0, 10) || '',
      path: r.link_to || '/profile',
      icon: 'FileText',
    }))
    examReports.value = (eRes.data || []).map(r => ({
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

const iconMap = { FileText, Activity, ClipboardList, LayoutDashboard, HeartPulse, ShieldCheck, User }

// ==================== 通知 ====================
const showNotifications = ref(false)
const notifPanelRef = ref(null)
const allNotifications = ref([])

const READ_KEY = 'healthai_read_notifs'
function getReadSet() {
  try { return new Set(JSON.parse(localStorage.getItem(READ_KEY) || '[]')) } catch { return new Set() }
}
function saveReadSet(s) {
  localStorage.setItem(READ_KEY, JSON.stringify([...s]))
}

const readIds = ref(getReadSet())

const unreadCount = computed(() =>
  allNotifications.value.filter(n => !readIds.value.has(n.id)).length
)

const notificationsWithRead = computed(() =>
  allNotifications.value.map(n => ({ ...n, read: readIds.value.has(n.id) }))
)

const NOTIF_PREFS_KEY = 'healthai_notif_prefs'
function getNotifPrefs() {
  try { return JSON.parse(localStorage.getItem(NOTIF_PREFS_KEY) || '{}') } catch { return {} }
}

async function loadNotifications() {
  const notifs = []
  const prefs = getNotifPrefs()
  const showMetric  = prefs.metric_abnormal  !== false
  const showRisk    = prefs.risk_assessment   !== false
  const showExam    = prefs.exam_done         !== false
  const showMed     = prefs.med_reminder      !== false

  try {
    const [metricsRes, riskRes, examRes] = await Promise.all([
      api.getMetrics(),
      api.getRiskAssessments(),
      api.getExamReports(5),
    ])

    // 指标异常通知（metricsRes.data 是数组 [{metric_type, name, value, unit, status, updated_at, ...}]）
    if (showMetric) {
      const NORMAL_RANGE = {
        heart_rate:         { min: 60, max: 100 },
        blood_pressure_sys: { min: 90, max: 140 },
        blood_pressure_dia: { min: 60, max: 90 },
        blood_sugar:        { min: 3.9, max: 6.1 },
        bmi:                { min: 18.5, max: 24.9 },
      }
      const metricsList = metricsRes.data || []
      for (const m of metricsList) {
        const range = NORMAL_RANGE[m.metric_type]
        if (!range || m.value == null) continue
        if (m.value > range.max) {
          notifs.push({ id: `metric_high_${m.metric_type}`, type: 'warning', icon: 'AlertTriangle',
            title: `${m.name}偏高`, body: `当前 ${m.value} ${m.unit}，超过正常上限 ${range.max} ${m.unit}`,
            time: m.updated_at?.slice(0, 10) || '', path: '/health-data' })
        } else if (m.value < range.min) {
          notifs.push({ id: `metric_low_${m.metric_type}`, type: 'warning', icon: 'AlertTriangle',
            title: `${m.name}偏低`, body: `当前 ${m.value} ${m.unit}，低于正常下限 ${range.min} ${m.unit}`,
            time: m.updated_at?.slice(0, 10) || '', path: '/health-data' })
        }
      }
    }

    // 风险评估通知（API 返回 {success, data: [...]}，data 是数组）
    if (showRisk) {
      const assessments = riskRes.data || []
      for (const a of assessments.slice(0, 3)) {
        if (a.risk_level === 'high' || a.risk_level === 'medium') {
          notifs.push({ id: `risk_${a.id}`, type: a.risk_level === 'high' ? 'danger' : 'warning',
            icon: 'TrendingUp', title: `${a.name}${a.risk_level === 'high' ? '较高' : '中等'}`,
            body: `评估得分 ${a.score ?? ''}，建议关注相关健康指标`,
            time: a.date || '', path: '/risk-assessment' })
        }
      }
    }

    // 体检报告解析完成通知
    if (showExam) {
      const exams = examRes.data || []
      for (const e of exams.slice(0, 2)) {
        if (e.status === 'done') {
          notifs.push({ id: `exam_done_${e.id}`, type: 'success', icon: 'CheckCircle',
            title: '体检报告解析完成', body: e.filename || '体检报告已可查看',
            time: e.uploaded_at?.slice(0, 10) || '', path: `/exam-report?id=${e.id}` })
        }
      }
    }
  } catch (err) {
    console.error('loadNotifications error:', err)
  }

  // 用药提醒通知（来自 localStorage，到点时注入铃铛）
  if (showMed) {
    try {
      const reminders = JSON.parse(localStorage.getItem('med_reminders') || '[]')
      const now = new Date()
      const hhmm = `${String(now.getHours()).padStart(2,'0')}:${String(now.getMinutes()).padStart(2,'0')}`
      reminders.forEach(r => {
        const todayKey = `med_notif_${r.medId}_${hhmm}_${now.toDateString()}`
        if (r.time === hhmm && !sessionStorage.getItem(todayKey)) {
          sessionStorage.setItem(todayKey, '1')
          notifs.unshift({ id: `med_${r.medId}_${hhmm}`, type: 'info', icon: 'CheckCircle',
            title: `💊 服药提醒：${r.medName}`, body: `${r.dose || ''} ${r.relation ? '（' + ({before_meal:'饭前',after_meal:'饭后',with_meal:'随餐',before_sleep:'睡前',anytime:'不限'}[r.relation]||'') + '）' : ''}`.trim(),
            time: hhmm, path: '/medication' })
        }
      })
    } catch {}
  }

  allNotifications.value = notifs
}

function toggleNotifications() {
  showNotifications.value = !showNotifications.value
}

function markAllRead() {
  const s = new Set(allNotifications.value.map(n => n.id))
  readIds.value = s
  saveReadSet(s)
}

function clickNotif(notif) {
  const s = new Set(readIds.value)
  s.add(notif.id)
  readIds.value = s
  saveReadSet(s)
  showNotifications.value = false
  router.push(notif.path)
}

function handleNotifClickOutside(e) {
  if (notifPanelRef.value && !notifPanelRef.value.contains(e.target)) {
    showNotifications.value = false
  }
}

function handleGlobalClick(e) {
  handleClickOutside(e)
  handleNotifClickOutside(e)
}

onMounted(() => {
  loadNotifications()
  document.addEventListener('mousedown', handleGlobalClick)
})
onBeforeUnmount(() => document.removeEventListener('mousedown', handleGlobalClick))

const notifIconMap = { AlertTriangle, CheckCircle, TrendingUp }
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
      <!-- 通知铃铛 -->
      <div class="notif-wrap" ref="notifPanelRef">
        <button class="btn btn-icon notif-btn" @click="toggleNotifications">
          <Bell :size="20" />
          <span v-if="unreadCount > 0" class="notif-badge">{{ unreadCount > 9 ? '9+' : unreadCount }}</span>
        </button>
        <div v-if="showNotifications" class="notif-dropdown">
          <div class="notif-header">
            <span class="notif-title">通知</span>
            <button v-if="unreadCount > 0" class="notif-read-all" @click="markAllRead">全部已读</button>
          </div>
          <div v-if="notificationsWithRead.length === 0" class="notif-empty">暂无通知</div>
          <div v-else class="notif-list">
            <button
              v-for="n in notificationsWithRead"
              :key="n.id"
              class="notif-item"
              :class="[`notif-${n.type}`, { 'notif-read': n.read }]"
              @click="clickNotif(n)"
            >
              <component :is="notifIconMap[n.icon]" :size="16" class="notif-icon" />
              <div class="notif-body">
                <div class="notif-item-title">{{ n.title }}</div>
                <div class="notif-item-body">{{ n.body }}</div>
                <div class="notif-item-time">{{ n.time }}</div>
              </div>
              <span v-if="!n.read" class="notif-dot" />
            </button>
          </div>
        </div>
      </div>
      <button class="btn btn-icon" @click="router.push('/settings')">
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

/* ==================== 通知面板 ==================== */
.notif-wrap {
  position: relative;
}

.notif-btn {
  position: relative;
}

.notif-badge {
  position: absolute;
  top: 2px;
  right: 2px;
  min-width: 16px;
  height: 16px;
  padding: 0 4px;
  border-radius: 8px;
  background: #ef4444;
  color: #fff;
  font-size: 10px;
  font-weight: 700;
  line-height: 16px;
  text-align: center;
}

.notif-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 340px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  z-index: 200;
  overflow: hidden;
}

.notif-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px 8px;
  border-bottom: 1px solid var(--color-border);
}

.notif-title {
  font-size: var(--font-size-sm);
  font-weight: 600;
  color: var(--color-text-primary);
}

.notif-read-all {
  background: none;
  border: none;
  font-size: 12px;
  color: var(--color-primary);
  cursor: pointer;
  padding: 0;
}

.notif-empty {
  padding: 24px 16px;
  text-align: center;
  font-size: var(--font-size-sm);
  color: var(--color-text-tertiary);
}

.notif-list {
  max-height: 360px;
  overflow-y: auto;
}

.notif-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  width: 100%;
  padding: 10px 16px;
  background: none;
  border: none;
  border-bottom: 1px solid var(--color-border);
  cursor: pointer;
  text-align: left;
  transition: background var(--transition-fast);
  position: relative;
}

.notif-item:last-child {
  border-bottom: none;
}

.notif-item:hover {
  background: var(--color-bg);
}

.notif-item.notif-read {
  opacity: 0.6;
}

.notif-icon {
  flex-shrink: 0;
  margin-top: 2px;
}

.notif-warning .notif-icon { color: #f59e0b; }
.notif-danger .notif-icon  { color: #ef4444; }
.notif-success .notif-icon { color: #10b981; }

.notif-body {
  flex: 1;
  min-width: 0;
}

.notif-item-title {
  font-size: var(--font-size-sm);
  font-weight: 500;
  color: var(--color-text-primary);
  margin-bottom: 2px;
}

.notif-item-body {
  font-size: 12px;
  color: var(--color-text-secondary);
  line-height: 1.4;
  margin-bottom: 4px;
}

.notif-item-time {
  font-size: 11px;
  color: var(--color-text-tertiary);
}

.notif-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--color-primary);
  flex-shrink: 0;
  margin-top: 5px;
}
</style>
