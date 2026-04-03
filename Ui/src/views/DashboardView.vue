<script setup lang="ts">
import {ref, onMounted} from 'vue'
import {useRouter} from 'vue-router'
import {useAuthStore} from '../stores/auth'
import TheHeader from '../components/TheHeader.vue'

const router = useRouter()
const authStore = useAuthStore()

const isLoading = ref(true)
const courses = ref<any[]>([])
const errorMessage = ref('')

onMounted(async () => {
  try {
    const token = authStore.token;
    if (!token) throw new Error("Необходима авторизация");

    const response = await fetch('http://localhost:5135/api/student/courses', {
      headers: {'Authorization': `Bearer ${token}`}
    });

    if (!response.ok) throw new Error("Ошибка загрузки курсов");
    courses.value = await response.json();
  } catch (error: any) {
    errorMessage.value = error.message;
  } finally {
    isLoading.value = false;
  }
})

const goToCourse = (id: string) => router.push(`/course/${id}`);
</script>

<template>
  <div class="page-container">
    <TheHeader/>

    <main class="dashboard-content">
      <header class="content-header">
        <h1>Твои курсы под контролем <span class="ai-text">AI</span></h1>
        <p>Выберите курс для анализа успеваемости и получения рекомендаций.</p>
      </header>

      <div v-if="isLoading" class="loader-container">
        <div class="spinner"></div>
      </div>

      <div v-else-if="errorMessage" class="error-msg">{{ errorMessage }}</div>

      <div v-else class="course-grid">
        <div v-for="course in courses" :key="course.id || course.Id" class="course-card">
          <div class="card-content">
            <h3 class="course-title">{{ course.title || course.Title }}</h3>

            <div class="grade-section">
              <span class="label">Итоговый балл</span>
              <div class="grade-info">
                <span class="current">{{ course.overallGrade || course.OverallGrade || 0 }}</span>
                <span class="max">/ {{ course.maxGrade || course.MaxGrade || 0 }}</span>
              </div>
            </div>

            <!-- Прогресс-бар -->
            <div class="progress-track">
              <div class="progress-fill"
                   :style="{ width: ((course.overallGrade || 0) / (course.maxGrade || 1) * 100) + '%' }">
              </div>
            </div>

            <button @click="goToCourse(course.id || course.Id)" class="details-btn">
              Подробнее <span>➔</span>
            </button>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.page-container {
  min-height: 100vh;
  background-color: var(--bg-color);
  color: var(--text-color);
  transition: background 0.3s ease;
}

.dashboard-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px 24px;
}

.content-header {
  margin-bottom: 40px;
  text-align: center;
}

.content-header h1 {
  font-size: 36px;
  font-weight: 800;
  margin-bottom: 12px;
}

.ai-text {
  color: #a855f7;
}

.content-header p {
  color: var(--text-muted);
  font-size: 18px;
}

.course-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 25px;
}

.course-card {
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 24px;
  padding: 30px;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.course-card:hover {
  transform: translateY(-5px);
  border-color: #7c3aed;
  box-shadow: 0 10px 30px rgba(124, 58, 237, 0.1);
}

.course-title {
  font-size: 22px;
  font-weight: 700;
  margin-bottom: 25px;
  line-height: 1.3;
}

.grade-section {
  margin-bottom: 15px;
}

.label {
  font-size: 13px;
  color: var(--text-muted);
  display: block;
  margin-bottom: 5px;
}

.grade-info {
  font-size: 24px;
  font-weight: 800;
}

.max {
  font-size: 16px;
  color: var(--text-muted);
  font-weight: 400;
}

.progress-track {
  height: 8px;
  background: var(--hover-bg);
  border-radius: 10px;
  margin-bottom: 30px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #6366f1, #a855f7);
  border-radius: 10px;
  transition: width 1s ease;
}

.details-btn {
  width: 100%;
  padding: 14px;
  border-radius: 12px;
  border: none;
  background: var(--hover-bg);
  color: var(--text-color);
  font-weight: 700;
  cursor: pointer;
  transition: 0.2s;
}

.details-btn:hover {
  background: #7c3aed;
  color: white;
}

.loader-container {
  padding: 100px;
  text-align: center;
}

.spinner {
  width: 50px;
  height: 50px;
  border: 5px solid var(--hover-bg);
  border-top-color: #7c3aed;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 600px) {
  .course-grid {
    grid-template-columns: 1fr;
  }
}
</style>