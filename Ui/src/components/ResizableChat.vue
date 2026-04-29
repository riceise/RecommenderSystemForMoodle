<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import api from '../Api'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

interface GradeEntry {
  itemName: string
  grade: number | null
  maxGrade: number | null
}

interface CourseContext {
  courseName: string
  weakTopics: string[]
  strongTopics: string[]
  recentGrades: GradeEntry[]
}

const props = defineProps<{
  initialWidth?: number
  courseId?: string
}>()

const emit = defineEmits<{
  (e: 'resize', width: number): void
}>()

const messages = ref<Message[]>([
  {
    id: '1',
    role: 'assistant',
    content: 'Привет! Я AI-помощник NeuroTutor. Спроси меня о курсе, заданиях или сложных темах, и я помогу разобраться.',
    timestamp: new Date(),
  },
])
const input = ref('')
const isLoading = ref(false)
const chatContainer = ref<HTMLElement>()
const isFirstMessage = ref(true)
const courseContext = ref<CourseContext | null>(null)

const chatWidth = ref(props.initialWidth ?? 380)
const isResizing = ref(false)
const startX = ref(0)
const startWidth = ref(0)

const MIN_WIDTH = 300
const MAX_WIDTH = 600

const maxWidth = computed(() => {
  if (typeof window === 'undefined') return MAX_WIDTH
  return Math.min(MAX_WIDTH, window.innerWidth * 0.5)
})

const constrainedWidth = computed(() =>
  Math.max(MIN_WIDTH, Math.min(chatWidth.value, maxWidth.value)),
)

const onResizeMouseDown = (e: MouseEvent) => {
  isResizing.value = true
  startX.value = e.clientX
  startWidth.value = chatWidth.value
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
  e.preventDefault()
}

const onMouseMove = (e: MouseEvent) => {
  if (!isResizing.value) return
  const delta = startX.value - e.clientX
  const newWidth = startWidth.value - delta
  chatWidth.value = Math.max(MIN_WIDTH, Math.min(newWidth, maxWidth.value))
  emit('resize', chatWidth.value)
}

const onMouseUp = () => {
  if (!isResizing.value) return
  isResizing.value = false
  document.body.style.cursor = ''
  document.body.style.userSelect = ''
}

onMounted(async () => {
  window.addEventListener('mousemove', onMouseMove)
  window.addEventListener('mouseup', onMouseUp)

  if (props.courseId) {
    try {
      const { data } = await api.get(`/student/courses/${props.courseId}/context`)
      courseContext.value = data
    } catch {
      // Chat remains usable even when course context is unavailable.
    }
  }
})

onUnmounted(() => {
  window.removeEventListener('mousemove', onMouseMove)
  window.removeEventListener('mouseup', onMouseUp)
})

const sendMessage = async () => {
  if (!input.value.trim() || isLoading.value) return

  const userMsg: Message = {
    id: Date.now().toString(),
    role: 'user',
    content: input.value,
    timestamp: new Date(),
  }
  messages.value.push(userMsg)
  const userText = input.value
  input.value = ''
  isLoading.value = true
  await nextTick()
  scrollToBottom()

  try {
    const payload: any = {
      message: userText,
      context: 'course',
    }

    if (props.courseId) {
      payload.courseId = props.courseId
    }

    if (isFirstMessage.value && courseContext.value) {
      payload.contextData = courseContext.value
    }

    isFirstMessage.value = false

    const { data } = await api.post('/recommendations/chat', payload)
    messages.value.push({
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: data.reply || 'Извини, я не смог обработать запрос.',
      timestamp: new Date(),
    })
  } catch (err: any) {
    const detail = err.response?.data?.reply || err.response?.data?.error || 'Ошибка соединения.'
    messages.value.push({
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: detail,
      timestamp: new Date(),
    })
  } finally {
    isLoading.value = false
    await nextTick()
    scrollToBottom()
  }
}

const scrollToBottom = () => {
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }
}

const formatTime = (date: Date) =>
  new Date(date).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })
</script>

<template>
  <aside class="resizable-chat" :style="{ width: `${constrainedWidth}px` }">
    <div
      class="resize-handle"
      :class="{ 'resize-handle--active': isResizing }"
      @mousedown="onResizeMouseDown"
    >
      <div class="resize-handle-line" />
    </div>

    <div class="chat-inner">
      <div class="chat-header">
        <div class="chat-title">
          <div class="ai-avatar">AI</div>
          <div>
            <h4>AI-помощник</h4>
            <span class="status">онлайн</span>
          </div>
        </div>
      </div>

      <div ref="chatContainer" class="chat-messages">
        <div
          v-for="msg in messages"
          :key="msg.id"
          class="message"
          :class="msg.role"
        >
          <div class="message-content">
            <p>{{ msg.content }}</p>
            <span class="message-time">{{ formatTime(msg.timestamp) }}</span>
          </div>
        </div>

        <div v-if="isLoading" class="message assistant">
          <div class="message-content">
            <div class="typing-indicator">
              <span></span><span></span><span></span>
            </div>
          </div>
        </div>
      </div>

      <form @submit.prevent="sendMessage" class="chat-input-form">
        <input
          v-model="input"
          placeholder="Спросить о курсе..."
          class="chat-input"
          :disabled="isLoading"
        />
        <button type="submit" class="send-btn" :disabled="!input.trim() || isLoading" aria-label="Отправить сообщение">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
            />
          </svg>
        </button>
      </form>
    </div>
  </aside>
</template>

<style scoped>
.resizable-chat {
  align-self: start;
  flex-shrink: 0;
  position: relative;
}

.resize-handle {
  align-items: center;
  background: rgba(139, 92, 246, 0.18);
  border-radius: var(--radius-sm);
  bottom: var(--space-sm);
  cursor: col-resize;
  display: flex;
  justify-content: center;
  left: -5px;
  position: absolute;
  top: var(--space-sm);
  transition: background 0.2s;
  width: 10px;
  z-index: 10;
}

.resize-handle:hover,
.resize-handle--active {
  background: rgba(139, 92, 246, 0.5);
}

.resize-handle-line::before,
.resize-handle-line::after {
  background: rgba(255, 255, 255, 0.8);
  border-radius: 1px;
  content: '';
  display: block;
  height: 16px;
  width: 2px;
}

.resize-handle-line {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.chat-inner {
  background: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
  display: flex;
  flex-direction: column;
  height: calc(100vh - 110px);
  min-height: 600px;
  overflow: hidden;
}

.chat-header {
  border-bottom: 1px solid var(--border-color);
  padding: var(--space-lg);
}

.chat-title {
  align-items: center;
  display: flex;
  gap: var(--space-sm);
}

.ai-avatar {
  align-items: center;
  background: rgba(139, 92, 246, 0.12);
  border: 1px solid rgba(139, 92, 246, 0.28);
  border-radius: var(--radius-sm);
  color: var(--accent-indigo);
  display: flex;
  font-size: var(--text-sm);
  font-weight: 800;
  height: 44px;
  justify-content: center;
  width: 44px;
}

.chat-title h4 {
  color: var(--text-main);
  font-family: var(--font-display);
  font-size: var(--text-lg);
  font-weight: 700;
  margin: 0 0 2px;
}

.status {
  color: var(--accent-mint);
  font-size: var(--text-xs);
  font-weight: 800;
  letter-spacing: 0.7px;
  text-transform: uppercase;
}

.chat-messages {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: var(--space-md);
  overflow-y: auto;
  padding: var(--space-lg);
}

.chat-messages::-webkit-scrollbar {
  width: 5px;
}

.chat-messages::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 10px;
}

.message {
  display: flex;
  flex-direction: column;
  max-width: 86%;
  position: relative;
}

.message.user {
  align-items: flex-end;
  margin-left: auto;
}

.message.assistant {
  align-items: flex-start;
  margin-right: auto;
}

.message-content {
  border-radius: var(--radius-sm);
  box-shadow: var(--shadow-sm);
  font-size: var(--text-sm);
  line-height: 1.55;
  padding: var(--space-sm) var(--space-md);
}

.message.assistant .message-content {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  color: var(--text-main);
}

.message.user .message-content {
  background: var(--accent-indigo);
  color: white;
}

.message-content p {
  margin: 0 0 6px;
  white-space: pre-wrap;
}

.message-time {
  color: var(--text-muted);
  font-size: 12px;
  font-weight: 500;
}

.message.user .message-time {
  color: rgba(255, 255, 255, 0.72);
}

.chat-input-form {
  background: var(--bg-surface);
  border-top: 1px solid var(--border-color);
  display: flex;
  gap: var(--space-sm);
  padding: var(--space-lg);
}

.chat-input {
  background: var(--bg-surface-hover);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-main);
  flex: 1;
  font-size: var(--text-sm);
  outline: none;
  padding: var(--space-sm) var(--space-md);
  transition: border-color 0.2s, background 0.2s;
}

.chat-input:focus {
  background: var(--bg-card);
  border-color: var(--accent-indigo);
}

.chat-input::placeholder {
  color: var(--text-muted);
  opacity: 0.7;
}

.send-btn {
  align-items: center;
  background: var(--accent-indigo);
  border: none;
  border-radius: var(--radius-sm);
  color: white;
  cursor: pointer;
  display: flex;
  height: 44px;
  justify-content: center;
  transition: background 0.2s, transform 0.2s;
  width: 44px;
}

.send-btn:hover:not(:disabled) {
  background: #6d28d9;
  transform: translateY(-1px);
}

.send-btn:disabled {
  cursor: not-allowed;
  opacity: 0.45;
}

.typing-indicator {
  display: flex;
  gap: 5px;
  padding: 5px 0;
}

.typing-indicator span {
  animation: bounce 1.4s infinite ease-in-out;
  background: var(--text-muted);
  border-radius: 50%;
  height: 7px;
  width: 7px;
}

.typing-indicator span:nth-child(1) {
  animation-delay: -0.32s;
}

.typing-indicator span:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes bounce {
  0%, 80%, 100% {
    opacity: 0.4;
    transform: scale(0.3);
  }
  40% {
    opacity: 1;
    transform: scale(1);
  }
}

@media (max-width: 1100px) {
  .resizable-chat {
    max-width: 100%;
    width: 100% !important;
  }

  .chat-inner {
    height: auto;
    max-height: calc(100vh - 100px);
    min-height: 640px;
    position: static;
  }

  .resize-handle {
    display: none;
  }

  .chat-messages {
    max-height: 520px;
  }
}

@media (max-width: 600px) {
  .chat-inner {
    border-radius: var(--radius-md);
    max-height: calc(100vh - 90px);
    min-height: 620px;
  }

  .chat-header,
  .chat-messages,
  .chat-input-form {
    padding: var(--space-md);
  }

  .message-content {
    font-size: 15px;
  }

  .ai-avatar,
  .send-btn {
    height: 40px;
    width: 40px;
  }
}
</style>
