<script setup>
import { ref, onMounted, reactive, computed } from 'vue'
import { 
  User, 
  Calendar, 
  MapPin, 
  Phone,
  Mail,
  Edit3,
  FileText,
  Activity,
  Heart,
  Shield,
  ChevronRight,
  Download,
  Loader2,
  X,
  Save,
  ClipboardList,
  Tag,
  Plus,
  Trash2,
  ExternalLink,
  CheckCircle
} from 'lucide-vue-next'
import api from '../api'

// 图标映射
const iconMap = { Heart, FileText, Activity, Shield }

const loading = ref(true)
const userInfo = ref({})
const healthStats = ref([])
const healthReports = ref([])
const healthTags = ref([])
const healthProfile = ref(null)
const showAllReports = ref(false)
const visibleReports = computed(() =>
  showAllReports.value ? healthReports.value : healthReports.value.slice(0, 5)
)

// 标签管理
const showTagModal = ref(false)
const tagForm = reactive({ name: '', type: 'neutral' })
const savingTag = ref(false)
const editingTag = ref(null) // null=新建, object=编辑中

const openTagModal = (tag = null) => {
  editingTag.value = tag
  tagForm.name = tag ? tag.name : ''
  tagForm.type = tag ? tag.type : 'neutral'
  showTagModal.value = true
}
const closeTagModal = () => { showTagModal.value = false }

const saveTag = async () => {
  if (!tagForm.name.trim()) return
  savingTag.value = true
  try {
    let res
    if (editingTag.value) {
      res = await api.updateTag(editingTag.value.id, tagForm.name.trim(), tagForm.type)
    } else {
      res = await api.addTag(tagForm.name.trim(), tagForm.type)
    }
    if (res.success) {
      const tagsRes = await api.getUserTags()
      if (tagsRes.success) healthTags.value = tagsRes.data
      closeTagModal()
      showToast(editingTag.value ? '标签已更新' : '标签已添加')
    }
  } catch (e) {
    showToast(e.message || '操作失败', 'error')
  } finally {
    savingTag.value = false
  }
}

const deleteTag = async (tag) => {
  if (!confirm(`确认删除标签「${tag.name}」？`)) return
  try {
    const res = await api.deleteTag(tag.id)
    if (res.success) {
      healthTags.value = healthTags.value.filter(t => t.id !== tag.id)
      showToast('标签已删除')
    }
  } catch (e) {
    showToast('删除失败', 'error')
  }
}

// Toast 通知
const toast = ref({ show: false, message: '', type: 'success' })
let toastTimer = null
const showToast = (message, type = 'success') => {
  if (toastTimer) clearTimeout(toastTimer)
  toast.value = { show: true, message, type }
  toastTimer = setTimeout(() => { toast.value.show = false }, 3000)
}

// BMI 实时预览（弹窗内）
const previewBmi = computed(() => {
  const h = parseFloat(profileForm.height)
  const w = parseFloat(profileForm.weight)
  if (h > 0 && w > 0) return (w / ((h / 100) ** 2)).toFixed(1)
  return null
})

// 档案完整度
const profileCompleteness = computed(() => {
  const p = healthProfile.value
  if (!p) return 0
  const fields = [
    p.height, p.weight, p.waist,
    p.systolic_bp, p.diastolic_bp,
    p.total_cholesterol, p.hdl_cholesterol, p.fasting_glucose, p.hba1c,
    p.exercise_frequency, p.alcohol_frequency,
    p.has_diabetes !== null, p.has_hypertension !== null, p.has_heart_disease !== null,
  ]
  const filled = fields.filter(v => v !== null && v !== undefined && v !== '').length
  return Math.round((filled / fields.length) * 100)
})

const completenessColor = computed(() => {
  const p = profileCompleteness.value
  if (p >= 80) return '#31A24C'
  if (p >= 40) return '#F7B928'
  return '#FA383E'
})

// 健康档案编辑
const showProfileModal = ref(false)
const savingProfile = ref(false)
const profileForm = reactive({
  height: '', weight: '', waist: '',
  systolic_bp: '', diastolic_bp: '', on_bp_medication: false,
  total_cholesterol: '', hdl_cholesterol: '', ldl_cholesterol: '',
  triglycerides: '', fasting_glucose: '', hba1c: '',
  is_smoker: false, smoking_years: '',
  alcohol_frequency: 'never',
  exercise_frequency: '1-2/week', exercise_minutes_per_week: '',
  has_diabetes: false, has_hypertension: false, has_heart_disease: false,
  family_diabetes: false, family_heart_disease: false, family_hypertension: false,
  daily_fruit_vegetable: true, high_salt_diet: false,
})

// 编辑相关
const showEditModal = ref(false)
const saving = ref(false)
const editForm = reactive({
  name: '',
  gender: '',
  age: '',
  birthday: '',
  phone: '',
  email: '',
  location: ''
})

// 加载用户数据
const loadUserData = async () => {
  try {
    loading.value = true
    const [userRes, statsRes, tagsRes, reportsRes, profileRes] = await Promise.all([
      api.getUser(),
      api.getUserStats(),
      api.getUserTags(),
      api.getUserReports(),
      api.getHealthProfile().catch(() => null)
    ])
    
    if (userRes.success) userInfo.value = userRes.data
    if (statsRes.success) {
      healthStats.value = statsRes.data.map(s => ({
        ...s,
        icon: iconMap[s.icon] || Activity
      }))
    }
    if (tagsRes.success) healthTags.value = tagsRes.data
    if (reportsRes.success) healthReports.value = reportsRes.data
    if (profileRes?.success) healthProfile.value = profileRes.data
  } catch (error) {
    console.error('Failed to load user data:', error)
  } finally {
    loading.value = false
  }
}

// 打开健康档案编辑弹窗
const openProfileModal = () => {
  const p = healthProfile.value || {}
  Object.keys(profileForm).forEach(k => {
    profileForm[k] = p[k] !== undefined && p[k] !== null ? p[k] : profileForm[k]
  })
  showProfileModal.value = true
}

const closeProfileModal = () => { showProfileModal.value = false }

// 保存健康档案
const saveHealthProfile = async () => {
  savingProfile.value = true
  try {
    const payload = {}
    Object.keys(profileForm).forEach(k => {
      const v = profileForm[k]
      if (v !== '' && v !== null) {
        payload[k] = typeof v === 'string' && !isNaN(v) && v !== '' ? parseFloat(v) : v
      }
    })
    const res = await api.updateHealthProfile(payload)
    if (res.success) {
      healthProfile.value = res.data
      closeProfileModal()
      showToast('健康档案已保存')
      // 后端自动打标后，刷新标签列表
      api.getUserTags().then(r => { if (r.success) healthTags.value = r.data })
    }
  } catch (error) {
    console.error('Failed to save health profile:', error)
    showToast(error.message || '保存失败', 'error')
  } finally {
    savingProfile.value = false
  }
}

// 打开编辑弹窗
const openEditModal = () => {
  // 填充当前数据到表单
  editForm.name = userInfo.value.name || ''
  editForm.gender = userInfo.value.gender || ''
  editForm.age = userInfo.value.age || ''
  editForm.birthday = userInfo.value.birthday || ''
  editForm.phone = userInfo.value.phone || ''
  editForm.email = userInfo.value.email || ''
  editForm.location = userInfo.value.location || ''
  showEditModal.value = true
}

// 关闭编辑弹窗
const closeEditModal = () => {
  showEditModal.value = false
}

// 保存用户信息
const saveUserInfo = async () => {
  saving.value = true
  try {
    const data = {
      name: editForm.name,
      gender: editForm.gender,
      age: editForm.age ? parseInt(editForm.age) : null,
      birthday: editForm.birthday,
      phone: editForm.phone,
      email: editForm.email,
      location: editForm.location
    }
    
    const res = await api.updateUser(data)
    if (res.success) {
      userInfo.value = res.data
      const storedUser = JSON.parse(localStorage.getItem('user') || '{}')
      storedUser.name = res.data.name
      localStorage.setItem('user', JSON.stringify(storedUser))
      closeEditModal()
      showToast('个人资料已更新')
    }
  } catch (error) {
    console.error('Failed to save user info:', error)
    showToast(error.message || '保存失败', 'error')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadUserData()
})
</script>

<template>
  <!-- Toast 通知 -->
  <transition name="toast">
    <div v-if="toast.show" :class="['toast', toast.type]">{{ toast.message }}</div>
  </transition>

  <div class="profile">
    <!-- 用户信息卡片 -->
    <section class="user-section">
      <div class="card user-card">
        <div class="user-header">
          <div class="user-avatar">
            <img :src="userInfo.avatar" :alt="userInfo.name" />
          </div>
          <div class="user-info">
            <h2>{{ userInfo.name }}</h2>
            <div class="user-meta">
              <span>{{ userInfo.gender }}</span>
              <span>•</span>
              <span>{{ userInfo.age }}岁</span>
            </div>
          </div>
          <button class="btn btn-secondary" @click="openEditModal">
            <Edit3 :size="16" />
            编辑资料
          </button>
        </div>
        
        <div class="user-details">
          <div class="detail-item">
            <Calendar :size="16" />
            <span>{{ userInfo.birthday }}</span>
          </div>
          <div class="detail-item">
            <Phone :size="16" />
            <span>{{ userInfo.phone }}</span>
          </div>
          <div class="detail-item">
            <Mail :size="16" />
            <span>{{ userInfo.email }}</span>
          </div>
          <div class="detail-item">
            <MapPin :size="16" />
            <span>{{ userInfo.location }}</span>
          </div>
        </div>
      </div>
    </section>

    <!-- 健康统计 -->
    <section class="stats-section">
      <div class="stats-grid">
        <div 
          v-for="stat in healthStats" 
          :key="stat.label"
          class="stat-card card"
        >
          <div class="stat-icon" :style="{ backgroundColor: stat.color + '15', color: stat.color }">
            <component :is="stat.icon" :size="20" />
          </div>
          <div class="stat-content">
            <span class="stat-value">{{ stat.value }}<small>{{ stat.unit }}</small></span>
            <span class="stat-label">{{ stat.label }}</span>
          </div>
        </div>
      </div>
    </section>

    <!-- 健康标签 -->
    <section class="tags-section">
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">健康标签</h3>
          <button class="btn btn-secondary" @click="openTagModal()">
            <Plus :size="15" />
            添加标签
          </button>
        </div>
        <div class="health-tags">
          <!-- 系统自动标签（只读） -->
          <template v-if="healthTags.some(t => t.source === 'system')">
            <span class="tags-group-label">自动评估</span>
            <span
              v-for="tag in healthTags.filter(t => t.source === 'system')"
              :key="tag.id"
              :class="['health-tag', tag.type]"
              title="系统根据健康档案自动生成"
            >
              {{ tag.name }}
            </span>
          </template>
          <!-- 用户手动标签 -->
          <template v-if="healthTags.some(t => t.source === 'user')">
            <span class="tags-group-label">自定义</span>
            <span
              v-for="tag in healthTags.filter(t => t.source === 'user')"
              :key="tag.id"
              :class="['health-tag', tag.type, 'tag-editable']"
              @click="openTagModal(tag)"
            >
              {{ tag.name }}
              <button class="tag-del" @click.stop="deleteTag(tag)"><X :size="11" /></button>
            </span>
          </template>
          <span v-if="!healthTags.length" class="tags-empty">尚未生成健康标签，请先完善健康档案</span>
        </div>
      </div>
    </section>

    <!-- 健康报告 -->
    <section class="reports-section">
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">健康报告</h3>
          <button v-if="healthReports.length > 5" class="btn btn-ghost" @click="showAllReports = !showAllReports">
            {{ showAllReports ? '收起' : `查看全部 (${healthReports.length})` }}
          </button>
        </div>
        <div v-if="!healthReports.length" class="reports-empty">
          <FileText :size="32" />
          <p>暂无健康报告记录</p>
        </div>
        <div v-else class="reports-list">
          <div
            v-for="report in visibleReports"
            :key="report.id"
            class="report-item"
          >
            <div :class="['report-icon', report.source === 'exam' ? 'icon-exam' : 'icon-system']">
              <FileText :size="18" />
            </div>
            <div class="report-info">
              <span class="report-name">{{ report.name }}</span>
              <span class="report-meta">
                <span :class="['report-type-badge', report.source]">{{ report.type }}</span>
                <span>{{ report.date }}</span>
                <span v-if="report.hospital">· {{ report.hospital }}</span>
              </span>
              <span v-if="report.summary" class="report-summary">{{ report.summary }}</span>
            </div>
            <div class="report-actions">
              <router-link
                v-if="report.source === 'exam'"
                to="/exam-report"
                class="btn btn-icon"
                title="前往体检报告"
              >
                <ExternalLink :size="16" />
              </router-link>
              <CheckCircle v-if="report.source === 'exam' && report.status === 'done'" :size="16" class="report-done-icon" />
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 健康档案 -->
    <section class="health-profile-section">
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">健康档案</h3>
          <button class="btn btn-secondary" @click="openProfileModal">
            <Edit3 :size="16" />
            编辑档案
          </button>
        </div>
        <!-- 完整度进度条 -->
        <div v-if="healthProfile" class="completeness-bar-wrap">
          <div class="completeness-info">
            <span class="completeness-label">档案完整度</span>
            <span class="completeness-pct" :style="{ color: completenessColor }">{{ profileCompleteness }}%</span>
          </div>
          <div class="completeness-track">
            <div
              class="completeness-fill"
              :style="{ width: profileCompleteness + '%', background: completenessColor }"
            />
          </div>
          <p v-if="profileCompleteness < 80" class="completeness-tip">完善更多信息，风险评估结果将更精准</p>
        </div>
        <div v-if="healthProfile" class="profile-grid">
          <div class="profile-group">
            <h4 class="profile-group-title">身体数据</h4>
            <div class="profile-items">
              <div class="profile-item"><span class="pi-label">身高</span><span class="pi-value">{{ healthProfile.height ?? '--' }} cm</span></div>
              <div class="profile-item"><span class="pi-label">体重</span><span class="pi-value">{{ healthProfile.weight ?? '--' }} kg</span></div>
              <div class="profile-item"><span class="pi-label">BMI</span><span class="pi-value">{{ healthProfile.bmi ?? '--' }}</span></div>
              <div class="profile-item"><span class="pi-label">腰围</span><span class="pi-value">{{ healthProfile.waist ?? '--' }} cm</span></div>
              <div class="profile-item"><span class="pi-label">收缩压</span><span class="pi-value">{{ healthProfile.systolic_bp ?? '--' }} mmHg</span></div>
              <div class="profile-item"><span class="pi-label">舒张压</span><span class="pi-value">{{ healthProfile.diastolic_bp ?? '--' }} mmHg</span></div>
            </div>
          </div>
          <div class="profile-group">
            <h4 class="profile-group-title">血液指标</h4>
            <div class="profile-items">
              <div class="profile-item"><span class="pi-label">总胆固醇</span><span class="pi-value">{{ healthProfile.total_cholesterol ?? '--' }} mg/dL</span></div>
              <div class="profile-item"><span class="pi-label">HDL</span><span class="pi-value">{{ healthProfile.hdl_cholesterol ?? '--' }} mg/dL</span></div>
              <div class="profile-item"><span class="pi-label">LDL</span><span class="pi-value">{{ healthProfile.ldl_cholesterol ?? '--' }} mg/dL</span></div>
              <div class="profile-item"><span class="pi-label">甘油三酯</span><span class="pi-value">{{ healthProfile.triglycerides ?? '--' }} mg/dL</span></div>
              <div class="profile-item"><span class="pi-label">空腹血糖</span><span class="pi-value">{{ healthProfile.fasting_glucose ?? '--' }} mmol/L</span></div>
              <div class="profile-item"><span class="pi-label">糖化血红蛋白</span><span class="pi-value">{{ healthProfile.hba1c ?? '--' }} %</span></div>
            </div>
          </div>
          <div class="profile-group">
            <h4 class="profile-group-title">生活习惯</h4>
            <div class="profile-items">
              <div class="profile-item"><span class="pi-label">吸烟</span><span class="pi-value">{{ healthProfile.is_smoker ? '是' : '否' }}</span></div>
              <div class="profile-item"><span class="pi-label">饮酒频率</span><span class="pi-value">{{ { never:'从不', occasional:'偶尔', regular:'经常', heavy:'大量' }[healthProfile.alcohol_frequency] ?? '--' }}</span></div>
              <div class="profile-item"><span class="pi-label">运动频率</span><span class="pi-value">{{ healthProfile.exercise_frequency ?? '--' }}</span></div>
              <div class="profile-item"><span class="pi-label">每周运动</span><span class="pi-value">{{ healthProfile.exercise_minutes_per_week ?? '--' }} 分钟</span></div>
              <div class="profile-item"><span class="pi-label">每日蔬果</span><span class="pi-value">{{ healthProfile.daily_fruit_vegetable ? '是' : '否' }}</span></div>
              <div class="profile-item"><span class="pi-label">高盐饮食</span><span class="pi-value">{{ healthProfile.high_salt_diet ? '是' : '否' }}</span></div>
            </div>
          </div>
          <div class="profile-group">
            <h4 class="profile-group-title">病史</h4>
            <div class="profile-items">
              <div class="profile-item"><span class="pi-label">糖尿病</span><span :class="['pi-value', healthProfile.has_diabetes ? 'pi-risk' : '']">{{ healthProfile.has_diabetes ? '有' : '无' }}</span></div>
              <div class="profile-item"><span class="pi-label">高血压</span><span :class="['pi-value', healthProfile.has_hypertension ? 'pi-risk' : '']">{{ healthProfile.has_hypertension ? '有' : '无' }}</span></div>
              <div class="profile-item"><span class="pi-label">心脏病</span><span :class="['pi-value', healthProfile.has_heart_disease ? 'pi-risk' : '']">{{ healthProfile.has_heart_disease ? '有' : '无' }}</span></div>
              <div class="profile-item"><span class="pi-label">家族糖尿病</span><span :class="['pi-value', healthProfile.family_diabetes ? 'pi-risk' : '']">{{ healthProfile.family_diabetes ? '有' : '无' }}</span></div>
              <div class="profile-item"><span class="pi-label">家族心脏病</span><span :class="['pi-value', healthProfile.family_heart_disease ? 'pi-risk' : '']">{{ healthProfile.family_heart_disease ? '有' : '无' }}</span></div>
              <div class="profile-item"><span class="pi-label">家族高血压</span><span :class="['pi-value', healthProfile.family_hypertension ? 'pi-risk' : '']">{{ healthProfile.family_hypertension ? '有' : '无' }}</span></div>
            </div>
          </div>
        </div>
        <div v-else class="profile-empty">
          <ClipboardList :size="32" class="empty-icon" />
          <p>尚未填写健康档案</p>
          <p class="text-sm text-secondary">完善健康档案后，风险评估模型将使用您的真实数据</p>
          <button class="btn btn-primary" style="margin-top: var(--spacing-md)" @click="openProfileModal">立即填写</button>
        </div>
      </div>
    </section>

    <!-- 隐私设置提示 -->
    <section class="privacy-section">
      <div class="card privacy-card">
        <Shield :size="20" class="privacy-icon" />
        <div class="privacy-content">
          <h4>数据安全</h4>
          <p class="text-sm text-secondary">
            您的健康数据已加密存储，仅您本人可查看。我们严格遵守隐私保护政策。
          </p>
        </div>
        <button class="btn btn-ghost">隐私设置</button>
      </div>
    </section>

    <!-- 健康档案编辑弹窗 -->
    <div v-if="showProfileModal" class="modal-overlay" @click.self="closeProfileModal">
      <div class="modal modal-wide">
        <div class="modal-header">
          <h3>编辑健康档案</h3>
          <button class="btn btn-icon" @click="closeProfileModal"><X :size="20" /></button>
        </div>
        <form class="modal-body" @submit.prevent="saveHealthProfile">

          <!-- 身体数据 -->
          <div class="form-section-title">身体数据</div>
          <div class="form-row">
            <div class="form-group">
              <label>身高 (cm)</label>
              <input v-model="profileForm.height" type="number" placeholder="例：175" step="0.1" />
            </div>
            <div class="form-group">
              <label>体重 (kg)</label>
              <input v-model="profileForm.weight" type="number" placeholder="例：70" step="0.1" />
            </div>
            <div class="form-group">
              <label>腰围 (cm)</label>
              <input v-model="profileForm.waist" type="number" placeholder="例：85" step="0.1" />
            </div>
          </div>
          <div v-if="previewBmi" class="bmi-preview">
            BMI 预估：<strong>{{ previewBmi }}</strong>
            <span :style="{ color: previewBmi < 18.5 ? '#F7B928' : previewBmi <= 24.9 ? '#31A24C' : '#FA383E' }">
              （{{ previewBmi < 18.5 ? '偏低' : previewBmi <= 24.9 ? '正常' : previewBmi <= 27.9 ? '偏高' : '肥胖' }}）
            </span>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>收缩压 (mmHg)</label>
              <input v-model="profileForm.systolic_bp" type="number" placeholder="例：120" />
            </div>
            <div class="form-group">
              <label>舒张压 (mmHg)</label>
              <input v-model="profileForm.diastolic_bp" type="number" placeholder="例：80" />
            </div>
            <div class="form-group">
              <label>服用降压药</label>
              <div class="radio-group">
                <label class="radio-item"><input type="radio" v-model="profileForm.on_bp_medication" :value="false" /><span>否</span></label>
                <label class="radio-item"><input type="radio" v-model="profileForm.on_bp_medication" :value="true" /><span>是</span></label>
              </div>
            </div>
          </div>

          <!-- 血液指标 -->
          <div class="form-section-title">血液指标</div>
          <div class="form-row">
            <div class="form-group">
              <label>总胆固醇 (mg/dL)</label>
              <input v-model="profileForm.total_cholesterol" type="number" placeholder="例：200" step="0.1" />
            </div>
            <div class="form-group">
              <label>HDL (mg/dL)</label>
              <input v-model="profileForm.hdl_cholesterol" type="number" placeholder="例：50" step="0.1" />
            </div>
            <div class="form-group">
              <label>LDL (mg/dL)</label>
              <input v-model="profileForm.ldl_cholesterol" type="number" placeholder="例：130" step="0.1" />
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>甘油三酯 (mg/dL)</label>
              <input v-model="profileForm.triglycerides" type="number" placeholder="例：150" step="0.1" />
            </div>
            <div class="form-group">
              <label>空腹血糖 (mmol/L)</label>
              <input v-model="profileForm.fasting_glucose" type="number" placeholder="例：5.6" step="0.1" />
            </div>
            <div class="form-group">
              <label>糖化血红蛋白 (%)</label>
              <input v-model="profileForm.hba1c" type="number" placeholder="例：5.7" step="0.1" />
            </div>
          </div>

          <!-- 生活习惯 -->
          <div class="form-section-title">生活习惯</div>
          <div class="form-row">
            <div class="form-group">
              <label>吸烟</label>
              <div class="radio-group">
                <label class="radio-item"><input type="radio" v-model="profileForm.is_smoker" :value="false" /><span>否</span></label>
                <label class="radio-item"><input type="radio" v-model="profileForm.is_smoker" :value="true" /><span>是</span></label>
              </div>
            </div>
            <div class="form-group" v-if="profileForm.is_smoker">
              <label>吸烟年数</label>
              <input v-model="profileForm.smoking_years" type="number" placeholder="例：10" />
            </div>
            <div class="form-group">
              <label>饮酒频率</label>
              <select v-model="profileForm.alcohol_frequency">
                <option value="never">从不</option>
                <option value="occasional">偶尔</option>
                <option value="regular">经常</option>
                <option value="heavy">大量</option>
              </select>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>运动频率</label>
              <select v-model="profileForm.exercise_frequency">
                <option value="never">从不</option>
                <option value="1-2/week">每周1-2次</option>
                <option value="3-4/week">每周3-4次</option>
                <option value="daily">每天</option>
              </select>
            </div>
            <div class="form-group">
              <label>每周运动时长 (分钟)</label>
              <input v-model="profileForm.exercise_minutes_per_week" type="number" placeholder="例：90" />
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>每日摄入蔬果</label>
              <div class="radio-group">
                <label class="radio-item"><input type="radio" v-model="profileForm.daily_fruit_vegetable" :value="true" /><span>是</span></label>
                <label class="radio-item"><input type="radio" v-model="profileForm.daily_fruit_vegetable" :value="false" /><span>否</span></label>
              </div>
            </div>
            <div class="form-group">
              <label>高盐饮食</label>
              <div class="radio-group">
                <label class="radio-item"><input type="radio" v-model="profileForm.high_salt_diet" :value="false" /><span>否</span></label>
                <label class="radio-item"><input type="radio" v-model="profileForm.high_salt_diet" :value="true" /><span>是</span></label>
              </div>
            </div>
          </div>

          <!-- 病史 -->
          <div class="form-section-title">病史</div>
          <div class="form-row">
            <div class="form-group">
              <label>糖尿病史</label>
              <div class="radio-group">
                <label class="radio-item"><input type="radio" v-model="profileForm.has_diabetes" :value="false" /><span>无</span></label>
                <label class="radio-item"><input type="radio" v-model="profileForm.has_diabetes" :value="true" /><span>有</span></label>
              </div>
            </div>
            <div class="form-group">
              <label>高血压史</label>
              <div class="radio-group">
                <label class="radio-item"><input type="radio" v-model="profileForm.has_hypertension" :value="false" /><span>无</span></label>
                <label class="radio-item"><input type="radio" v-model="profileForm.has_hypertension" :value="true" /><span>有</span></label>
              </div>
            </div>
            <div class="form-group">
              <label>心脏病史</label>
              <div class="radio-group">
                <label class="radio-item"><input type="radio" v-model="profileForm.has_heart_disease" :value="false" /><span>无</span></label>
                <label class="radio-item"><input type="radio" v-model="profileForm.has_heart_disease" :value="true" /><span>有</span></label>
              </div>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>家族糖尿病史</label>
              <div class="radio-group">
                <label class="radio-item"><input type="radio" v-model="profileForm.family_diabetes" :value="false" /><span>无</span></label>
                <label class="radio-item"><input type="radio" v-model="profileForm.family_diabetes" :value="true" /><span>有</span></label>
              </div>
            </div>
            <div class="form-group">
              <label>家族心脏病史</label>
              <div class="radio-group">
                <label class="radio-item"><input type="radio" v-model="profileForm.family_heart_disease" :value="false" /><span>无</span></label>
                <label class="radio-item"><input type="radio" v-model="profileForm.family_heart_disease" :value="true" /><span>有</span></label>
              </div>
            </div>
            <div class="form-group">
              <label>家族高血压史</label>
              <div class="radio-group">
                <label class="radio-item"><input type="radio" v-model="profileForm.family_hypertension" :value="false" /><span>无</span></label>
                <label class="radio-item"><input type="radio" v-model="profileForm.family_hypertension" :value="true" /><span>有</span></label>
              </div>
            </div>
          </div>

          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="closeProfileModal">取消</button>
            <button type="submit" class="btn btn-primary" :disabled="savingProfile">
              <Loader2 v-if="savingProfile" :size="16" class="spin" />
              <Save v-else :size="16" />
              保存档案
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- 编辑资料弹窗 -->
    <div v-if="showEditModal" class="modal-overlay" @click.self="closeEditModal">
      <div class="modal">
        <div class="modal-header">
          <h3>编辑个人资料</h3>
          <button class="btn btn-icon" @click="closeEditModal">
            <X :size="20" />
          </button>
        </div>
        
        <form class="modal-body" @submit.prevent="saveUserInfo">
          <!-- 姓名 -->
          <div class="form-group">
            <label>姓名</label>
            <div class="input-wrapper">
              <User :size="18" class="input-icon" />
              <input 
                v-model="editForm.name"
                type="text"
                placeholder="请输入姓名"
              />
            </div>
          </div>
          
          <!-- 性别 -->
          <div class="form-group">
            <label>性别</label>
            <div class="radio-group">
              <label class="radio-item">
                <input type="radio" v-model="editForm.gender" value="男" />
                <span>男</span>
              </label>
              <label class="radio-item">
                <input type="radio" v-model="editForm.gender" value="女" />
                <span>女</span>
              </label>
            </div>
          </div>
          
          <!-- 年龄和生日 -->
          <div class="form-row">
            <div class="form-group">
              <label>年龄</label>
              <div class="input-wrapper">
                <input 
                  v-model="editForm.age"
                  type="number"
                  placeholder="年龄"
                  min="1"
                  max="150"
                />
              </div>
            </div>
            <div class="form-group">
              <label>生日</label>
              <div class="input-wrapper">
                <Calendar :size="18" class="input-icon" />
                <input 
                  v-model="editForm.birthday"
                  type="date"
                />
              </div>
            </div>
          </div>
          
          <!-- 手机号 -->
          <div class="form-group">
            <label>手机号</label>
            <div class="input-wrapper">
              <Phone :size="18" class="input-icon" />
              <input 
                v-model="editForm.phone"
                type="tel"
                placeholder="请输入手机号"
              />
            </div>
          </div>
          
          <!-- 邮箱 -->
          <div class="form-group">
            <label>邮箱</label>
            <div class="input-wrapper">
              <Mail :size="18" class="input-icon" />
              <input 
                v-model="editForm.email"
                type="email"
                placeholder="请输入邮箱"
              />
            </div>
          </div>
          
          <!-- 地址 -->
          <div class="form-group">
            <label>所在地</label>
            <div class="input-wrapper">
              <MapPin :size="18" class="input-icon" />
              <input 
                v-model="editForm.location"
                type="text"
                placeholder="请输入所在地"
              />
            </div>
          </div>
          
          <!-- 按钮 -->
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="closeEditModal">
              取消
            </button>
            <button type="submit" class="btn btn-primary" :disabled="saving">
              <Loader2 v-if="saving" :size="16" class="spin" />
              <Save v-else :size="16" />
              保存
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- 标签管理弹窗 -->
    <div v-if="showTagModal" class="modal-overlay" @click.self="closeTagModal">
      <div class="modal modal-sm">
        <div class="modal-header">
          <h3>{{ editingTag ? '编辑标签' : '添加健康标签' }}</h3>
          <button class="btn btn-icon" @click="closeTagModal"><X :size="20" /></button>
        </div>
        <form class="modal-body" @submit.prevent="saveTag">
          <div class="form-group">
            <label>标签名称</label>
            <input v-model="tagForm.name" type="text" placeholder="例：高血压风险、规律运动" maxlength="20" autofocus />
          </div>
          <div class="form-group">
            <label>标签类型</label>
            <div class="tag-type-group">
              <label :class="['tag-type-item', tagForm.type === 'positive' ? 'selected' : '']">
                <input type="radio" v-model="tagForm.type" value="positive" />
                <span class="health-tag positive">积极</span>
              </label>
              <label :class="['tag-type-item', tagForm.type === 'warning' ? 'selected' : '']">
                <input type="radio" v-model="tagForm.type" value="warning" />
                <span class="health-tag warning">警示</span>
              </label>
              <label :class="['tag-type-item', tagForm.type === 'neutral' ? 'selected' : '']">
                <input type="radio" v-model="tagForm.type" value="neutral" />
                <span class="health-tag neutral">中性</span>
              </label>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="closeTagModal">取消</button>
            <button type="submit" class="btn btn-primary" :disabled="savingTag || !tagForm.name.trim()">
              <Loader2 v-if="savingTag" :size="16" class="spin" />
              <Save v-else :size="16" />
              {{ editingTag ? '保存' : '添加' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
.profile {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

/* User Card */
.user-card {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.user-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-lg);
}

.user-avatar {
  width: 80px;
  height: 80px;
  border-radius: var(--radius-full);
  overflow: hidden;
  flex-shrink: 0;
}

.user-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.user-info {
  flex: 1;
}

.user-info h2 {
  margin-bottom: 4px;
}

.user-meta {
  display: flex;
  gap: var(--spacing-sm);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.user-details {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--spacing-md);
  padding-top: var(--spacing-lg);
  border-top: 1px solid var(--color-border);
}

.detail-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

/* Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--spacing-md);
}

.stat-card {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.stat-icon {
  width: 44px;
  height: 44px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-content {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: var(--font-size-xl);
  font-weight: 600;
}

.stat-value small {
  font-size: var(--font-size-sm);
  font-weight: 400;
  color: var(--color-text-tertiary);
  margin-left: 2px;
}

.stat-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

/* Health Tags */
.health-tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
}

.health-tag {
  padding: 6px 12px;
  border-radius: var(--radius-full);
  font-size: var(--font-size-sm);
  font-weight: 500;
}

.health-tag.positive {
  background-color: rgba(49, 162, 76, 0.15);
  color: var(--color-success);
}

.health-tag.warning {
  background-color: rgba(247, 185, 40, 0.15);
  color: #B88A00;
}

.health-tag.neutral {
  background-color: var(--color-bg);
  color: var(--color-text-secondary);
}

.tag-editable {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  transition: opacity var(--transition-fast);
}

.tag-editable:hover {
  opacity: 0.8;
}

.tag-del {
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  line-height: 1;
  color: inherit;
  opacity: 0.5;
  display: flex;
  align-items: center;
}

.tag-del:hover {
  opacity: 1;
}

.tags-empty {
  font-size: var(--font-size-sm);
  color: var(--color-text-tertiary);
}

.tags-group-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--color-text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  align-self: center;
  padding-right: 2px;
}

/* Reports list updated */
.reports-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-xl) 0;
  color: var(--color-text-tertiary);
  font-size: var(--font-size-sm);
}

.report-icon.icon-exam {
  background: rgba(247, 185, 40, 0.12);
  color: #B88A00;
}

.report-icon.icon-system {
  background: rgba(8, 102, 255, 0.1);
  color: var(--color-primary);
}

.report-meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
  margin-top: 2px;
}

.report-type-badge {
  padding: 1px 8px;
  border-radius: var(--radius-full);
  font-size: 11px;
  font-weight: 500;
}

.report-type-badge.exam {
  background: rgba(247, 185, 40, 0.12);
  color: #B88A00;
}

.report-type-badge.system {
  background: rgba(8, 102, 255, 0.1);
  color: var(--color-primary);
}

.report-summary {
  display: block;
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
  margin-top: 3px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 480px;
}

.report-done-icon {
  color: #31A24C;
  flex-shrink: 0;
}

/* Tag type selector */
.tag-type-group {
  display: flex;
  gap: var(--spacing-md);
}

.tag-type-item {
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: 6px 10px;
  border-radius: var(--radius-md);
  border: 2px solid transparent;
  transition: border-color var(--transition-fast);
}

.tag-type-item input[type="radio"] {
  display: none;
}

.tag-type-item.selected {
  border-color: var(--color-primary);
}

/* Small modal */
.modal-sm {
  max-width: 400px;
}

/* Reports List */
.reports-list {
  display: flex;
  flex-direction: column;
}

.report-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-md) 0;
  border-bottom: 1px solid var(--color-border);
}

.report-item:last-child {
  border-bottom: none;
}

.report-icon {
  width: 40px;
  height: 40px;
  background-color: var(--color-bg);
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-primary);
}

.report-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.report-name {
  font-weight: 500;
}

.report-actions {
  display: flex;
  gap: var(--spacing-xs);
}

/* Privacy Card */
.privacy-card {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  background-color: rgba(8, 102, 255, 0.05);
  border: 1px solid rgba(8, 102, 255, 0.2);
}

.privacy-icon {
  color: var(--color-primary);
  flex-shrink: 0;
}

.privacy-content {
  flex: 1;
}

.privacy-content h4 {
  margin-bottom: 4px;
}

/* Responsive */
@media (max-width: 1024px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 640px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .user-header {
    flex-direction: column;
    text-align: center;
  }
  
  .user-details {
    grid-template-columns: 1fr;
  }
  
  .privacy-card {
    flex-direction: column;
    text-align: center;
  }
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
  padding: var(--spacing-lg);
}

.modal {
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  width: 100%;
  max-width: 480px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-lg);
  border-bottom: 1px solid var(--color-border);
}

.modal-header h3 {
  font-size: var(--font-size-lg);
  font-weight: 600;
}

.modal-body {
  padding: var(--spacing-lg);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-sm);
  padding-top: var(--spacing-md);
  border-top: 1px solid var(--color-border);
  margin-top: var(--spacing-sm);
}

/* Form */
.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.form-group label {
  font-size: var(--font-size-sm);
  font-weight: 500;
  color: var(--color-text-secondary);
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-md);
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.input-icon {
  position: absolute;
  left: var(--spacing-md);
  color: var(--color-text-tertiary);
  pointer-events: none;
}

.input-wrapper input {
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-md);
  padding-left: 40px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: var(--font-size-base);
  transition: all var(--transition-fast);
  background: var(--color-bg);
}

.input-wrapper input:not([type="date"]):not([type="number"]) {
  padding-left: 40px;
}

.input-wrapper input[type="number"] {
  padding-left: var(--spacing-md);
}

.input-wrapper input:focus {
  outline: none;
  border-color: var(--color-primary);
  background: white;
  box-shadow: 0 0 0 3px rgba(8, 102, 255, 0.1);
}

.input-wrapper input::placeholder {
  color: var(--color-text-tertiary);
}

/* Radio Group */
.radio-group {
  display: flex;
  gap: var(--spacing-lg);
}

.radio-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  cursor: pointer;
}

.radio-item input[type="radio"] {
  width: 18px;
  height: 18px;
  accent-color: var(--color-primary);
}

.radio-item span {
  font-size: var(--font-size-base);
}

/* Button Primary */
.btn-primary {
  background: linear-gradient(135deg, #0866FF, #00C6FF);
  color: white;
  border: none;
  padding: var(--spacing-sm) var(--spacing-lg);
  border-radius: var(--radius-md);
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(8, 102, 255, 0.4);
}

.btn-primary:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Toast */
.toast {
  position: fixed;
  top: var(--spacing-lg);
  left: 50%;
  transform: translateX(-50%);
  padding: var(--spacing-sm) var(--spacing-xl);
  border-radius: var(--radius-full);
  font-size: var(--font-size-sm);
  font-weight: 500;
  z-index: 9999;
  box-shadow: 0 4px 16px rgba(0,0,0,0.12);
  pointer-events: none;
}

.toast.success {
  background: #31A24C;
  color: white;
}

.toast.error {
  background: #FA383E;
  color: white;
}

.toast-enter-active, .toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from, .toast-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(-12px);
}

/* Completeness Bar */
.completeness-bar-wrap {
  padding: var(--spacing-sm) var(--spacing-lg) var(--spacing-md);
  border-bottom: 1px solid var(--color-border);
}

.completeness-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.completeness-label {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
}

.completeness-pct {
  font-size: var(--font-size-sm);
  font-weight: 600;
}

.completeness-track {
  height: 6px;
  background: var(--color-border);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.completeness-fill {
  height: 100%;
  border-radius: var(--radius-full);
  transition: width 0.6s ease;
}

.completeness-tip {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
  margin-top: 6px;
}

/* BMI Preview */
.bmi-preview {
  background: rgba(8, 102, 255, 0.04);
  border: 1px solid rgba(8, 102, 255, 0.15);
  border-radius: var(--radius-md);
  padding: var(--spacing-sm) var(--spacing-md);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-md);
}

.bmi-preview strong {
  color: var(--color-text-primary);
  font-size: var(--font-size-base);
}

/* Health Profile Section */
.profile-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--spacing-lg);
  margin-top: var(--spacing-md);
}

.profile-group-title {
  font-size: var(--font-size-sm);
  font-weight: 600;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: var(--spacing-sm);
}

.profile-items {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.profile-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 0;
  border-bottom: 1px solid var(--color-border);
  font-size: var(--font-size-sm);
}

.profile-item:last-child {
  border-bottom: none;
}

.pi-label {
  color: var(--color-text-secondary);
}

.pi-value {
  font-weight: 500;
  color: var(--color-text-primary);
}

.pi-risk {
  color: var(--color-danger);
}

.profile-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--spacing-xl) 0;
  gap: var(--spacing-sm);
  color: var(--color-text-secondary);
}

.empty-icon {
  color: var(--color-text-tertiary);
  margin-bottom: var(--spacing-sm);
}

/* Modal Wide */
.modal-wide {
  max-width: 720px;
  width: 90vw;
  max-height: 85vh;
  overflow-y: auto;
}

/* Form Section Title */
.form-section-title {
  font-size: var(--font-size-sm);
  font-weight: 600;
  color: var(--color-primary);
  padding: var(--spacing-sm) 0 var(--spacing-xs);
  border-bottom: 1px solid var(--color-border);
  margin-bottom: var(--spacing-sm);
  margin-top: var(--spacing-md);
}

.form-section-title:first-child {
  margin-top: 0;
}

/* select in form */
.modal-body select {
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background-color: var(--color-surface);
  color: var(--color-text-primary);
  font-size: var(--font-size-base);
  outline: none;
  cursor: pointer;
}

.modal-body select:focus {
  border-color: var(--color-primary);
}

/* plain input (no wrapper) */
.modal-body .form-group > input {
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background-color: var(--color-surface);
  color: var(--color-text-primary);
  font-size: var(--font-size-base);
  outline: none;
  box-sizing: border-box;
}

.modal-body .form-group > input:focus {
  border-color: var(--color-primary);
}

@media (max-width: 480px) {
  .form-row {
    grid-template-columns: 1fr;
  }
  
  .modal {
    margin: var(--spacing-md);
  }

  .profile-grid {
    grid-template-columns: 1fr;
  }
}
</style>
