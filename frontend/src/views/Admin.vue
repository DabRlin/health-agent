<script setup>
import { ref, onMounted } from 'vue'
import {
  Users,
  ToggleLeft,
  ToggleRight,
  KeyRound,
  X,
  Loader2,
  Shield,
} from 'lucide-vue-next'
import api from '../api'

const activeTab = ref('users')
const loading = ref(true)

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


// ==================== 初始化 ====================
const tabs = [
  { id: 'users', name: '用户管理', icon: Users },
]

onMounted(async () => {
  loading.value = true
  await loadUsers()
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
