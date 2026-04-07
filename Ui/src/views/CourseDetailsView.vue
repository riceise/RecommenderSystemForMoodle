<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import ResizableChat from '../components/ResizableChat.vue'

const assignmentIcons = {
  code: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="16 18 22 12 16 6"></polyline><polyline points="8 6 2 12 8 18"></polyline></svg>',
  database: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5" rx="9" ry="3"></ellipse><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"></path><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"></path></svg>',
  account_tree: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="5" r="3"></circle><path d="M12 8v8"></path><path d="M8 20h8"></path><path d="M6 16l-3 4"></path><path d="M18 16l3 4"></path></svg>',
  data_array: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"></rect><line x1="9" y1="9" x2="15" y2="9"></line><line x1="9" y1="15" x2="15" y2="15"></line></svg>',
  functions: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 18h4l4-12h4"></path><path d="M14 18h6"></path><path d="M2 12h2"></path><path d="M20 12h2"></path></svg>',
  security: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>',
}

const isActiveIndicator = (index: number, percentage: number): boolean => {
  const thresholds = [1, 25, 50, 90]
  const idx = index - 1
  const threshold = thresholds[idx]
  return idx >= 0 && threshold !== undefined && percentage >= threshold
}

interface Assignment {
  id: string
  name: string
  grade: number
  maxGrade: number
  submittedDate?: string
  difficulty?: string
  percentage: number
}

interface SkillChart {
  name: string
  percentage: number
  description: string
  color: string
}

interface AIRecommendation {
  title: string
  description: string
  resourceType: string
  url: string | null
  relevanceScore: number
  difficulty: string
}

interface AIAnalysis {
  analysis: string
  weakTopics: string[]
  strongTopics: string[]
  recommendations: AIRecommendation[]
}

const route = useRoute()
const authStore = useAuthStore()

const isLoading = ref(true)
const courseTitle = ref('')
const totalEarned = ref(0)
const totalMax = ref(0)
const assignments = ref<Assignment[]>([])
const skillCharts = ref<SkillChart[]>([])

const isAILoading = ref(false)
const aiAnalysis = ref<AIAnalysis | null>(null)

const getGradeColor = (percentage: number): string => {
  if (percentage >= 90) return '#4ade80'
  if (percentage >= 70) return '#60a5fa'
  if (percentage >= 60) return '#fbbf24'
  return '#f87171'
}

const getGradeFromPercent = (percentage: number): number => {
  if (percentage >= 90) return 5
  if (percentage >= 70) return 4
  if (percentage >= 60) return 3
  return 2
}

const calculatePercentage = (grade: number, maxGrade: number): number => {
  if (!maxGrade || maxGrade === 0) return 0
  return Math.min(Math.round((grade / maxGrade) * 100), 100)
}

const findWeakestSkill = (): SkillChart => {
  if (assignments.value.length === 0) {
    return {
      name: 'GENERAL',
      percentage: 0,
      description: 'Нет данных для анализа',
      color: '#f87171',
    }
  }

  const weakest = assignments.value.reduce((min, current) => {
    return current.percentage < min.percentage ? current : min
  })

  const topicName = extractTopicFromName(weakest.name)
  const description = generateWeaknessDescription(topicName, weakest.percentage)

  return {
    name: topicName,
    percentage: weakest.percentage,
    description,
    color: getGradeColor(weakest.percentage),
  }
}

const extractTopicFromName = (name: string): string => {
  const nameLower = name.toLowerCase()

  if (nameLower.includes('sql') || nameLower.includes('query') || nameLower.includes('database'))
    return 'SQL PROFICIENCY'
  if (nameLower.includes('oop') || nameLower.includes('class') || nameLower.includes('object'))
    return 'OOP FOCUS'
  if (nameLower.includes('array') || nameLower.includes('list'))
    return 'ARRAYS'
  if (nameLower.includes('algorithm') || nameLower.includes('sort') || nameLower.includes('search'))
    return 'ALGORITHMS'
  if (nameLower.includes('tree') || nameLower.includes('graph'))
    return 'DATA STRUCTURES'

  return 'COURSE SKILLS'
}

const generateWeaknessDescription = (topic: string, percentage: number): string => {
  const grade = getGradeFromPercent(percentage)

  if (grade === 2) return `Критический уровень. Требуется срочная работа над ${topic.toLowerCase()}.`
  if (grade === 3) return `Базовое понимание есть, но нужно больше практики в ${topic.toLowerCase()}.`
  if (grade === 4) return `Хороший результат, но есть пространство для улучшения в ${topic.toLowerCase()}.`
  return `Отличная работа! ${topic} усвоен хорошо.`
}

const getAssignmentIcon = (_index: number, name: string): string => {
  const nameLower = name.toLowerCase()

  if (nameLower.includes('sql') || nameLower.includes('query') || nameLower.includes('database'))
    return assignmentIcons.database
  if (nameLower.includes('array') || nameLower.includes('list'))
    return assignmentIcons.data_array
  if (nameLower.includes('oop') || nameLower.includes('class') || nameLower.includes('object'))
    return assignmentIcons.code
  if (nameLower.includes('tree'))
    return assignmentIcons.account_tree
  if (nameLower.includes('exception') || nameLower.includes('error'))
    return assignmentIcons.security
  if (nameLower.includes('function') || nameLower.includes('method'))
    return assignmentIcons.functions

  return assignmentIcons.code
}

const getDifficultyLabel = (diff?: string): string => {
  if (!diff) return 'Standard difficulty'
  if (diff === 'Advanced') return 'Advanced difficulty'
  if (diff === 'Medium') return 'Medium difficulty'
  return 'Standard difficulty'
}

const getIndicatorColor = (percentage: number): string => {
  if (percentage >= 90) return '#4ade80'
  if (percentage >= 70) return '#60a5fa'
  if (percentage >= 60) return '#fbbf24'
  return '#f87171'
}

const resourceTypeLabel = (type: string): string => {
  const map: Record<string, string> = {
    article: '📄 Статья',
    video: '🎬 Видео',
    course: '📚 Курс',
    exercise: '✏️ Упражнение',
  }
  return map[type] || '📄 Ресурс'
}

const loadAIAnalysis = async () => {
  isAILoading.value = true
  try {
    const token = authStore.token
    if (!token) return

    const courseId = route.params.id as string
    const response = await fetch(`http://localhost:5135/api/student/courses/${courseId}/ai-analysis`, {
      headers: { Authorization: `Bearer ${token}` },
    })

    if (response.ok) {
      aiAnalysis.value = await response.json()
    } else {
      aiAnalysis.value = {
        analysis: 'AI-анализ временно недоступен. Попробуйте позже.',
        weakTopics: [],
        strongTopics: [],
        recommendations: [],
      }
    }
  } catch (err) {
    console.error('AI analysis load error:', err)
    aiAnalysis.value = {
      analysis: 'Ошибка загрузки AI-анализа.',
      weakTopics: [],
      strongTopics: [],
      recommendations: [],
    }
  } finally {
    isAILoading.value = false
  }
}

onMounted(async () => {
  try {
    const token = authStore.token
    if (!token) return

    const courseRes = await fetch(`http://localhost:5135/api/student/courses/${route.params.id}`, {
      headers: { Authorization: `Bearer ${token}` },
    })

    if (courseRes.ok) {
      const data = await courseRes.json()
      courseTitle.value = data.title || 'Course'

      const rawAssignments = data.assignments || []

      let totalEarnedSum = 0
      let totalMaxSum = 0

      assignments.value = rawAssignments.map((a: any, index: number) => {
        const grade = a.grade ?? 0
        const maxGrade = a.maxGrade || 1

        totalEarnedSum += grade
        totalMaxSum += maxGrade

        const percentage = calculatePercentage(grade, maxGrade)

        return {
          id: a.id?.toString() || index.toString(),
          name: a.name || 'Unnamed Assignment',
          grade,
          maxGrade,
          percentage,
          difficulty: a.difficulty || (index % 2 === 0 ? 'Advanced' : 'Standard'),
          submittedDate: a.submittedDate || `Jan ${14 + index * 7}`,
        }
      })

      totalEarned.value = totalEarnedSum
      totalMax.value = totalMaxSum

      const overallPercent = calculatePercentage(totalEarnedSum, totalMaxSum)
      const weakestSkill = findWeakestSkill()

      skillCharts.value = [
        {
          name: 'COURSE PROGRESS',
          percentage: overallPercent,
          description: `Вы набрали ${totalEarnedSum} из ${totalMaxSum} баллов`,
          color: getGradeColor(overallPercent),
        },
        weakestSkill,
      ]

      await loadAIAnalysis()
    }
  } catch (error) {
    console.error('Ошибка загрузки данных:', error)
  } finally {
    isLoading.value = false
  }
})

const coursePercentage = computed(() => {
  return calculatePercentage(totalEarned.value, totalMax.value)
})
</script>

<template>
  <!-- Loader -->
  <div v-if="isLoading" class="loader-container">
    <div class="spinner"></div>
  </div>

  <div v-else class="course-view-wrapper">
    <div class="course-main-content">
      <!-- Заголовок -->
      <header class="course-header">
        <div>
          <h1 class="course-title">{{ courseTitle }}</h1>
          <p class="course-meta">Advanced Computer Science track • Semester 2, 2024</p>
        </div>
        <div class="grade-summary">
          <span class="grade-label">OVERALL GRADE</span>
          <div class="grade-value-wrapper">
            <span class="grade-value">{{ coursePercentage }}%</span>
            <div
              class="grade-badge"
              :style="{
                borderColor: getGradeColor(coursePercentage),
                color: getGradeColor(coursePercentage),
              }"
            >
              {{ getGradeFromPercent(coursePercentage) }}.0
            </div>
          </div>
        </div>
      </header>

      <!-- ═══════════ AI ANALYTICS SECTION ═══════════ -->
      <section class="ai-analytics-section">
        <div class="ai-analytics-header">
          <h2>
            <span class="ai-icon">🧠</span>
            AI-Аналитика
          </h2>
          <button
            v-if="!isAILoading && !aiAnalysis"
            @click="loadAIAnalysis"
            class="btn-reload"
          >
            Обновить
          </button>
        </div>

        <!-- Skeleton Loader -->
        <div v-if="isAILoading" class="ai-skeleton">
          <div class="skeleton-line skeleton-wide"></div>
          <div class="skeleton-row">
            <div class="skeleton-line skeleton-short"></div>
            <div class="skeleton-line skeleton-short"></div>
          </div>
          <div class="skeleton-line skeleton-wide"></div>
          <div class="skeleton-line skeleton-medium"></div>
          <div class="skeleton-cards">
            <div class="skeleton-card"></div>
            <div class="skeleton-card"></div>
            <div class="skeleton-card"></div>
          </div>
        </div>

        <!-- AI Content -->
        <div v-else-if="aiAnalysis" class="ai-content">
          <!-- Analysis text -->
          <div class="ai-analysis-text">
            <p>{{ aiAnalysis.analysis }}</p>
          </div>

          <!-- Weak & Strong topics -->
          <div class="topics-row">
            <div v-if="aiAnalysis.weakTopics.length" class="topic-column weak-column">
              <h3 class="topic-column-title">
                <span class="topic-dot weak-dot"></span>
                Слабые темы
              </h3>
              <ul class="topic-list">
                <li
                  v-for="(topic, i) in aiAnalysis.weakTopics"
                  :key="i"
                  class="topic-item topic-weak"
                >
                  {{ topic }}
                </li>
              </ul>
            </div>

            <div v-if="aiAnalysis.strongTopics.length" class="topic-column strong-column">
              <h3 class="topic-column-title">
                <span class="topic-dot strong-dot"></span>
                Сильные темы
              </h3>
              <ul class="topic-list">
                <li
                  v-for="(topic, i) in aiAnalysis.strongTopics"
                  :key="i"
                  class="topic-item topic-strong"
                >
                  {{ topic }}
                </li>
              </ul>
            </div>
          </div>

          <!-- Recommendations cards -->
          <div v-if="aiAnalysis.recommendations.length" class="ai-recommendations">
            <h3 class="recommendations-title">Персональные рекомендации</h3>
            <div class="recommendations-grid">
              <div
                v-for="(rec, idx) in aiAnalysis.recommendations"
                :key="idx"
                class="rec-card"
              >
                <div class="rec-card-header">
                  <span class="rec-type">{{ resourceTypeLabel(rec.resourceType) }}</span>
                  <span
                    class="rec-score"
                    :style="{
                      color: getGradeColor(rec.relevanceScore * 100),
                      borderColor: getGradeColor(rec.relevanceScore * 100),
                    }"
                  >
                    {{ Math.round(rec.relevanceScore * 100) }}%
                  </span>
                </div>
                <h4 class="rec-title">{{ rec.title }}</h4>
                <p class="rec-description">{{ rec.description }}</p>
                <div
                  v-if="rec.url"
                  class="rec-link-wrapper"
                >
                  <a :href="rec.url" target="_blank" rel="noopener" class="rec-link">
                    Перейти →
                  </a>
                </div>
                <div class="rec-difficulty">{{ rec.difficulty }}</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <div class="widgets-grid">
        <div class="main-widgets-col">
          <section class="widget dark-widget assignments-widget">
            <div class="widget-header">
              <h3>Assignment Performance <span class="pulse-dot"></span></h3>
              <div class="header-icons">⋮</div>
            </div>

            <div class="assignments-list">
              <div
                v-for="(item, idx) in assignments"
                :key="item.id"
                class="assignment-card"
                :class="{ critical: item.percentage < 60 }"
              >
                <div class="assign-left">
                  <div
                    class="assign-icon-wrapper"
                    v-html="getAssignmentIcon(idx, item.name)"
                  ></div>
                  <div class="assign-info">
                    <h4 class="assign-title">{{ item.name }}</h4>
                    <p class="assign-meta">
                      Submitted {{ item.submittedDate }} • {{ getDifficultyLabel(item.difficulty) }}
                    </p>
                  </div>
                </div>

                <div class="assign-right">
                  <div class="progress-wrapper">
                    <div class="progress-track">
                      <div
                        class="progress-fill"
                        :style="{
                          width: `${item.percentage}%`,
                          backgroundColor: getGradeColor(item.percentage),
                        }"
                      ></div>
                    </div>
                  </div>
                  <div
                    class="grade-badge-large"
                    :style="{
                      borderColor: getGradeColor(item.percentage),
                      color: getGradeColor(item.percentage),
                    }"
                  >
                    {{ getGradeFromPercent(item.percentage) }}
                  </div>
                </div>
              </div>
            </div>
          </section>
        </div>

        <div class="side-widgets-col">
          <section
            v-for="(skill, index) in skillCharts"
            :key="index"
            class="widget dark-widget skill-widget"
          >
            <div class="circular-chart-wrapper">
              <svg class="circular-chart" viewBox="0 0 36 36">
                <path
                  class="circle-bg"
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                />
                <path
                  class="circle"
                  :stroke="skill.color"
                  :stroke-dasharray="`${skill.percentage}, 100`"
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                />
              </svg>
              <div class="chart-center">
                <span class="chart-percentage" :style="{ color: skill.color }">
                  {{ skill.percentage }}%
                </span>
                <span class="chart-label">{{ skill.name }}</span>
              </div>
            </div>

            <p class="skill-description">{{ skill.description }}</p>

            <div class="skill-indicators">
              <div
                v-for="i in 4"
                :key="i"
                class="indicator-bar"
                :class="{ active: isActiveIndicator(i, skill.percentage) }"
                :style="{
                  backgroundColor: isActiveIndicator(i, skill.percentage)
                    ? getIndicatorColor(skill.percentage)
                    : '',
                }"
              ></div>
            </div>
          </section>
        </div>
      </div>
    </div>

    <ResizableChat :course-id="(route.params.id as string)" />
  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@500;700&display=swap');


.loader-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: calc(100vh - 120px);
  width: 100%;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid var(--border-color);
  border-top-color: #ba9eff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.course-view-wrapper {
  display: grid;
  grid-template-columns: 1fr 380px;
  gap: 24px;
  max-width: 1600px;
  margin: 0 auto;
  font-family: 'Inter', sans-serif;
}

@media (max-width: 1100px) {
  .course-view-wrapper {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 600px) {
  .course-view-wrapper {
    gap: 16px;
  }
}

.course-main-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* ─── AI Analytics Section ──────────────────────────────── */
.ai-analytics-section {
  background: var(--bg-surface);
  backdrop-filter: var(--glass-blur);
  border: 1px solid var(--border-color);
  border-radius: 20px;
  padding: 28px;
  position: relative;
  overflow: hidden;
}

.ai-analytics-section::before {
  content: '';
  position: absolute;
  top: -50%;
  right: -10%;
  width: 250px;
  height: 250px;
  background: radial-gradient(circle, rgba(139, 92, 246, 0.08) 0%, transparent 70%);
  pointer-events: none;
}

.ai-analytics-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.ai-analytics-header h2 {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 22px;
  font-weight: 700;
  color: var(--text-main);
  margin: 0;
  display: flex;
  align-items: center;
  gap: 10px;
}

.ai-icon {
  font-size: 28px;
}

.btn-reload {
  background: var(--bg-surface-hover);
  border: 1px solid var(--border-color);
  color: var(--text-main);
  padding: 8px 18px;
  border-radius: 10px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-reload:hover {
  background: var(--accent-indigo);
  color: white;
  border-color: var(--accent-indigo);
}

.ai-skeleton {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.skeleton-line {
  height: 16px;
  border-radius: 8px;
  background: linear-gradient(90deg, var(--bg-surface-hover) 25%, var(--border-color) 50%, var(--bg-surface-hover) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

.skeleton-wide {
  width: 100%;
}

.skeleton-medium {
  width: 70%;
}

.skeleton-short {
  width: 30%;
}

.skeleton-row {
  display: flex;
  gap: 12px;
}

.skeleton-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-top: 8px;
}

.skeleton-card {
  height: 120px;
  border-radius: 12px;
  background: linear-gradient(90deg, var(--bg-surface-hover) 25%, var(--border-color) 50%, var(--bg-surface-hover) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

@keyframes shimmer {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}

/* AI Content */
.ai-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.ai-analysis-text p {
  font-size: 17px;
  line-height: 1.7;
  color: var(--text-main);
  margin: 0;
}

/* Topics */
.topics-row {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
}

.topic-column {
  flex: 1;
  min-width: 180px;
}

.topic-column-title {
  font-size: 15px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: var(--text-muted);
  margin: 0 0 12px 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.topic-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}

.weak-dot {
  background: #ef4444;
}

.strong-dot {
  background: #10b981;
}

.topic-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.topic-item {
  padding: 8px 14px;
  border-radius: 10px;
  font-size: 16px;
  font-weight: 500;
}

.topic-weak {
  background: rgba(239, 68, 68, 0.08);
  color: #ef4444;
  border: 1px solid rgba(239, 68, 68, 0.15);
}

.topic-strong {
  background: rgba(16, 185, 129, 0.08);
  color: #10b981;
  border: 1px solid rgba(16, 185, 129, 0.15);
}

.recommendations-title {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 18px;
  font-weight: 700;
  color: var(--text-main);
  margin: 0 0 16px 0;
}

.recommendations-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 16px;
}

.rec-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 14px;
  padding: 18px;
  transition: all 0.2s;
}

.rec-card:hover {
  border-color: var(--accent-indigo);
  transform: translateY(-2px);
}

.rec-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.rec-type {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-muted);
}

.rec-score {
  font-size: 14px;
  font-weight: 700;
  border: 1px solid;
  padding: 2px 8px;
  border-radius: 8px;
}

.rec-title {
  font-size: 17px;
  font-weight: 600;
  color: var(--text-main);
  margin: 0 0 8px 0;
  line-height: 1.3;
}

.rec-description {
  font-size: 15px;
  color: var(--text-muted);
  line-height: 1.5;
  margin: 0 0 12px 0;
}

.rec-link-wrapper {
  margin-bottom: 8px;
}

.rec-link {
  font-size: 15px;
  font-weight: 600;
  color: var(--accent-indigo);
  text-decoration: none;
}

.rec-link:hover {
  text-decoration: underline;
}

.rec-difficulty {
  font-size: 13px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.course-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 10px;
  flex-wrap: wrap;
  gap: 20px;
}

.course-title {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 36px;
  font-weight: 700;
  margin: 0 0 8px 0;
  color: var(--text-main);
  letter-spacing: -0.5px;
}

.course-meta {
  color: var(--text-muted);
  font-size: 16px;
  margin: 0;
}

.grade-summary {
  text-align: right;
}

.grade-label {
  font-size: 12px;
  font-weight: 700;
  color: var(--text-muted);
  letter-spacing: 1.5px;
  text-transform: uppercase;
  display: block;
}

.grade-value-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 6px;
}

.grade-value {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 40px;
  font-weight: 700;
  color: var(--text-main);
  letter-spacing: -1px;
}

.grade-badge {
  padding: 6px 12px;
  border: 2px solid;
  border-radius: 12px;
  font-family: 'Space Grotesk', sans-serif;
  font-weight: 700;
  font-size: 20px;
  background: var(--bg-card);
}

/* Grid */
.widgets-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 24px;
}

@media (max-width: 850px) {
  .widgets-grid {
    grid-template-columns: 1fr;
  }
}

.main-widgets-col,
.side-widgets-col {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.widget {
  border-radius: 16px;
  padding: 24px;
  position: relative;
  overflow: hidden;
  background: var(--bg-surface);
  backdrop-filter: var(--glass-blur);
  border: 1px solid var(--border-color);
  transition: all 0.3s ease;
}

.widget-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 24px;
  align-items: center;
}

.widget-header h3 {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 20px;
  margin: 0;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--text-main);
  letter-spacing: -0.3px;
}

.pulse-dot {
  width: 8px;
  height: 8px;
  background: #ba9eff;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.header-icons {
  color: var(--text-muted);
  font-size: 22px;
  letter-spacing: 2px;
  cursor: pointer;
}

.assignments-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.assignment-card {
  background: var(--bg-card);
  padding: 16px;
  border-radius: 12px;
  border: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  transition: all 0.2s ease;
}

.assignment-card:hover {
  border-color: rgba(186, 158, 255, 0.3);
  transform: translateY(-2px);
}

.assignment-card.critical {
  border-color: rgba(248, 113, 113, 0.3);
  background: rgba(248, 113, 113, 0.05);
}

.assign-left {
  display: flex;
  align-items: center;
  gap: 14px;
  flex: 1;
}

.assign-icon-wrapper {
  width: 44px;
  height: 44px;
  background: var(--bg-surface-hover);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.assign-icon-wrapper :deep(svg) {
  width: 24px;
  height: 24px;
  color: #ba9eff;
}

.assignment-card.critical .assign-icon-wrapper :deep(svg) {
  color: #f87171;
}

.assign-info {
  min-width: 0;
}

.assign-title {
  margin: 0 0 4px 0;
  font-size: 17px;
  font-weight: 600;
  color: var(--text-main);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.assign-meta {
  margin: 0;
  font-size: 14px;
  color: var(--text-muted);
}

.assign-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.progress-wrapper {
  width: 120px;
}

.progress-track {
  height: 6px;
  background: var(--border-color);
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.8s ease;
}

.grade-badge-large {
  width: 44px;
  height: 44px;
  border: 2px solid;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: 'Space Grotesk', sans-serif;
  font-size: 20px;
  font-weight: 700;
  background: var(--bg-card);
  flex-shrink: 0;
}

.skill-widget {
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 28px 20px;
}

.circular-chart-wrapper {
  position: relative;
  width: 140px;
  height: 140px;
  margin-bottom: 20px;
}

.circular-chart {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

.circle-bg {
  fill: none;
  stroke: var(--border-color);
  stroke-width: 2.5;
}

.circle {
  fill: none;
  stroke-width: 3;
  stroke-linecap: round;
  transition: stroke-dasharray 1s ease;
}

.chart-center {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.chart-percentage {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 32px;
  font-weight: 700;
  line-height: 1;
  letter-spacing: -1px;
}

.chart-label {
  font-size: 11px;
  font-weight: 700;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 1px;
}

.skill-description {
  font-size: 15px;
  color: var(--text-muted);
  line-height: 1.6;
  max-width: 220px;
  margin: 0 0 20px 0;
}

.skill-indicators {
  display: flex;
  gap: 6px;
  width: 100%;
  justify-content: center;
}

.indicator-bar {
  flex: 1;
  height: 4px;
  background: var(--border-color);
  border-radius: 2px;
  transition: all 0.3s ease;
}

@media (max-width: 600px) {
  .course-title {
    font-size: 24px;
  }

  .course-meta {
    font-size: 13px;
  }

  .grade-label {
    font-size: 9px;
  }

  .grade-value {
    font-size: 28px;
  }

  .grade-badge {
    font-size: 14px;
    padding: 4px 8px;
  }

  .ai-analytics-section {
    padding: 18px;
  }

  .ai-analytics-header h2 {
    font-size: 18px;
  }

  .ai-analysis-text p {
    font-size: 14px;
  }

  .topic-item {
    font-size: 13px;
    padding: 6px 10px;
  }

  .topic-column-title {
    font-size: 12px;
  }

  .rec-title {
    font-size: 14px;
  }

  .rec-description {
    font-size: 12px;
  }

  .rec-type {
    font-size: 10px;
  }

  .rec-score {
    font-size: 11px;
  }

  .rec-difficulty {
    font-size: 10px;
  }

  .assign-title {
    font-size: 14px;
  }

  .assign-meta {
    font-size: 12px;
  }

  .grade-badge-large {
    font-size: 16px;
  }

  .widget-header h3 {
    font-size: 16px;
  }

  .chart-percentage {
    font-size: 22px;
  }

  .skill-description {
    font-size: 13px;
  }

  .course-header {
    flex-direction: column;
  }

  .grade-summary {
    text-align: left;
    width: 100%;
  }

  .grade-value-wrapper {
    justify-content: flex-start;
  }

  .assignment-card {
    flex-direction: column;
    align-items: flex-start;
  }

  .assign-right {
    width: 100%;
    justify-content: space-between;
  }

  .progress-wrapper {
    width: 60%;
  }

  .circular-chart-wrapper {
    width: 120px;
    height: 120px;
  }

  .chart-percentage {
    font-size: 28px;
  }

  .topics-row {
    flex-direction: column;
  }

  .recommendations-grid {
    grid-template-columns: 1fr;
  }

  .skeleton-cards {
    grid-template-columns: 1fr;
  }
}
</style>
