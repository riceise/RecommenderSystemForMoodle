<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

interface Course {
  id: string
  title: string
  overallGrade: number
  maxGrade: number
  /** Вычисляется автоматически */
  percentage: number
  /** Флаг «горячего» курса (оценка > 80%) */
  isHot: boolean
  /** Флаг курса, требующего внимания (оценка < 60%) */
  needsAttention: boolean
  /** Случайный размер для bento-раскладки */
  sizeVariant: number
}

const router = useRouter()
const authStore = useAuthStore()

const isLoading = ref(true)
const courses = ref<Course[]>([])
const errorMessage = ref('')

/** Фильтрация по поисковому запросу (приходит из Header через query param) */
const searchQuery = ref('')

const filteredCourses = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return courses.value
  return courses.value.filter((c) => c.title.toLowerCase().includes(q))
})

onMounted(async () => {
  try {
    const token = authStore.token
    if (!token) throw new Error('Необходима авторизация')

    const response = await fetch('http://localhost:5135/api/student/courses', {
      headers: { Authorization: `Bearer ${token}` },
    })

    if (!response.ok) throw new Error('Ошибка загрузки курсов')
    const raw: any[] = await response.json()

    courses.value = raw.map((c, i) => {
      const overallGrade = c.overallGrade ?? c.OverallGrade ?? 0
      const maxGrade = c.maxGrade ?? c.MaxGrade ?? 0
      const percentage = maxGrade > 0 ? Math.round((overallGrade / maxGrade) * 100) : 0

      return {
        id: c.id ?? c.Id,
        title: c.title ?? c.Title ?? 'Без названия',
        overallGrade,
        maxGrade,
        percentage,
        isHot: percentage >= 80,
        needsAttention: percentage < 60,
        // Распределяем размер: каждый 3-й курс — широкий
        sizeVariant: i % 3 === 0 ? 2 : 1,
      }
    })
  } catch (error: any) {
    errorMessage.value = error.message
  } finally {
    isLoading.value = false
  }
})

/** Слушаем query-параметр ?search=... */
const updateSearchFromQuery = () => {
  const params = new URLSearchParams(window.location.search)
  searchQuery.value = params.get('search') ?? ''
}

/** Наблюдаем за изменениями URL */
import { watch } from 'vue'
import { useRoute } from 'vue-router'
const route = useRoute()
watch(
  () => route.query.search,
  (val) => {
    searchQuery.value = (val as string) ?? ''
  },
)

onMounted(() => {
  updateSearchFromQuery()
})

const goToCourse = (id: string) => router.push(`/course/${id}`)

const gradeColor = (pct: number): string => {
  if (pct >= 90) return '#4ade80'
  if (pct >= 70) return '#60a5fa'
  if (pct >= 60) return '#fbbf24'
  return '#f87171'
}

const gradeLabel = (pct: number): string => {
  if (pct >= 90) return '5.0 — Отлично'
  if (pct >= 70) return '4.0 — Хорошо'
  if (pct >= 60) return '3.0 — Удовл.'
  return '2.0 — Требуется работа'
}
</script>

<template>
  <div class="page-container">
    <main class="dashboard-content">
      <header class="content-header">
        <p class="eyebrow">Учебный кабинет</p>
        <h1>Курсы и прогресс</h1>
        <p>Откройте курс, чтобы посмотреть оценки, слабые темы и рекомендации.</p>
      </header>

      <!-- Loader -->
      <div v-if="isLoading" class="loader-container">
        <div class="spinner"></div>
      </div>

      <!-- Error -->
      <div v-else-if="errorMessage" class="error-msg">{{ errorMessage }}</div>

      <!-- Empty search -->
      <div
        v-else-if="filteredCourses.length === 0 && searchQuery"
        class="empty-search"
      >
        <p>Ничего не найдено по запросу «{{ searchQuery }}»</p>
      </div>

      <!-- Bento Grid -->
      <div v-else class="bento-grid">
        <div
          v-for="(course, idx) in filteredCourses"
          :key="course.id"
          class="bento-card"
          :class="{
            'card-wide': course.sizeVariant === 2,
            'card-hot': course.isHot,
            'card-attention': course.needsAttention,
          }"
        >
          <!-- Декоративный градиент-фон -->
          <div class="card-glow" :style="{ background: gradeColor(course.percentage) + '15' }"></div>

          <!-- Бейджи -->
          <div class="card-badges">
            <span v-if="course.isHot" class="badge badge-hot">Высокий прогресс</span>
            <span v-if="course.needsAttention" class="badge badge-attention">Нужно внимание</span>
            <span class="badge badge-index">#{{ idx + 1 }}</span>
          </div>

          <div class="card-content">
            <h3 class="course-title">{{ course.title }}</h3>

            <!-- Grade -->
            <div class="grade-section">
              <span class="label">Итоговый балл</span>
              <div class="grade-info">
                <span
                  class="current"
                  :style="{ color: gradeColor(course.percentage) }"
                >
                  {{ course.overallGrade }}
                </span>
                <span class="max">/ {{ course.maxGrade }}</span>
                <span class="grade-tag" :style="{ borderColor: gradeColor(course.percentage), color: gradeColor(course.percentage) }">
                  {{ gradeLabel(course.percentage) }}
                </span>
              </div>
            </div>

            <!-- Progress bar -->
            <div class="progress-track">
              <div
                class="progress-fill"
                :style="{
                  width: `${course.percentage}%`,
                  background: `linear-gradient(90deg, ${gradeColor(course.percentage)}, ${gradeColor(course.percentage)}99)`,
                }"
              ></div>
            </div>

            <!-- CTA -->
            <button @click="goToCourse(course.id)" class="details-btn">
              Открыть курс
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
  background-color: var(--bg-body);
  color: var(--text-main);
  transition: background 0.3s ease;
}

.dashboard-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: var(--space-xl) var(--space-lg);
}

.content-header {
  margin-bottom: var(--space-xl);
  text-align: left;
}

.eyebrow {
  color: var(--accent-mint);
  font-size: var(--text-xs);
  font-weight: 800;
  letter-spacing: 1px;
  margin: 0 0 var(--space-xs);
  text-transform: uppercase;
}

.content-header h1 {
  font-size: var(--text-4xl);
  font-weight: 800;
  margin-bottom: var(--space-xs);
  font-family: var(--font-display);
}

.content-header p {
  color: var(--text-muted);
  font-size: var(--text-lg);
  margin: 0;
}

/* ─── Bento Grid ─────────────────────────────────────────── */
.bento-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-lg);
}

@media (max-width: 1100px) {
  .bento-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 640px) {
  .bento-grid {
    grid-template-columns: 1fr;
  }
}

/* ─── Card ───────────────────────────────────────────────── */
.bento-card {
  background: var(--bg-surface);
  backdrop-filter: var(--glass-blur);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: var(--space-lg);
  position: relative;
  overflow: hidden;
  transition: border-color 0.2s ease, transform 0.2s ease;
  box-shadow: var(--shadow-sm);
}

.bento-card:hover {
  transform: translateY(-2px);
  border-color: rgba(139, 92, 246, 0.45);
}

/* Широкая карточка (занимает 2 колонки) */
.card-wide {
  grid-column: span 2;
}

@media (max-width: 640px) {
  .card-wide {
    grid-column: span 1;
  }
}

/* Glow-эффект */
.card-glow {
  position: absolute;
  top: -40%;
  right: -20%;
  width: 200px;
  height: 200px;
  border-radius: 50%;
  filter: blur(60px);
  opacity: 0.18;
  pointer-events: none;
}

/* Бейджи */
.card-badges {
  display: flex;
  gap: var(--space-xs);
  flex-wrap: wrap;
  margin-bottom: var(--space-lg);
  position: relative;
  z-index: 1;
}

.badge {
  font-size: 12px;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 999px;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.badge-hot {
  background: rgba(245, 158, 11, 0.15);
  color: #f59e0b;
}

.badge-attention {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
}

.badge-index {
  background: var(--bg-surface-hover);
  color: var(--text-muted);
}

/* Content */
.card-content {
  position: relative;
  z-index: 1;
}

.course-title {
  font-size: var(--text-xl);
  font-weight: 700;
  margin-bottom: var(--space-lg);
  line-height: 1.3;
  color: var(--text-main);
  font-family: var(--font-display);
}

.grade-section {
  margin-bottom: var(--space-sm);
}

.label {
  font-size: var(--text-sm);
  color: var(--text-muted);
  display: block;
  margin-bottom: 5px;
}

.grade-info {
  display: flex;
  align-items: baseline;
  gap: 6px;
  flex-wrap: wrap;
}

.current {
  font-size: var(--text-3xl);
  font-weight: 800;
  font-family: var(--font-display);
}

.max {
  font-size: var(--text-lg);
  color: var(--text-muted);
  font-weight: 400;
}

.grade-tag {
  font-size: 13px;
  font-weight: 600;
  border: 1px solid;
  padding: 2px 8px;
  border-radius: 999px;
}

.progress-track {
  height: 8px;
  background: var(--bg-surface-hover);
  border-radius: var(--radius-sm);
  margin-bottom: var(--space-xl);
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: var(--radius-sm);
  transition: width 1s ease;
}

.details-btn {
  width: 100%;
  padding: var(--space-sm) var(--space-md);
  border-radius: var(--radius-sm);
  border: none;
  background: var(--bg-surface-hover);
  color: var(--text-main);
  font-weight: 700;
  cursor: pointer;
  transition: 0.2s;
  font-size: var(--text-base);
}

.details-btn:hover {
  background: var(--accent-indigo);
  color: white;
}

/* Loader */
.loader-container {
  padding: 100px;
  text-align: center;
}

.spinner {
  width: 50px;
  height: 50px;
  border: 5px solid var(--bg-surface-hover);
  border-top-color: var(--accent-indigo);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* Error / Empty */
.error-msg {
  text-align: center;
  padding: var(--space-xl);
  color: #ef4444;
  font-size: var(--text-lg);
  font-weight: 600;
}

.empty-search {
  text-align: center;
  padding: 80px var(--space-lg);
  color: var(--text-muted);
  font-size: var(--text-lg);
}

/* ─── Mobile ─────────────────────────────────────────── */
@media (max-width: 768px) {
  .content-header h1 {
    font-size: 28px;
  }

  .content-header p {
    font-size: 15px;
  }

  .course-title {
    font-size: 18px;
  }

  .current {
    font-size: 28px;
  }

  .bento-card {
    padding: 20px;
  }

  .badge {
    font-size: 11px;
  }

  .details-btn {
    font-size: 15px;
  }
}
</style>
