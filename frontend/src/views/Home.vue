<script setup>
import { ref, onMounted } from 'vue'
import { 
  MessageCircle, 
  Activity, 
  ShieldCheck, 
  TrendingUp,
  Heart,
  Droplets,
  Gauge,
  Moon,
  ArrowRight,
  Loader2
} from 'lucide-vue-next'
import api from '../api'

// 图标映射
const iconMap = {
  Heart, Droplets, Gauge, Moon, Activity,
  MessageCircle, ShieldCheck
}

// 状态
const loading = ref(true)
const dashboardData = ref(null)
const healthMetrics = ref([])
const quickActions = ref([])
const recentRecords = ref([])

// 获取问候语
const getGreeting = () => {
  const hour = new Date().getHours()
  if (hour < 12) return '早上好'
  if (hour < 18) return '下午好'
  return '晚上好'
}

// 加载数据
const loadDashboard = async () => {
  try {
    loading.value = true
    const res = await api.getDashboard()
    
    if (res?.success && res.data) {
      dashboardData.value = res.data
      healthMetrics.value = res.data.metrics.map(m => ({
        ...m,
        icon: iconMap[m.icon] || Activity
      }))
      quickActions.value = res.data.quick_actions.map(a => ({
        ...a,
        icon: iconMap[a.icon] || Activity
      }))
      recentRecords.value = res.data.recent_records
    }
  } catch (error) {
    console.error('Failed to load dashboard:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadDashboard()
})
</script>

<template>
  <div class="home">
    <!-- 加载状态 -->
    <div v-if="loading" class="loading-state">
      <Loader2 :size="32" class="spin" />
      <span>加载中...</span>
    </div>

    <template v-else>
    <!-- 欢迎区域 -->
    <section class="welcome-section">
      <div class="welcome-content">
        <h2>{{ getGreeting() }}，{{ dashboardData?.user?.name || '用户' }}</h2>
        <p class="text-secondary">今天是您健康管理的第 {{ dashboardData?.user?.health_days || 0 }} 天，继续保持！</p>
      </div>
      <div class="health-score">
        <div class="score-circle">
          <span class="score-value">{{ dashboardData?.user?.health_score || 0 }}</span>
          <span class="score-label">健康评分</span>
        </div>
      </div>
    </section>

    <!-- 健康指标卡片 -->
    <section class="metrics-section">
      <div class="section-header">
        <h3>今日健康指标</h3>
        <router-link to="/health-data" class="view-all">
          查看全部 <ArrowRight :size="16" />
        </router-link>
      </div>
      <div class="metrics-grid">
        <div 
          v-for="metric in healthMetrics" 
          :key="metric.name" 
          class="metric-card card"
        >
          <div class="metric-icon" :style="{ backgroundColor: metric.color + '15', color: metric.color }">
            <component :is="metric.icon" :size="20" />
          </div>
          <div class="metric-info">
            <span class="metric-name">{{ metric.name }}</span>
            <div class="metric-value">
              <span class="value">{{ metric.value }}</span>
              <span class="unit">{{ metric.unit }}</span>
            </div>
          </div>
          <span :class="['badge', `badge-${metric.status === 'normal' || metric.status === 'good' ? 'low' : 'medium'}`]">
            {{ metric.status === 'normal' ? '正常' : '良好' }}
          </span>
        </div>
      </div>
    </section>

    <!-- 快捷操作 -->
    <section class="actions-section">
      <h3 class="mb-md">快捷操作</h3>
      <div class="actions-grid">
        <router-link 
          v-for="action in quickActions" 
          :key="action.title" 
          :to="action.path"
          class="action-card card"
        >
          <div class="action-icon" :style="{ backgroundColor: action.color + '15', color: action.color }">
            <component :is="action.icon" :size="24" />
          </div>
          <div class="action-content">
            <h4>{{ action.title }}</h4>
            <p class="text-secondary text-sm">{{ action.desc }}</p>
          </div>
          <ArrowRight :size="20" class="action-arrow" />
        </router-link>
      </div>
    </section>

    <!-- 最近记录 -->
    <section class="records-section">
      <div class="section-header">
        <h3>最近记录</h3>
        <router-link to="/profile" class="view-all">
          查看全部 <ArrowRight :size="16" />
        </router-link>
      </div>
      <div class="card">
        <div class="records-list">
          <div 
            v-for="record in recentRecords" 
            :key="record.date" 
            class="record-item"
          >
            <div class="record-info">
              <span class="record-type">{{ record.type }}</span>
              <span class="record-date text-secondary text-sm">{{ record.date }}</span>
            </div>
            <div class="record-status">
              <span :class="['badge', `badge-${record.risk}`]">
                {{ record.risk === 'low' ? '低风险' : record.risk === 'medium' ? '中风险' : '高风险' }}
              </span>
              <span class="text-sm text-secondary">{{ record.status }}</span>
            </div>
          </div>
        </div>
      </div>
    </section>
    </template>
  </div>
</template>

<style scoped>
.home {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

/* Loading State */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-md);
  padding: var(--spacing-xl);
  color: var(--color-text-secondary);
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Welcome Section */
.welcome-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-xl);
  background: linear-gradient(135deg, var(--color-primary), #00C6FF);
  border-radius: var(--radius-lg);
  color: white;
}

.welcome-content h2 {
  color: white;
  margin-bottom: var(--spacing-xs);
}

.welcome-content p {
  color: rgba(255, 255, 255, 0.8);
}

.health-score {
  display: flex;
  align-items: center;
}

.score-circle {
  width: 100px;
  height: 100px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: var(--radius-full);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(10px);
}

.score-value {
  font-size: 32px;
  font-weight: 700;
}

.score-label {
  font-size: var(--font-size-xs);
  opacity: 0.9;
}

/* Section Header */
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-md);
}

.view-all {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  font-size: var(--font-size-sm);
  color: var(--color-primary);
}

/* Metrics Grid */
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--spacing-md);
}

.metric-card {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.metric-icon {
  width: 44px;
  height: 44px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.metric-info {
  flex: 1;
}

.metric-name {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.metric-value {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.metric-value .value {
  font-size: var(--font-size-xl);
  font-weight: 600;
}

.metric-value .unit {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
}

/* Actions Grid */
.actions-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--spacing-md);
}

.action-card {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  text-decoration: none;
  transition: all var(--transition-fast);
}

.action-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.action-icon {
  width: 52px;
  height: 52px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.action-content {
  flex: 1;
}

.action-content h4 {
  margin-bottom: 2px;
}

.action-arrow {
  color: var(--color-text-tertiary);
}

/* Records List */
.records-list {
  display: flex;
  flex-direction: column;
}

.record-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-md) 0;
  border-bottom: 1px solid var(--color-border);
}

.record-item:last-child {
  border-bottom: none;
}

.record-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.record-type {
  font-weight: 500;
}

.record-status {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

/* Responsive */
@media (max-width: 1024px) {
  .metrics-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .actions-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 640px) {
  .metrics-grid,
  .actions-grid {
    grid-template-columns: 1fr;
  }
  
  .welcome-section {
    flex-direction: column;
    text-align: center;
    gap: var(--spacing-lg);
  }
}
</style>
