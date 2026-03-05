<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { Send, Bot, User, Sparkles, AlertCircle, Plus, Trash2, MessageSquare, Pencil, Check, X } from 'lucide-vue-next'
import { marked } from 'marked'
import api from '../api'

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
      scrollToBottom()
    }
  } catch (e) {
    console.error('Failed to switch conversation', e)
  }
}

// 新建会话：只准备本地欢迎消息，不调后端
const newConversation = () => {
  if (isNewSession.value) return  // 当前已是未保存的新会话，不重复创建
  cancelRename()
  conversationId.value = null
  isNewSession.value = true
  messages.value = [localWelcomeMessage()]
  scrollToBottom()
}

// 生成本地欢迎消息（不入库）
const localWelcomeMessage = () => ({
  id: 'local-welcome',
  role: 'assistant',
  content: '您好！我是 HealthAI 智能健康助手，很高兴为您服务！\n\n我可以帮您：\n- 📊 查看您的健康指标（血压、血糖、心率、BMI、睡眠等）\n- 📈 分析健康数据的变化趋势\n- 🛡️ 进行健康风险评估（心血管、糖尿病、代谢综合征、骨质疏松）\n- 📋 解读您的体检报告\n- 💡 提供健康知识和专业建议\n\n请问今天有什么我可以帮助您的吗？',
  time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
})

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

const quickQuestions = [
  '最近经常头痛是什么原因？',
  '血压偏高应该注意什么？',
  '如何改善睡眠质量？',
  '体检报告中血糖偏高怎么办？'
]

// 滚动到底部
const scrollToBottom = async () => {
  await nextTick()
  if (messagesArea.value) {
    messagesArea.value.scrollTop = messagesArea.value.scrollHeight
  }
}

// 流式 AI 消息的引用
const streamingMessageIndex = ref(-1)

// 发送消息（流式模式）
const sendMessage = async () => {
  if (!inputMessage.value.trim() || isLoading.value) return

  const userContent = inputMessage.value.trim()
  inputMessage.value = ''
  isLoading.value = true

  // 懒创建：第一条消息时才调后端 /start 建立会话
  if (isNewSession.value) {
    try {
      const res = await api.startConsultation()
      if (res.success) {
        conversationId.value = res.data.conversation_id
        // 替换本地欢迎消息为后端返回的欢迎消息
        messages.value = res.data.messages
      }
    } catch (error) {
      console.error('Failed to start consultation:', error)
    }
    isNewSession.value = false
  }

  // 先显示用户消息
  messages.value.push({
    id: messages.value.length + 1,
    role: 'user',
    content: userContent,
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
        // 第一条消息发完后刷新历史列表（获取后端自动生成的会话名称）
        if (isFirstMessage) {
          await loadHistory()
        } else {
          // 后续消息无需全量刷新，仅在 historyList 中更新当前会话排序
          await loadHistory()
        }
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
      }
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
          <div class="input-wrapper">
            <textarea
              v-model="inputMessage"
              class="chat-input"
              placeholder="描述您的症状或健康问题..."
              rows="1"
              @keydown.enter.exact.prevent="sendMessage"
            ></textarea>
            <button 
              class="send-btn" 
              :disabled="!inputMessage.trim() || isLoading"
              @click="sendMessage"
            >
              <Send :size="20" />
            </button>
          </div>
          <p class="input-hint">
            <AlertCircle :size="14" />
            AI 建议仅供参考，不能替代专业医疗诊断
          </p>
        </div>
      </div>

      <!-- 侧边栏 -->
      <aside class="chat-sidebar">
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

.input-hint {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  margin-top: var(--spacing-sm);
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
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
