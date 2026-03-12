<script setup>
import { ref, onMounted, nextTick, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Send, Bot, User, Sparkles, AlertCircle, Plus, Trash2, MessageSquare, Pencil, Check, X, ArrowLeft, ImagePlus } from 'lucide-vue-next'
import { marked } from 'marked'
import api from '../api'

const route = useRoute()
const router = useRouter()

const DEPARTMENTS = {
  general:       { name: '全科门诊',  icon: '🏥', color: '#2563EB' },
  cardiology:    { name: '心血管科',  icon: '❤️', color: '#E11D48' },
  endocrinology: { name: '内分泌科',  icon: '🩸', color: '#16A34A' },
  dermatology:   { name: '皮肤科',   icon: '🔬', color: '#EA580C' },
}

const QUICK_QUESTIONS = {
  general:       ['最近经常头痛是什么原因？', '血压偏高应该注意什么？', '如何改善睡眠质量？', '体检报告中血糖偏高怎么办？'],
  cardiology:    ['高血压日常如何管理？', '心率偏快是什么原因？', '血脂异常有哪些风险？', '如何预防冠心病？'],
  endocrinology: ['血糖偏高需要注意什么？', '糖尿病前期如何干预？', '甲状腺结节需要治疗吗？', '如何控制体重和血糖？'],
  dermatology:   ['皮肤出现红疹是什么原因？', '痤疮如何正确护理？', '湿疹反复发作怎么办？', '皮肤瘙痒有哪些常见原因？'],
}

const currentDepartment = computed(() => {
  const id = route.query.department || 'general'
  return { id, ...DEPARTMENTS[id] || DEPARTMENTS.general }
})

// 配置 marked
marked.setOptions({ breaks: true, gfm: true })

const renderMarkdown = (text) => {
  if (!text) return ''
  return marked.parse(text)
}

const inputMessage = ref('')
const isLoading = ref(false)
const conversationId = ref(null)   // null = 当前是未保存的新会话
const messages = ref([])
const messagesArea = ref(null)
const isNewSession = ref(true)     // true = 还没发过消息，会话未写入 DB

// 会话历史
const historyList = ref([])

// 重命名状态
const renamingId = ref(null)
const renameInput = ref('')

const loadHistory = async () => {
  try {
    const res = await api.getConsultationHistory()
    if (res.success) historyList.value = res.data
  } catch (e) {
    console.error('Failed to load history', e)
  }
}

const switchConversation = async (sessionId) => {
  if (sessionId === conversationId.value) return
  cancelRename()
  try {
    const res = await api.getConsultationDetail(sessionId)
    if (res.success) {
      conversationId.value = sessionId
      isNewSession.value = false
      messages.value = res.data.messages.map(m => ({ ...m, time: m.time || '' }))
      // 同步 URL 的 department，使 currentDepartment computed 自动刷新
      const dept = res.data.department || 'general'
      if (route.query.department !== dept) {
        router.replace({ query: { ...route.query, department: dept } })
      }
      scrollToBottom()
      await loadHistory()
    }
  } catch (e) {
    console.error('Failed to switch conversation', e)
  }
}

// 新建会话：跳回科室选择页
const newConversation = () => {
  router.push({ name: 'DepartmentSelect' })
}

// 生成本地欢迎消息（不入库）
const localWelcomeMessage = () => {
  const dept = currentDepartment.value
  const tips = QUICK_QUESTIONS[dept.id] || QUICK_QUESTIONS.general
  const tipsText = tips.map(q => `- ${q}`).join('\n')
  return {
    id: 'local-welcome',
    role: 'assistant',
    content: `您好！我是 HealthAI **${dept.name}**智能助手，很高兴为您服务！\n\n我可以帮您解答如：\n${tipsText}\n\n请问今天有什么可以帮助您的吗？`,
    time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  }
}

const deleteConversation = async (sessionId, e) => {
  e.stopPropagation()
  if (!confirm('确认删除该会话？')) return
  try {
    await api.deleteConsultation(sessionId)
    historyList.value = historyList.value.filter(h => h.session_id !== sessionId)
    if (sessionId === conversationId.value) {
      newConversation()
    }
  } catch (e) {
    console.error('Failed to delete conversation', e)
  }
}

// 重命名
const startRename = (h, e) => {
  e.stopPropagation()
  renamingId.value = h.session_id
  renameInput.value = h.summary || ''
  nextTick(() => {
    const el = document.getElementById(`rename-input-${h.session_id}`)
    if (el) { el.focus(); el.select() }
  })
}

const confirmRename = async (sessionId, e) => {
  e?.stopPropagation()
  const val = renameInput.value.trim()
  if (!val) { cancelRename(); return }
  try {
    await api.renameConsultation(sessionId, val)
    const item = historyList.value.find(h => h.session_id === sessionId)
    if (item) item.summary = val
  } catch (e) {
    console.error('Failed to rename', e)
  }
  cancelRename()
}

const cancelRename = () => {
  renamingId.value = null
  renameInput.value = ''
}

const quickQuestions = computed(() =>
  QUICK_QUESTIONS[currentDepartment.value.id] || QUICK_QUESTIONS.general
)

// 滚动到底部
const scrollToBottom = async () => {
  await nextTick()
  if (messagesArea.value) {
    messagesArea.value.scrollTop = messagesArea.value.scrollHeight
  }
}

// 流式 AI 消息的引用
const streamingMessageIndex = ref(-1)

// 图片上传（皮肤科）
const uploadedImage = ref(null)  // { base64, mime, previewUrl, name }
const imageInputRef = ref(null)
const isDermatology = computed(() => currentDepartment.value.id === 'dermatology')

const handleImageSelect = (e) => {
  const file = e.target.files?.[0]
  if (!file) return
  const ALLOWED = ['image/jpeg', 'image/png', 'image/webp']
  if (!ALLOWED.includes(file.type)) {
    alert('请上传 JPG、PNG 或 WebP 格式的图片')
    return
  }
  if (file.size > 10 * 1024 * 1024) {
    alert('图片不能超过 10MB')
    return
  }
  const reader = new FileReader()
  reader.onload = (ev) => {
    const dataUrl = ev.target.result
    // dataUrl = "data:image/jpeg;base64,xxxxx"
    const [header, base64] = dataUrl.split(',')
    const mime = header.match(/:(.*?);/)[1]
    uploadedImage.value = {
      base64,
      mime,
      previewUrl: dataUrl,
      name: file.name,
    }
  }
  reader.readAsDataURL(file)
  // 清空 input，允许重复选择同一文件
  e.target.value = ''
}

const clearImage = () => {
  uploadedImage.value = null
}

// 发送消息（流式模式）
const sendMessage = async () => {
  if (!inputMessage.value.trim() || isLoading.value) return

  const userContent = inputMessage.value.trim()
  inputMessage.value = ''
  isLoading.value = true

  // 懒创建：第一条消息时才调后端 /start 建立会话
  if (isNewSession.value) {
    try {
      const res = await api.startConsultation(currentDepartment.value.id)
      if (res.success) {
        conversationId.value = res.data.conversation_id
        messages.value = res.data.messages
      }
    } catch (error) {
      console.error('Failed to start consultation:', error)
    }
    isNewSession.value = false
  }

  // 拿出图片信息（发送后清空）
  const imgBase64 = uploadedImage.value?.base64 || null
  const imgMime = uploadedImage.value?.mime || null
  const imgPreview = uploadedImage.value?.previewUrl || null
  clearImage()

  // 先显示用户消息
  messages.value.push({
    id: messages.value.length + 1,
    role: 'user',
    content: userContent,
    image: imgPreview,  // 图片预览展示
    time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  })
  scrollToBottom()

  // 创建空的 AI 消息占位
  const aiMessageId = messages.value.length + 1
  messages.value.push({
    id: aiMessageId,
    role: 'assistant',
    content: '',
    time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
    isStreaming: true,
    thinkingText: ''
  })
  streamingMessageIndex.value = messages.value.length - 1
  scrollToBottom()

  const isFirstMessage = historyList.value.every(h => h.session_id !== conversationId.value)

  try {
    await api.sendMessageStream(
      conversationId.value,
      userContent,
      (chunk) => {
        if (streamingMessageIndex.value >= 0) {
          messages.value[streamingMessageIndex.value].thinkingText = ''
          messages.value[streamingMessageIndex.value].content += chunk
          scrollToBottom()
        }
      },
      async () => {
        if (streamingMessageIndex.value >= 0) {
          messages.value[streamingMessageIndex.value].isStreaming = false
          messages.value[streamingMessageIndex.value].thinkingText = ''
        }
        streamingMessageIndex.value = -1
        isLoading.value = false
        await loadHistory()
      },
      (error) => {
        console.error('Stream error:', error)
        if (streamingMessageIndex.value >= 0) {
          messages.value[streamingMessageIndex.value].content = '抱歉，服务暂时不可用，请稍后再试。'
          messages.value[streamingMessageIndex.value].isStreaming = false
          messages.value[streamingMessageIndex.value].thinkingText = ''
        }
        streamingMessageIndex.value = -1
        isLoading.value = false
      },
      (text) => {
        if (streamingMessageIndex.value >= 0) {
          messages.value[streamingMessageIndex.value].thinkingText = text
          scrollToBottom()
        }
      },
      imgBase64,
      imgMime,
    )
  } catch (error) {
    console.error('Failed to send message:', error)
    if (streamingMessageIndex.value >= 0) {
      messages.value[streamingMessageIndex.value].content = '抱歉，服务暂时不可用，请稍后再试。'
      messages.value[streamingMessageIndex.value].isStreaming = false
    }
    streamingMessageIndex.value = -1
    isLoading.value = false
  }
}

const askQuickQuestion = (question) => {
  inputMessage.value = question
  sendMessage()
}

onMounted(async () => {
  // 只加载历史列表，不创建空会话
  messages.value = [localWelcomeMessage()]
  await loadHistory()
})
</script>

<template>
  <div class="consultation">
    <div class="chat-container">
      <!-- 聊天区域 -->
      <div class="chat-main">
        <!-- 消息列表 -->
        <div class="messages-area" ref="messagesArea">
          <div 
            v-for="message in messages" 
            :key="message.id"
            :class="['message', message.role]"
          >
            <div class="message-avatar">
              <Bot v-if="message.role === 'assistant'" :size="20" />
              <User v-else :size="20" />
            </div>
            <div class="message-content">
              <div v-if="message.thinkingText && !message.content" class="message-bubble thinking-bubble">
                <span class="thinking-label">正在调用工具链</span>
                <span class="dot"></span>
                <span class="dot"></span>
                <span class="dot"></span>
              </div>
              <div v-else class="message-bubble">
                <img v-if="message.image" :src="message.image" class="msg-image" alt="上传的皮肤图片" />
                <div class="markdown-body" v-html="renderMarkdown(message.content)"></div>
                <span v-if="message.isStreaming && message.content" class="cursor-blink">|</span>
              </div>
              <span class="message-time">{{ message.time }}</span>
            </div>
          </div>
          
          <!-- 加载中（仅在等待首个 chunk 时显示） -->
          <div v-if="isLoading && streamingMessageIndex === -1" class="message assistant">
            <div class="message-avatar">
              <Bot :size="20" />
            </div>
            <div class="message-content">
              <div class="message-bubble loading">
                <span class="dot"></span>
                <span class="dot"></span>
                <span class="dot"></span>
              </div>
            </div>
          </div>
        </div>

        <!-- 输入区域 -->
        <div class="input-area">
          <!-- 皮肤科图片预览条 -->
          <div v-if="uploadedImage" class="image-preview-bar">
            <img :src="uploadedImage.previewUrl" class="preview-thumb" alt="预览" />
            <span class="preview-name">{{ uploadedImage.name }}</span>
            <button class="preview-remove" @click="clearImage" title="移除图片">
              <X :size="14" />
            </button>
          </div>

          <div class="input-wrapper">
            <!-- 皮肤科图片上传按鈕 -->
            <template v-if="isDermatology">
              <input
                ref="imageInputRef"
                type="file"
                accept="image/jpeg,image/png,image/webp"
                style="display:none"
                @change="handleImageSelect"
              />
              <button
                class="img-upload-btn"
                :class="{ 'has-image': uploadedImage }"
                @click="imageInputRef.click()"
                title="上传皮肤图片"
                :disabled="isLoading"
              >
                <ImagePlus :size="20" />
              </button>
            </template>

            <textarea
              v-model="inputMessage"
              class="chat-input"
              :placeholder="isDermatology ? '描述皮肤症状，可上传图片辅助分析...' : '描述您的症状或健康问题...'"
              rows="1"
              @keydown.enter.exact.prevent="sendMessage"
            ></textarea>
            <button 
              class="send-btn" 
              :disabled="(!inputMessage.trim() && !uploadedImage) || isLoading"
              @click="sendMessage"
            >
              <Send :size="20" />
            </button>
          </div>
          <p class="input-hint">
            <AlertCircle :size="14" />
            <span v-if="isDermatology">AI 分析仅供参考，皮肤诊断请就诊皮肤科医生</span>
            <span v-else>AI 建议仅供参考，不能替代专业医疗诊断</span>
          </p>
        </div>
      </div>

      <!-- 侧边栏 -->
      <aside class="chat-sidebar">
        <!-- 当前科室 badge -->
        <div class="dept-badge" :style="{ '--dept-color': currentDepartment.color }">
          <span class="dept-icon">{{ currentDepartment.icon }}</span>
          <span class="dept-name-text">{{ currentDepartment.name }}</span>
          <button class="dept-change-btn" @click="router.push({ name: 'DepartmentSelect' })" title="切换科室">
            <ArrowLeft :size="12" /> 切换
          </button>
        </div>

        <!-- 会话历史 -->
        <div class="sidebar-section history-section">
          <div class="history-header">
            <h4><MessageSquare :size="14" />会话历史</h4>
            <button class="btn-new-chat" @click="newConversation" title="新建会话">
              <Plus :size="14" />
            </button>
          </div>
          <div class="history-list">
            <div
              v-for="h in historyList"
              :key="h.session_id"
              :class="['history-item', { active: h.session_id === conversationId }]"
              @click="switchConversation(h.session_id)"
            >
              <!-- 重命名编辑态 -->
              <template v-if="renamingId === h.session_id">
                <input
                  :id="`rename-input-${h.session_id}`"
                  v-model="renameInput"
                  class="rename-input"
                  maxlength="30"
                  @click.stop
                  @keydown.enter.prevent="confirmRename(h.session_id, $event)"
                  @keydown.esc.prevent="cancelRename"
                />
                <button class="history-action confirm" @click.stop="confirmRename(h.session_id, $event)" title="确认">
                  <Check :size="11" />
                </button>
                <button class="history-action cancel" @click.stop="cancelRename" title="取消">
                  <X :size="11" />
                </button>
              </template>
              <!-- 正常展示态 -->
              <template v-else>
                <span class="history-title">{{ h.summary || '健康咨询' }}</span>
                <span v-if="h.department_name" class="history-dept-tag">{{ h.department_name }}</span>
                <span class="history-date">{{ h.date }}</span>
                <button class="history-action rename" @click="startRename(h, $event)" title="重命名">
                  <Pencil :size="11" />
                </button>
                <button class="history-action del" @click="deleteConversation(h.session_id, $event)" title="删除">
                  <Trash2 :size="11" />
                </button>
              </template>
            </div>
            <div v-if="!historyList.length" class="history-empty">暂无历史会话</div>
          </div>
        </div>

        <div class="sidebar-section">
          <h4>
            <Sparkles :size="16" />
            快捷提问
          </h4>
          <div class="quick-questions">
            <button 
              v-for="question in quickQuestions" 
              :key="question"
              class="quick-btn"
              @click="askQuickQuestion(question)"
            >
              {{ question }}
            </button>
          </div>
        </div>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.consultation {
  height: calc(100vh - 140px);
}

.chat-container {
  display: flex;
  gap: var(--spacing-lg);
  height: 100%;
}

/* Chat Main */
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background-color: var(--color-surface);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.messages-area {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-lg);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

/* Messages */
.message {
  display: flex;
  gap: var(--spacing-sm);
  max-width: 80%;
}

.message.user {
  flex-direction: row-reverse;
  align-self: flex-end;
}

.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-full);
  background-color: var(--color-bg);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: var(--color-text-secondary);
}

.message.assistant .message-avatar {
  background-color: var(--color-primary);
  color: white;
}

.message-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.message.user .message-content {
  align-items: flex-end;
}

.message-bubble {
  padding: var(--spacing-md);
  border-radius: var(--radius-lg);
  background-color: var(--color-bg);
  line-height: 1.6;
}

.message.user .message-bubble {
  background-color: var(--color-primary);
  color: white;
}

.message-bubble p {
  color: inherit;
}

/* Markdown 渲染样式（用 :deep() 穿透 v-html） */
.markdown-body :deep(p) {
  margin: 0 0 8px;
  color: inherit;
}

.markdown-body :deep(p:last-child) {
  margin-bottom: 0;
}

.markdown-body :deep(strong) {
  font-weight: 600;
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  margin: 6px 0 8px;
  padding-left: 20px;
}

.markdown-body :deep(li) {
  margin-bottom: 4px;
  color: inherit;
}

.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3) {
  margin: 12px 0 6px;
  font-weight: 600;
  color: inherit;
}

.markdown-body :deep(h1) { font-size: 1.1em; }
.markdown-body :deep(h2) { font-size: 1.05em; }
.markdown-body :deep(h3) { font-size: 1em; }

.markdown-body :deep(code) {
  background: rgba(0, 0, 0, 0.06);
  padding: 1px 5px;
  border-radius: 3px;
  font-size: 0.9em;
  font-family: monospace;
}

.markdown-body :deep(pre) {
  background: rgba(0, 0, 0, 0.06);
  padding: 10px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 8px 0;
}

.markdown-body :deep(pre code) {
  background: none;
  padding: 0;
}

.markdown-body :deep(blockquote) {
  border-left: 3px solid var(--color-border);
  margin: 8px 0;
  padding: 4px 12px;
  color: var(--color-text-secondary);
}

.markdown-body :deep(hr) {
  border: none;
  border-top: 1px solid var(--color-border);
  margin: 10px 0;
}

/* 用户消息气泡内 Markdown 颜色覆盖 */
.message.user .markdown-body :deep(p),
.message.user .markdown-body :deep(li),
.message.user .markdown-body :deep(h1),
.message.user .markdown-body :deep(h2),
.message.user .markdown-body :deep(h3),
.message.user .markdown-body :deep(strong) {
  color: white;
}

.message.user .markdown-body :deep(code) {
  background: rgba(255, 255, 255, 0.2);
  color: white;
}

.message.user .markdown-body :deep(blockquote) {
  border-left-color: rgba(255, 255, 255, 0.5);
  color: rgba(255, 255, 255, 0.85);
}

.message-time {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
}

/* Thinking State */
.thinking-bubble {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: var(--spacing-md) var(--spacing-lg);
}

.thinking-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin-right: 2px;
}

/* Loading Animation */
.message-bubble.loading {
  display: flex;
  gap: 4px;
  padding: var(--spacing-md) var(--spacing-lg);
}

.dot {
  width: 8px;
  height: 8px;
  background-color: var(--color-text-tertiary);
  border-radius: var(--radius-full);
  animation: bounce 1.4s infinite ease-in-out both;
}

.dot:nth-child(1) { animation-delay: -0.32s; }
.dot:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

/* 流式输出光标闪烁 */
.cursor-blink {
  display: inline;
  color: var(--color-primary);
  font-weight: bold;
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

/* Input Area */
.input-area {
  padding: var(--spacing-md) var(--spacing-lg);
  border-top: 1px solid var(--color-border);
}

.input-wrapper {
  display: flex;
  align-items: flex-end;
  gap: var(--spacing-sm);
  background-color: var(--color-bg);
  border-radius: var(--radius-lg);
  padding: var(--spacing-sm);
}

.chat-input {
  flex: 1;
  border: none;
  background: transparent;
  padding: var(--spacing-sm) var(--spacing-md);
  font-size: var(--font-size-base);
  font-family: inherit;
  resize: none;
  outline: none;
  max-height: 120px;
}

.chat-input::placeholder {
  color: var(--color-text-tertiary);
}

.send-btn {
  width: 40px;
  height: 40px;
  border: none;
  border-radius: var(--radius-md);
  background-color: var(--color-primary);
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--transition-fast);
}

.send-btn:hover:not(:disabled) {
  background-color: var(--color-primary-hover);
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Image upload button */
.img-upload-btn {
  width: 40px;
  height: 40px;
  border: none;
  border-radius: var(--radius-md);
  background: var(--color-bg);
  color: var(--color-text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all var(--transition-fast);
}

.img-upload-btn:hover:not(:disabled) {
  background: rgba(234, 88, 12, 0.1);
  color: #EA580C;
}

.img-upload-btn.has-image {
  background: rgba(234, 88, 12, 0.12);
  color: #EA580C;
}

.img-upload-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* Image preview bar */
.image-preview-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  background: rgba(234, 88, 12, 0.06);
  border: 1px solid rgba(234, 88, 12, 0.2);
  border-radius: var(--radius-md);
  margin-bottom: 8px;
}

.preview-thumb {
  width: 40px;
  height: 40px;
  object-fit: cover;
  border-radius: 6px;
  flex-shrink: 0;
}

.preview-name {
  flex: 1;
  font-size: 12px;
  color: var(--color-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.preview-remove {
  width: 22px;
  height: 22px;
  border: none;
  background: none;
  color: var(--color-text-tertiary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  flex-shrink: 0;
}

.preview-remove:hover {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

/* Image in message bubble */
.msg-image {
  display: block;
  max-width: 220px;
  max-height: 200px;
  border-radius: 8px;
  margin-bottom: 8px;
  object-fit: cover;
  cursor: pointer;
}

.input-hint {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  margin-top: var(--spacing-sm);
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
}

/* Dept Badge */
.dept-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  padding: 10px 14px;
  border-left: 3px solid var(--dept-color);
}

.dept-icon {
  font-size: 16px;
  flex-shrink: 0;
}

.dept-name-text {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-primary);
  flex: 1;
}

.dept-change-btn {
  display: flex;
  align-items: center;
  gap: 3px;
  border: none;
  background: none;
  font-size: 11px;
  color: var(--color-text-secondary);
  cursor: pointer;
  padding: 2px 6px;
  border-radius: var(--radius-sm);
  flex-shrink: 0;
}

.dept-change-btn:hover {
  background: var(--color-bg);
  color: var(--color-primary);
}

.history-dept-tag {
  font-size: 10px;
  padding: 1px 5px;
  border-radius: 4px;
  background: rgba(8, 102, 255, 0.08);
  color: var(--color-primary);
  flex-shrink: 0;
  white-space: nowrap;
}

/* History Section */
.history-section {
  padding-bottom: var(--spacing-md);
}

.history-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-sm);
}

.history-header h4 {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 0;
}

.btn-new-chat {
  width: 26px;
  height: 26px;
  border: none;
  border-radius: var(--radius-sm);
  background-color: var(--color-primary);
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.btn-new-chat:hover {
  background-color: var(--color-primary-hover);
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
  max-height: 200px;
  overflow-y: auto;
}

.history-item {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px;
  padding: 6px 8px;
  border-radius: var(--radius-md);
  cursor: pointer;
  position: relative;
  transition: background var(--transition-fast);
}

.history-item:hover {
  background-color: var(--color-bg);
}

.history-item.active {
  background-color: rgba(8, 102, 255, 0.08);
}

.history-title {
  flex: 1;
  font-size: var(--font-size-sm);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  min-width: 0;
}

.history-item.active .history-title {
  color: var(--color-primary);
  font-weight: 500;
}

.history-date {
  font-size: 11px;
  color: var(--color-text-tertiary);
  flex-shrink: 0;
}

.history-action {
  border: none;
  background: none;
  color: var(--color-text-tertiary);
  cursor: pointer;
  padding: 2px;
  border-radius: 3px;
  display: flex;
  align-items: center;
  opacity: 0;
  transition: opacity var(--transition-fast);
  flex-shrink: 0;
}

.history-item:hover .history-action {
  opacity: 1;
}

.history-action.del:hover {
  color: #ef4444;
}

.history-action.rename:hover {
  color: var(--color-primary);
}

.history-action.confirm {
  opacity: 1;
  color: #10b981;
}

.history-action.confirm:hover {
  color: #059669;
}

.history-action.cancel {
  opacity: 1;
  color: var(--color-text-tertiary);
}

.history-action.cancel:hover {
  color: #ef4444;
}

.rename-input {
  flex: 1;
  min-width: 0;
  font-size: var(--font-size-sm);
  border: 1px solid var(--color-primary);
  border-radius: 3px;
  padding: 1px 5px;
  outline: none;
  background: var(--color-bg);
  color: var(--color-text);
}

.history-empty {
  font-size: var(--font-size-sm);
  color: var(--color-text-tertiary);
  padding: 8px;
  text-align: center;
}

/* Sidebar */
.chat-sidebar {
  width: 280px;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.sidebar-section {
  background-color: var(--color-surface);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
}

.sidebar-section h4 {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.quick-questions {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.quick-btn {
  padding: var(--spacing-sm) var(--spacing-md);
  background-color: var(--color-bg);
  border: none;
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
  color: var(--color-text-primary);
  text-align: left;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.quick-btn:hover {
  background-color: rgba(8, 102, 255, 0.1);
  color: var(--color-primary);
}

.tips-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.tips-list li {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  padding-left: var(--spacing-md);
  position: relative;
}

.tips-list li::before {
  content: '•';
  position: absolute;
  left: 0;
  color: var(--color-primary);
}

@media (max-width: 1024px) {
  .chat-sidebar {
    display: none;
  }
}
</style>
