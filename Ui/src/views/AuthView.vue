<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useThemeStore } from '../stores/theme'

const router = useRouter()
const authStore = useAuthStore()
const themeStore = useThemeStore()

const isRegister = ref(false)
const isLoading = ref(false)

const formData = reactive({
  email: '',
  password: '',
  fullName: '',
})

const handleSubmit = async () => {
  isLoading.value = true
  try {
    if (isRegister.value) {
      await authStore.register(formData)
    } else {
      await authStore.login({ email: formData.email, password: formData.password })
    }
    router.push('/dashboard')
  } catch (error: any) {
    alert('Ошибка: ' + (error.response?.data || 'Проверьте данные'))
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <main class="auth-page">
    <button
      @click="themeStore.toggleTheme"
      class="theme-toggle-btn"
      :aria-label="themeStore.isDark ? 'Включить светлую тему' : 'Включить темную тему'"
    >
      {{ themeStore.isDark ? '☀️' : '🌙' }}
    </button>

    <section class="auth-shell">
      <div class="brand-panel">
        <div class="brand-mark">NT</div>
        <div>
          <h1>Neuro<span>Tutor</span></h1>
          <p>Персональный учебный кабинет с AI-анализом прогресса, курсов и зон внимания.</p>
        </div>

        <div class="brand-points">
          <div class="point">
            <span class="point-index">01</span>
            <div>
              <strong>Курсы под контролем</strong>
              <p>Смотрите оценки, прогресс и задания в одном месте.</p>
            </div>
          </div>
          <div class="point">
            <span class="point-index">02</span>
            <div>
              <strong>AI-рекомендации</strong>
              <p>Получайте подсказки по слабым темам и материалам.</p>
            </div>
          </div>
        </div>
      </div>

      <div class="form-panel">
        <div class="form-header">
          <p class="eyebrow">{{ isRegister ? 'Регистрация' : 'Вход' }}</p>
          <h2>{{ isRegister ? 'Создать аккаунт' : 'С возвращением' }}</h2>
          <p class="subtitle">
            {{ isRegister ? 'Заполните данные для синхронизации с Moodle.' : 'Введите данные, чтобы открыть учебный кабинет.' }}
          </p>
        </div>

        <form @submit.prevent="handleSubmit" class="neuro-form">
          <div v-if="isRegister" class="input-group">
            <label>Полное имя</label>
            <input type="text" v-model="formData.fullName" placeholder="Иван Петров" required />
          </div>

          <div class="input-group">
            <label>Email</label>
            <input type="email" v-model="formData.email" placeholder="student@university.com" required />
            <span v-if="isRegister" class="hint">Используйте email из Moodle для синхронизации.</span>
          </div>

          <div class="input-group">
            <label>Пароль</label>
            <input type="password" v-model="formData.password" placeholder="••••••••" required />
          </div>

          <button type="submit" class="btn-primary" :disabled="isLoading">
            <span v-if="isLoading" class="loader"></span>
            <span v-else>{{ isRegister ? 'Зарегистрироваться' : 'Войти' }}</span>
          </button>
        </form>

        <div class="switch-mode">
          <span>{{ isRegister ? 'Уже есть аккаунт?' : 'Нет аккаунта?' }}</span>
          <button type="button" @click="isRegister = !isRegister">
            {{ isRegister ? 'Войти' : 'Создать' }}
          </button>
        </div>
      </div>
    </section>
  </main>
</template>

<style scoped>
.auth-page {
  align-items: center;
  background: var(--bg-body);
  color: var(--text-main);
  display: flex;
  justify-content: center;
  min-height: 100vh;
  padding: var(--space-xl);
  position: relative;
}

.theme-toggle-btn {
  align-items: center;
  background: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-main);
  cursor: pointer;
  display: flex;
  font-size: var(--text-lg);
  height: 44px;
  justify-content: center;
  position: absolute;
  right: var(--space-lg);
  top: var(--space-lg);
  transition: background 0.2s, border-color 0.2s;
  width: 44px;
}

.theme-toggle-btn:hover {
  background: var(--bg-surface-hover);
  border-color: var(--accent-indigo);
}

.auth-shell {
  background: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  display: grid;
  grid-template-columns: minmax(320px, 0.9fr) minmax(340px, 1fr);
  max-width: 980px;
  overflow: hidden;
  width: 100%;
}

.brand-panel {
  background: var(--bg-card);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  gap: var(--space-xl);
  justify-content: center;
  padding: var(--space-2xl);
}

.brand-mark {
  align-items: center;
  background: rgba(139, 92, 246, 0.12);
  border: 1px solid rgba(139, 92, 246, 0.3);
  border-radius: var(--radius-md);
  color: var(--accent-indigo);
  display: flex;
  font-family: var(--font-display);
  font-size: var(--text-xl);
  font-weight: 800;
  height: 56px;
  justify-content: center;
  width: 56px;
}

.brand-panel h1 {
  color: var(--text-main);
  font-size: var(--text-4xl);
  font-weight: 800;
  margin-bottom: var(--space-sm);
}

.brand-panel h1 span {
  color: var(--accent-indigo);
}

.brand-panel p {
  color: var(--text-muted);
  font-size: var(--text-base);
  margin: 0;
}

.brand-points {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.point {
  display: flex;
  gap: var(--space-md);
}

.point-index {
  color: var(--accent-mint);
  flex-shrink: 0;
  font-family: var(--font-display);
  font-weight: 800;
}

.point strong {
  color: var(--text-main);
  display: block;
  font-size: var(--text-sm);
  margin-bottom: 2px;
}

.point p {
  font-size: var(--text-sm);
  line-height: 1.5;
}

.form-panel {
  background: var(--bg-surface);
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: var(--space-2xl);
}

.form-header {
  margin-bottom: var(--space-xl);
}

.eyebrow {
  color: var(--accent-mint);
  font-size: var(--text-xs);
  font-weight: 800;
  letter-spacing: 1px;
  margin: 0 0 var(--space-xs);
  text-transform: uppercase;
}

.form-header h2 {
  color: var(--text-main);
  font-size: var(--text-3xl);
  font-weight: 800;
  margin-bottom: var(--space-xs);
}

.subtitle {
  color: var(--text-muted);
  font-size: var(--text-sm);
  margin: 0;
}

.neuro-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.input-group label {
  color: var(--text-muted);
  font-size: var(--text-sm);
  font-weight: 700;
}

.input-group input {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-main);
  font-size: var(--text-base);
  outline: none;
  padding: var(--space-sm) var(--space-md);
  transition: border-color 0.2s, box-shadow 0.2s;
}

.input-group input:focus {
  border-color: var(--accent-indigo);
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.15);
}

.hint {
  color: #f59e0b;
  font-size: var(--text-xs);
}

.btn-primary {
  align-items: center;
  background: var(--accent-indigo);
  border: none;
  border-radius: var(--radius-sm);
  color: white;
  cursor: pointer;
  display: flex;
  font-size: var(--text-base);
  font-weight: 800;
  justify-content: center;
  margin-top: var(--space-xs);
  min-height: 48px;
  padding: var(--space-sm) var(--space-lg);
  transition: background 0.2s, transform 0.2s;
}

.btn-primary:hover:not(:disabled) {
  background: #6d28d9;
  transform: translateY(-1px);
}

.btn-primary:disabled {
  cursor: not-allowed;
  opacity: 0.65;
}

.loader {
  animation: spin 0.8s linear infinite;
  border: 3px solid rgba(255, 255, 255, 0.35);
  border-radius: 50%;
  border-top-color: white;
  height: 20px;
  width: 20px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.switch-mode {
  align-items: center;
  color: var(--text-muted);
  display: flex;
  font-size: var(--text-sm);
  gap: var(--space-xs);
  justify-content: center;
  margin-top: var(--space-lg);
}

.switch-mode button {
  background: transparent;
  border: none;
  color: var(--accent-indigo);
  cursor: pointer;
  font-weight: 800;
  padding: 0;
}

@media (max-width: 820px) {
  .auth-page {
    padding: var(--space-md);
  }

  .auth-shell {
    grid-template-columns: 1fr;
  }

  .brand-panel {
    border-bottom: 1px solid var(--border-color);
    border-right: none;
    padding: var(--space-xl);
  }

  .brand-points {
    display: none;
  }

  .form-panel {
    padding: var(--space-xl);
  }
}

@media (max-width: 520px) {
  .theme-toggle-btn {
    right: var(--space-md);
    top: var(--space-md);
  }

  .brand-panel h1 {
    font-size: var(--text-3xl);
  }

  .form-header h2 {
    font-size: var(--text-2xl);
  }
}
</style>
