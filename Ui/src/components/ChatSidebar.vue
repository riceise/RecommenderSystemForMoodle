<script setup lang="ts">
import {ref, nextTick} from 'vue'
import {useAuthStore} from '../stores/auth'

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date
}

const authStore = useAuthStore()
const messages = ref<Message[]>([
  {
    id: '1', role: 'assistant',
    content: 'Привет! Я AI-помощник NeuroTutor. Спроси меня о курсе, заданиях или сложных темах, и я помогу разобраться.',
    timestamp: new Date()
  }
])
const input = ref('')
const isLoading = ref(false)
const chatContainer = ref<HTMLElement>()

const sendMessage = async () => {
  if (!input.value.trim() || isLoading.value) return

  const userMsg: Message = {id: Date.now().toString(), role: 'user', content: input.value, timestamp: new Date()}
  messages.value.push(userMsg)
  const userText = input.value
  input.value = ''
  isLoading.value = true
  await nextTick()
  scrollToBottom()

  try {
    const token = authStore.token
    const response = await fetch('http://localhost:5135/api/chat', {
      method: 'POST',
      headers: {'Content-Type': 'application/json', 'Authorization': `Bearer ${token}`},
      body: JSON.stringify({message: userText, context: 'course'})
    })

    const data = await response.json()
    messages.value.push({
      id: (Date.now() + 1).toString(), role: 'assistant',
      content: data.reply || 'Извини, я не смог обработать запрос.', timestamp: new Date()
    })
  } catch (error) {
    messages.value.push({
      id: (Date.now() + 1).toString(), role: 'assistant',
      content: 'Ошибка соединения.', timestamp: new Date()
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
const formatTime = (date: Date) => new Date(date).toLocaleTimeString('ru-RU', {hour: '2-digit', minute: '2-digit'})
</script>

<template>
  <aside class="chat-sidebar">
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
      <div v-for="msg in messages" :key="msg.id" class="message" :class="msg.role">
        <div class="message-content">
          <p>{{ msg.content }}</p>
          <span class="message-time">{{ formatTime(msg.timestamp) }}</span>
        </div>
      </div>

      <div v-if="isLoading" class="message assistant">
        <div class="message-content">
          <div class="typing-indicator"><span></span><span></span><span></span></div>
        </div>
      </div>
    </div>

    <form @submit.prevent="sendMessage" class="chat-input-form">
      <input v-model="input" placeholder="Спросить о курсе..." class="chat-input" :disabled="isLoading"/>
      <button type="submit" class="send-btn" :disabled="!input.trim() || isLoading">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/>
        </svg>
      </button>
    </form>
  </aside>
</template>

<style scoped>
.chat-sidebar {
  background: var(--bg-surface);
  backdrop-filter: var(--glass-blur);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  display: flex;
  flex-direction: column;
  height: calc(100vh - 110px);
  min-height: 600px;
  position: sticky;
  top: 24px;
  box-shadow: var(--shadow-sm);
}

.chat-header {
  padding: 24px;
  border-bottom: 1px solid var(--border-color);
}

.chat-title {
  display: flex;
  align-items: center;
  gap: 14px;
}

.ai-avatar {
  width: 44px;
  height: 44px;
  background: rgba(139, 92, 246, 0.12);
  border: 1px solid rgba(139, 92, 246, 0.28);
  border-radius: var(--radius-sm);
  color: var(--accent-indigo);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--text-sm);
  font-weight: 800;
}

.chat-title h4 {
  margin: 0 0 4px 0;
  font-size: 18px;
  color: var(--text-main);
  font-weight: 700;
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
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* Стилизация скроллбара */
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
  padding: 14px 18px;
  border-radius: var(--radius-sm);
  font-size: 16px;
  line-height: 1.6;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.02);
}

.message.assistant .message-content {
  background: var(--bg-card);
  color: var(--text-main);
  border: 1px solid var(--border-color);
}

.message.user .message-content {
  background: var(--accent-indigo);
  color: white;
}

.message-content p {
  margin: 0 0 6px 0;
}

.message-time {
  font-size: 12px;
  color: var(--text-muted);
  font-weight: 500;
}

.message.user .message-time {
  color: rgba(255, 255, 255, 0.7);
}

.chat-input-form {
  padding: 20px;
  border-top: 1px solid var(--border-color);
  display: flex;
  gap: 12px;
  background: var(--bg-surface);
}

.chat-input {
  flex: 1;
  background: var(--bg-surface-hover);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  padding: 14px 18px;
  color: var(--text-main);
  font-size: 16px;
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
  border-radius: var(--radius-sm);
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  cursor: pointer;
  transition: all 0.2s;
}

.send-btn:hover:not(:disabled) {
  background: #6d28d9;
  transform: translateY(-1px);
}

.send-btn:disabled {
  opacity: 0.4;
  filter: grayscale(1);
}

/* Typing indicator */
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
  .chat-sidebar {
    height: 550px;
    position: static;
    margin-top: 24px;
  }
}
</style>
