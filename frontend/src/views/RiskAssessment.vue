<script setup>
import { ref, onMounted } from 'vue'
import { 
  ShieldCheck, 
  AlertTriangle, 
  CheckCircle,
  XCircle,
  ChevronRight,
  FileText,
  Heart,
  Droplets,
  Brain,
  Bone,
  Loader2,
  X,
  Info,
  RefreshCw
} from 'lucide-vue-next'
import api from '../api'

const loading = ref(false)
const assessmentResults = ref([])
const selectedResult = ref(null)
const showDetailModal = ref(false)

const openDetail = (result) => {
  selectedResult.value = result
  showDetailModal.value = true
}
const closeDetail = () => { showDetailModal.value = false }

// 风险评估类型
const assessmentTypes = [
  {
    id: 'cardiovascular',
    name: '心血管疾病风险',
    icon: Heart,
    color: '#FA383E',
    description: '评估心脏病、高血压等心血管疾病风险',
    factors: ['年龄', '血压', '胆固醇', '吸烟史', '家族史']
  },
  {
    id: 'diabetes',
    name: '糖尿病风险',
    icon: Droplets,
    color: '#F7B928',
    description: '评估2型糖尿病发病风险',
    factors: ['BMI', '血糖', '年龄', '家族史', '运动习惯']
  },
  {
    id: 'metabolic',
    name: '代谢综合征风险',
    icon: Brain,
    color: '#8B5CF6',
    description: '评估代谢相关健康问题风险',
    factors: ['腰围', '血压', '血糖', '血脂', 'BMI']
  },
  {
    id: 'osteoporosis',
    name: '骨质疏松风险',
    icon: Bone,
    color: '#0866FF',
    description: '评估骨质疏松发生风险',
    factors: ['年龄', '性别', '体重', '钙摄入', '运动']
  },
]

// 加载评估历史
const loadAssessments = async () => {
  try {
    const res = await api.getRiskAssessments()
    if (res.success) {
      assessmentResults.value = res.data.map(r => ({
        ...r,
        riskLevel: r.risk_level
      }))
    }
  } catch (error) {
    console.error('Failed to load assessments:', error)
  }
}

// 开始新评估
const startAssessment = async (type) => {
  loading.value = true
  try {
    const res = await api.createRiskAssessment(type.id)
    if (res.success) {
      const item = { ...res.data, riskLevel: res.data.risk_level }
      assessmentResults.value.unshift(item)
      openDetail(item)
    }
  } catch (error) {
    console.error('Failed to create assessment:', error)
  } finally {
    loading.value = false
  }
}

// 重新评估
const reassess = async (result) => {
  const type = assessmentTypes.find(t => t.id === result.type)
  if (type) await startAssessment(type)
}

// factor 图标
const getFactorIcon = (positive) => {
  if (positive === true) return CheckCircle
  if (positive === false) return XCircle
  return Info
}
const getFactorClass = (positive) => {
  if (positive === true) return 'positive'
  if (positive === false) return 'negative'
  return 'missing'
}

const getRiskColor = (level) => {
  switch (level) {
    case 'low': return 'var(--color-success)'
    case 'medium': return 'var(--color-warning)'
    case 'high': return 'var(--color-danger)'
    default: return 'var(--color-text-tertiary)'
  }
}

const getRiskLabel = (level) => {
  switch (level) {
    case 'low': return '低风险'
    case 'medium': return '中风险'
    case 'high': return '高风险'
    default: return '未评估'
  }
}

const getMissingFields = (result) => {
  return result.details?.missing_fields || []
}

onMounted(() => {
  loadAssessments()
})
</script>

<template>
  <div class="risk-assessment">
    <!-- 评估类型选择 -->
    <section class="assessment-types">
      <h3 class="section-title">选择评估类型</h3>
      <div class="types-grid">
        <div 
          v-for="type in assessmentTypes" 
          :key="type.id"
          class="type-card card"
          @click="startAssessment(type)"
        >
          <div class="type-icon" :style="{ backgroundColor: type.color + '15', color: type.color }">
            <component :is="type.icon" :size="24" />
          </div>
          <div class="type-content">
            <h4>{{ type.name }}</h4>
            <p class="text-sm text-secondary">{{ type.description }}</p>
            <div class="type-factors">
              <span 
                v-for="factor in type.factors.slice(0, 3)" 
                :key="factor"
                class="factor-tag"
              >
                {{ factor }}
              </span>
              <span v-if="type.factors.length > 3" class="factor-more">
                +{{ type.factors.length - 3 }}
              </span>
            </div>
          </div>
          <ChevronRight :size="20" class="type-arrow" />
        </div>
      </div>
    </section>

    <!-- 历史评估结果 -->
    <section class="assessment-results">
      <h3 class="section-title">评估历史</h3>
      <div class="results-list">
        <div 
          v-for="result in assessmentResults" 
          :key="result.id"
          class="result-card card"
        >
          <div class="result-header">
            <div class="result-info">
              <h4>{{ result.name || result.type }}</h4>
              <span class="text-sm text-secondary">{{ result.date }}</span>
            </div>
            <div class="result-score">
              <div 
                class="score-circle"
                :style="{ 
                  '--score-color': getRiskColor(result.riskLevel),
                  '--score-percent': result.score + '%'
                }"
              >
                <span class="score-value">{{ result.score }}</span>
              </div>
              <span 
                :class="['badge', `badge-${result.riskLevel}`]"
              >
                {{ getRiskLabel(result.riskLevel) }}
              </span>
            </div>
          </div>
          
          <!-- 缺失字段提示 -->
          <div v-if="getMissingFields(result).length" class="missing-notice">
            <Info :size="14" />
            <span>以下字段使用默认值，结果仅供参考：{{ getMissingFields(result).join('、') }}</span>
          </div>

          <div class="result-factors">
            <div 
              v-for="factor in (result.factors || []).slice(0, 6)" 
              :key="factor.name"
              class="factor-item"
            >
              <component
                :is="getFactorIcon(factor.positive)"
                :size="16"
                :class="['factor-icon', getFactorClass(factor.positive)]"
              />
              <span>{{ factor.name }}</span>
            </div>
          </div>

          <div class="result-actions">
            <button class="btn btn-ghost" @click="openDetail(result)">
              <FileText :size="16" />
              查看详情
            </button>
            <button class="btn btn-secondary" :disabled="loading" @click="reassess(result)">
              <RefreshCw :size="14" />
              重新评估
            </button>
          </div>
        </div>
      </div>
    </section>

    <!-- 风险说明 -->
    <section class="risk-info">
      <div class="card info-card">
        <AlertTriangle :size="20" class="info-icon" />
        <div class="info-content">
          <h4>重要提示</h4>
          <p class="text-sm text-secondary">
            风险评估结果仅供参考，不能替代专业医疗诊断。如评估结果显示中高风险，建议及时就医进行专业检查。
          </p>
        </div>
      </div>
    </section>

    <!-- 评估详情弹窗 -->
    <div v-if="showDetailModal && selectedResult" class="modal-overlay" @click.self="closeDetail">
      <div class="modal detail-modal">
        <div class="modal-header">
          <h3>{{ selectedResult.name || selectedResult.type }}</h3>
          <button class="btn btn-icon" @click="closeDetail"><X :size="20" /></button>
        </div>
        <div class="modal-body">

          <!-- 评分概览 -->
          <div class="detail-overview">
            <div class="detail-score-wrap">
              <div
                class="score-circle score-lg"
                :style="{
                  '--score-color': getRiskColor(selectedResult.riskLevel),
                  '--score-percent': selectedResult.score + '%'
                }"
              >
                <span class="score-value">{{ selectedResult.score }}</span>
              </div>
              <div>
                <span :class="['badge', `badge-${selectedResult.riskLevel}`]">{{ getRiskLabel(selectedResult.riskLevel) }}</span>
                <p class="text-sm text-secondary" style="margin-top:4px">{{ selectedResult.date }}</p>
              </div>
            </div>

            <!-- 缺失字段提示 -->
            <div v-if="getMissingFields(selectedResult).length" class="detail-missing">
              <Info :size="14" />
              <span>以下字段使用默认值，建议前往健康档案补充：<strong>{{ getMissingFields(selectedResult).join('、') }}</strong></span>
            </div>
          </div>

          <!-- 影响因素 -->
          <div class="detail-section">
            <h4 class="detail-section-title">影响因素</h4>
            <div class="detail-factors">
              <div
                v-for="factor in (selectedResult.factors || [])"
                :key="factor.name"
                :class="['detail-factor-item', getFactorClass(factor.positive)]"
              >
                <div class="detail-factor-header">
                  <component :is="getFactorIcon(factor.positive)" :size="16" :class="['factor-icon', getFactorClass(factor.positive)]" />
                  <span class="detail-factor-name">{{ factor.name }}</span>
                </div>
                <p v-if="factor.detail" class="detail-factor-detail">{{ factor.detail }}</p>
              </div>
            </div>
          </div>

          <!-- 健康建议 -->
          <div class="detail-section">
            <h4 class="detail-section-title">健康建议</h4>
            <ul class="detail-recs">
              <li v-for="(rec, i) in (selectedResult.recommendations || [])" :key="i">
                {{ rec }}
              </li>
            </ul>
          </div>

        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeDetail">关闭</button>
          <button class="btn btn-primary" :disabled="loading" @click="reassess(selectedResult); closeDetail()">
            <RefreshCw :size="14" />
            重新评估
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.risk-assessment {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.section-title {
  margin-bottom: var(--spacing-md);
}

/* Assessment Types */
.types-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--spacing-md);
}

.type-card {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.type-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.type-icon {
  width: 56px;
  height: 56px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.type-content {
  flex: 1;
}

.type-content h4 {
  margin-bottom: 4px;
}

.type-factors {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-xs);
  margin-top: var(--spacing-sm);
}

.factor-tag {
  padding: 2px 8px;
  background-color: var(--color-bg);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
}

.factor-more {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
}

.type-arrow {
  color: var(--color-text-tertiary);
}

/* Results */
.results-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.result-card {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.result-info h4 {
  margin-bottom: 4px;
}

.result-score {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-sm);
}

.score-circle {
  width: 60px;
  height: 60px;
  border-radius: var(--radius-full);
  background: conic-gradient(
    var(--score-color) var(--score-percent),
    var(--color-border) var(--score-percent)
  );
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.score-circle::before {
  content: '';
  position: absolute;
  width: 48px;
  height: 48px;
  background-color: var(--color-surface);
  border-radius: var(--radius-full);
}

.score-value {
  position: relative;
  font-size: var(--font-size-lg);
  font-weight: 600;
}

.result-factors {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--spacing-sm);
  padding: var(--spacing-md);
  background-color: var(--color-bg);
  border-radius: var(--radius-md);
}

.factor-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: var(--font-size-sm);
}

.factor-icon.positive {
  color: var(--color-success);
}

.factor-icon.negative {
  color: var(--color-danger);
}

.factor-icon.missing {
  color: var(--color-warning);
}

.result-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-sm);
  padding-top: var(--spacing-md);
  border-top: 1px solid var(--color-border);
}

/* Missing notice */
.missing-notice {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm) var(--spacing-md);
  background-color: rgba(247, 185, 40, 0.08);
  border: 1px solid rgba(247, 185, 40, 0.3);
  border-radius: var(--radius-md);
  font-size: var(--font-size-xs);
  color: #996600;
  line-height: 1.5;
}

.missing-notice svg {
  flex-shrink: 0;
  margin-top: 1px;
  color: var(--color-warning);
}

/* Modal overlay */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: var(--spacing-md);
}

.modal {
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  width: 100%;
  max-width: 560px;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  box-shadow: var(--shadow-lg);
}

.detail-modal {
  max-width: 600px;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-lg);
  border-bottom: 1px solid var(--color-border);
  flex-shrink: 0;
}

.modal-header h3 {
  font-size: var(--font-size-lg);
  font-weight: 600;
}

.modal-body {
  overflow-y: auto;
  padding: var(--spacing-lg);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-sm);
  padding: var(--spacing-md) var(--spacing-lg);
  border-top: 1px solid var(--color-border);
  flex-shrink: 0;
}

/* Detail overview */
.detail-overview {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.detail-score-wrap {
  display: flex;
  align-items: center;
  gap: var(--spacing-lg);
}

.score-lg {
  width: 80px !important;
  height: 80px !important;
}

.score-lg::before {
  width: 64px !important;
  height: 64px !important;
}

.score-lg .score-value {
  font-size: var(--font-size-xl) !important;
}

.detail-missing {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm) var(--spacing-md);
  background-color: rgba(247, 185, 40, 0.08);
  border: 1px solid rgba(247, 185, 40, 0.3);
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
  color: #996600;
  line-height: 1.5;
}

.detail-missing svg {
  flex-shrink: 0;
  margin-top: 2px;
  color: var(--color-warning);
}

/* Detail sections */
.detail-section-title {
  font-size: var(--font-size-sm);
  font-weight: 600;
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-md);
  padding-bottom: var(--spacing-xs);
  border-bottom: 1px solid var(--color-border);
}

.detail-factors {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.detail-factor-item {
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--radius-md);
  border-left: 3px solid transparent;
}

.detail-factor-item.positive {
  background-color: rgba(52, 199, 89, 0.06);
  border-left-color: var(--color-success);
}

.detail-factor-item.negative {
  background-color: rgba(255, 59, 48, 0.06);
  border-left-color: var(--color-danger);
}

.detail-factor-item.missing {
  background-color: rgba(247, 185, 40, 0.06);
  border-left-color: var(--color-warning);
}

.detail-factor-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.detail-factor-name {
  font-size: var(--font-size-sm);
  font-weight: 500;
}

.detail-factor-detail {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  margin-top: 4px;
  margin-left: 24px;
  line-height: 1.5;
}

/* Recommendations */
.detail-recs {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  padding-left: var(--spacing-lg);
}

.detail-recs li {
  font-size: var(--font-size-sm);
  color: var(--color-text-primary);
  line-height: 1.6;
}

/* Btn styles needed in this component */
.btn {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
  font-weight: 500;
  cursor: pointer;
  border: none;
  transition: all var(--transition-fast);
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-icon {
  padding: var(--spacing-xs);
  background: transparent;
  color: var(--color-text-secondary);
}

.btn-icon:hover {
  background: var(--color-bg);
}

.btn-ghost {
  background: transparent;
  color: var(--color-primary);
}

.btn-ghost:hover {
  background: var(--color-bg);
}

.btn-secondary {
  background: var(--color-bg);
  color: var(--color-text-primary);
  border: 1px solid var(--color-border);
}

.btn-secondary:hover:not(:disabled) {
  background: var(--color-border);
}

.btn-primary {
  background: linear-gradient(135deg, #0866FF, #00C6FF);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(8, 102, 255, 0.35);
}

/* Badges */
.badge {
  padding: 2px 10px;
  border-radius: var(--radius-full);
  font-size: var(--font-size-xs);
  font-weight: 600;
}

.badge-low    { background: rgba(52,199,89,0.15);  color: var(--color-success); }
.badge-medium { background: rgba(247,185,40,0.15); color: #996600; }
.badge-high   { background: rgba(255,59,48,0.15);  color: var(--color-danger); }
.badge-unknown{ background: var(--color-bg);       color: var(--color-text-tertiary); }

/* Info Card */
.info-card {
  display: flex;
  gap: var(--spacing-md);
  background-color: rgba(247, 185, 40, 0.1);
  border: 1px solid rgba(247, 185, 40, 0.3);
}

.info-icon {
  color: var(--color-warning);
  flex-shrink: 0;
}

.info-content h4 {
  margin-bottom: 4px;
  color: #B88A00;
}

/* Responsive */
@media (max-width: 768px) {
  .types-grid {
    grid-template-columns: 1fr;
  }
  
  .result-factors {
    grid-template-columns: 1fr;
  }
}
</style>
