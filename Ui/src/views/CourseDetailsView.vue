<script setup lang="ts">
import {ref, onMounted, computed} from 'vue'
import {useRoute, useRouter} from 'vue-router'
import {useAuthStore} from '../stores/auth'
import {useThemeStore} from '../stores/theme'
import TheHeader from '../components/TheHeader.vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const themeStore = useThemeStore()

const isLoading = ref(true)
const errorMessage = ref('')
const courseTitle = ref("")
const assignments = ref<any[]>([])

const isAnalyzing = ref(false)
const recommendationsResult = ref<string | null>(null)

const calculateGradeInfo = (grade: any, maxGrade: any) => {
  const g = parseFloat(grade) || 0;
  const m = parseFloat(maxGrade) || 0;
  if (m === 0) return {percent: 0, mark: 0, color: 'var(--text-muted)', bg: 'var(--hover-bg)'}

  const percent = Math.round((g / m) * 100)

  if (percent >= 90) return {percent, mark: 5, color: '#4ade80', bg: 'rgba(74, 222, 128, 0.15)'}
  if (percent >= 70) return {percent, mark: 4, color: '#60a5fa', bg: 'rgba(96, 165, 251, 0.15)'}
  if (percent >= 60) return {percent, mark: 3, color: '#fbbf24', bg: 'rgba(251, 191, 36, 0.15)'}
  return {percent, mark: 2, color: '#f87171', bg: 'rgba(248, 113, 113, 0.15)'}
}

onMounted(async () => {
  try {
    const token = authStore.token;
    if (!token) throw new Error("Необходима авторизация");

    const response = await fetch(`http://localhost:5135/api/student/courses/${route.params.id}`, {
      headers: {'Authorization': `Bearer ${token}`}
    });

    if (!response.ok) throw new Error("Не удалось загрузить данные курса");

    const data = await response.json();
    courseTitle.value = data.title || data.Title || "Курс";
    assignments.value = data.assignments || data.Assignments || [];
  } catch (error: any) {
    errorMessage.value = error.message;
  } finally {
    isLoading.value = false;
  }
})

const hasLowGrades = computed(() => {
  return assignments.value.some(a => calculateGradeInfo(a.grade || a.Grade, a.maxGrade || a.MaxGrade).mark <= 3)
})
//To do
//Необходимо доделать рекомендации для курса
const generateAiPlan = async () => {
  isAnalyzing.value = true;
  recommendationsResult.value = null;
  const token = authStore.token;

  try {
    const response = await fetch(`http://localhost:5135/api/student/analyze?courseId=1`, {
      headers: {'Authorization': `Bearer ${token}`}
    });

    if (!response.ok) throw new Error("Ошибка связи с AI сервисом");
    const data = await response.json();
    recommendationsResult.value = data.recommendations;
  } catch (err: any) {
    alert(err.message);
  } finally {
    isAnalyzing.value = false;
  }
}
</script>


<template>
  <div class="page-container">
    <TheHeader/>

    <main class="content-wrapper">
      <nav class="breadcrumb">
        <button @click="router.push('/dashboard')" class="back-link">
          <span>←</span> <span class="hide-mobile">Назад к курсам</span><span class="show-mobile">Назад</span>
        </button>
      </nav>

      <div v-if="isLoading" class="loader">
        <div class="spinner"></div>
      </div>

      <div v-else>
        <header class="course-header">
          <div class="title-area">
            <h1>{{ courseTitle }}</h1>
            <p>Отчет успеваемости</p>
          </div>

          <button v-if="hasLowGrades" @click="generateAiPlan" :disabled="isAnalyzing" class="ai-button">
            <span v-if="isAnalyzing">...</span>
            <span v-else>🤖 <span class="hide-mobile">AI План спасения</span><span
                class="show-mobile">AI План</span></span>
          </button>
        </header>

        <div class="assignments-grid">
          <div v-for="item in assignments" :key="item.id || item.Id" class="assignment-card">
            <div class="card-top">
              <h3 class="task-name">{{ item.name || item.Name }}</h3>
              <div class="mark-badge" :style="{ 
                color: calculateGradeInfo(item.grade || item.Grade, item.maxGrade || item.MaxGrade).color,
                backgroundColor: calculateGradeInfo(item.grade || item.Grade, item.maxGrade || item.MaxGrade).bg,
                borderColor: calculateGradeInfo(item.grade || item.Grade, item.maxGrade || item.MaxGrade).color
              }">
                {{ calculateGradeInfo(item.grade || item.Grade, item.maxGrade || item.MaxGrade).mark }}
              </div>
            </div>

            <div class="card-details">
              <div class="data-row">
                <span class="label">Баллы:</span>
                <span class="val">{{ item.grade || item.Grade || 0 }} / {{ item.maxGrade || item.MaxGrade || 0 }}</span>
              </div>

              <div class="progress-track">
                <div class="progress-bar" :style="{ 
                  width: calculateGradeInfo(item.grade || item.Grade, item.maxGrade || item.MaxGrade).percent + '%',
                  backgroundColor: calculateGradeInfo(item.grade || item.Grade, item.maxGrade || item.MaxGrade).color
                }"></div>
              </div>
              <div class="percent-label">
                {{ calculateGradeInfo(item.grade || item.Grade, item.maxGrade || item.MaxGrade).percent }}% качества
              </div>
            </div>
          </div>
        </div>

        <section v-if="recommendationsResult" class="ai-results">
          <h2>🧠 Рекомендации AI</h2>
          <div class="ai-content">{{ recommendationsResult }}</div>
        </section>
      </div>
    </main>
  </div>
</template>

<style scoped>
.page-container {
  min-height: 100vh;
  background-color: var(--bg-color);
  color: var(--text-color);
  transition: background 0.3s;
}

.content-wrapper {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px 15px 60px 15px; 
}

.breadcrumb {
  margin-bottom: 20px;
}

.back-link {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 5px;
}

.course-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  gap: 15px;
}

.course-header h1 {
  font-size: 24px;
  font-weight: 800;
  margin: 0;
  line-height: 1.2;
}

.course-header p {
  color: var(--text-muted);
  font-size: 14px;
  margin: 4px 0 0 0;
}

.ai-button {
  background: linear-gradient(90deg, #7c3aed, #4f46e5);
  border: none;
  color: white;
  padding: 12px 20px;
  border-radius: 12px;
  font-weight: 700;
  cursor: pointer;
  white-space: nowrap;
  font-size: 14px;
}

.assignments-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 15px;
}

.assignment-card {
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 20px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.card-top {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 15px;
}

.task-name {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-color);
}

.mark-badge {
  min-width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: 900;
  border: 2px solid;
}

.progress-track {
  height: 6px;
  background: var(--hover-bg);
  border-radius: 10px;
  margin: 10px 0 5px 0;
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  transition: width 0.5s ease;
}

.percent-label {
  font-size: 12px;
  color: var(--text-muted);
  text-align: right;
}

.ai-results {
  margin-top: 30px;
  padding: 20px;
  background: var(--hover-bg);
  border-radius: 20px;
  border: 1px solid #7c3aed;
}

.show-mobile {
  display: none;
}

@media (max-width: 768px) {
  .course-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .ai-button {
    width: 100%;
    text-align: center;
  }

  .course-header h1 {
    font-size: 20px;
  }
}

@media (max-width: 480px) {
  .hide-mobile {
    display: none;
  }

  .show-mobile {
    display: inline;
  }

  .assignments-grid {
    grid-template-columns: 1fr;
  }

}

.loader {
  text-align: center;
  padding: 50px;
}

.spinner {
  width: 30px;
  height: 30px;
  border: 3px solid var(--hover-bg);
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
</style>