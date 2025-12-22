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
  Loader2
} from 'lucide-vue-next'
import api from '../api'

const loading = ref(false)
const assessmentResults = ref([])

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
      // 将新评估结果添加到列表顶部
      assessmentResults.value.unshift({
        ...res.data,
        riskLevel: res.data.risk_level
      })
    }
  } catch (error) {
    console.error('Failed to create assessment:', error)
  } finally {
    loading.value = false
  }
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
              <h4>{{ result.type }}</h4>
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
          
          <div class="result-factors">
            <div 
              v-for="factor in result.factors" 
              :key="factor.name"
              class="factor-item"
            >
              <CheckCircle 
                v-if="factor.positive" 
                :size="16" 
                class="factor-icon positive"
              />
              <XCircle 
                v-else 
                :size="16" 
                class="factor-icon negative"
              />
              <span>{{ factor.name }}</span>
            </div>
          </div>

          <div class="result-actions">
            <button class="btn btn-ghost">
              <FileText :size="16" />
              查看详情
            </button>
            <button class="btn btn-secondary">重新评估</button>
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

.result-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-sm);
  padding-top: var(--spacing-md);
  border-top: 1px solid var(--color-border);
}

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
