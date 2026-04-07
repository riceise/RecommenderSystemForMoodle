<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js'
import { Doughnut } from 'vue-chartjs'
import { useAuthStore } from '../stores/auth'

ChartJS.register(ArcElement, Tooltip, Legend)

interface GradeDistribution {
  two: number
  three: number
  four: number
  five: number
}

interface CourseProgress {
  courseTitle: string
  averagePercentage: number
}

interface Statistics {
  totalGradesCount: number
  overallAverageScore: number
  gradeDistribution: GradeDistribution
  weakCount: number
  coursesCount: number
  courseProgress: CourseProgress[]
}

const authStore = useAuthStore()
const isLoading = ref(true)
const isError = ref(false)
const isEmpty = ref(false)
const stats = ref<Statistics>({
  totalGradesCount: 0,
  overallAverageScore: 0,
  gradeDistribution: { two: 0, three: 0, four: 0, five: 0 },
  weakCount: 0,
  coursesCount: 0,
  courseProgress: [],
})

const loadStats = async () => {
  isLoading.value = true
  isError.value = false
  try {
    const token = authStore.token
    if (!token) return

    const res = await fetch('http://localhost:5135/api/student/statistics', {
      headers: { Authorization: `Bearer ${token}` },
    })

    if (res.ok) {
      const data = await res.json()
      stats.value = data
      isEmpty.value = data.totalGradesCount === 0 && data.coursesCount === 0
    } else {
      isError.value = true
    }
  } catch {
    isError.value = true
  } finally {
    isLoading.value = false
  }
}

onMounted(loadStats)

const palette = ['#ef4444', '#f59e0b', '#3b82f6', '#10b981']

const donutData = computed(() => ({
  labels: ['2 (Неудовл.)', '3 (Удовл.)', '4 (Хорошо)', '5 (Отлично)'],
  datasets: [{
    data: [
      stats.value.gradeDistribution.two,
      stats.value.gradeDistribution.three,
      stats.value.gradeDistribution.four,
      stats.value.gradeDistribution.five,
    ],
    backgroundColor: palette,
    borderColor: 'transparent',
    borderWidth: 0,
    hoverOffset: 8,
    spacing: 2,
    borderRadius: 4,
  }],
}))

const donutOptions = {
  responsive: true,
  maintainAspectRatio: false,
  cutout: '68%',
  plugins: {
    legend: {
      position: 'bottom' as const,
      labels: {
        padding: 14,
        usePointStyle: true,
        pointStyleWidth: 12,
        color: '#9ca3af',
        font: { family: 'Inter, sans-serif', size: 12 },
      },
    },
    tooltip: {
      backgroundColor: '#1e293b',
      cornerRadius: 8,
      padding: 12,
    },
  },
}

const avgLabel = (v: number): string => {
  if (v >= 4.5) return 'Отлично'
  if (v >= 3.5) return 'Хорошо'
  if (v >= 2.5) return 'Удовл.'
  return 'Неудовл.'
}

const avgColor = (v: number): string => {
  if (v >= 4.5) return '#10b981'
  if (v >= 3.5) return '#3b82f6'
  if (v >= 2.5) return '#f59e0b'
  return '#ef4444'
}
</script>

<template>
  <div class="page-container">
    <main class="dashboard">
      <header class="page-header">
        <h1>Моя <span class="accent">Статистика</span></h1>
        <p>Обзор успеваемости по всем курсам</p>
      </header>

      <div v-if="isLoading" class="grid-4">
        <div v-for="i in 4" :key="i" class="kpi-skeleton">
          <div class="sk sk-icon" />
          <div class="sk sk-num" />
          <div class="sk sk-label" />
        </div>
      </div>

      <div v-else-if="isError" class="state-card">
        <span class="state-icon">⚠️</span>
        <h3>Не удалось загрузить данные</h3>
        <p>Проверьте подключение и попробуйте ещё раз.</p>
        <button class="retry-btn" @click="loadStats">Повторить</button>
      </div>

      <div v-else-if="isEmpty" class="state-card">
        <span class="state-icon">📭</span>
        <h3>Пока нет данных</h3>
        <p>Оценки появятся после синхронизации с Moodle.</p>
      </div>

      <template v-else>
        <div class="grid-4">
          <div class="kpi-card">
            <div class="kpi-icon">📝</div>
            <div class="kpi-value">{{ stats.totalGradesCount }}</div>
            <div class="kpi-label">Всего оценок</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-icon">📊</div>
            <div class="kpi-value" :style="{ color: avgColor(stats.overallAverageScore) }">
              {{ stats.overallAverageScore }}
            </div>
            <div class="kpi-label">{{ avgLabel(stats.overallAverageScore) }} (из 5)</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-icon">📚</div>
            <div class="kpi-value">{{ stats.coursesCount }}</div>
            <div class="kpi-label">Курсов</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-icon">🔴</div>
            <div class="kpi-value" :style="{ color: stats.weakCount > 0 ? '#ef4444' : 'var(--text-muted)' }">
              {{ stats.weakCount }}
            </div>
            <div class="kpi-label">Слабых оценок</div>
          </div>
        </div>

        <div class="chart-card">
          <h3 class="chart-title">Распределение оценок</h3>
          <div class="donut-wrapper">
            <Doughnut :data="donutData" :options="donutOptions" />
            <div class="donut-center">
              <span class="donut-total">{{ stats.totalGradesCount }}</span>
              <span class="donut-sub">оценок</span>
            </div>
          </div>
        </div>
      </template>
    </main>
  </div>
</template>

<style scoped>
.page-container {
  min-height: 100vh;
  background-color: var(--bg-body);
  color: var(--text-main);
}

.dashboard {
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px 24px;
}

.page-header {
  text-align: center;
  margin-bottom: 36px;
}

.page-header h1 {
  font-size: 40px;
  font-weight: 800;
  margin: 0 0 6px;
}

.accent {
  color: var(--accent-indigo);
}

.page-header p {
  color: var(--text-muted);
  font-size: 18px;
  margin: 0;
}

.grid-4 {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}

@media (max-width: 900px) {
  .grid-4 {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 500px) {
  .grid-4 {
    grid-template-columns: 1fr;
  }
}

.kpi-card {
  background: var(--bg-surface);
  backdrop-filter: var(--glass-blur);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 24px;
  text-align: center;
  transition: transform 0.2s, box-shadow 0.2s;
}

.kpi-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
}

.kpi-icon {
  font-size: 36px;
  margin-bottom: 8px;
}

.kpi-value {
  font-size: 40px;
  font-weight: 800;
  color: var(--text-main);
  line-height: 1;
  margin-bottom: 4px;
}

.kpi-label {
  font-size: 15px;
  color: var(--text-muted);
}

.chart-card {
  background: var(--bg-surface);
  backdrop-filter: var(--glass-blur);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 28px;
  margin-top: 24px;
}

.chart-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-main);
  margin: 0 0 20px;
}

.donut-wrapper {
  position: relative;
  height: 340px;
  max-width: 540px;
  margin: 0 auto;
}

.donut-center {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  pointer-events: none;
  z-index: 2;
  line-height: 1;
}

.donut-total {
  font-size: 44px;
  font-weight: 800;
  color: var(--text-main);
  letter-spacing: -1px;
}

.donut-sub {
  font-size: 15px;
  color: var(--text-muted);
  margin-top: 4px;
}

.kpi-skeleton {
  background: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.sk {
  border-radius: 8px;
  background: linear-gradient(90deg, var(--bg-surface-hover) 25%, var(--border-color) 50%, var(--bg-surface-hover) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

.sk-icon {
  width: 32px;
  height: 32px;
  border-radius: 50%;
}

.sk-num {
  width: 60px;
  height: 28px;
}

.sk-label {
  width: 90px;
  height: 14px;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.state-card {
  background: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 60px 24px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.state-icon {
  font-size: 52px;
}

.state-card h3 {
  font-size: 22px;
  font-weight: 700;
  color: var(--text-main);
  margin: 0;
}

.state-card p {
  color: var(--text-muted);
  margin: 0;
  font-size: 17px;
}

.retry-btn {
  margin-top: 12px;
  padding: 10px 28px;
  border: none;
  border-radius: 10px;
  background: var(--accent-indigo);
  color: white;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.retry-btn:hover {
  background: #6d28d9;
}

/* ─── Mobile ─────────────────────────────────────────── */
@media (max-width: 768px) {
  .page-header h1 {
    font-size: 28px;
  }

  .page-header p {
    font-size: 14px;
  }

  .kpi-value {
    font-size: 28px;
  }

  .kpi-label {
    font-size: 13px;
  }

  .kpi-icon {
    font-size: 28px;
  }

  .chart-title {
    font-size: 15px;
  }

  .donut-total {
    font-size: 32px;
  }

  .donut-sub {
    font-size: 13px;
  }

  .state-card h3 {
    font-size: 18px;
  }

  .state-card p {
    font-size: 14px;
  }

  .state-icon {
    font-size: 40px;
  }

  .retry-btn {
    font-size: 14px;
    padding: 8px 20px;
  }

  .grid-4 {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }
}
</style>
