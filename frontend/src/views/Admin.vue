<script setup>
import { ref, onMounted, computed } from 'vue'
import {
  Users,
  BookOpen,
  ToggleLeft,
  ToggleRight,
  KeyRound,
  Plus,
  Pencil,
  Trash2,
  X,
  Search,
  Loader2,
  Shield,
  ChevronDown,
  Database,
  ChevronLeft,
  ChevronRight
} from 'lucide-vue-next'
import api from '../api'

const activeTab = ref('users')
const loading = ref(true)

const switchTab = (id) => {
  activeTab.value = id
  if (id === 'medical' && ragChunks.value.length === 0) {
    loadRagChunks(1)
  }
}

// ==================== 用户管理 ====================
const users = ref([])
const userLoading = ref(false)
const showResetModal = ref(false)
const resetTarget = ref(null)
const resetPassword = ref('')

const loadUsers = async () => {
  userLoading.value = true
  try {
    const res = await api.adminListUsers()
    if (res.success) users.value = res.data
  } catch (e) {
    console.error('Failed to load users:', e)
  } finally {
    userLoading.value = false
  }
}

const handleToggle = async (user) => {
  try {
    await api.adminToggleUser(user.id)
    await loadUsers()
  } catch (e) {
    console.error('Toggle failed:', e)
  }
}

const openResetModal = (user) => {
  resetTarget.value = user
  resetPassword.value = ''
  showResetModal.value = true
}

const submitReset = async () => {
  if (!resetPassword.value || resetPassword.value.length < 6) return
  try {
    await api.adminResetPassword(resetTarget.value.id, resetPassword.value)
    showResetModal.value = false
    resetPassword.value = ''
  } catch (e) {
    console.error('Reset failed:', e)
  }
}

// ==================== 知识库管理 ====================
const knowledge = ref([])
const knowledgeLoading = ref(false)
const knowledgeFilter = ref('')
const searchQuery = ref('')
const showKnowledgeModal = ref(false)
const editingItem = ref(null)
const knowledgeForm = ref({ category: '', subcategory: '', title: '', keywords: '', content: '' })

const categoryOptions = [
  { value: '', label: '全部分类' },
  { value: 'disease', label: '疾病' },
  { value: 'indicator', label: '指标参考' },
  { value: 'diet', label: '饮食' },
  { value: 'lifestyle', label: '生活方式' },
  { value: 'drug', label: '药物' },
  { value: 'symptom', label: '症状' },
]

const categoryLabels = {
  disease: '疾病',
  indicator: '指标参考',
  diet: '饮食',
  lifestyle: '生活方式',
  drug: '药物',
  symptom: '症状',
}

const filteredKnowledge = computed(() => {
  let items = knowledge.value
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    items = items.filter(k =>
      k.title.toLowerCase().includes(q) ||
      (k.keywords || '').toLowerCase().includes(q)
    )
  }
  return items
})

const loadKnowledge = async () => {
  knowledgeLoading.value = true
  try {
    const res = await api.adminListKnowledge(knowledgeFilter.value || undefined)
    if (res.success) knowledge.value = res.data
  } catch (e) {
    console.error('Failed to load knowledge:', e)
  } finally {
    knowledgeLoading.value = false
  }
}

const openCreateModal = () => {
  editingItem.value = null
  knowledgeForm.value = { category: 'disease', subcategory: '', title: '', keywords: '', content: '' }
  showKnowledgeModal.value = true
}

const openEditModal = async (item) => {
  try {
    const res = await api.adminGetKnowledge(item.id)
    if (res.success) {
      editingItem.value = res.data
      knowledgeForm.value = {
        category: res.data.category || '',
        subcategory: res.data.subcategory || '',
        title: res.data.title || '',
        keywords: res.data.keywords || '',
        content: res.data.content || '',
      }
      showKnowledgeModal.value = true
    }
  } catch (e) {
    console.error('Failed to load knowledge item:', e)
  }
}

const submitKnowledge = async () => {
  const form = knowledgeForm.value
  if (!form.title || !form.category || !form.content) return
  try {
    if (editingItem.value) {
      await api.adminUpdateKnowledge(editingItem.value.id, form)
    } else {
      await api.adminCreateKnowledge(form)
    }
    showKnowledgeModal.value = false
    await loadKnowledge()
  } catch (e) {
    console.error('Save failed:', e)
  }
}

const handleDeleteKnowledge = async (item) => {
  if (!confirm(`确定删除「${item.title}」？`)) return
  try {
    await api.adminDeleteKnowledge(item.id)
    await loadKnowledge()
  } catch (e) {
    console.error('Delete failed:', e)
  }
}

// ==================== RAG 知识库 ====================
const ragStats = ref({ ready: false, chunk_count: 0, collection: null })
const ragChunks = ref([])
const ragTotal = ref(0)
const ragPage = ref(1)
const ragPageSize = 20
const ragPages = ref(1)
const ragSearch = ref('')
const ragLoading = ref(false)
const ragSearchQuery = ref('')
const ragSearchLoading = ref(false)
const ragSearchResults = ref([])
const ragSearchDone = ref(false)
const expandedChunk = ref(null)
const ragFullChunks = ref({})

const loadRagStats = async () => {
  try {
    const res = await api.adminRagStats()
    if (res.success) ragStats.value = res.data
  } catch (e) {
    console.error('RAG stats failed:', e)
  }
}

const loadRagChunks = async (page = 1) => {
  ragLoading.value = true
  try {
    const res = await api.adminRagChunks(page, ragPageSize, ragSearch.value)
    if (res.success) {
      ragChunks.value = res.data.chunks
      ragTotal.value = res.data.total
      ragPage.value = res.data.page
      ragPages.value = res.data.pages
    }
  } catch (e) {
    console.error('RAG chunks failed:', e)
  } finally {
    ragLoading.value = false
  }
}

const ragSearchHandle = async () => {
  if (!ragSearchQuery.value.trim()) return
  ragSearchLoading.value = true
  ragSearchResults.value = []
  ragSearchDone.value = false
  try {
    const res = await api.adminRagSearch(ragSearchQuery.value.trim(), 5)
    if (res.success) {
      ragSearchResults.value = res.data.results
      ragSearchDone.value = true
    }
  } catch (e) {
    console.error('RAG search failed:', e)
  } finally {
    ragSearchLoading.value = false
  }
}

const toggleChunk = (idx) => {
  expandedChunk.value = expandedChunk.value === idx ? null : idx
}

const ragSuggestions = [
  '高血压并发症',
  '糖尿病诊断',
  '心脏病预防',
  '药物副作用',
]

const ragQuickSearch = (q) => {
  ragSearchQuery.value = q
  ragSearchHandle()
}

// ==================== 初始化 ====================
const tabs = [
  { id: 'users', name: '用户管理', icon: Users },
  { id: 'medical', name: '医疗资料', icon: BookOpen },
]

onMounted(async () => {
  loading.value = true
  await Promise.all([loadUsers(), loadKnowledge(), loadRagStats()])
  loading.value = false
})
</script>

<template>
  <div class="admin-page">
    <!-- 页头 -->
    <div class="page-header">
      <div class="page-title-row">
        <Shield :size="24" class="title-icon" />
        <h2>管理后台</h2>
      </div>
      <div class="tabs">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          :class="['tab-btn', { active: activeTab === tab.id }]"
          @click="switchTab(tab.id)"
        >
          <component :is="tab.icon" :size="16" />
          {{ tab.name }}
        </button>
      </div>
    </div>

    <!-- ==================== 用户管理 ==================== -->
    <section v-if="activeTab === 'users'" class="section">
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">用户列表</h3>
        </div>
        <div v-if="userLoading" class="loading-box"><Loader2 :size="28" class="spin" /></div>
        <table v-else class="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>用户名</th>
              <th>关联用户</th>
              <th>角色</th>
              <th>状态</th>
              <th>最后登录</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="u in users" :key="u.id">
              <td>{{ u.id }}</td>
              <td class="font-medium">{{ u.username }}</td>
              <td>{{ u.user_name || '--' }}</td>
              <td>
                <span :class="['role-badge', u.role]">{{ u.role === 'admin' ? '管理员' : '普通用户' }}</span>
              </td>
              <td>
                <span :class="['status-badge', u.is_active ? 'active' : 'inactive']">
                  {{ u.is_active ? '正常' : '已禁用' }}
                </span>
              </td>
              <td class="text-secondary">{{ u.last_login ? u.last_login.slice(0, 16).replace('T', ' ') : '--' }}</td>
              <td>
                <div class="action-btns">
                  <button
                    v-if="u.role !== 'admin'"
                    class="btn-sm"
                    :class="u.is_active ? 'btn-warning' : 'btn-success'"
                    @click="handleToggle(u)"
                    :title="u.is_active ? '禁用' : '启用'"
                  >
                    <component :is="u.is_active ? ToggleRight : ToggleLeft" :size="14" />
                    {{ u.is_active ? '禁用' : '启用' }}
                  </button>
                  <button class="btn-sm btn-ghost" @click="openResetModal(u)" title="重置密码">
                    <KeyRound :size="14" />
                    重置密码
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- ==================== 医疗资料 ==================== -->
    <section v-if="activeTab === 'medical'" class="section">

      <!-- RAG 默克手册检索 -->
      <div class="rag-panel card">
        <div class="rag-topbar">
          <div class="rag-topbar-left">
            <Database :size="16" class="rag-stat-icon" />
            <span class="rag-source-name">默克家庭诊疗手册</span>
            <span class="rag-dot">·</span>
            <span class="rag-stat-label">{{ ragStats.chunk_count }} 个文档块</span>
          </div>
          <span :class="['status-badge', ragStats.ready ? 'active' : 'inactive']">
            {{ ragStats.ready ? '索引就绪' : '未就绪' }}
          </span>
        </div>
        <div class="rag-search-section">
          <div class="rag-search-row">
            <span class="rag-search-label">检索测试</span>
            <input
              v-model="ragSearchQuery"
              class="rag-input"
              placeholder="输入查询词..."
              @keydown.enter="ragSearchHandle"
            />
            <button class="rag-search-btn" @click="ragSearchHandle" :disabled="ragSearchLoading">
              <Loader2 v-if="ragSearchLoading" :size="15" class="spin" />
              <Search v-else :size="15" />
            </button>
            <span class="rag-search-divider" />
            <span v-for="q in ragSuggestions" :key="q" class="rag-tag" @click="ragQuickSearch(q)">{{ q }}</span>
          </div>
        </div>
        <div v-if="ragSearchLoading" class="rag-loading"><Loader2 :size="20" class="spin" /></div>
        <div v-else-if="ragSearchDone" class="rag-results-section">
          <div v-if="!ragSearchResults.length" class="rag-empty">未找到相关内容</div>
          <div v-else class="rag-results-grid">
            <div v-for="(r, i) in ragSearchResults" :key="i" class="rag-result-card">
              <div class="rag-result-head">
                <span class="rag-result-title">{{ r.title || '（无标题）' }}</span>
                <span class="rag-score">{{ (r.score * 100).toFixed(0) }}%</span>
              </div>
              <p class="rag-result-text">{{ r.text }}</p>
            </div>
          </div>
        </div>
        <div class="rag-chunk-header">
          <span class="rag-chunk-label">文档块列表</span>
          <div class="rag-filter-row">
            <Search :size="13" class="rag-filter-icon" />
            <input v-model="ragSearch" class="rag-filter-input" placeholder="过滤..." @keydown.enter="loadRagChunks(1)" />
          </div>
        </div>
        <div v-if="ragLoading" class="rag-loading"><Loader2 :size="20" class="spin" /></div>
        <template v-else>
          <div v-if="!ragChunks.length" class="rag-empty">{{ ragStats.ready ? '暂无匹配内容' : 'RAG 索引未就绪' }}</div>
          <div v-for="chunk in ragChunks" :key="chunk.index" class="chunk-item">
            <div class="chunk-row" @click="toggleChunk(chunk.index)">
              <span class="chunk-index">#{{ chunk.index + 1 }}</span>
              <span class="chunk-title">{{ chunk.title }}</span>
              <span class="chunk-length">{{ chunk.length }}字</span>
              <ChevronDown :size="14" class="chunk-chevron" :style="{ transform: expandedChunk === chunk.index ? 'rotate(180deg)' : '' }" />
            </div>
            <div class="chunk-preview" :class="{ expanded: expandedChunk === chunk.index }">
              <p class="chunk-text">{{ chunk.preview }}</p>
            </div>
          </div>
          <div class="rag-pagination">
            <button class="rag-page-btn" :disabled="ragPage <= 1" @click="loadRagChunks(ragPage - 1)"><ChevronLeft :size="14" /></button>
            <span class="rag-page-info">{{ ragPage }} / {{ ragPages }}页 · {{ ragTotal }}条</span>
            <button class="rag-page-btn" :disabled="ragPage >= ragPages" @click="loadRagChunks(ragPage + 1)"><ChevronRight :size="14" /></button>
          </div>
        </template>
      </div>

      <!-- 结构化知识库 -->
      <div class="card" style="margin-top: var(--spacing-lg)">
        <div class="card-header">
          <h3 class="card-title">结构化知识条目</h3>
          <div class="header-actions">
            <div class="search-box">
              <Search :size="16" />
              <input v-model="searchQuery" placeholder="搜索标题或关键词" class="search-input" />
            </div>
            <select v-model="knowledgeFilter" @change="loadKnowledge" class="filter-select">
              <option v-for="opt in categoryOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
            </select>
            <button class="btn btn-primary" @click="openCreateModal">
              <Plus :size="16" />
              新增
            </button>
          </div>
        </div>
        <div v-if="knowledgeLoading" class="loading-box"><Loader2 :size="28" class="spin" /></div>
        <table v-else class="data-table">
          <thead>
            <tr>
              <th style="width:40px">ID</th>
              <th style="width:80px">分类</th>
              <th>标题</th>
              <th>关键词</th>
              <th style="width:120px">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in filteredKnowledge" :key="item.id">
              <td>{{ item.id }}</td>
              <td><span class="category-badge">{{ categoryLabels[item.category] || item.category }}</span></td>
              <td class="font-medium">{{ item.title }}</td>
              <td class="text-secondary text-ellipsis">{{ item.keywords || '--' }}</td>
              <td>
                <div class="action-btns">
                  <button class="btn-sm btn-ghost" @click="openEditModal(item)" title="编辑">
                    <Pencil :size="14" />
                  </button>
                  <button class="btn-sm btn-danger-ghost" @click="handleDeleteKnowledge(item)" title="删除">
                    <Trash2 :size="14" />
                  </button>
                </div>
              </td>
            </tr>
            <tr v-if="!filteredKnowledge.length">
              <td colspan="5" class="empty-row">暂无数据</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>


    <!-- ==================== 重置密码弹窗 ==================== -->
    <div v-if="showResetModal" class="modal-overlay" @click.self="showResetModal = false">
      <div class="modal">
        <div class="modal-header">
          <h3>重置密码 — {{ resetTarget?.username }}</h3>
          <button class="btn-icon" @click="showResetModal = false"><X :size="20" /></button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>新密码（至少6位）</label>
            <input v-model="resetPassword" type="password" class="form-input" placeholder="输入新密码" />
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showResetModal = false">取消</button>
          <button class="btn btn-primary" @click="submitReset" :disabled="resetPassword.length < 6">确认重置</button>
        </div>
      </div>
    </div>

    <!-- ==================== 知识编辑弹窗 ==================== -->
    <div v-if="showKnowledgeModal" class="modal-overlay" @click.self="showKnowledgeModal = false">
      <div class="modal modal-lg">
        <div class="modal-header">
          <h3>{{ editingItem ? '编辑知识条目' : '新增知识条目' }}</h3>
          <button class="btn-icon" @click="showKnowledgeModal = false"><X :size="20" /></button>
        </div>
        <div class="modal-body">
          <div class="form-row">
            <div class="form-group flex-1">
              <label>分类 *</label>
              <select v-model="knowledgeForm.category" class="form-select">
                <option v-for="opt in categoryOptions.slice(1)" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
              </select>
            </div>
            <div class="form-group flex-1">
              <label>子分类</label>
              <input v-model="knowledgeForm.subcategory" class="form-input" placeholder="如 cardiovascular" />
            </div>
          </div>
          <div class="form-group">
            <label>标题 *</label>
            <input v-model="knowledgeForm.title" class="form-input" placeholder="知识条目标题" />
          </div>
          <div class="form-group">
            <label>关键词（逗号分隔）</label>
            <input v-model="knowledgeForm.keywords" class="form-input" placeholder="高血压,血压高,降压" />
          </div>
          <div class="form-group">
            <label>内容 *</label>
            <textarea v-model="knowledgeForm.content" class="form-textarea" rows="8" placeholder="知识内容"></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showKnowledgeModal = false">取消</button>
          <button class="btn btn-primary" @click="submitKnowledge">{{ editingItem ? '保存修改' : '确认新增' }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.admin-page {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.page-header {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.page-title-row {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.page-title-row h2 {
  margin: 0;
}

.title-icon {
  color: var(--color-primary);
}

.tabs {
  display: flex;
  gap: var(--spacing-xs);
  background-color: var(--color-surface);
  padding: var(--spacing-xs);
  border-radius: var(--radius-md);
  width: fit-content;
}

.tab-btn {
  display: flex;
  align-items: center;
  gap: 6px;
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


/* Table */
.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th,
.data-table td {
  padding: 12px 16px;
  text-align: left;
  border-bottom: 1px solid var(--color-border);
  font-size: var(--font-size-sm);
}

.data-table th {
  font-weight: 600;
  color: var(--color-text-secondary);
  background: var(--color-bg);
}

.data-table tbody tr:hover {
  background: var(--color-bg);
}

.font-medium {
  font-weight: 500;
}

.text-secondary {
  color: var(--color-text-secondary);
}

.text-ellipsis {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.empty-row {
  text-align: center !important;
  color: var(--color-text-tertiary);
  padding: var(--spacing-xl) !important;
}

/* Badges */
.role-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: var(--radius-full);
  font-size: var(--font-size-xs);
  font-weight: 500;
}

.role-badge.admin {
  background: rgba(8, 102, 255, 0.1);
  color: #0866FF;
}

.role-badge.user {
  background: var(--color-bg);
  color: var(--color-text-secondary);
}

.status-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: var(--radius-full);
  font-size: var(--font-size-xs);
  font-weight: 500;
}

.status-badge.active {
  background: rgba(49, 162, 76, 0.1);
  color: #31A24C;
}

.status-badge.inactive {
  background: rgba(250, 56, 62, 0.1);
  color: #FA383E;
}

.category-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  font-size: var(--font-size-xs);
  background: rgba(139, 92, 246, 0.1);
  color: #8B5CF6;
}

/* Action buttons */
.action-btns {
  display: flex;
  gap: 6px;
}

.btn-sm {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-xs);
  background: white;
  cursor: pointer;
  transition: all var(--transition-fast);
  white-space: nowrap;
}

.btn-sm:hover {
  background: var(--color-bg);
}

.btn-sm.btn-warning {
  color: #D97706;
  border-color: #FDE68A;
}

.btn-sm.btn-warning:hover {
  background: #FFFBEB;
}

.btn-sm.btn-success {
  color: #31A24C;
  border-color: #BBF7D0;
}

.btn-sm.btn-success:hover {
  background: #F0FDF4;
}

.btn-sm.btn-ghost {
  border-color: transparent;
  color: var(--color-text-secondary);
}

.btn-sm.btn-ghost:hover {
  background: var(--color-bg);
  color: var(--color-text-primary);
}

.btn-sm.btn-danger-ghost {
  border-color: transparent;
  color: var(--color-text-tertiary);
}

.btn-sm.btn-danger-ghost:hover {
  background: #FEF2F2;
  color: #DC2626;
}

/* Header actions */
.header-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.search-box {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-tertiary);
}

.search-input {
  border: none;
  outline: none;
  font-size: var(--font-size-sm);
  width: 160px;
  background: transparent;
}

.filter-select {
  padding: 6px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
  background: white;
  cursor: pointer;
}

/* Loading */
.loading-box {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-xl);
  color: var(--color-text-tertiary);
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
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
  max-width: 420px;
  box-shadow: var(--shadow-lg);
}

.modal-lg {
  max-width: 640px;
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
  font-size: var(--font-size-lg);
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

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-sm);
  padding: var(--spacing-lg);
  border-top: 1px solid var(--color-border);
}

/* Form */
.form-group {
  margin-bottom: var(--spacing-md);
}

.form-group label {
  display: block;
  margin-bottom: var(--spacing-xs);
  font-weight: 500;
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.form-input,
.form-select,
.form-textarea {
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
  transition: border-color var(--transition-fast);
  box-sizing: border-box;
}

.form-input:focus,
.form-select:focus,
.form-textarea:focus {
  outline: none;
  border-color: var(--color-primary);
}

.form-textarea {
  resize: vertical;
  font-family: inherit;
  line-height: 1.6;
}

.form-row {
  display: flex;
  gap: var(--spacing-md);
}

.flex-1 {
  flex: 1;
}

/* ==================== RAG 一体化面板 ==================== */
.rag-panel {
  padding: 0;
  overflow: hidden;
}

/* 顶部信息条 */
.rag-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-bg);
}

.rag-topbar-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.rag-stat-icon { color: #8B5CF6; flex-shrink: 0; }
.rag-source-name { font-weight: 600; font-size: 13px; color: var(--color-text-primary); }
.rag-dot { color: var(--color-text-tertiary); }
.rag-stat-label { font-size: 13px; color: var(--color-text-secondary); }

/* 检索行 */
.rag-search-section {
  padding: 14px 20px;
  border-bottom: 1px solid var(--color-border);
}

.rag-search-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.rag-search-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  flex-shrink: 0;
}

.rag-input {
  width: 220px;
  padding: 6px 10px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: 13px;
  outline: none;
  transition: border-color var(--transition-fast);
}

.rag-input:focus { border-color: var(--color-primary); }

.rag-search-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-primary);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  flex-shrink: 0;
}

.rag-search-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.rag-search-btn:hover:not(:disabled) { opacity: 0.85; }

.rag-search-divider {
  width: 1px;
  height: 18px;
  background: var(--color-border);
  flex-shrink: 0;
}

.rag-tag {
  font-size: 11px;
  padding: 3px 10px;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: 999px;
  color: var(--color-text-secondary);
  cursor: pointer;
  white-space: nowrap;
  transition: all var(--transition-fast);
}

.rag-tag:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

/* 检索结果 */
.rag-results-section {
  padding: 16px 20px;
  border-bottom: 1px solid var(--color-border);
}

.rag-results-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
}

.rag-result-card {
  padding: 12px;
  background: var(--color-bg);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
}

.rag-result-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.rag-result-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.rag-score {
  font-size: 11px;
  font-weight: 600;
  color: #8B5CF6;
  background: rgba(139,92,246,0.08);
  padding: 1px 6px;
  border-radius: 999px;
  flex-shrink: 0;
}

.rag-result-text {
  margin: 0;
  font-size: 12px;
  color: var(--color-text-secondary);
  line-height: 1.7;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.rag-loading {
  display: flex;
  justify-content: center;
  padding: 20px;
  color: var(--color-text-tertiary);
}

.rag-empty {
  font-size: 13px;
  color: var(--color-text-tertiary);
  text-align: center;
  padding: 20px;
}

/* 文档块列表头 */
.rag-chunk-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-bg);
}

.rag-chunk-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.rag-filter-row {
  display: flex;
  align-items: center;
  gap: 4px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 4px 8px;
  background: white;
}

.rag-filter-icon { color: var(--color-text-tertiary); flex-shrink: 0; }

.rag-filter-input {
  border: none;
  outline: none;
  font-size: 12px;
  width: 100px;
  background: transparent;
  color: var(--color-text-primary);
}

/* Chunk 行 */
.chunk-item {
  border-bottom: 1px solid var(--color-border);
}

.chunk-item:last-of-type { border-bottom: none; }

.chunk-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 9px 20px;
  cursor: pointer;
  transition: background var(--transition-fast);
}

.chunk-row:hover { background: var(--color-bg); }

.chunk-index {
  font-size: 11px;
  color: var(--color-text-tertiary);
  flex-shrink: 0;
  width: 32px;
}

.chunk-title {
  flex: 1;
  font-size: 13px;
  color: var(--color-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.chunk-length {
  font-size: 11px;
  color: var(--color-text-tertiary);
  flex-shrink: 0;
}

.chunk-chevron {
  color: var(--color-text-tertiary);
  transition: transform 0.2s ease;
  flex-shrink: 0;
}

.chunk-preview {
  max-height: 0;
  overflow: hidden;
  transition: max-height 0.25s ease;
}

.chunk-preview.expanded { max-height: 400px; overflow-y: auto; }

.chunk-text {
  margin: 0;
  padding: 0 20px 10px 60px;
  font-size: 12px;
  color: var(--color-text-secondary);
  line-height: 1.8;
  white-space: pre-wrap;
}

/* 分页 */
.rag-pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 10px;
  border-top: 1px solid var(--color-border);
}

.rag-page-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: white;
  cursor: pointer;
  color: var(--color-text-secondary);
}

.rag-page-btn:hover:not(:disabled) { background: var(--color-bg); }
.rag-page-btn:disabled { opacity: 0.35; cursor: not-allowed; }

.rag-page-info {
  font-size: 12px;
  color: var(--color-text-secondary);
}

/* Responsive */
@media (max-width: 640px) {
  .header-actions {
    flex-wrap: wrap;
  }
}
</style>
