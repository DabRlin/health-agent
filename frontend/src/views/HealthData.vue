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
const trendData = ref([])          // 概览：多指标综合数组
const singleTrend = ref(null)      // 单指标：TrendService 完整结果
const singleLoading = ref(false)
const selectedDays = ref(30)

// 添加数据弹窗
const showAddModal = ref(false)
const addForm = ref({
  type: 'heart_rate',
  value: '',
  valueDia: ''
})
const metricOptions = [
  { value: 'heart_rate',         label: '心率',   unit: 'bpm' },
  { value: 'blood_pressure',     label: '血压',   unit: 'mmHg' },
  { value: 'blood_sugar',        label: '空腹血糖', unit: 'mmol/L' },
  { value: 'bmi',                label: 'BMI',   unit: 'kg/m²' },
  { value: 'sleep',              label: '睡眠时长', unit: '小时' },
]

const isBloodPressure = computed(() => addForm.value.type === 'blood_pressure')

// Tab 对应的指标名称映射
const TAB_METRIC_NAMES = {
  'overview':       null, // 全部显示
  'blood-pressure': ['收缩压', '舒张压'],
  'blood-sugar':    ['空腹血糖'],
  'heart-rate':     ['心率'],
}

// 当前 Tab 可见的指标卡
const visibleIndicators = computed(() => {
  const names = TAB_METRIC_NAMES[activeTab.value]
  if (!names) return healthIndicators.value
  return healthIndicators.value.filter(m => names.includes(m.name))
})

// 历史记录始终显示全部（record.type 是事件类型，与指标 Tab 无对应关系）
const visibleRecords = computed(() => historyRecords.value)

// 基础图表公共配置
const baseChart = (dates) => ({
  tooltip: {
    trigger: 'axis',
    backgroundColor: 'rgba(255,255,255,0.95)',
    borderColor: '#e5e5e5',
    textStyle: { color: '#333' }
  },
  grid: { left: '3%', right: '4%', bottom: '15%', top: '14%', containLabel: true },
  xAxis: {
    type: 'category',
    data: dates,
    axisLine: { lineStyle: { color: '#e5e5e5' } },
    axisLabel: { color: '#666' }
  },
})

// ECharts 配置（根据 activeTab 动态切换）
const chartTitle = computed(() => {
  const map = {
    'overview':       '综合趋势',
    'blood-pressure': '血压趋势',
    'blood-sugar':    '血糖趋势',
    'heart-rate':     '心率趋势',
  }
  return map[activeTab.value] || '趋势分析'
})

// 从 singleTrend 的 anomalies 提取异常点索引集合
const anomalyIndexSet = computed(() => {
  const indices = singleTrend.value?.anomalies?.anomaly_indices || []
  return new Set(indices)
})

// 构建带异常标注的数据点
const buildSeriesData = (values, anomalySet, normalColor, anomalyColor) => {
  return values.map((v, i) => ({
    value: v,
    itemStyle: anomalySet.has(i)
      ? { color: anomalyColor, borderWidth: 2, borderColor: anomalyColor }
      : { color: normalColor },
    symbolSize: anomalySet.has(i) ? 10 : 4,
  }))
}

const chartOption = computed(() => {
  const tab = activeTab.value

  // 概览：用综合数组
  if (tab === 'overview') {
    if (!trendData.value.length) return {}
    const dates      = trendData.value.map(d => d.date.slice(5))
    const base       = baseChart(dates)
    const heartRates = trendData.value.map(d => d.heart_rate ?? null)
    const systolic   = trendData.value.map(d => d.systolic   ?? null)
    const diastolic  = trendData.value.map(d => d.diastolic  ?? null)
    const bloodSugar = trendData.value.map(d => d.blood_sugar ?? null)
    return {
      ...base,
      legend: { data: ['心率', '收缩压', '舒张压', '血糖'], bottom: 0 },
      yAxis: [
        { type: 'value', name: 'bpm/mmHg', axisLine: { show: false }, splitLine: { lineStyle: { color: '#f0f0f0' } }, axisLabel: { color: '#666' } },
        { type: 'value', name: 'mmol/L',   axisLine: { show: false }, splitLine: { show: false }, axisLabel: { color: '#666' } }
      ],
      series: [
        { name: '心率',   type: 'line', data: heartRates, smooth: true, lineStyle: { color: '#FA383E' }, itemStyle: { color: '#FA383E' }, symbolSize: 4 },
        { name: '收缩压', type: 'line', data: systolic,   smooth: true, lineStyle: { color: '#0866FF' }, itemStyle: { color: '#0866FF' }, symbolSize: 4 },
        { name: '舒张压', type: 'line', data: diastolic,  smooth: true, lineStyle: { color: '#00C6FF' }, itemStyle: { color: '#00C6FF' }, symbolSize: 4 },
        { name: '血糖',   type: 'line', yAxisIndex: 1, data: bloodSugar, smooth: true, lineStyle: { color: '#F7B928' }, itemStyle: { color: '#F7B928' }, symbolSize: 4 },
      ]
    }
  }

  // 单指标 Tab：用 singleTrend
  if (!singleTrend.value) return {}
  const st      = singleTrend.value
  const dates   = (st.dates || []).map(d => d.slice(5))
  const base    = baseChart(dates)
  const anomSet = anomalyIndexSet.value

  // 预测线数据（接在历史后面，用虚线区分）
  const predValues = st.prediction?.values || []
  const predDates  = (st.prediction?.dates || []).map(d => d.slice(5))
  const allDates   = [...dates, ...predDates]

  if (tab === 'blood-pressure') {
    const sysSeries  = buildSeriesData(st.data || [], anomSet, '#0866FF', '#FA383E')
    const diaSeries  = singleTrendDia.value
      ? buildSeriesData(singleTrendDia.value.data || [], new Set(), '#00C6FF', '#FA383E')
      : []
    const predSeries = predValues.map(v => ({ value: v, itemStyle: { color: '#0866FF', opacity: 0.5 } }))
    const legend = diaSeries.length ? ['收缩压', '舒张压', '预测趋势'] : ['收缩压', '预测趋势']
    return {
      ...base,
      xAxis: { ...base.xAxis, data: allDates },
      legend: { data: legend, bottom: 0 },
      yAxis: [{ type: 'value', name: 'mmHg', axisLine: { show: false }, splitLine: { lineStyle: { color: '#f0f0f0' } }, axisLabel: { color: '#666' } }],
      series: [
        { name: '收缩压', type: 'line', data: [...sysSeries, ...Array(predDates.length).fill(null)],
          smooth: true, lineStyle: { color: '#0866FF' }, areaStyle: { color: 'rgba(8,102,255,0.06)' },
          markLine: { silent: true, lineStyle: { color: '#0866FF', type: 'dashed', opacity: 0.4 }, data: [{ yAxis: 120, name: '正常上限' }] } },
        ...(diaSeries.length ? [{ name: '舒张压', type: 'line', data: [...diaSeries, ...Array(predDates.length).fill(null)],
          smooth: true, lineStyle: { color: '#00C6FF' }, areaStyle: { color: 'rgba(0,198,255,0.06)' },
          markLine: { silent: true, lineStyle: { color: '#00C6FF', type: 'dashed', opacity: 0.4 }, data: [{ yAxis: 80, name: '正常上限' }] } }] : []),
        { name: '预测趋势', type: 'line', data: [...Array(dates.length).fill(null), ...predSeries],
          smooth: true, lineStyle: { color: '#0866FF', type: 'dashed', opacity: 0.6 }, itemStyle: { color: '#0866FF' }, symbolSize: 4 },
      ]
    }
  }

  if (tab === 'blood-sugar') {
    const bsSeries   = buildSeriesData(st.data || [], anomSet, '#F7B928', '#FA383E')
    const predSeries = predValues.map(v => ({ value: v, itemStyle: { color: '#F7B928', opacity: 0.5 } }))
    return {
      ...base,
      xAxis: { ...base.xAxis, data: allDates },
      legend: { data: ['空腹血糖', '预测趋势'], bottom: 0 },
      yAxis: [{ type: 'value', name: 'mmol/L', axisLine: { show: false }, splitLine: { lineStyle: { color: '#f0f0f0' } }, axisLabel: { color: '#666' } }],
      series: [
        { name: '空腹血糖', type: 'line', data: [...bsSeries, ...Array(predDates.length).fill(null)],
          smooth: true, lineStyle: { color: '#F7B928' }, areaStyle: { color: 'rgba(247,185,40,0.1)' },
          markArea: { silent: true, itemStyle: { color: 'rgba(52,199,89,0.05)' }, data: [[{ yAxis: 3.9 }, { yAxis: 6.1 }]] },
          markLine: { silent: true, lineStyle: { color: '#F7B928', type: 'dashed', opacity: 0.4 }, data: [{ yAxis: 6.1, name: '正常上限' }] } },
        { name: '预测趋势', type: 'line', data: [...Array(dates.length).fill(null), ...predSeries],
          smooth: true, lineStyle: { color: '#F7B928', type: 'dashed', opacity: 0.6 }, itemStyle: { color: '#F7B928' }, symbolSize: 4 },
      ]
    }
  }

  if (tab === 'heart-rate') {
    const hrSeries   = buildSeriesData(st.data || [], anomSet, '#FA383E', '#8B5CF6')
    const predSeries = predValues.map(v => ({ value: v, itemStyle: { color: '#FA383E', opacity: 0.5 } }))
    return {
      ...base,
      xAxis: { ...base.xAxis, data: allDates },
      legend: { data: ['心率', '预测趋势'], bottom: 0 },
      yAxis: [{ type: 'value', name: 'bpm', axisLine: { show: false }, splitLine: { lineStyle: { color: '#f0f0f0' } }, axisLabel: { color: '#666' } }],
      series: [
        { name: '心率', type: 'line', data: [...hrSeries, ...Array(predDates.length).fill(null)],
          smooth: true, lineStyle: { color: '#FA383E' }, areaStyle: { color: 'rgba(250,56,62,0.08)' },
          markArea: { silent: true, itemStyle: { color: 'rgba(52,199,89,0.05)' }, data: [[{ yAxis: 60 }, { yAxis: 100 }]] },
          markLine: { silent: true, lineStyle: { color: '#FA383E', type: 'dashed', opacity: 0.4 }, data: [{ yAxis: 100, name: '正常上限' }] } },
        { name: '预测趋势', type: 'line', data: [...Array(dates.length).fill(null), ...predSeries],
          smooth: true, lineStyle: { color: '#FA383E', type: 'dashed', opacity: 0.6 }, itemStyle: { color: '#FA383E' }, symbolSize: 4 },
      ]
    }
  }

  return {}
})

// 各 Tab 统计摘要（单指标从 singleTrend.statistics 读取）
const tabStats = computed(() => {
  const tab = activeTab.value
  if (tab === 'overview') return []
  if (!singleTrend.value) return []
  const stats = singleTrend.value.statistics || {}
  const trend = singleTrend.value.trend || {}
  const anomCount = singleTrend.value.anomalies?.anomaly_indices?.length || 0
  const fmt = (v) => v != null ? Number(v).toFixed(1) : '--'

  if (tab === 'blood-pressure') {
    const diaStats = singleTrendDia.value?.statistics || {}
    return [
      { label: '平均收缩压', value: fmt(stats.mean),    unit: 'mmHg', color: '#0866FF' },
      { label: '平均舒张压', value: fmt(diaStats.mean), unit: 'mmHg', color: '#00C6FF' },
      { label: '最高收缩压', value: fmt(stats.max),     unit: 'mmHg', color: '#FA383E' },
      { label: '异常次数',   value: anomCount,           unit: '次',   color: anomCount > 0 ? '#FA383E' : '#31A24C' },
    ]
  }
  if (tab === 'blood-sugar') {
    return [
      { label: '平均血糖', value: fmt(stats.mean), unit: 'mmol/L', color: '#F7B928' },
      { label: '最高血糖', value: fmt(stats.max),  unit: 'mmol/L', color: '#FA383E' },
      { label: '最低血糖', value: fmt(stats.min),  unit: 'mmol/L', color: '#31A24C' },
      { label: '异常次数', value: anomCount,        unit: '次',     color: anomCount > 0 ? '#FA383E' : '#31A24C' },
    ]
  }
  if (tab === 'heart-rate') {
    return [
      { label: '平均心率', value: fmt(stats.mean), unit: 'bpm', color: '#FA383E' },
      { label: '最高心率', value: fmt(stats.max),  unit: 'bpm', color: '#FA383E' },
      { label: '最低心率', value: fmt(stats.min),  unit: 'bpm', color: '#31A24C' },
      { label: '异常次数', value: anomCount,        unit: '次',  color: anomCount > 0 ? '#FA383E' : '#31A24C' },
    ]
  }
  return []
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

// 血压双轨数据
const singleTrendDia = ref(null)

// Tab -> 单指标 metric_type 映射
const TAB_METRIC_TYPE = {
  'blood-pressure': 'blood_pressure_sys',
  'blood-sugar':    'blood_sugar',
  'heart-rate':     'heart_rate',
}

// 加载概览趋势数据（多指标综合）
const loadTrend = async (days) => {
  try {
    selectedDays.value = days
    if (activeTab.value === 'overview') {
      const res = await api.getMetricsTrend(days, 'all')
      if (res.success) trendData.value = res.data
    } else {
      await loadSingleTrend(TAB_METRIC_TYPE[activeTab.value], days)
    }
  } catch (error) {
    console.error('Failed to load trend:', error)
  }
}

// 加载单指标趋势（带异常+预测）
const loadSingleTrend = async (metricType, days) => {
  if (!metricType) return
  singleLoading.value = true
  try {
    const daysVal = days || selectedDays.value
    if (metricType === 'blood_pressure_sys') {
      const [resSys, resDia] = await Promise.all([
        api.getMetricsTrend(daysVal, 'blood_pressure_sys'),
        api.getMetricsTrend(daysVal, 'blood_pressure_dia'),
      ])
      if (resSys.success) singleTrend.value = resSys.data
      if (resDia.success) singleTrendDia.value = resDia.data
    } else {
      const res = await api.getMetricsTrend(daysVal, metricType)
      if (res.success) singleTrend.value = res.data
      singleTrendDia.value = null
    }
  } catch (error) {
    console.error('Failed to load single trend:', error)
  } finally {
    singleLoading.value = false
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

// 切换 Tab
watch(activeTab, async (tab) => {
  if (tab === 'overview') {
    const res = await api.getMetricsTrend(selectedDays.value, 'all')
    if (res.success) trendData.value = res.data
  } else {
    await loadSingleTrend(TAB_METRIC_TYPE[tab])
  }
})

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
  if (isBloodPressure.value && !addForm.value.valueDia) return

  try {
    if (isBloodPressure.value) {
      await Promise.all([
        api.addMetric({ type: 'blood_pressure_sys', value: parseFloat(addForm.value.value) }),
        api.addMetric({ type: 'blood_pressure_dia', value: parseFloat(addForm.value.valueDia) }),
      ])
    } else {
      await api.addMetric({
        type: addForm.value.type,
        value: parseFloat(addForm.value.value)
      })
    }
    showAddModal.value = false
    addForm.value.value = ''
    addForm.value.valueDia = ''
    await loadMetrics()
  } catch (error) {
    console.error('Failed to add metric:', error)
  }
}

// 获取当前选中指标的单位
const currentUnit = computed(() => {
  const option = metricOptions.find(o => o.value === addForm.value.type)
  return option ? option.unit : ''
})

// 弹窗关闭时重置 valueDia
const closeAddModal = () => {
  showAddModal.value = false
  addForm.value.value = ''
  addForm.value.valueDia = ''
}
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
          v-for="indicator in visibleIndicators" 
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

    <!-- Tab 统计摘要（非概览时显示）-->
    <section v-if="activeTab !== 'overview' && tabStats.length" class="stats-section">
      <div class="stats-grid">
        <div v-for="stat in tabStats" :key="stat.label" class="stat-card card">
          <span class="stat-label">{{ stat.label }}</span>
          <div class="stat-value-row">
            <span class="stat-value" :style="{ color: stat.color }">{{ stat.value }}</span>
            <span class="stat-unit">{{ stat.unit }}</span>
          </div>
        </div>
      </div>
    </section>

    <!-- 趋势图表区域 -->
    <section class="chart-section">
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ chartTitle }}</h3>
          <div class="chart-controls">
            <button :class="['btn', selectedDays === 7 ? 'btn-secondary' : 'btn-ghost']" @click="loadTrend(7)">7天</button>
            <button :class="['btn', selectedDays === 30 ? 'btn-secondary' : 'btn-ghost']" @click="loadTrend(30)">30天</button>
            <button :class="['btn', selectedDays === 90 ? 'btn-secondary' : 'btn-ghost']" @click="loadTrend(90)">90天</button>
          </div>
        </div>
        <div class="chart-container">
          <div v-if="singleLoading" class="chart-placeholder">
            <Loader2 :size="32" class="spin" />
            <p>加载中...</p>
          </div>
          <v-chart
            v-else-if="Object.keys(chartOption).length"
            :option="chartOption"
            autoresize
          />
          <div v-else class="chart-placeholder">
            <Activity :size="48" />
            <p>暂无数据</p>
          </div>
        </div>
      </div>
    </section>

    <!-- 添加数据弹窗 -->
    <div v-if="showAddModal" class="modal-overlay" @click.self="closeAddModal">
      <div class="modal">
        <div class="modal-header">
          <h3>添加健康数据</h3>
          <button class="btn-icon" @click="closeAddModal">
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
          <template v-if="isBloodPressure">
            <div class="form-group">
              <label>收缩压 (mmHg)</label>
              <input
                v-model="addForm.value"
                type="number"
                step="1"
                class="form-input"
                placeholder="请输入收缩压，如 120"
              />
            </div>
            <div class="form-group">
              <label>舒张压 (mmHg)</label>
              <input
                v-model="addForm.valueDia"
                type="number"
                step="1"
                class="form-input"
                placeholder="请输入舒张压，如 80"
              />
            </div>
          </template>
          <div v-else class="form-group">
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
          <button class="btn btn-secondary" @click="closeAddModal">取消</button>
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
            v-for="record in visibleRecords" 
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

/* Stats Section */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--spacing-md);
}

.stat-card {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
  padding: var(--spacing-md) var(--spacing-lg);
}

.stat-label {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
}

.stat-value-row {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.stat-value {
  font-size: var(--font-size-xl);
  font-weight: 700;
}

.stat-unit {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
}

/* History empty */
.history-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-xl) 0;
  color: var(--color-text-tertiary);
  font-size: var(--font-size-sm);
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to   { transform: rotate(360deg); }
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
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 640px) {
  .indicators-grid {
    grid-template-columns: 1fr;
  }
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
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
