<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js'
import { Doughnut } from 'vue-chartjs'
import { useAuthStore } from '../stores/auth'
import { useThemeStore } from '../stores/theme'

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
const themeStore = useThemeStore()
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
  isEmpty.value = false

  try {
    const token = authStore.token
    if (!token) return

    const res = await fetch('http://localhost:5135/api/student/statistics', {
      headers: { Authorization: `Bearer ${token}` },
    })

    if (res.ok) {
      const data = await res.json()
      stats.value = {
        ...data,
        courseProgress: data.courseProgress ?? [],
      }
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

const palette = ['#ef4444', '#f59e0b', '#64748b', '#10b981']

const donutData = computed(() => ({
  labels: ['2 - нужно внимание', '3 - базовый уровень', '4 - уверенно', '5 - отлично'],
  datasets: [
    {
      data: [
        stats.value.gradeDistribution.two,
        stats.value.gradeDistribution.three,
        stats.value.gradeDistribution.four,
        stats.value.gradeDistribution.five,
      ],
      backgroundColor: palette,
      borderColor: 'rgba(15, 23, 42, 0.92)',
      borderWidth: 6,
      hoverOffset: 8,
      spacing: 3,
      borderRadius: 8,
    },
  ],
}))

const donutOptions = {
  responsive: true,
  maintainAspectRatio: false,
  cutout: '72%',
  animation: {
    animateRotate: true,
    animateScale: true,
    duration: 900,
  },
  plugins: {
    legend: {
      display: false,
    },
    tooltip: {
      backgroundColor: 'rgba(15, 23, 42, 0.96)',
      borderColor: 'rgba(148, 163, 184, 0.22)',
      borderWidth: 1,
      titleColor: '#f8fafc',
      bodyColor: '#cbd5e1',
      cornerRadius: 10,
      padding: 12,
    },
  },
}

const avgLabel = (value: number): string => {
  if (value >= 4.5) return 'Отличный темп'
  if (value >= 3.5) return 'Стабильный прогресс'
  if (value >= 2.5) return 'Есть база для роста'
  return 'Нужен фокус'
}

const avgColor = (value: number): string => {
  if (value >= 4.5) return '#10b981'
  if (value >= 3.5) return '#64748b'
  if (value >= 2.5) return '#f59e0b'
  return '#ef4444'
}

const progressColor = (percentage: number): string => {
  if (percentage >= 85) return '#10b981'
  if (percentage >= 70) return '#64748b'
  if (percentage >= 60) return '#f59e0b'
  return '#ef4444'
}

const progressLabel = (percentage: number): string => {
  if (percentage >= 85) return 'сильный'
  if (percentage >= 70) return 'уверенный'
  if (percentage >= 60) return 'средний'
  return 'рисковый'
}

const scorePercent = computed(() =>
  Math.min(Math.max((stats.value.overallAverageScore / 5) * 100, 0), 100),
)

const sortedCourses = computed(() =>
  [...stats.value.courseProgress].sort((a, b) => b.averagePercentage - a.averagePercentage),
)

const strongestCourse = computed(() => sortedCourses.value[0])

const weakestCourse = computed(() => sortedCourses.value[sortedCourses.value.length - 1])

const insightText = computed(() => {
  if (stats.value.weakCount > 0) {
    return `Найдено ${stats.value.weakCount} слабых оценок. Начните с курса с минимальным прогрессом и закрепите темы с низкими баллами.`
  }

  if (stats.value.overallAverageScore >= 4.5) {
    return 'Профиль выглядит сильным: оценки ровные, а прогресс держится на высоком уровне.'
  }

  if (stats.value.overallAverageScore >= 3.5) {
    return 'Динамика стабильная. Следующий шаг - подтянуть отдельные курсы до сильной зоны.'
  }

  return 'Статистика показывает пространство для роста. Лучше выбрать один курс и довести его до уверенного уровня.'
})

const gradeLegend = computed(() => [
  { label: '2', caption: 'нужно внимание', value: stats.value.gradeDistribution.two, color: palette[0] },
  { label: '3', caption: 'базовый уровень', value: stats.value.gradeDistribution.three, color: palette[1] },
  { label: '4', caption: 'уверенно', value: stats.value.gradeDistribution.four, color: palette[2] },
  { label: '5', caption: 'отлично', value: stats.value.gradeDistribution.five, color: palette[3] },
])
</script>

<template>
  <div class="stats-page" :class="{ 'stats-page--light': !themeStore.isDark }">
    <div class="surface-grid"></div>
    <main class="stats-shell">
      <section v-if="isLoading" class="state-panel loading-panel">
        <div class="skeleton-head"></div>
        <div class="skeleton-title"></div>
        <div class="skeleton-copy"></div>
        <div class="skeleton-layout">
          <div v-for="i in 5" :key="i" class="skeleton-block"></div>
        </div>
      </section>

      <section v-else-if="isError" class="state-panel">
        <span class="state-mark">!</span>
        <p class="eyebrow">Ошибка загрузки</p>
        <h1>Не удалось получить статистику</h1>
        <p>Проверьте подключение к API и попробуйте еще раз.</p>
        <button class="action-button" @click="loadStats">Повторить</button>
      </section>

      <section v-else-if="isEmpty" class="state-panel">
        <span class="state-mark">i</span>
        <p class="eyebrow">Данных пока нет</p>
        <h1>Статистика появится после синхронизации</h1>
        <p>Когда Moodle передаст оценки, здесь появится аналитика прогресса по курсам.</p>
      </section>

      <template v-else>
        <section class="hero-grid reveal">
          <div class="hero-copy">
            <p class="eyebrow">Учебная аналитика</p>
            <h1>Статистика прогресса</h1>
            <p>
              Сводка показывает средний балл, распределение оценок и курсы,
              которым сейчас нужно больше внимания.
            </p>
          </div>

          <aside class="score-panel liquid-panel">
            <div class="score-meter" :style="{ '--score': `${scorePercent}%`, '--score-color': avgColor(stats.overallAverageScore) }">
              <span>{{ stats.overallAverageScore }}</span>
              <small>из 5</small>
            </div>
            <div class="score-text">
              <strong :style="{ color: avgColor(stats.overallAverageScore) }">{{ avgLabel(stats.overallAverageScore) }}</strong>
              <p>{{ insightText }}</p>
            </div>
          </aside>
        </section>

        <section class="metric-strip reveal" style="--delay: 90ms" aria-label="Ключевые показатели">
          <div class="metric-item">
            <span>Всего оценок</span>
            <strong>{{ stats.totalGradesCount }}</strong>
            <p>учтено в аналитике</p>
          </div>
          <div class="metric-item">
            <span>Курсов</span>
            <strong>{{ stats.coursesCount }}</strong>
            <p>активных направлений</p>
          </div>
          <div class="metric-item">
            <span>Риски</span>
            <strong :style="{ color: stats.weakCount > 0 ? '#ef4444' : '#10b981' }">{{ stats.weakCount }}</strong>
            <p>{{ stats.weakCount > 0 ? 'требуют разбора' : 'критичных нет' }}</p>
          </div>
          <div class="metric-item accent-line">
            <span>Сильный курс</span>
            <strong>{{ strongestCourse ? Math.round(strongestCourse.averagePercentage) : 0 }}%</strong>
            <p>{{ strongestCourse?.courseTitle || 'нет данных' }}</p>
          </div>
        </section>

        <section class="analytics-layout">
          <article class="chart-panel liquid-panel reveal" style="--delay: 180ms">
            <div class="section-heading">
              <div>
                <p class="eyebrow">Распределение</p>
                <h2>Спектр оценок</h2>
              </div>
              <span class="panel-pill">{{ stats.totalGradesCount }} оценок</span>
            </div>

            <div class="chart-wrap">
              <Doughnut :data="donutData" :options="donutOptions" />
              <div class="chart-center">
                <strong>{{ stats.totalGradesCount }}</strong>
                <span>оценок</span>
              </div>
            </div>

            <div class="legend-list">
              <div v-for="item in gradeLegend" :key="item.label" class="legend-row">
                <span class="legend-dot" :style="{ background: item.color }"></span>
                <span>Оценка {{ item.label }}</span>
                <small>{{ item.caption }}</small>
                <strong>{{ item.value }}</strong>
              </div>
            </div>
          </article>

          <aside class="insight-panel liquid-panel reveal" style="--delay: 260ms">
            <p class="eyebrow">Фокус</p>
            <h2>Что важно сейчас</h2>
            <p>{{ insightText }}</p>
            <div class="focus-grid">
              <div>
                <span>Лучший курс</span>
                <strong>{{ strongestCourse?.courseTitle || 'нет данных' }}</strong>
              </div>
              <div>
                <span>Нижняя зона</span>
                <strong>{{ weakestCourse?.courseTitle || 'нет данных' }}</strong>
              </div>
            </div>
          </aside>
        </section>

        <section class="courses-panel liquid-panel reveal" style="--delay: 340ms">
          <div class="section-heading">
            <div>
              <p class="eyebrow">Курсы</p>
              <h2>Прогресс по направлениям</h2>
            </div>
            <span class="panel-pill">{{ stats.coursesCount }} курсов</span>
          </div>

          <div class="course-list">
            <article
              v-for="(course, index) in sortedCourses"
              :key="course.courseTitle"
              class="course-row reveal-row"
              :style="{ '--row-delay': `${index * 70}ms` }"
            >
              <div class="course-rank">{{ String(index + 1).padStart(2, '0') }}</div>
              <div class="course-body">
                <div class="course-head">
                  <strong>{{ course.courseTitle }}</strong>
                  <span :style="{ color: progressColor(course.averagePercentage), borderColor: progressColor(course.averagePercentage) }">
                    {{ progressLabel(course.averagePercentage) }}
                  </span>
                </div>
                <div class="progress-track">
                  <div
                    class="progress-fill"
                    :style="{
                      width: `${Math.min(Math.max(course.averagePercentage, 0), 100)}%`,
                      background: progressColor(course.averagePercentage),
                    }"
                  ></div>
                </div>
              </div>
              <div class="course-percent" :style="{ color: progressColor(course.averagePercentage) }">
                {{ Math.round(course.averagePercentage) }}%
              </div>
            </article>
          </div>
        </section>
      </template>
    </main>
  </div>
</template>

<style scoped>
.stats-page {
  --stats-bg: #0f172a;
  --stats-surface: rgba(15, 23, 42, 0.74);
  --stats-surface-strong: rgba(15, 23, 42, 0.9);
  --stats-card: rgba(30, 41, 59, 0.58);
  --stats-border: rgba(148, 163, 184, 0.18);
  --stats-text: #f8fafc;
  --stats-muted: #94a3b8;
  --stats-soft: rgba(16, 185, 129, 0.12);
  --stats-accent: #10b981;
  --stats-shadow: 0 28px 80px -42px rgba(2, 6, 23, 0.9);
  background:
    radial-gradient(circle at 14% 16%, rgba(16, 185, 129, 0.14), transparent 30%),
    linear-gradient(135deg, #111827 0%, var(--stats-bg) 54%, #182033 100%);
  color: var(--stats-text);
  font-family: 'Satoshi', 'Geist', 'Outfit', system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
  min-height: 100dvh;
  overflow: hidden;
  position: relative;
}

.stats-page--light,
:global(body.light-theme) .stats-page,
:global(html.light-theme) .stats-page,
:global([data-theme='light']) .stats-page {
  --stats-bg: #f8fafc;
  --stats-surface: rgba(255, 255, 255, 0.78);
  --stats-surface-strong: rgba(255, 255, 255, 0.94);
  --stats-card: rgba(255, 255, 255, 0.66);
  --stats-border: rgba(15, 23, 42, 0.1);
  --stats-text: #0f172a;
  --stats-muted: #64748b;
  --stats-soft: rgba(16, 185, 129, 0.1);
  --stats-shadow: 0 28px 80px -48px rgba(15, 23, 42, 0.32);
  background:
    radial-gradient(circle at 18% 8%, rgba(16, 185, 129, 0.12), transparent 30%),
    linear-gradient(135deg, #f8fafc 0%, #eef2f7 58%, #f9fafb 100%);
}

.surface-grid {
  background-image:
    linear-gradient(var(--stats-border) 1px, transparent 1px),
    linear-gradient(90deg, var(--stats-border) 1px, transparent 1px);
  background-size: 52px 52px;
  inset: 0;
  mask-image: linear-gradient(to bottom, rgba(0, 0, 0, 0.8), transparent 82%);
  opacity: 0.28;
  pointer-events: none;
  position: fixed;
}

.stats-shell {
  margin: 0 auto;
  max-width: 1400px;
  padding: clamp(24px, 4vw, 48px) clamp(16px, 3vw, 32px) 56px;
  position: relative;
}

.hero-grid {
  display: grid;
  gap: clamp(24px, 5vw, 72px);
  grid-template-columns: minmax(0, 1.45fr) minmax(320px, 0.75fr);
  margin-bottom: 28px;
}

.hero-copy {
  padding-top: clamp(8px, 4vw, 48px);
}

.eyebrow {
  color: var(--stats-accent);
  font-size: 0.78rem;
  font-weight: 900;
  letter-spacing: 0.16em;
  margin: 0 0 10px;
  text-transform: uppercase;
}

.hero-copy h1 {
  color: var(--stats-text);
  font-size: clamp(2.7rem, 7vw, 5.7rem);
  font-weight: 900;
  letter-spacing: 0;
  line-height: 0.95;
  max-width: 820px;
}

.hero-copy p:not(.eyebrow) {
  color: var(--stats-muted);
  font-size: clamp(1rem, 1.6vw, 1.22rem);
  line-height: 1.8;
  margin: 24px 0 0;
  max-width: 680px;
}

.liquid-panel,
.state-panel {
  backdrop-filter: blur(24px);
  background: var(--stats-surface);
  border: 1px solid var(--stats-border);
  box-shadow: var(--stats-shadow), inset 0 1px 0 rgba(255, 255, 255, 0.08);
}

.score-panel {
  align-self: stretch;
  border-radius: 32px;
  display: grid;
  gap: 24px;
  min-height: 360px;
  padding: 28px;
  place-items: center;
}

.score-meter {
  --score: 0%;
  --score-color: var(--stats-accent);
  align-items: center;
  background:
    radial-gradient(circle at center, var(--stats-surface-strong) 0 58%, transparent 59%),
    conic-gradient(var(--score-color) var(--score), rgba(148, 163, 184, 0.18) 0);
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  height: clamp(180px, 20vw, 240px);
  justify-content: center;
  position: relative;
  width: clamp(180px, 20vw, 240px);
}

.score-meter::after {
  border: 1px solid var(--stats-border);
  border-radius: inherit;
  content: '';
  inset: 14px;
  position: absolute;
}

.score-meter span {
  color: var(--stats-text);
  font-family: 'Geist Mono', 'JetBrains Mono', Consolas, monospace;
  font-size: clamp(3.4rem, 6vw, 5rem);
  font-weight: 900;
  line-height: 1;
}

.score-meter small,
.chart-center span {
  color: var(--stats-muted);
  font-size: 0.82rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.score-text {
  text-align: center;
}

.score-text strong {
  display: block;
  font-size: 1.22rem;
  margin-bottom: 8px;
}

.score-text p {
  color: var(--stats-muted);
  line-height: 1.65;
  margin: 0;
}

.metric-strip {
  border-bottom: 1px solid var(--stats-border);
  border-top: 1px solid var(--stats-border);
  display: grid;
  grid-template-columns: 1.1fr 0.8fr 0.8fr 1.3fr;
  margin-bottom: 28px;
}

.metric-item {
  padding: 24px 28px;
  position: relative;
}

.metric-item + .metric-item {
  border-left: 1px solid var(--stats-border);
}

.metric-item span,
.focus-grid span {
  color: var(--stats-muted);
  display: block;
  font-size: 0.82rem;
  font-weight: 800;
  margin-bottom: 10px;
}

.metric-item strong {
  color: var(--stats-text);
  display: block;
  font-family: 'Geist Mono', 'JetBrains Mono', Consolas, monospace;
  font-size: clamp(2.1rem, 4vw, 3.25rem);
  font-weight: 900;
  line-height: 1;
}

.metric-item p {
  color: var(--stats-muted);
  font-size: 0.92rem;
  margin: 10px 0 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.accent-line::before {
  background: var(--stats-accent);
  content: '';
  height: 100%;
  left: -1px;
  position: absolute;
  top: 0;
  width: 2px;
}

.analytics-layout {
  display: grid;
  gap: 28px;
  grid-template-columns: minmax(0, 1.2fr) minmax(300px, 0.8fr);
  margin-bottom: 28px;
}

.chart-panel,
.insight-panel,
.courses-panel {
  border-radius: 32px;
  padding: clamp(22px, 3vw, 34px);
}

.section-heading {
  align-items: flex-start;
  display: flex;
  gap: 16px;
  justify-content: space-between;
  margin-bottom: 28px;
}

.section-heading h2,
.insight-panel h2 {
  color: var(--stats-text);
  font-size: clamp(1.6rem, 3vw, 2.2rem);
  font-weight: 900;
}

.panel-pill {
  border: 1px solid var(--stats-border);
  border-radius: 999px;
  color: var(--stats-muted);
  flex-shrink: 0;
  font-size: 0.78rem;
  font-weight: 900;
  padding: 7px 12px;
}

.chart-wrap {
  height: 360px;
  margin: 0 auto;
  max-width: 520px;
  position: relative;
}

.chart-center {
  align-items: center;
  display: flex;
  flex-direction: column;
  inset: 0;
  justify-content: center;
  pointer-events: none;
  position: absolute;
}

.chart-center strong {
  color: var(--stats-text);
  font-family: 'Geist Mono', 'JetBrains Mono', Consolas, monospace;
  font-size: 3.2rem;
  font-weight: 900;
  line-height: 1;
}

.legend-list {
  display: grid;
  gap: 10px;
  margin-top: 24px;
}

.legend-row {
  align-items: center;
  border-top: 1px solid var(--stats-border);
  display: grid;
  gap: 12px;
  grid-template-columns: 12px 1fr 1fr auto;
  padding-top: 12px;
}

.legend-dot {
  border-radius: 50%;
  height: 9px;
  width: 9px;
}

.legend-row span,
.legend-row small {
  color: var(--stats-muted);
  font-size: 0.9rem;
}

.legend-row strong {
  color: var(--stats-text);
  font-family: 'Geist Mono', 'JetBrains Mono', Consolas, monospace;
}

.insight-panel {
  display: flex;
  flex-direction: column;
}

.insight-panel p:not(.eyebrow) {
  color: var(--stats-muted);
  font-size: 1rem;
  line-height: 1.75;
}

.focus-grid {
  display: grid;
  gap: 14px;
  margin-top: auto;
  padding-top: 28px;
}

.focus-grid div {
  border-top: 1px solid var(--stats-border);
  padding-top: 16px;
}

.focus-grid strong {
  color: var(--stats-text);
  display: block;
  font-size: 1rem;
  line-height: 1.35;
}

.course-list {
  display: grid;
  gap: 12px;
}

.course-row {
  align-items: center;
  background: var(--stats-card);
  border: 1px solid var(--stats-border);
  border-radius: 20px;
  display: grid;
  gap: 18px;
  grid-template-columns: 54px minmax(0, 1fr) 80px;
  padding: 16px;
  transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1), border-color 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.course-row:hover {
  border-color: rgba(16, 185, 129, 0.42);
  transform: translateY(-2px);
}

.course-row:active,
.action-button:active {
  transform: translateY(1px) scale(0.99);
}

.course-rank {
  color: var(--stats-muted);
  font-family: 'Geist Mono', 'JetBrains Mono', Consolas, monospace;
  font-size: 1.25rem;
  font-weight: 900;
}

.course-head {
  align-items: center;
  display: flex;
  gap: 12px;
  justify-content: space-between;
  margin-bottom: 10px;
}

.course-head strong {
  color: var(--stats-text);
  font-size: 1rem;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.course-head span {
  border: 1px solid;
  border-radius: 999px;
  flex-shrink: 0;
  font-size: 0.72rem;
  font-weight: 900;
  letter-spacing: 0.06em;
  padding: 4px 8px;
  text-transform: uppercase;
}

.progress-track {
  background: rgba(148, 163, 184, 0.16);
  border-radius: 999px;
  height: 8px;
  overflow: hidden;
}

.progress-fill {
  animation: fillIn 0.9s cubic-bezier(0.16, 1, 0.3, 1) both;
  border-radius: inherit;
  height: 100%;
  transform-origin: left;
}

.course-percent {
  font-family: 'Geist Mono', 'JetBrains Mono', Consolas, monospace;
  font-size: 1.25rem;
  font-weight: 900;
  text-align: right;
}

.state-panel {
  align-items: center;
  border-radius: 32px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin: 56px auto;
  max-width: 760px;
  padding: clamp(32px, 7vw, 72px);
  text-align: center;
}

.state-mark {
  align-items: center;
  background: var(--stats-soft);
  border: 1px solid rgba(16, 185, 129, 0.26);
  border-radius: 50%;
  color: var(--stats-accent);
  display: inline-flex;
  font-size: 1.5rem;
  font-weight: 900;
  height: 64px;
  justify-content: center;
  width: 64px;
}

.state-panel h1 {
  color: var(--stats-text);
  font-size: clamp(2rem, 5vw, 3.5rem);
  font-weight: 900;
}

.state-panel p:not(.eyebrow) {
  color: var(--stats-muted);
  margin: 0;
}

.action-button {
  background: var(--stats-accent);
  border: none;
  border-radius: 999px;
  color: #ffffff;
  font-size: 1rem;
  font-weight: 900;
  margin-top: 8px;
  padding: 12px 28px;
  transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1), filter 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.action-button:hover {
  filter: brightness(0.94);
  transform: translateY(-1px);
}

.loading-panel {
  align-items: stretch;
}

.skeleton-head,
.skeleton-title,
.skeleton-copy,
.skeleton-block {
  animation: skeletonSweep 1.35s ease-in-out infinite;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.12), transparent), var(--stats-card);
  background-size: 240% 100%;
  border: 1px solid var(--stats-border);
  border-radius: 18px;
}

.skeleton-head {
  height: 18px;
  width: 180px;
}

.skeleton-title {
  height: 58px;
  width: min(520px, 100%);
}

.skeleton-copy {
  height: 22px;
  width: min(640px, 100%);
}

.skeleton-layout {
  display: grid;
  gap: 16px;
  grid-template-columns: 1.4fr 1fr;
  margin-top: 20px;
}

.skeleton-block {
  height: 156px;
}

.skeleton-block:first-child {
  grid-row: span 2;
  height: auto;
}

.reveal {
  animation: revealUp 0.75s cubic-bezier(0.16, 1, 0.3, 1) both;
  animation-delay: var(--delay, 0ms);
}

.reveal-row {
  animation: revealUp 0.65s cubic-bezier(0.16, 1, 0.3, 1) both;
  animation-delay: var(--row-delay, 0ms);
}

@keyframes revealUp {
  from {
    opacity: 0;
    transform: translateY(24px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fillIn {
  from {
    transform: scaleX(0);
  }
  to {
    transform: scaleX(1);
  }
}

@keyframes skeletonSweep {
  from {
    background-position: 180% 0;
  }
  to {
    background-position: -80% 0;
  }
}

@media (max-width: 1080px) {
  .hero-grid,
  .analytics-layout {
    grid-template-columns: 1fr;
  }

  .metric-strip {
    grid-template-columns: repeat(2, 1fr);
  }

  .metric-item:nth-child(3) {
    border-left: none;
    border-top: 1px solid var(--stats-border);
  }

  .metric-item:nth-child(4) {
    border-top: 1px solid var(--stats-border);
  }
}

@media (max-width: 720px) {
  .stats-shell {
    padding: 28px 16px 40px;
  }

  .hero-grid {
    gap: 22px;
  }

  .hero-copy {
    padding-top: 0;
  }

  .hero-copy h1 {
    font-size: 2.7rem;
  }

  .score-panel,
  .chart-panel,
  .insight-panel,
  .courses-panel,
  .state-panel {
    border-radius: 24px;
    padding: 20px;
  }

  .metric-strip,
  .skeleton-layout {
    grid-template-columns: 1fr;
  }

  .metric-item,
  .metric-item:nth-child(3),
  .metric-item:nth-child(4) {
    border-left: none;
    border-top: 1px solid var(--stats-border);
  }

  .metric-item:first-child {
    border-top: none;
  }

  .section-heading,
  .course-head {
    align-items: flex-start;
    flex-direction: column;
  }

  .legend-row {
    grid-template-columns: 12px 1fr auto;
  }

  .legend-row small {
    display: none;
  }

  .chart-wrap {
    height: 300px;
  }

  .course-row {
    grid-template-columns: 1fr;
  }

  .course-head strong {
    white-space: normal;
  }

  .course-percent {
    text-align: left;
  }
}

@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
</style>
