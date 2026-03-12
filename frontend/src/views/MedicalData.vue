<script setup>
import { ref, onMounted } from 'vue'
import { Search, BookOpen, Database, Loader2, ChevronDown, Tag } from 'lucide-vue-next'
import api from '../api'


// ==================== RAG 检索 ====================
const ragStats = ref({ ready: false, chunk_count: 0 })
const ragSearchQuery = ref('')
const ragSearchLoading = ref(false)
const ragSearchResults = ref([])
const ragSearchDone = ref(false)

const ragSuggestions = ['高血压并发症', '糖尿病诊断', '心脏病预防', '痤疮护理', '甲状腺结节']

const loadRagStats = async () => {
  try {
    const res = await api.adminRagStats()
    if (res.success) ragStats.value = res.data
  } catch (e) { /* 非管理员可能无权限，静默处理 */ }
}

const ragSearch = async () => {
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

const quickSearch = (q) => {
  ragSearchQuery.value = q
  ragSearch()
}

// ==================== 结构化知识库（只读） ====================
const knowledge = ref([])
const knowledgeLoading = ref(false)
const knowledgeFilter = ref('')
const knowledgeSearch = ref('')
const expandedId = ref(null)

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
  disease: '疾病', indicator: '指标参考', diet: '饮食',
  lifestyle: '生活方式', drug: '药物', symptom: '症状',
}

const categoryColors = {
  disease: '#E11D48', indicator: '#2563EB', diet: '#16A34A',
  lifestyle: '#8B5CF6', drug: '#EA580C', symptom: '#CA8A04',
}

const filteredKnowledge = computed(() => {
  let items = knowledge.value
  const q = knowledgeSearch.value.toLowerCase()
  if (q) {
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

const toggleExpand = (id) => {
  expandedId.value = expandedId.value === id ? null : id
}

onMounted(async () => {
  await Promise.all([loadRagStats(), loadKnowledge()])
})
</script>

<template>
  <div class="medical-page">
    <!-- 页头 -->
    <div class="page-header">
      <div class="page-title-row">
        <BookOpen :size="24" class="title-icon" />
        <div>
          <h2>医疗资料</h2>
          <p class="page-subtitle">查阅《默克家庭诊疗手册》语义检索及结构化医学知识库</p>
        </div>
      </div>
    </div>

    <!-- RAG 检索区 -->
    <div class="card rag-card">
      <div class="card-header">
        <div class="card-title-row">
          <Database :size="18" class="section-icon" />
          <div>
            <h3 class="card-title">默克家庭诊疗手册检索</h3>
            <p class="card-subtitle">基于语义向量检索，覆盖 {{ ragStats.chunk_count }} 个文档块</p>
          </div>
        </div>
        <span :class="['status-badge', ragStats.ready ? 'active' : 'inactive']">
          {{ ragStats.ready ? '索引就绪' : '未就绪' }}
        </span>
      </div>

      <div class="search-bar">
        <div class="search-input-wrap">
          <Search :size="16" class="search-icon" />
          <input
            v-model="ragSearchQuery"
            class="search-input"
            placeholder="输入医学问题或关键词，如「高血压治疗方法」..."
            @keydown.enter="ragSearch"
          />
          <button class="search-btn" @click="ragSearch" :disabled="ragSearchLoading || !ragSearchQuery.trim()">
            <Loader2 v-if="ragSearchLoading" :size="16" class="spin" />
            <span v-else>检索</span>
          </button>
        </div>
        <div class="suggestions">
          <span class="suggestions-label">快捷：</span>
          <button
            v-for="q in ragSuggestions"
            :key="q"
            class="suggestion-tag"
            @click="quickSearch(q)"
          >{{ q }}</button>
        </div>
      </div>

      <!-- 检索结果 -->
      <div v-if="ragSearchLoading" class="loading-center">
        <Loader2 :size="24" class="spin" />
        <span>正在语义检索...</span>
      </div>
      <div v-else-if="ragSearchDone">
        <div v-if="!ragSearchResults.length" class="empty-tip">未找到相关内容，请尝试其他关键词</div>
        <div v-else class="rag-results">
          <div v-for="(r, i) in ragSearchResults" :key="i" class="rag-result-card">
            <div class="rag-result-head">
              <span class="rag-result-title">{{ r.title || '（无标题）' }}</span>
              <span class="rag-score" :style="{ opacity: 0.5 + r.score * 0.5 }">
                相关度 {{ (r.score * 100).toFixed(0) }}%
              </span>
            </div>
            <p class="rag-result-text">{{ r.text }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 结构化知识库 -->
    <div class="card knowledge-card">
      <div class="card-header">
        <div class="card-title-row">
          <BookOpen :size="18" class="section-icon" />
          <div>
            <h3 class="card-title">结构化医学知识库</h3>
            <p class="card-subtitle">疾病、指标、药物、饮食等分类知识条目</p>
          </div>
        </div>
        <div class="header-controls">
          <div class="search-input-wrap compact">
            <Search :size="14" class="search-icon" />
            <input v-model="knowledgeSearch" class="search-input" placeholder="搜索标题或关键词..." />
          </div>
          <select v-model="knowledgeFilter" @change="loadKnowledge" class="filter-select">
            <option v-for="opt in categoryOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
          </select>
        </div>
      </div>

      <div v-if="knowledgeLoading" class="loading-center">
        <Loader2 :size="24" class="spin" />
      </div>
      <div v-else class="knowledge-list">
        <div v-if="!filteredKnowledge.length" class="empty-tip">暂无匹配的知识条目</div>
        <div
          v-for="item in filteredKnowledge"
          :key="item.id"
          class="knowledge-item"
          :class="{ expanded: expandedId === item.id }"
          @click="toggleExpand(item.id)"
        >
          <div class="knowledge-item-header">
            <span
              class="category-dot"
              :style="{ background: categoryColors[item.category] || '#9CA3AF' }"
            ></span>
            <span class="knowledge-title">{{ item.title }}</span>
            <span class="category-label" :style="{ color: categoryColors[item.category] || '#9CA3AF' }">
              {{ categoryLabels[item.category] || item.category }}
            </span>
            <div v-if="item.keywords" class="keywords">
              <Tag :size="11" />
              {{ item.keywords }}
            </div>
            <ChevronDown
              :size="14"
              class="expand-icon"
              :style="{ transform: expandedId === item.id ? 'rotate(180deg)' : '' }"
            />
          </div>
          <div v-if="expandedId === item.id" class="knowledge-content" @click.stop>
            <p>{{ item.content }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.medical-page {
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

.page-subtitle {
  margin: 4px 0 0;
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.title-icon { color: var(--color-primary); }


/* Card */
.card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
}

.card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
}

.card-title-row {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.section-icon { color: var(--color-primary); flex-shrink: 0; }

.card-title { margin: 0; font-size: var(--font-size-lg); }

.card-subtitle {
  margin: 3px 0 0;
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.header-controls {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  flex-shrink: 0;
}

/* Status badge */
.status-badge {
  font-size: 12px;
  padding: 3px 10px;
  border-radius: 20px;
  font-weight: 500;
  white-space: nowrap;
}

.status-badge.active { background: #DCFCE7; color: #15803D; }
.status-badge.inactive { background: #FEE2E2; color: #DC2626; }

/* Search bar */
.search-bar {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
}

.search-input-wrap {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 0 var(--spacing-sm);
  transition: border-color var(--transition-fast);
}

.search-input-wrap:focus-within {
  border-color: var(--color-primary);
}

.search-input-wrap.compact {
  padding: 0 8px;
}

.search-icon { color: var(--color-text-tertiary); flex-shrink: 0; }

.search-input {
  flex: 1;
  border: none;
  background: transparent;
  padding: 10px 4px;
  font-size: var(--font-size-sm);
  color: var(--color-text-primary);
  outline: none;
}

.search-input-wrap.compact .search-input {
  padding: 7px 4px;
}

.search-btn {
  padding: 6px 16px;
  background: var(--color-primary);
  color: white;
  border: none;
  border-radius: var(--radius-sm);
  font-size: var(--font-size-sm);
  cursor: pointer;
  white-space: nowrap;
  transition: background var(--transition-fast);
}

.search-btn:hover:not(:disabled) { background: var(--color-primary-hover); }
.search-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.suggestions {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
}

.suggestions-label {
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.suggestion-tag {
  font-size: 12px;
  padding: 3px 10px;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: 20px;
  cursor: pointer;
  color: var(--color-text-secondary);
  transition: all var(--transition-fast);
}

.suggestion-tag:hover {
  background: rgba(8, 102, 255, 0.06);
  border-color: var(--color-primary);
  color: var(--color-primary);
}

/* RAG results */
.rag-results {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.rag-result-card {
  padding: var(--spacing-md);
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
}

.rag-result-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-sm);
  margin-bottom: 8px;
}

.rag-result-title {
  font-size: var(--font-size-sm);
  font-weight: 600;
  color: var(--color-text-primary);
}

.rag-score {
  font-size: 12px;
  color: var(--color-primary);
  font-weight: 500;
  white-space: nowrap;
}

.rag-result-text {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  line-height: 1.6;
  margin: 0;
}

/* Knowledge list */
.knowledge-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.knowledge-item {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  overflow: hidden;
  transition: border-color var(--transition-fast);
  cursor: pointer;
}

.knowledge-item:hover,
.knowledge-item.expanded {
  border-color: var(--color-primary);
}

.knowledge-item-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px var(--spacing-md);
  user-select: none;
}

.category-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.knowledge-title {
  flex: 1;
  font-size: var(--font-size-sm);
  font-weight: 500;
  color: var(--color-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.category-label {
  font-size: 11px;
  font-weight: 500;
  flex-shrink: 0;
}

.keywords {
  display: flex;
  align-items: center;
  gap: 3px;
  font-size: 11px;
  color: var(--color-text-tertiary);
  max-width: 200px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.expand-icon {
  flex-shrink: 0;
  color: var(--color-text-tertiary);
  transition: transform 0.2s;
}

.knowledge-content {
  padding: var(--spacing-md);
  border-top: 1px solid var(--color-border);
  background: var(--color-bg);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  line-height: 1.7;
  cursor: auto;
}

.knowledge-content p { margin: 0; }

/* Loading & empty */
.loading-center {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-xl);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.empty-tip {
  text-align: center;
  padding: var(--spacing-xl);
  color: var(--color-text-tertiary);
  font-size: var(--font-size-sm);
}

.filter-select {
  padding: 6px 10px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg);
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
  cursor: pointer;
}

@keyframes spin { to { transform: rotate(360deg); } }
.spin { animation: spin 1s linear infinite; }
</style>
