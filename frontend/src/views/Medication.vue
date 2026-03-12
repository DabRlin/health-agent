<script setup>
import { ref, computed, onMounted } from 'vue'
import {
  Pill, Plus, Upload, X, ChevronDown, Loader2,
  Bell, Trash2, Clock, AlertTriangle, Package, CheckCircle2
} from 'lucide-vue-next'
import api from '../api'

// ==================== 列表 ====================
const medications = ref([])
const listLoading = ref(false)
const expandedId = ref(null)

const loadList = async () => {
  listLoading.value = true
  try {
    const res = await api.medicationList()
    if (res.success) medications.value = res.data
  } catch (e) {
    console.error('Failed to load medications:', e)
  } finally {
    listLoading.value = false
  }
}

const toggleExpand = (id) => {
  expandedId.value = expandedId.value === id ? null : id
}

const deleteMedication = async (id, name) => {
  if (!confirm(`确定删除「${name}」的用药记录？`)) return
  try {
    await api.medicationDelete(id)
    medications.value = medications.value.filter(m => m.id !== id)
    if (expandedId.value === id) expandedId.value = null
  } catch (e) {
    console.error('Delete failed:', e)
  }
}

// ==================== 上传 & OCR ====================
const showUploadPanel = ref(false)
const uploadStep = ref('idle') // idle | extracting | confirm | saving
const extractedData = ref(null)
const uploadPreview = ref(null)
const uploadBase64 = ref(null)
const uploadMime = ref(null)
const fileInputRef = ref(null)
const extractError = ref('')

const MED_TYPES = [
  { value: 'oral', label: '口服' },
  { value: 'injection', label: '注射' },
  { value: 'topical', label: '外用涂抹' },
  { value: 'patch', label: '贴敷' },
  { value: 'wash', label: '洗剂' },
]

const RELATION_LABELS = {
  before_meal: '饭前', after_meal: '饭后', with_meal: '随餐',
  before_sleep: '睡前', anytime: '不限时'
}

const openUpload = () => {
  showUploadPanel.value = true
  uploadStep.value = 'idle'
  extractedData.value = null
  uploadPreview.value = null
  uploadBase64.value = null
  extractError.value = ''
}

const closeUpload = () => {
  showUploadPanel.value = false
}

const onFileChange = (e) => {
  const file = e.target.files?.[0]
  if (!file) return
  uploadMime.value = file.type
  const reader = new FileReader()
  reader.onload = (ev) => {
    const dataUrl = ev.target.result
    uploadPreview.value = dataUrl
    uploadBase64.value = dataUrl.split(',')[1]
  }
  reader.readAsDataURL(file)
}

const triggerFileInput = () => fileInputRef.value?.click()

const extractInfo = async () => {
  if (!uploadBase64.value) return
  uploadStep.value = 'extracting'
  extractError.value = ''
  try {
    const res = await api.medicationExtract(uploadBase64.value, uploadMime.value)
    if (res.success) {
      extractedData.value = { ...res.data, start_date: new Date().toISOString().slice(0, 10) }
      uploadStep.value = 'confirm'
    } else {
      extractError.value = res.error || '识别失败'
      uploadStep.value = 'idle'
    }
  } catch (e) {
    extractError.value = '识别失败，请检查图片是否清晰'
    uploadStep.value = 'idle'
  }
}

const addReminder = () => {
  extractedData.value.reminders.push({ time: '08:00', relation: 'after_meal', dose: '' })
}

const removeReminder = (i) => {
  extractedData.value.reminders.splice(i, 1)
}

const saveMedication = async () => {
  uploadStep.value = 'saving'
  try {
    const payload = {
      ...extractedData.value,
      image_base64: uploadBase64.value,
      image_mime: uploadMime.value,
    }
    const res = await api.medicationCreate(payload)
    if (res.success) {
      medications.value.unshift(res.data)
      closeUpload()
    }
  } catch (e) {
    console.error('Save failed:', e)
    uploadStep.value = 'confirm'
  }
}

// ==================== 提醒通知 ====================
const notifEnabled = ref(false)
const notifChecking = ref(false)

const requestNotifPermission = async () => {
  if (!('Notification' in window)) return
  notifChecking.value = true
  const perm = await Notification.requestPermission()
  notifEnabled.value = perm === 'granted'
  notifChecking.value = false
  if (perm === 'granted') {
    saveRemindersToStorage()
    startReminderCheck()
  }
}

const saveRemindersToStorage = () => {
  const reminders = []
  medications.value.forEach(med => {
    (med.reminders || []).forEach(r => {
      reminders.push({
        medId: med.id,
        medName: med.name,
        time: r.time,
        dose: r.dose,
        relation: r.relation,
      })
    })
  })
  localStorage.setItem('med_reminders', JSON.stringify(reminders))
}

let reminderTimer = null
const startReminderCheck = () => {
  if (reminderTimer) return
  reminderTimer = setInterval(() => {
    const now = new Date()
    const hhmm = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`
    const reminders = JSON.parse(localStorage.getItem('med_reminders') || '[]')
    reminders.forEach(r => {
      if (r.time === hhmm) {
        const lastKey = `med_notif_${r.medId}_${hhmm}_${now.toDateString()}`
        if (!sessionStorage.getItem(lastKey)) {
          sessionStorage.setItem(lastKey, '1')
          new Notification(`💊 服药提醒：${r.medName}`, {
            body: `${RELATION_LABELS[r.relation] || ''}服用 ${r.dose || ''}`,
            icon: '/favicon.ico',
          })
        }
      }
    })
  }, 30000) // 每30秒检查一次
}

// ==================== 初始化 ====================
onMounted(async () => {
  await loadList()
  if (Notification?.permission === 'granted') {
    notifEnabled.value = true
    saveRemindersToStorage()
    startReminderCheck()
  }
})
</script>

<template>
  <div class="medication-page">
    <!-- 页头 -->
    <div class="page-header">
      <div class="page-title-row">
        <Pill :size="24" class="title-icon" />
        <div>
          <h2>用药管理</h2>
          <p class="page-subtitle">上传药品说明书，AI 自动提取用法信息，支持服药提醒</p>
        </div>
      </div>
      <div class="header-actions">
        <button
          class="notif-btn"
          :class="{ enabled: notifEnabled }"
          @click="requestNotifPermission"
          :disabled="notifChecking || notifEnabled"
          :title="notifEnabled ? '提醒已开启' : '开启服药提醒'"
        >
          <Bell :size="16" />
          {{ notifEnabled ? '提醒已开启' : '开启提醒' }}
        </button>
        <button class="btn btn-primary" @click="openUpload">
          <Plus :size="16" />
          添加药品
        </button>
      </div>
    </div>

    <!-- 药品列表 -->
    <div class="card">
      <div v-if="listLoading" class="loading-center">
        <Loader2 :size="24" class="spin" />
      </div>
      <div v-else-if="!medications.length" class="empty-state">
        <Package :size="48" class="empty-icon" />
        <p>暂无用药记录</p>
        <p class="empty-tip">点击「添加药品」上传说明书，AI 自动识别用法</p>
        <button class="btn btn-primary mt-md" @click="openUpload">
          <Upload :size="16" />
          上传说明书
        </button>
      </div>
      <div v-else class="med-list">
        <div
          v-for="med in medications"
          :key="med.id"
          class="med-item"
          :class="{ expanded: expandedId === med.id }"
        >
          <!-- 折叠头 -->
          <div class="med-header" @click="toggleExpand(med.id)">
            <span class="med-type-dot" :class="med.med_type"></span>
            <div class="med-info">
              <span class="med-name">{{ med.name }}</span>
              <span class="med-type-label">{{ { oral:'口服', injection:'注射', topical:'外用', patch:'贴敷', wash:'洗剂' }[med.med_type] || med.med_type }}</span>
            </div>
            <div class="med-reminders-preview">
              <Clock :size="13" />
              <span v-if="med.reminders?.length">
                {{ med.reminders.map(r => r.time).join(' / ') }}
              </span>
              <span v-else class="text-tertiary">未设置提醒</span>
            </div>
            <button class="btn-icon-sm danger" @click.stop="deleteMedication(med.id, med.name)" title="删除">
              <Trash2 :size="14" />
            </button>
            <ChevronDown
              :size="16"
              class="chevron"
              :style="{ transform: expandedId === med.id ? 'rotate(180deg)' : '' }"
            />
          </div>

          <!-- 展开详情 -->
          <div v-if="expandedId === med.id" class="med-detail" @click.stop>
            <div class="detail-grid">
              <div v-if="med.reminders?.length" class="detail-section">
                <h4 class="detail-label"><Bell :size="14" /> 服药提醒</h4>
                <div class="reminder-tags">
                  <span v-for="(r, i) in med.reminders" :key="i" class="reminder-tag">
                    {{ r.time }} · {{ { before_meal:'饭前', after_meal:'饭后', with_meal:'随餐', before_sleep:'睡前', anytime:'不限' }[r.relation] || r.relation }}
                    <span v-if="r.dose"> · {{ r.dose }}</span>
                  </span>
                </div>
              </div>
              <div v-if="med.raw_instructions" class="detail-section">
                <h4 class="detail-label">用法用量</h4>
                <p class="detail-text">{{ med.raw_instructions }}</p>
              </div>
              <div v-if="med.contraindications" class="detail-section warn">
                <h4 class="detail-label"><AlertTriangle :size="14" /> 禁忌</h4>
                <p class="detail-text">{{ med.contraindications }}</p>
              </div>
              <div v-if="med.side_effects" class="detail-section">
                <h4 class="detail-label">不良反应</h4>
                <p class="detail-text">{{ med.side_effects }}</p>
              </div>
              <div v-if="med.storage" class="detail-section">
                <h4 class="detail-label">储存条件</h4>
                <p class="detail-text">{{ med.storage }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ==================== 上传弹窗 ==================== -->
    <div v-if="showUploadPanel" class="modal-overlay" @click.self="closeUpload">
      <div class="modal">
        <div class="modal-header">
          <h3>添加药品说明书</h3>
          <button class="btn-icon" @click="closeUpload"><X :size="20" /></button>
        </div>

        <!-- Step 1: 上传图片 -->
        <div v-if="uploadStep === 'idle' || uploadStep === 'extracting'" class="modal-body">
          <div
            class="upload-zone"
            :class="{ 'has-image': uploadPreview }"
            @click="triggerFileInput"
          >
            <img v-if="uploadPreview" :src="uploadPreview" class="preview-img" />
            <div v-else class="upload-placeholder">
              <Upload :size="36" class="upload-icon" />
              <p>点击上传药品说明书图片</p>
              <p class="upload-tip">支持 JPG、PNG，建议拍摄清晰平铺照片</p>
            </div>
          </div>
          <input
            ref="fileInputRef"
            type="file"
            accept="image/jpeg,image/png,image/webp"
            style="display:none"
            @change="onFileChange"
          />
          <p v-if="extractError" class="error-tip">{{ extractError }}</p>
        </div>

        <!-- Step 2: 确认提取结果 -->
        <div v-if="uploadStep === 'confirm'" class="modal-body confirm-body">
          <div class="confirm-split">
            <img :src="uploadPreview" class="confirm-img" />
            <div class="confirm-form">
              <div class="form-group">
                <label>药品名称 *</label>
                <input v-model="extractedData.name" class="form-input" />
              </div>
              <div class="form-group">
                <label>剂型</label>
                <select v-model="extractedData.med_type" class="form-select">
                  <option v-for="t in MED_TYPES" :key="t.value" :value="t.value">{{ t.label }}</option>
                </select>
              </div>
              <div class="form-group">
                <label>开始日期</label>
                <input v-model="extractedData.start_date" type="date" class="form-input" />
              </div>
              <div class="form-group">
                <label>疗程天数</label>
                <input v-model.number="extractedData.duration_days" type="number" min="1" class="form-input" placeholder="不填则不限" />
              </div>

              <!-- 提醒时间编辑 -->
              <div class="form-group">
                <label>服药提醒</label>
                <div v-for="(r, i) in extractedData.reminders" :key="i" class="reminder-row">
                  <input v-model="r.time" type="time" class="form-input time-input" />
                  <select v-model="r.relation" class="form-select relation-select">
                    <option value="before_meal">饭前</option>
                    <option value="after_meal">饭后</option>
                    <option value="with_meal">随餐</option>
                    <option value="before_sleep">睡前</option>
                    <option value="anytime">不限</option>
                  </select>
                  <input v-model="r.dose" class="form-input dose-input" placeholder="剂量" />
                  <button class="btn-icon-sm danger" @click="removeReminder(i)"><X :size="12" /></button>
                </div>
                <button class="btn-add-reminder" @click="addReminder">
                  <Plus :size="14" /> 添加提醒
                </button>
              </div>

              <div class="form-group">
                <label>用法用量</label>
                <textarea v-model="extractedData.raw_instructions" class="form-textarea" rows="3" />
              </div>
            </div>
          </div>
        </div>

        <div class="modal-footer">
          <template v-if="uploadStep === 'idle'">
            <button class="btn btn-secondary" @click="closeUpload">取消</button>
            <button class="btn btn-primary" @click="extractInfo" :disabled="!uploadBase64">
              AI 识别说明书
            </button>
          </template>
          <template v-else-if="uploadStep === 'extracting'">
            <div class="extracting-status">
              <Loader2 :size="18" class="spin" />
              正在识别说明书，请稍候...
            </div>
          </template>
          <template v-else-if="uploadStep === 'confirm'">
            <button class="btn btn-secondary" @click="uploadStep = 'idle'">重新上传</button>
            <button class="btn btn-primary" @click="saveMedication" :disabled="!extractedData?.name">
              <CheckCircle2 :size="16" />
              确认保存
            </button>
          </template>
          <template v-else-if="uploadStep === 'saving'">
            <div class="extracting-status">
              <Loader2 :size="18" class="spin" />
              保存中...
            </div>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.medication-page {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--spacing-md);
}

.page-title-row {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.page-title-row h2 { margin: 0; }
.page-subtitle { margin: 4px 0 0; font-size: var(--font-size-sm); color: var(--color-text-secondary); }
.title-icon { color: var(--color-primary); }

.header-actions { display: flex; align-items: center; gap: var(--spacing-sm); flex-shrink: 0; }

.notif-btn {
  display: flex; align-items: center; gap: 6px;
  padding: 8px 14px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: transparent;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
}
.notif-btn:hover:not(:disabled) { border-color: var(--color-primary); color: var(--color-primary); }
.notif-btn.enabled { background: #DCFCE7; border-color: #16A34A; color: #15803D; cursor: default; }

.btn {
  display: flex; align-items: center; gap: 6px;
  padding: 8px 16px; border: none; border-radius: var(--radius-md);
  font-size: var(--font-size-sm); cursor: pointer; transition: all var(--transition-fast);
}
.btn-primary { background: var(--color-primary); color: white; }
.btn-primary:hover:not(:disabled) { background: var(--color-primary-hover); }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-secondary { background: var(--color-bg); border: 1px solid var(--color-border); color: var(--color-text-primary); }

.mt-md { margin-top: var(--spacing-md); }

/* Card */
.card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

/* Empty state */
.empty-state {
  padding: var(--spacing-xl) var(--spacing-lg);
  text-align: center;
  color: var(--color-text-secondary);
}
.empty-icon { color: var(--color-text-tertiary); margin-bottom: var(--spacing-md); }
.empty-tip { font-size: var(--font-size-sm); color: var(--color-text-tertiary); }

/* Med list */
.med-list { display: flex; flex-direction: column; }

.med-item { border-bottom: 1px solid var(--color-border); }
.med-item:last-child { border-bottom: none; }

.med-header {
  display: flex; align-items: center; gap: var(--spacing-sm);
  padding: 14px var(--spacing-md);
  cursor: pointer;
  transition: background var(--transition-fast);
}
.med-header:hover { background: var(--color-bg); }

.med-type-dot {
  width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0;
}
.med-type-dot.oral { background: #2563EB; }
.med-type-dot.injection { background: #DC2626; }
.med-type-dot.topical { background: #16A34A; }
.med-type-dot.patch { background: #8B5CF6; }
.med-type-dot.wash { background: #EA580C; }

.med-info { display: flex; align-items: center; gap: 8px; flex: 1; min-width: 0; }
.med-name { font-size: var(--font-size-sm); font-weight: 600; color: var(--color-text-primary); }
.med-type-label { font-size: 11px; color: var(--color-text-tertiary); padding: 2px 6px; background: var(--color-bg); border-radius: 4px; }

.med-reminders-preview {
  display: flex; align-items: center; gap: 4px;
  font-size: 12px; color: var(--color-text-secondary); flex-shrink: 0;
}

.btn-icon-sm {
  display: flex; align-items: center; justify-content: center;
  width: 26px; height: 26px; border: none; border-radius: 6px;
  background: transparent; cursor: pointer; transition: all var(--transition-fast); flex-shrink: 0;
}
.btn-icon-sm.danger { color: var(--color-text-tertiary); }
.btn-icon-sm.danger:hover { background: #FEE2E2; color: #DC2626; }

.chevron { color: var(--color-text-tertiary); flex-shrink: 0; transition: transform 0.2s; }

.text-tertiary { color: var(--color-text-tertiary); }

/* Detail */
.med-detail {
  padding: var(--spacing-md) var(--spacing-lg);
  background: var(--color-bg);
  border-top: 1px solid var(--color-border);
}

.detail-grid { display: flex; flex-direction: column; gap: var(--spacing-md); }

.detail-section { display: flex; flex-direction: column; gap: 6px; }
.detail-section.warn .detail-label { color: #B45309; }

.detail-label {
  display: flex; align-items: center; gap: 4px;
  font-size: 12px; font-weight: 600; color: var(--color-text-secondary);
  text-transform: uppercase; letter-spacing: 0.5px;
}

.detail-text {
  font-size: var(--font-size-sm); color: var(--color-text-primary);
  line-height: 1.6; margin: 0;
}

.reminder-tags { display: flex; flex-wrap: wrap; gap: 6px; }
.reminder-tag {
  font-size: 12px; padding: 3px 10px;
  background: rgba(8, 102, 255, 0.08); color: var(--color-primary);
  border-radius: 20px; font-weight: 500;
}

/* Modal */
.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.5);
  display: flex; align-items: center; justify-content: center; z-index: 200;
}

.modal {
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  width: 90%; max-width: 760px; max-height: 90vh;
  display: flex; flex-direction: column;
  box-shadow: 0 20px 60px rgba(0,0,0,0.2);
}

.modal-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: var(--spacing-md) var(--spacing-lg);
  border-bottom: 1px solid var(--color-border);
}
.modal-header h3 { margin: 0; }

.btn-icon {
  display: flex; align-items: center; justify-content: center;
  width: 32px; height: 32px; border: none; border-radius: var(--radius-sm);
  background: transparent; cursor: pointer; color: var(--color-text-secondary);
}
.btn-icon:hover { background: var(--color-bg); }

.modal-body { padding: var(--spacing-lg); overflow-y: auto; flex: 1; }

.modal-footer {
  display: flex; align-items: center; justify-content: flex-end; gap: var(--spacing-sm);
  padding: var(--spacing-md) var(--spacing-lg);
  border-top: 1px solid var(--color-border);
}

.extracting-status {
  display: flex; align-items: center; gap: var(--spacing-sm);
  font-size: var(--font-size-sm); color: var(--color-text-secondary);
}

/* Upload zone */
.upload-zone {
  border: 2px dashed var(--color-border);
  border-radius: var(--radius-lg);
  min-height: 200px;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; transition: all var(--transition-fast);
  overflow: hidden;
}
.upload-zone:hover { border-color: var(--color-primary); background: rgba(8,102,255,0.02); }
.upload-zone.has-image { border-style: solid; }

.upload-placeholder { text-align: center; color: var(--color-text-secondary); }
.upload-icon { color: var(--color-text-tertiary); margin-bottom: var(--spacing-sm); }
.upload-tip { font-size: 12px; color: var(--color-text-tertiary); margin-top: 4px; }

.preview-img { max-height: 300px; max-width: 100%; object-fit: contain; }

.error-tip { color: #DC2626; font-size: var(--font-size-sm); margin-top: var(--spacing-sm); }

/* Confirm split layout */
.confirm-split {
  display: grid; grid-template-columns: 200px 1fr; gap: var(--spacing-lg);
}

.confirm-img {
  width: 200px; height: auto; max-height: 400px;
  object-fit: contain; border-radius: var(--radius-md);
  border: 1px solid var(--color-border); align-self: start; position: sticky; top: 0;
}

.confirm-form { display: flex; flex-direction: column; gap: var(--spacing-md); }

.form-group { display: flex; flex-direction: column; gap: 6px; }
.form-group label { font-size: 12px; font-weight: 600; color: var(--color-text-secondary); }

.form-input, .form-select, .form-textarea {
  padding: 8px 10px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg);
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
}
.form-input:focus, .form-select:focus, .form-textarea:focus {
  outline: none; border-color: var(--color-primary);
}
.form-textarea { resize: vertical; }

/* Reminder rows */
.reminder-row {
  display: flex; align-items: center; gap: 6px; margin-bottom: 6px;
}
.time-input { width: 90px; flex-shrink: 0; }
.relation-select { flex: 1; }
.dose-input { width: 80px; flex-shrink: 0; }

.btn-add-reminder {
  display: flex; align-items: center; gap: 4px;
  padding: 5px 12px;
  border: 1px dashed var(--color-border);
  border-radius: var(--radius-md);
  background: transparent;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
  margin-top: 4px;
}
.btn-add-reminder:hover { border-color: var(--color-primary); color: var(--color-primary); }

/* Loading */
.loading-center {
  display: flex; align-items: center; justify-content: center;
  padding: var(--spacing-xl); gap: var(--spacing-sm);
  color: var(--color-text-secondary);
}

@keyframes spin { to { transform: rotate(360deg); } }
.spin { animation: spin 1s linear infinite; }

@media (max-width: 600px) {
  .confirm-split { grid-template-columns: 1fr; }
  .confirm-img { width: 100%; max-height: 180px; position: static; }
}
</style>
