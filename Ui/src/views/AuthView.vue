<script setup lang="ts">
import {ref, reactive} from 'vue';
import {useRouter} from 'vue-router';
import {useAuthStore} from '../stores/auth';
import {useThemeStore} from '../stores/theme'; // Подключаем тему

const router = useRouter();
const authStore = useAuthStore();
const themeStore = useThemeStore(); // Инициализируем тему

const isRegister = ref(false);
const isLoading = ref(false);

const formData = reactive({
  email: '',
  password: '',
  fullName: ''
});

const handleSubmit = async () => {
  isLoading.value = true;
  try {
    if (isRegister.value) {
      await authStore.register(formData);
    } else {
      await authStore.login({email: formData.email, password: formData.password});
    }
    router.push('/dashboard');
  } catch (error: any) {
    alert('Ошибка: ' + (error.response?.data || 'Проверьте данные'));
  } finally {
    isLoading.value = false;
  }
};
</script>

<template>
  <div class="auth-container">
    <!-- Кнопка переключения темы сверху справа -->
    <button @click="themeStore.toggleTheme" class="theme-toggle-btn">
      {{ themeStore.isDark ? '☀️' : '🌙' }}
    </button>

    <div class="background-orb orb-1"></div>
    <div class="background-orb orb-2"></div>

    <div class="glass-wrapper">
      <!-- Левая часть (Арт) -->
      <div class="art-section">
        <div class="content">
          <h1 class="logo-text">Neuro<span class="highlight">Tutor</span></h1>
          <p class="tagline">Твой персональный AI-тьютор.<br>Учись умнее, а не дольше.</p>
          <div class="illustration-3d">
            <div class="sphere main-sphere"></div>
            <div class="sphere small-sphere"></div>
          </div>
        </div>
      </div>

      <!-- Правая часть (Форма) -->
      <div class="form-section">
        <div class="form-header">
          <h2>{{ isRegister ? 'Создать аккаунт' : 'С возвращением!' }}</h2>
          <p class="subtitle">
            {{ isRegister ? 'Заполните данные для начала обучения' : 'Введите данные для входа в систему' }}
          </p>
        </div>

        <form @submit.prevent="handleSubmit" class="neuro-form">
          <div v-if="isRegister" class="input-group slide-in">
            <label>Полное имя</label>
            <input type="text" v-model="formData.fullName" placeholder="Иван Петров" required/>
          </div>

          <div class="input-group">
            <label>Email</label>
            <input type="email" v-model="formData.email" placeholder="student@university.com" required/>
            <span v-if="isRegister" class="hint">Используйте email из Moodle для синхронизации</span>
          </div>

          <div class="input-group">
            <label>Пароль</label>
            <input type="password" v-model="formData.password" placeholder="••••••••" required/>
          </div>

          <button type="submit" class="btn-primary" :disabled="isLoading">
            <span v-if="isLoading" class="loader"></span>
            <span v-else>{{ isRegister ? 'Зарегистрироваться' : 'Войти' }}</span>
          </button>
        </form>

        <div class="switch-mode">
          <p>
            {{ isRegister ? 'Уже есть аккаунт?' : 'Нет аккаунта?' }}
            <a href="#" @click.prevent="isRegister = !isRegister">
              {{ isRegister ? 'Войти' : 'Создать' }}
            </a>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.auth-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-color); /* Глобальный фон */
  position: relative;
  overflow: hidden;
  font-family: 'Inter', sans-serif;
  transition: background 0.3s ease;
}

/* Кнопка переключения темы */
.theme-toggle-btn {
  position: absolute;
  top: 20px;
  right: 20px;
  z-index: 10;
  width: 45px;
  height: 45px;
  border-radius: 12px;
  border: 1px solid var(--border-color);
  background: var(--card-bg);
  cursor: pointer;
  font-size: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

/* Фоновые пятна */
.background-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  z-index: 0;
  opacity: 0.4;
}

.orb-1 {
  width: 400px;
  height: 400px;
  background: #7c3aed;
  top: -100px;
  left: -100px;
}

.orb-2 {
  width: 300px;
  height: 300px;
  background: #2dd4bf;
  bottom: -50px;
  right: -50px;
}

/* Основная панель */
.glass-wrapper {
  display: flex;
  width: 900px;
  max-width: 95%;
  min-height: 600px;
  background: var(--card-bg); /* Использование переменной */
  backdrop-filter: blur(16px);
  border: 1px solid var(--border-color);
  border-radius: 24px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
  z-index: 1;
  overflow: hidden;
  transition: all 0.3s ease;
}

.art-section {
  flex: 1;
  background: linear-gradient(135deg, rgba(124, 58, 237, 0.1), rgba(45, 212, 191, 0.05));
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 40px;
  position: relative;
}

.logo-text {
  font-size: 2.5rem;
  font-weight: 800;
  color: var(--text-color);
  margin-bottom: 10px;
}

.highlight {
  color: #2dd4bf;
}

.tagline {
  font-size: 1.1rem;
  color: var(--text-muted);
  line-height: 1.5;
}

/* 3D Сферы */
.illustration-3d {
  position: relative;
  height: 200px;
  margin-top: 40px;
}

.sphere {
  border-radius: 50%;
  position: absolute;
}

.main-sphere {
  width: 120px;
  height: 120px;
  background: linear-gradient(135deg, #6366f1, #a855f7);
  top: 20%;
  left: 20%;
  animation: float 6s ease-in-out infinite;
  box-shadow: 0 10px 30px rgba(99, 102, 241, 0.4);
}

.small-sphere {
  width: 60px;
  height: 60px;
  background: linear-gradient(135deg, #2dd4bf, #06b6d4);
  top: 60%;
  left: 60%;
  animation: float 4s ease-in-out infinite reverse;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-20px);
  }
}

/* Правая часть (Форма) */
.form-section {
  flex: 1;
  padding: 50px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  background: var(--card-bg);
}

.form-header h2 {
  color: var(--text-color);
  font-size: 2rem;
  margin-bottom: 10px;
}

.subtitle {
  color: var(--text-muted);
  font-size: 0.9rem;
  margin-bottom: 30px;
}

.input-group {
  margin-bottom: 20px;
  display: flex;
  flex-direction: column;
}

.input-group label {
  color: var(--text-color);
  font-size: 0.9rem;
  margin-bottom: 8px;
  font-weight: 500;
}

.input-group input {
  background: var(--hover-bg);
  border: 1px solid var(--border-color);
  padding: 12px 16px;
  border-radius: 12px;
  color: var(--text-color);
  font-size: 1rem;
  transition: all 0.3s;
}

.input-group input:focus {
  outline: none;
  border-color: #7c3aed;
  box-shadow: 0 0 0 4px rgba(124, 58, 237, 0.1);
}

.hint {
  font-size: 0.75rem;
  color: #f59e0b;
  margin-top: 5px;
}

.btn-primary {
  width: 100%;
  padding: 14px;
  border-radius: 12px;
  background: linear-gradient(90deg, #4f46e5, #9333ea);
  color: white;
  border: none;
  font-weight: 600;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.3s;
  margin-top: 10px;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(124, 58, 237, 0.4);
}

.switch-mode {
  text-align: center;
  margin-top: 20px;
  color: var(--text-muted);
  font-size: 0.9rem;
}

.switch-mode a {
  color: #2dd4bf;
  text-decoration: none;
  font-weight: 600;
  margin-left: 5px;
}

@media (max-width: 768px) {
  .glass-wrapper {
    flex-direction: column;
    height: auto;
  }

  .art-section {
    display: none;
  }

  .form-section {
    padding: 30px;
  }
}

.slide-in {
  animation: slideDown 0.3s ease-out;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>