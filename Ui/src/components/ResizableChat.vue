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
    content: 'Привет! Я твой AI-помощник. Спроси меня о курсе, заданиях или сложных темах — я помогу разобраться! 🎓',
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
  Math.max(MIN_WIDTH, Math.min(chatWidth.value, maxWidth.value))
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
  // Inverse logic: dragging right (currentX > startX → delta < 0) increases width
  // dragging left (currentX < startX → delta > 0) decreases width
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
      // Context fetch failed — chat will work without it
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
    const detail = err.response?.data?.reply || err.response?.data?.error || '⚠️ Ошибка соединения.'
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
  <aside
    class="resizable-chat"
    :style="{ width: `${constrainedWidth}px` }"
  >
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
          <div class="ai-avatar">🤖</div>
          <div>
            <h4>AI Assistant</h4>
            <span class="status">Online</span>
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
          placeholder="Ask about the course..."
          class="chat-input"
          :disabled="isLoading"
        />
        <button type="submit" class="send-btn" :disabled="!input.trim() || isLoading">
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
  position: relative;
  flex-shrink: 0;
  align-self: start;
}

.resize-handle {
  position: absolute;
  top: 8px;
  bottom: 8px;
  left: -5px;
  width: 10px;
  cursor: col-resize;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 16px;
  background: rgba(139, 92, 246, 0.25);
  transition: background 0.2s;
}

.resize-handle:hover,
.resize-handle--active {
  background: rgba(139, 92, 246, 0.6);
}

.resize-handle-line {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.resize-handle-line::before,
.resize-handle-line::after {
  content: '';
  display: block;
  width: 2px;
  height: 16px;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 1px;
}

.chat-inner {
  background: var(--bg-surface);
  backdrop-filter: var(--glass-blur);
  border: 1.5px solid var(--border-color);
  border-radius: var(--radius-xl);
  display: flex;
  flex-direction: column;
  height: calc(100vh - 110px);
  min-height: 600px;
  overflow: hidden;
  box-shadow: var(--shadow-lg);
}

.chat-header {
  padding: var(--space-lg);
  border-bottom: 1.5px solid var(--border-color);
}

.chat-title {
  display: flex;
  align-items: center;
  gap: 14px;
}

.ai-avatar {
  width: 48px;
  height: 48px;
  background: rgba(79, 70, 229, 0.1);
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
}

.chat-title h4 {
  margin: 0 0 4px 0;
  font-size: var(--text-lg);
  color: var(--text-main);
  font-weight: 700;
  font-family: var(--font-display);
}

.status {
  font-size: 13px;
  color: var(--accent-mint);
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-lg);
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
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
  max-width: 85%;
  position: relative;
}

.message.user {
  margin-left: auto;
  align-items: flex-end;
}

.message.assistant {
  margin-right: auto;
  align-items: flex-start;
}

.message-content {
  padding: var(--space-md) var(--space-lg);
  border-radius: var(--radius-md);
  font-size: var(--text-base);
  line-height: 1.6;
  box-shadow: var(--shadow-sm);
}

.message.assistant .message-content {
  background: var(--bg-card);
  color: var(--text-main);
  border: 1px solid var(--border-color);
  border-top-left-radius: 4px;
}

.message.user .message-content {
  background: linear-gradient(135deg, var(--accent-indigo), #6366f1);
  color: white;
  border-top-right-radius: 4px;
}

.message-content p {
  margin: 0 0 6px 0;
  white-space: pre-wrap;

}

.message-time {
  font-size: 13px;
  color: var(--text-muted);
  font-weight: 500;
}

.message.user .message-time {
  color: rgba(255, 255, 255, 0.7);
}

.chat-input-form {
  padding: var(--space-lg);
  border-top: 1.5px solid var(--border-color);
  display: flex;
  gap: var(--space-sm);
  background: var(--bg-surface);
  border-bottom-left-radius: var(--radius-xl);
  border-bottom-right-radius: var(--radius-xl);
}

.chat-input {
  flex: 1;
  background: var(--bg-surface-hover);
  border: 1.5px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: var(--space-md) var(--space-lg);
  color: var(--text-main);
  font-size: var(--text-base);
  outline: none;
  transition: all 0.2s;
}

.chat-input:focus {
  border-color: var(--accent-indigo);
  background: var(--bg-card);
}

.chat-input::placeholder {
  color: var(--text-muted);
  opacity: 0.6;
}

.send-btn {
  background: var(--accent-indigo);
  border: none;
  border-radius: var(--radius-md);
  width: 52px;
  height: 52px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  cursor: pointer;
  transition: all 0.2s;
}

.send-btn:hover:not(:disabled) {
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3);
}

.send-btn:disabled {
  opacity: 0.4;
  filter: grayscale(1);
}

.typing-indicator {
  display: flex;
  gap: 5px;
  padding: 5px 0;
}

.typing-indicator span {
  width: 7px;
  height: 7px;
  background: var(--text-muted);
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out;
}

.typing-indicator span:nth-child(1) {
  animation-delay: -0.32s;
}

.typing-indicator span:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes bounce {
  0%, 80%, 100% {
    transform: scale(0.3);
    opacity: 0.4;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

@media (max-width: 1100px) {
  .resizable-chat {
    width: 100% !important;
    max-width: 100%;
  }

  .chat-inner {
    height: auto;
    min-height: 750px;
    max-height: calc(100vh - 100px);
    position: static;
  }

  .resize-handle {
    display: none;
  }

  .chat-messages {
    max-height: 600px;
  }
}

@media (max-width: 600px) {
  .resizable-chat {
    width: 100% !important;
    margin: 0;
  }

  .chat-inner {
    border-radius: var(--radius-lg);
    min-height: 820px;
    max-height: calc(100vh - 90px);
  }

  .chat-header {
    padding: var(--space-md);
  }

  .chat-messages {
    padding: var(--space-md);
    max-height: 680px;
    gap: var(--space-md);
  }

  .chat-input-form {
    padding: var(--space-md);
  }

  .message-content {
    padding: var(--space-sm) var(--space-md);
    font-size: 15px;
  }

  .send-btn {
    width: 44px;
    height: 44px;
  }

  .ai-avatar {
    width: 40px;
    height: 40px;
    font-size: 20px;
  }

  .chat-title h4 {
    font-size: var(--text-base);
  }
}
</style>
