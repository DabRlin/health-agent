<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import { 
  Plus, 
  Upload, 
  Calendar,
  Heart,
  Droplets,
  Gauge,
  Activity,
  TrendingUp,
  TrendingDown,
  Minus,
  Moon,
  Loader2,
  X
} from 'lucide-vue-next'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import api from '../api'

// 注册 ECharts 组件
use([CanvasRenderer, LineChart, GridComponent, TooltipComponent, LegendComponent])

// 图标映射
const iconMap = { Heart, Droplets, Gauge, Activity, Moon }

const activeTab = ref('overview')
const loading = ref(true)
const healthIndicators = ref([])
const historyRecords = ref([])
const trendData = ref([])
const selectedDays = ref(30)

// 添加数据弹窗
const showAddModal = ref(false)
const addForm = ref({
  type: 'heart_rate',
  value: ''
})
const metricOptions = [
  { value: 'heart_rate', label: '心率', unit: 'bpm' },
  { value: 'blood_pressure_sys', label: '收缩压', unit: 'mmHg' },
  { value: 'blood_pressure_dia', label: '舒张压', unit: 'mmHg' },
  { value: 'blood_sugar', label: '空腹血糖', unit: 'mmol/L' },
  { value: 'bmi', label: 'BMI', unit: 'kg/m²' },
  { value: 'sleep', label: '睡眠时长', unit: '小时' },
]

// ECharts 配置
const chartOption = computed(() => {
  if (!trendData.value.length) return {}
  
  const dates = trendData.value.map(d => d.date.slice(5)) // MM-DD
  const heartRates = trendData.value.map(d => d.heart_rate)
  const systolic = trendData.value.map(d => d.systolic)
  const diastolic = trendData.value.map(d => d.diastolic)
  const bloodSugar = trendData.value.map(d => d.blood_sugar)
  
  return {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#e5e5e5',
      textStyle: { color: '#333' }
    },
    legend: {
      data: ['心率', '收缩压', '舒张压', '血糖'],
      bottom: 0
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      top: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: dates,
      axisLine: { lineStyle: { color: '#e5e5e5' } },
      axisLabel: { color: '#666' }
    },
    yAxis: [
      {
        type: 'value',
        name: 'bpm/mmHg',
        axisLine: { show: false },
        splitLine: { lineStyle: { color: '#f0f0f0' } },
        axisLabel: { color: '#666' }
      },
      {
        type: 'value',
        name: 'mmol/L',
        axisLine: { show: false },
        splitLine: { show: false },
        axisLabel: { color: '#666' }
      }
    ],
    series: [
      {
        name: '心率',
        type: 'line',
        data: heartRates,
        smooth: true,
        lineStyle: { color: '#FA383E' },
        itemStyle: { color: '#FA383E' }
      },
      {
        name: '收缩压',
        type: 'line',
        data: systolic,
        smooth: true,
        lineStyle: { color: '#0866FF' },
        itemStyle: { color: '#0866FF' }
      },
      {
        name: '舒张压',
        type: 'line',
        data: diastolic,
        smooth: true,
        lineStyle: { color: '#00C6FF' },
        itemStyle: { color: '#00C6FF' }
      },
      {
        name: '血糖',
        type: 'line',
        yAxisIndex: 1,
        data: bloodSugar,
        smooth: true,
        lineStyle: { color: '#F7B928' },
        itemStyle: { color: '#F7B928' }
      }
    ]
  }
})

const tabs = [
  { id: 'overview', name: '概览' },
  { id: 'blood-pressure', name: '血压' },
  { id: 'blood-sugar', name: '血糖' },
  { id: 'heart-rate', name: '心率' },
]

// 加载健康指标
const loadMetrics = async () => {
  try {
    const res = await api.getMetrics()
    if (res.success) {
      healthIndicators.value = res.data.map(m => ({
        ...m,
        icon: iconMap[m.icon] || Activity,
        normalRange: m.normal_range
      }))
    }
  } catch (error) {
    console.error('Failed to load metrics:', error)
  }
}

// 加载趋势数据
const loadTrend = async (days) => {
  try {
    selectedDays.value = days
    const res = await api.getMetricsTrend(days)
    if (res.success) {
      trendData.value = res.data
    }
  } catch (error) {
    console.error('Failed to load trend:', error)
  }
}

// 加载历史记录
const loadRecords = async () => {
  try {
    const res = await api.getRecords()
    if (res.success) {
      historyRecords.value = res.data
    }
  } catch (error) {
    console.error('Failed to load records:', error)
  }
}

// 初始化
const init = async () => {
  loading.value = true
  await Promise.all([loadMetrics(), loadTrend(30), loadRecords()])
  loading.value = false
}

onMounted(() => {
  init()
})

const getTrendIcon = (trend) => {
  switch (trend) {
    case 'up': return TrendingUp
    case 'down': return TrendingDown
    default: return Minus
  }
}

const getTrendColor = (trend, status) => {
  if (status === 'warning') return 'var(--color-warning)'
  if (status === 'danger') return 'var(--color-danger)'
  return 'var(--color-text-tertiary)'
}

// 添加健康数据
const submitAddForm = async () => {
  if (!addForm.value.value) return
  
  try {
    const res = await api.addMetric({
      type: addForm.value.type,
      value: parseFloat(addForm.value.value)
    })
    if (res.success) {
      showAddModal.value = false
      addForm.value.value = ''
      // 刷新数据
      await loadMetrics()
    }
  } catch (error) {
    console.error('Failed to add metric:', error)
  }
}

// 获取当前选中指标的单位
const currentUnit = computed(() => {
  const option = metricOptions.find(o => o.value === addForm.value.type)
  return option ? option.unit : ''
})
</script>

<template>
  <div class="health-data">
    <!-- 顶部操作栏 -->
    <div class="page-header">
      <div class="tabs">
        <button 
          v-for="tab in tabs" 
          :key="tab.id"
          :class="['tab-btn', { active: activeTab === tab.id }]"
          @click="activeTab = tab.id"
        >
          {{ tab.name }}
        </button>
      </div>
      <div class="header-actions">
        <button class="btn btn-primary" @click="showAddModal = true">
          <Plus :size="18" />
          添加记录
        </button>
      </div>
    </div>

    <!-- 指标卡片网格 -->
    <section class="indicators-section">
      <h3 class="section-title">健康指标</h3>
      <div class="indicators-grid">
        <div 
          v-for="indicator in healthIndicators" 
          :key="indicator.name"
          class="indicator-card card"
        >
          <div class="indicator-header">
            <div class="indicator-icon" :style="{ backgroundColor: indicator.color + '15', color: indicator.color }">
              <component :is="indicator.icon" :size="20" />
            </div>
            <div class="indicator-trend" :style="{ color: getTrendColor(indicator.trend, indicator.status) }">
              <component :is="getTrendIcon(indicator.trend)" :size="16" />
            </div>
          </div>
          <div class="indicator-body">
            <span class="indicator-name">{{ indicator.name }}</span>
            <div class="indicator-value">
              <span class="value">{{ indicator.value }}</span>
              <span class="unit">{{ indicator.unit }}</span>
            </div>
          </div>
          <div class="indicator-footer">
            <span class="normal-range">正常范围: {{ indicator.normalRange }}</span>
            <span :class="['status-dot', indicator.status]"></span>
          </div>
        </div>
      </div>
    </section>

    <!-- 趋势图表区域 -->
    <section class="chart-section">
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">趋势分析</h3>
          <div class="chart-controls">
            <button :class="['btn', selectedDays === 7 ? 'btn-secondary' : 'btn-ghost']" @click="loadTrend(7)">7天</button>
            <button :class="['btn', selectedDays === 30 ? 'btn-secondary' : 'btn-ghost']" @click="loadTrend(30)">30天</button>
            <button :class="['btn', selectedDays === 90 ? 'btn-secondary' : 'btn-ghost']" @click="loadTrend(90)">90天</button>
          </div>
        </div>
        <div class="chart-container">
          <v-chart v-if="trendData.length" :option="chartOption" autoresize />
          <div v-else class="chart-placeholder">
            <Activity :size="48" />
            <p>暂无数据</p>
          </div>
        </div>
      </div>
    </section>

    <!-- 添加数据弹窗 -->
    <div v-if="showAddModal" class="modal-overlay" @click.self="showAddModal = false">
      <div class="modal">
        <div class="modal-header">
          <h3>添加健康数据</h3>
          <button class="btn-icon" @click="showAddModal = false">
            <X :size="20" />
          </button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>指标类型</label>
            <select v-model="addForm.type" class="form-select">
              <option v-for="opt in metricOptions" :key="opt.value" :value="opt.value">
                {{ opt.label }}
              </option>
            </select>
          </div>
          <div class="form-group">
            <label>数值 ({{ currentUnit }})</label>
            <input 
              v-model="addForm.value" 
              type="number" 
              step="0.1"
              class="form-input" 
              :placeholder="`请输入${currentUnit}`"
            />
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showAddModal = false">取消</button>
          <button class="btn btn-primary" @click="submitAddForm">确认添加</button>
        </div>
      </div>
    </div>

    <!-- 历史记录 -->
    <section class="history-section">
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">历史记录</h3>
          <button class="btn btn-ghost">查看全部</button>
        </div>
        <div class="history-list">
          <div 
            v-for="record in historyRecords" 
            :key="record.date"
            class="history-item"
          >
            <div class="history-icon">
              <Calendar :size="18" />
            </div>
            <div class="history-info">
              <span class="history-type">{{ record.type }}</span>
              <span class="history-date text-sm text-secondary">{{ record.date }}</span>
            </div>
            <span class="history-source text-sm text-secondary">{{ record.source }}</span>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.health-data {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

/* Page Header */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--spacing-md);
}

.tabs {
  display: flex;
  gap: var(--spacing-xs);
  background-color: var(--color-surface);
  padding: var(--spacing-xs);
  border-radius: var(--radius-md);
}

.tab-btn {
  padding: var(--spacing-sm) var(--spacing-md);
  border: none;
  background: transparent;
  border-radius: var(--radius-sm);
  font-size: var(--font-size-sm);
  font-weight: 500;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.tab-btn:hover {
  color: var(--color-text-primary);
}

.tab-btn.active {
  background-color: var(--color-primary);
  color: white;
}

.header-actions {
  display: flex;
  gap: var(--spacing-sm);
}

/* Section Title */
.section-title {
  margin-bottom: var(--spacing-md);
}

/* Indicators Grid */
.indicators-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--spacing-md);
}

.indicator-card {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.indicator-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.indicator-icon {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
}

.indicator-trend {
  display: flex;
  align-items: center;
}

.indicator-body {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.indicator-name {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.indicator-value {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.indicator-value .value {
  font-size: var(--font-size-2xl);
  font-weight: 600;
}

.indicator-value .unit {
  font-size: var(--font-size-sm);
  color: var(--color-text-tertiary);
}

.indicator-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: var(--spacing-sm);
  border-top: 1px solid var(--color-border);
}

.normal-range {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: var(--radius-full);
}

.status-dot.normal {
  background-color: var(--color-success);
}

.status-dot.warning {
  background-color: var(--color-warning);
}

.status-dot.danger {
  background-color: var(--color-danger);
}

/* Chart Section */
.chart-controls {
  display: flex;
  gap: var(--spacing-xs);
}

.chart-container {
  height: 300px;
}

.chart-container .v-chart {
  width: 100%;
  height: 100%;
}

.chart-placeholder {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-sm);
  color: var(--color-text-tertiary);
  background-color: var(--color-bg);
  border-radius: var(--radius-md);
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: white;
  border-radius: var(--radius-lg);
  width: 100%;
  max-width: 400px;
  box-shadow: var(--shadow-lg);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-lg);
  border-bottom: 1px solid var(--color-border);
}

.modal-header h3 {
  margin: 0;
}

.btn-icon {
  background: none;
  border: none;
  cursor: pointer;
  padding: var(--spacing-xs);
  border-radius: var(--radius-sm);
  color: var(--color-text-secondary);
}

.btn-icon:hover {
  background: var(--color-bg);
}

.modal-body {
  padding: var(--spacing-lg);
}

.form-group {
  margin-bottom: var(--spacing-md);
}

.form-group label {
  display: block;
  margin-bottom: var(--spacing-xs);
  font-weight: 500;
  color: var(--color-text-secondary);
}

.form-input,
.form-select {
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: var(--font-size-base);
  transition: border-color var(--transition-fast);
}

.form-input:focus,
.form-select:focus {
  outline: none;
  border-color: var(--color-primary);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-sm);
  padding: var(--spacing-lg);
  border-top: 1px solid var(--color-border);
}

/* History List */
.history-list {
  display: flex;
  flex-direction: column;
}

.history-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-md) 0;
  border-bottom: 1px solid var(--color-border);
}

.history-item:last-child {
  border-bottom: none;
}

.history-icon {
  width: 36px;
  height: 36px;
  background-color: var(--color-bg);
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-secondary);
}

.history-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.history-type {
  font-weight: 500;
}

/* Responsive */
@media (max-width: 1024px) {
  .indicators-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 640px) {
  .indicators-grid {
    grid-template-columns: 1fr;
  }
  
  .page-header {
    flex-direction: column;
    align-items: stretch;
  }
  
  .tabs {
    overflow-x: auto;
  }
}
</style>
