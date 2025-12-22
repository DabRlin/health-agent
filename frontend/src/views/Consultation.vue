<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { Send, Bot, User, Sparkles, AlertCircle } from 'lucide-vue-next'
import api from '../api'

const inputMessage = ref('')
const isLoading = ref(false)
const conversationId = ref(null)
const messages = ref([])
const messagesArea = ref(null)

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

// 开始新会话
const startNewConversation = async () => {
  try {
    const res = await api.startConsultation()
    if (res.success) {
      conversationId.value = res.data.conversation_id
      messages.value = res.data.messages
    }
  } catch (error) {
    console.error('Failed to start consultation:', error)
    // 降级处理：使用本地消息
    messages.value = [{
      id: 1,
      role: 'assistant',
      content: '您好！我是 HealthAI 智能健康助手。请描述您的症状或健康问题，我会为您提供专业的健康建议。\n\n您可以这样描述：\n• 最近有什么不舒服的症状？\n• 症状持续多长时间了？\n• 有没有其他伴随症状？',
      time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
    }]
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
    isStreaming: true
  })
  streamingMessageIndex.value = messages.value.length - 1
  scrollToBottom()
  
  try {
    await api.sendMessageStream(
      conversationId.value,
      userContent,
      // onChunk: 收到文本块
      (chunk) => {
        if (streamingMessageIndex.value >= 0) {
          messages.value[streamingMessageIndex.value].content += chunk
          scrollToBottom()
        }
      },
      // onDone: 流式结束
      () => {
        if (streamingMessageIndex.value >= 0) {
          messages.value[streamingMessageIndex.value].isStreaming = false
        }
        streamingMessageIndex.value = -1
        isLoading.value = false
      },
      // onError: 错误处理
      (error) => {
        console.error('Stream error:', error)
        if (streamingMessageIndex.value >= 0) {
          messages.value[streamingMessageIndex.value].content = '抱歉，服务暂时不可用，请稍后再试。'
          messages.value[streamingMessageIndex.value].isStreaming = false
        }
        streamingMessageIndex.value = -1
        isLoading.value = false
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

onMounted(() => {
  startNewConversation()
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
              <div class="message-bubble">
                <p v-html="message.content.replace(/\n/g, '<br>').replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')"></p>
                <span v-if="message.isStreaming" class="cursor-blink">|</span>
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

        <div class="sidebar-section">
          <h4>使用提示</h4>
          <ul class="tips-list">
            <li>尽量详细描述症状</li>
            <li>说明症状持续时间</li>
            <li>提及相关病史</li>
            <li>描述症状变化情况</li>
          </ul>
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

.message-time {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
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
