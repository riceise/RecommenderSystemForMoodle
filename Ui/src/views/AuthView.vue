<script setup lang="ts">
import { ref, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../stores/auth'; 

const router = useRouter();
const authStore = useAuthStore();

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
      await authStore.login({ email: formData.email, password: formData.password });
    }
    router.push('/dashboard');
  } catch (error) {
    alert('Ошибка: ' + (error.response?.data || 'Проверьте данные'));
  } finally {
    isLoading.value = false;
  }
};
</script>

<template>
  <div class="auth-container">
    <div class="background-orb orb-1"></div>
    <div class="background-orb orb-2"></div>

    <div class="glass-wrapper">
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
            <input type="text" v-model="formData.fullName" placeholder="Иван Петров" required />
          </div>

          <div class="input-group">
            <label>Email</label>
            <input type="email" v-model="formData.email" placeholder="student@university.com" required />
            <span v-if="isRegister" class="hint">Используйте email из Moodle для синхронизации</span>
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
/* Основной контейнер на весь экран */
.auth-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #0f172a; 
  position: relative;
  overflow: hidden;
  font-family: 'Inter', sans-serif;
}

/* Фоновые "пятна" градиенты */
.background-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  z-index: 0;
  opacity: 0.6;
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

/* Стеклянная панель (Glassmorphism) */
.glass-wrapper {
  display: flex;
  width: 900px;
  max-width: 95%;
  min-height: 600px;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 24px;
  box-shadow: 0 4px 30px rgba(0, 0, 0, 0.3);
  z-index: 1;
  overflow: hidden;
}

/* Левая часть (Арт) */
.art-section {
  flex: 1;
  background: linear-gradient(135deg, rgba(255,255,255,0.1), rgba(255,255,255,0));
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 40px;
  position: relative;
  color: white;
}

.logo-text {
  font-size: 2.5rem; 
  font-weight: 700; 
  margin-bottom: 10px; 
}
.highlight { color: #2dd4bf; }
.tagline { 
  font-size: 1.1rem;
  opacity: 0.8; 
  line-height: 1.5; 
}

/* 3D Иллюстрация (CSS Сферы) */
.illustration-3d {
  position: relative; 
  height: 200px;
  margin-top: 40px;
}
.sphere {
  border-radius: 50%;
  position: absolute;
  box-shadow: inset -10px -10px 20px rgba(0,0,0,0.5), inset 10px 10px 20px rgba(255,255,255,0.2);
}
.main-sphere {
  width: 120px; height: 120px;
  background: linear-gradient(135deg, #6366f1, #a855f7);
  top: 20%; left: 20%;
  animation: float 6s ease-in-out infinite;
}
.small-sphere {
  width: 60px; height: 60px;
  background: linear-gradient(135deg, #2dd4bf, #06b6d4);
  top: 60%; left: 60%;
  animation: float 4s ease-in-out infinite reverse;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-20px); }
}

/* Правая часть (Форма) */
.form-section {
  flex: 1;
  padding: 50px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  background: rgba(15, 23, 42, 0.6); /* Чуть темнее для контраста полей */
}

.form-header h2 { 
  color: white; 
  font-size: 2rem; 
  margin-bottom: 10px; 
}
.subtitle { color: #94a3b8;
  font-size: 0.9rem;
  margin-bottom: 30px; 
}

/* Поля ввода */
.input-group { margin-bottom: 20px;
  display: flex;
  flex-direction: column; 
}
.input-group label { 
  color: #cbd5e1;
  font-size: 0.9rem;
  margin-bottom: 8px;
}
.input-group input {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 12px 16px;
  border-radius: 12px;
  color: white;
  font-size: 1rem;
  transition: all 0.3s;
}
.input-group input:focus {
  outline: none;
  border-color: #7c3aed;
  box-shadow: 0 0 15px rgba(124, 58, 237, 0.3);
  background: rgba(255, 255, 255, 0.1);
}

.hint { font-size: 0.75rem; color: #f59e0b; margin-top: 5px; }

/* Кнопка */
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
  transition: transform 0.2s, box-shadow 0.2s;
  margin-top: 10px;
}
.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 20px rgba(124, 58, 237, 0.4);
}
.btn-primary:disabled { opacity: 0.7; cursor: not-allowed; }

.switch-mode { 
  text-align: center;
  margin-top: 20px;
  color: #94a3b8;
  font-size: 0.9rem; 
}
.switch-mode a { 
  color: #2dd4bf;
  text-decoration: none;
  font-weight: 600; 
  margin-left: 5px; 
}
.switch-mode a:hover { text-decoration: underline; }

/* Адаптивность */
@media (max-width: 768px) {
  .glass-wrapper { flex-direction: column; height: auto; }
  .art-section { display: none; }
  .form-section { padding: 30px; }
}

/* Анимация появления поля */
.slide-in { animation: slideDown 0.3s ease-out; }
@keyframes slideDown {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>