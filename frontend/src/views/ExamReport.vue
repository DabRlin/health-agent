<script setup>
import { ref, computed, onMounted } from 'vue'
import {
  Upload, FileText, Trash2, ChevronDown, ChevronUp,
  CheckCircle, AlertCircle, Clock, X, Eye
} from 'lucide-vue-next'
import { api } from '@/api'

const reports = ref([])
const loading = ref(true)
const uploading = ref(false)
const uploadError = ref('')
const expandedId = ref(null)
const fileInput = ref(null)
const dragOver = ref(false)

// 加载列表
const loadReports = async () => {
  loading.value = true
  try {
    const res = await api.getExamReports()
    if (res.success) reports.value = res.data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

onMounted(loadReports)

// 状态显示
const statusMap = {
  pending:    { label: '等待处理', color: '#8B5CF6', icon: Clock },
  processing: { label: '解析中…',  color: '#F7B928', icon: Clock },
  done:       { label: '解析完成', color: '#31A24C', icon: CheckCircle },
  failed:     { label: '解析失败', color: '#FA383E', icon: AlertCircle },
}
const getStatus = (s) => statusMap[s] || statusMap.pending

// 展开/收起
const toggle = (id) => {
  expandedId.value = expandedId.value === id ? null : id
}

// 触发文件选择
const triggerUpload = () => fileInput.value?.click()

// 拖拽
const onDragOver = (e) => { e.preventDefault(); dragOver.value = true }
const onDragLeave = () => { dragOver.value = false }
const onDrop = (e) => {
  e.preventDefault()
  dragOver.value = false
  const file = e.dataTransfer.files[0]
  if (file) handleFile(file)
}

// 文件选择回调
const onFileChange = (e) => {
  const file = e.target.files[0]
  if (file) handleFile(file)
  e.target.value = ''
}

// 核心：上传 + 解析
const handleFile = async (file) => {
  const allowed = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'application/pdf']
  if (!allowed.includes(file.type)) {
    uploadError.value = '仅支持 JPG / PNG / WebP / PDF 格式'
    return
  }
  if (file.size > 10 * 1024 * 1024) {
    uploadError.value = '文件大小不能超过 10MB'
    return
  }
  uploadError.value = ''
  uploading.value = true
  try {
    const res = await api.uploadExamReport(file)
    if (res.success) {
      reports.value.unshift(res.data)
      expandedId.value = res.data.id
    }
  } catch (e) {
    uploadError.value = e.message || '上传失败，请重试'
  } finally {
    uploading.value = false
  }
}

// 删除
const deleteReport = async (id) => {
  if (!confirm('确认删除该体检报告？此操作不可恢复。')) return
  try {
    await api.deleteExamReport(id)
    reports.value = reports.value.filter(r => r.id !== id)
    if (expandedId.value === id) expandedId.value = null
  } catch (e) {
    alert('删除失败')
  }
}

// 指标状态色
const itemColor = (status) => {
  if (status === '偏高' || status === '异常') return '#FA383E'
  if (status === '偏低') return '#F7B928'
  if (status === '正常') return '#31A24C'
  return '#8E8E93'
}
</script>

<template>
  <div class="page">
    <!-- 页头 -->
    <div class="page-header">
      <div>
        <h1 class="page-title">体检报告</h1>
        <p class="page-subtitle">上传体检报告，AI 自动识别并解析检查指标</p>
      </div>
    </div>

    <!-- 上传区 -->
    <section class="upload-section">
      <div
        :class="['upload-zone', { dragging: dragOver, disabled: uploading }]"
        @click="triggerUpload"
        @dragover="onDragOver"
        @dragleave="onDragLeave"
        @drop="onDrop"
      >
        <input
          ref="fileInput"
          type="file"
          accept=".jpg,.jpeg,.png,.webp,.pdf"
          class="hidden-input"
          @change="onFileChange"
        />
        <div v-if="uploading" class="upload-state">
          <div class="spinner" />
          <p class="upload-hint">正在上传并解析，请稍候…</p>
        </div>
        <div v-else class="upload-state">
          <div class="upload-icon-wrap">
            <Upload :size="28" />
          </div>
          <p class="upload-label">点击或拖拽文件到此处上传</p>
          <p class="upload-hint">支持 JPG、PNG、WebP、PDF，最大 10MB</p>
        </div>
      </div>
      <p v-if="uploadError" class="upload-error">
        <AlertCircle :size="14" />
        {{ uploadError }}
      </p>
    </section>

    <!-- 报告列表 -->
    <section class="list-section">
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">历史报告</h3>
          <span class="count-badge">{{ reports.length }} 份</span>
        </div>

        <div v-if="loading" class="list-loading">
          <div class="spinner" />
        </div>

        <div v-else-if="!reports.length" class="list-empty">
          <FileText :size="48" />
          <p>暂无体检报告，上传第一份吧</p>
        </div>

        <div v-else class="report-list">
          <div
            v-for="report in reports"
            :key="report.id"
            class="report-item"
          >
            <!-- 报告头 -->
            <div class="report-header" @click="toggle(report.id)">
              <div class="report-meta">
                <FileText :size="18" class="report-file-icon" />
                <div class="report-info">
                  <span class="report-name">{{ report.filename }}</span>
                  <span class="report-sub">
                    {{ report.report_date || '日期未知' }}
                    <template v-if="report.hospital"> · {{ report.hospital }}</template>
                    · 上传于 {{ report.uploaded_at }}
                  </span>
                </div>
              </div>
              <div class="report-actions">
                <span class="status-badge" :style="{ color: getStatus(report.status).color }">
                  <component :is="getStatus(report.status).icon" :size="13" />
                  {{ getStatus(report.status).label }}
                </span>
                <button class="btn-icon" @click.stop="deleteReport(report.id)">
                  <Trash2 :size="15" />
                </button>
                <component
                  :is="expandedId === report.id ? ChevronUp : ChevronDown"
                  :size="16"
                  class="expand-icon"
                />
              </div>
            </div>

            <!-- 展开内容 -->
            <div v-if="expandedId === report.id" class="report-detail">
              <!-- 解析中 / 失败 状态 -->
              <div v-if="report.status === 'processing'" class="detail-state">
                <div class="spinner" />
                <p>AI 正在解析报告，请稍候…</p>
              </div>
              <div v-else-if="report.status === 'failed'" class="detail-state error">
                <AlertCircle :size="24" />
                <p>解析失败，请尝试重新上传更清晰的图片</p>
              </div>

              <!-- 解析结果 -->
              <template v-else-if="report.status === 'done' && report.parsed_data">
                <!-- 总结 -->
                <div v-if="report.parsed_data.summary" class="summary-card">
                  <p>{{ report.parsed_data.summary }}</p>
                </div>

                <!-- 指标表格 -->
                <div v-if="report.parsed_data.items && report.parsed_data.items.length" class="items-table-wrap">
                  <table class="items-table">
                    <thead>
                      <tr>
                        <th>检查项目</th>
                        <th>结果</th>
                        <th>参考范围</th>
                        <th>状态</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="(item, i) in report.parsed_data.items" :key="i">
                        <td>{{ item.name }}</td>
                        <td class="value-cell">
                          {{ item.value }}
                          <span v-if="item.unit" class="unit">{{ item.unit }}</span>
                        </td>
                        <td class="ref-cell">{{ item.reference_range || '—' }}</td>
                        <td>
                          <span class="item-status" :style="{ color: itemColor(item.status) }">
                            {{ item.status || '—' }}
                          </span>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>

                <!-- 原始文字折叠 -->
                <details class="raw-text-details">
                  <summary>查看 OCR 原始文字</summary>
                  <pre class="raw-text">{{ report.raw_text }}</pre>
                </details>
              </template>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
/* ===== Layout ===== */
.page {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}

.page-title {
  font-size: var(--font-size-2xl);
  font-weight: 700;
  color: var(--color-text-primary);
  margin: 0;
}

.page-subtitle {
  font-size: var(--font-size-sm);
  color: var(--color-text-tertiary);
  margin: var(--spacing-xs) 0 0;
}

/* ===== Upload Zone ===== */
.upload-section {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.upload-zone {
  border: 2px dashed var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--spacing-2xl) var(--spacing-lg);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all var(--transition-fast);
  background: var(--color-surface);
}

.upload-zone:hover,
.upload-zone.dragging {
  border-color: var(--color-primary);
  background: rgba(8, 102, 255, 0.03);
}

.upload-zone.disabled {
  pointer-events: none;
  opacity: 0.7;
}

.hidden-input {
  display: none;
}

.upload-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-sm);
}

.upload-icon-wrap {
  width: 56px;
  height: 56px;
  border-radius: var(--radius-full);
  background: rgba(8, 102, 255, 0.08);
  color: var(--color-primary);
  display: flex;
  align-items: center;
  justify-content: center;
}

.upload-label {
  font-size: var(--font-size-base);
  font-weight: 500;
  color: var(--color-text-primary);
  margin: 0;
}

.upload-hint {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
  margin: 0;
}

.upload-error {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: var(--font-size-xs);
  color: #FA383E;
  padding-left: var(--spacing-xs);
}

/* ===== Report List ===== */
.list-section {}

.count-badge {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  padding: 2px 10px;
}

.list-loading,
.list-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-2xl) 0;
  color: var(--color-text-tertiary);
  font-size: var(--font-size-sm);
}

.report-list {
  display: flex;
  flex-direction: column;
}

.report-item {
  border-bottom: 1px solid var(--color-border);
}

.report-item:last-child {
  border-bottom: none;
}

.report-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-md) var(--spacing-lg);
  cursor: pointer;
  transition: background var(--transition-fast);
}

.report-header:hover {
  background: var(--color-bg);
}

.report-meta {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  min-width: 0;
}

.report-file-icon {
  flex-shrink: 0;
  color: var(--color-text-tertiary);
}

.report-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.report-name {
  font-size: var(--font-size-sm);
  font-weight: 500;
  color: var(--color-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.report-sub {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
}

.report-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  flex-shrink: 0;
}

.status-badge {
  display: flex;
  align-items: center;
  gap: 3px;
  font-size: var(--font-size-xs);
  font-weight: 500;
}

.btn-icon {
  background: none;
  border: none;
  color: var(--color-text-tertiary);
  cursor: pointer;
  padding: 4px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  transition: all var(--transition-fast);
}

.btn-icon:hover {
  background: #FEE2E2;
  color: #DC2626;
}

.expand-icon {
  color: var(--color-text-tertiary);
}

/* ===== Report Detail ===== */
.report-detail {
  padding: 0 var(--spacing-lg) var(--spacing-lg);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.detail-state {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  color: var(--color-text-tertiary);
  font-size: var(--font-size-sm);
  padding: var(--spacing-md) 0;
}

.detail-state.error {
  color: #FA383E;
}

.summary-card {
  background: rgba(8, 102, 255, 0.04);
  border-left: 3px solid var(--color-primary);
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
  padding: var(--spacing-sm) var(--spacing-md);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  line-height: 1.6;
}

/* ===== Items Table ===== */
.items-table-wrap {
  overflow-x: auto;
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
}

.items-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--font-size-sm);
}

.items-table th {
  background: var(--color-bg);
  padding: var(--spacing-sm) var(--spacing-md);
  text-align: left;
  font-weight: 500;
  color: var(--color-text-tertiary);
  font-size: var(--font-size-xs);
  border-bottom: 1px solid var(--color-border);
}

.items-table td {
  padding: var(--spacing-sm) var(--spacing-md);
  color: var(--color-text-primary);
  border-bottom: 1px solid var(--color-border);
}

.items-table tr:last-child td {
  border-bottom: none;
}

.items-table tr:hover td {
  background: var(--color-bg);
}

.value-cell {
  font-weight: 500;
}

.unit {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
  margin-left: 2px;
}

.ref-cell {
  color: var(--color-text-tertiary);
  font-size: var(--font-size-xs);
}

.item-status {
  font-weight: 500;
  font-size: var(--font-size-xs);
}

/* ===== Raw Text ===== */
.raw-text-details {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
}

.raw-text-details summary {
  cursor: pointer;
  padding: var(--spacing-xs) 0;
  user-select: none;
}

.raw-text {
  margin-top: var(--spacing-sm);
  padding: var(--spacing-md);
  background: var(--color-bg);
  border-radius: var(--radius-md);
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 300px;
  overflow-y: auto;
  line-height: 1.6;
}

/* ===== Spinner ===== */
.spinner {
  width: 24px;
  height: 24px;
  border: 2px solid var(--color-border);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
