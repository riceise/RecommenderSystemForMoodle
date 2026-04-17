<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useThemeStore } from '../stores/theme'
import api from '../Api'
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
)

const themeStore = useThemeStore()

interface AdminStats {
  totalStudents: number
  activeCourses: number
  syncedGradesCount: number
  lastSyncStatus: string
  lastSyncDate: string | null
  pythonServiceOnline: boolean
  recommendationsGenerated: number
  avgResponseTimeMs: number
}

interface SyncResult {
  success: boolean
  addedCount: number
  updatedCount: number
  newStudentsCount: number
  gradesUpdatedCount: number
  assignmentsUpdatedCount: number
  message: string
}

interface CourseAdmin {
  id: string
  title: string
  platform: string
  topics: string[]
  difficulty: string
}

interface ActivityDataPoint {
  date: string
  registrations: number
  gradesReceived: number
}

const isLoading = ref(true)
const stats = ref<AdminStats>({
  totalStudents: 0,
  activeCourses: 0,
  syncedGradesCount: 0,
  lastSyncStatus: 'Unknown',
  lastSyncDate: null,
  pythonServiceOnline: false,
  recommendationsGenerated: 0,
  avgResponseTimeMs: 0,
})

const syncingCourses = ref(false)
const syncingGrades = ref(false)
const syncResult = ref<SyncResult | null>(null)
const showToast = ref(false)
const toastMessage = ref('')
const toastType = ref<'success' | 'error' | 'info'>('success')

const courses = ref<CourseAdmin[]>([])
const editingCourse = ref<CourseAdmin | null>(null)
const editDifficulty = ref('Beginner')
const editTopics = ref('')
const isSavingCourse = ref(false)

const activityData = ref<ActivityDataPoint[]>([])

const chartData = computed(() => {
  const labels = activityData.value.map((d) => {
    const date = new Date(d.date)
    return date.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit' })
  })

  return {
    labels,
    datasets: [
      {
        label: 'Регистрации',
        data: activityData.value.map((d) => d.registrations),
        borderColor: '#8b5cf6',
        backgroundColor: 'rgba(139, 92, 246, 0.1)',
        fill: true,
        tension: 0.4,
        pointRadius: 4,
        pointHoverRadius: 6,
      },
      {
        label: 'Оценки',
        data: activityData.value.map((d) => d.gradesReceived),
        borderColor: '#34d399',
        backgroundColor: 'rgba(52, 211, 153, 0.1)',
        fill: true,
        tension: 0.4,
        pointRadius: 4,
        pointHoverRadius: 6,
      },
    ],
  }
})

const chartOptions = computed(() => {
  const isDark = themeStore.isDark
  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        labels: {
          color: isDark ? '#ffffff' : '#1E293B',
          font: { size: 14, family: 'Inter' },
        },
      },
      tooltip: {
        backgroundColor: isDark ? '#1f2937' : '#ffffff',
        titleColor: isDark ? '#fff' : '#1E293B',
        bodyColor: isDark ? '#d1d5db' : '#64748B',
        borderColor: isDark ? '#374151' : '#e2e8f0',
        borderWidth: 1,
        cornerRadius: 8,
      },
    },
    scales: {
      x: {
        ticks: { color: isDark ? '#9ca3af' : '#64748B', font: { size: 12 } },
        grid: { color: isDark ? 'rgba(55, 65, 81, 0.3)' : 'rgba(226, 232, 240, 0.5)' },
      },
      y: {
        beginAtZero: true,
        ticks: { color: isDark ? '#9ca3af' : '#64748B', font: { size: 12 }, stepSize: 1 },
        grid: { color: isDark ? 'rgba(55, 65, 81, 0.3)' : 'rgba(226, 232, 240, 0.5)' },
      },
    },
  }
})

const chartKey = computed(() => `chart-${themeStore.isDark ? 'dark' : 'light'}`)

const fetchDashboard = async () => {
  try {
    const { data } = await api.get<AdminStats>('/admin/dashboard')
    stats.value = data
  } catch {
    stats.value.lastSyncStatus = 'Error'
  }
}

const fetchCourses = async () => {
  try {
    const { data } = await api.get<CourseAdmin[]>('/admin/courses')
    courses.value = data
  } catch {
    courses.value = []
  }
}

const fetchActivity = async () => {
  try {
    const { data } = await api.get<ActivityDataPoint[]>('/admin/activity')
    activityData.value = data
  } catch {
    activityData.value = []
  }
}

const syncCourses = async () => {
  syncingCourses.value = true
  try {
    const { data } = await api.post<SyncResult>('/admin/sync-all-courses')
    syncResult.value = data
    toastMessage.value = `Синхронизация курсов завершена.\nДобавлено: ${data.addedCount}\nОбновлено: ${data.updatedCount}`
    toastType.value = 'success'
    showToast.value = true
    await fetchDashboard()
    await fetchCourses()
  } catch (error: any) {
    toastMessage.value = error.response?.data?.message || 'Ошибка синхронизации курсов'
    toastType.value = 'error'
    showToast.value = true
  } finally {
    syncingCourses.value = false
  }
}

const syncGrades = async () => {
  syncingGrades.value = true
  try {
    const { data } = await api.post<SyncResult>('/admin/sync-users-grades')
    syncResult.value = data
    toastMessage.value = `Синхронизация оценок завершена.\nНовых студентов: ${data.newStudentsCount}\nКурсов обновлено: ${data.gradesUpdatedCount}\nОценок сохранено: ${data.assignmentsUpdatedCount}`
    toastType.value = 'success'
    showToast.value = true
    await fetchDashboard()
  } catch (error: any) {
    toastMessage.value = error.response?.data || 'Ошибка синхронизации оценок'
    toastType.value = 'error'
    showToast.value = true
  } finally {
    syncingGrades.value = false
  }
}

const openEditCourse = (course: CourseAdmin) => {
  editingCourse.value = course
  editDifficulty.value = course.difficulty
  editTopics.value = course.topics.join(', ')
}

const closeEditCourse = () => {
  editingCourse.value = null
}

const saveCourse = async () => {
  if (!editingCourse.value) return
  isSavingCourse.value = true
  try {
    const topics = editTopics.value
      .split(',')
      .map((t) => t.trim())
      .filter((t) => t.length > 0)

    await api.put(`/admin/courses/${editingCourse.value.id}`, {
      difficulty: editDifficulty.value,
      topics,
    })

    toastMessage.value = 'Курс успешно обновлён'
    toastType.value = 'success'
    showToast.value = true

    closeEditCourse()
    await fetchCourses()
  } catch (error: any) {
    toastMessage.value = error.response?.data?.message || 'Ошибка сохранения курса'
    toastType.value = 'error'
    showToast.value = true
  } finally {
    isSavingCourse.value = false
  }
}

const dismissToast = () => {
  showToast.value = false
}

const formatDateTime = (dateStr: string | null) => {
  if (!dateStr) return 'Никогда'
  const date = new Date(dateStr)
  return date.toLocaleString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const difficultyColor = (difficulty: string) => {
  switch (difficulty) {
    case 'Advanced':
      return '#ef4444'
    case 'Standard':
      return '#f59e0b'
    default:
      return '#10b981'
  }
}

const difficultyLabel = (difficulty: string) => {
  switch (difficulty) {
    case 'Advanced':
      return 'Advanced'
    case 'Standard':
      return 'Standard'
    default:
      return 'Beginner'
  }
}

onMounted(async () => {
  isLoading.value = true
  await Promise.all([fetchDashboard(), fetchCourses(), fetchActivity()])
  isLoading.value = false
})
</script>

<template>
  <div class="admin-page">
    <Transition name="toast">
      <div v-if="showToast" class="toast" :class="`toast-${toastType}`">
        <div class="toast-icon">
          <svg v-if="toastType === 'success'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <pre class="toast-message">{{ toastMessage }}</pre>
        <button class="toast-close" @click="dismissToast">&times;</button>
      </div>
    </Transition>
    <div v-if="isLoading" class="skeleton-grid">
      <div v-for="i in 4" :key="i" class="skeleton-card">
        <div class="skeleton-line skeleton-short"></div>
        <div class="skeleton-line skeleton-long"></div>
      </div>
    </div>

    <div v-else class="admin-content">
      <header class="page-header">
        <h1>Admin Dashboard</h1>
        <p class="subtitle">System monitoring, sync control, and course management</p>
      </header>

      <section class="kpi-row">
        <!-- Total Students -->
        <div class="kpi-card kpi-indigo">
          <div class="kpi-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
              <circle cx="9" cy="7" r="4" />
              <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
              <path d="M16 3.13a4 4 0 0 1 0 7.75" />
            </svg>
          </div>
          <span class="kpi-label">Всего студентов</span>
          <span class="kpi-value">{{ stats.totalStudents }}</span>
        </div>

        <div class="kpi-card kpi-mint">
          <div class="kpi-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
              <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
            </svg>
          </div>
          <span class="kpi-label">Активных курсов</span>
          <span class="kpi-value">{{ stats.activeCourses }}</span>
        </div>

        <div class="kpi-card kpi-purple">
          <div class="kpi-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
            </svg>
          </div>
          <span class="kpi-label">Синхронизировано оценок</span>
          <span class="kpi-value">{{ stats.syncedGradesCount }}</span>
        </div>

        <div class="kpi-card" :class="stats.lastSyncStatus === 'Success' ? 'kpi-emerald' : 'kpi-amber'">
          <div class="kpi-icon">
            <svg v-if="stats.lastSyncStatus === 'Success'" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <svg v-else-if="stats.lastSyncStatus === 'Error'" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <svg v-else width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <circle cx="12" cy="12" r="10" />
              <polyline points="12 6 12 12 16 14" />
            </svg>
          </div>
          <span class="kpi-label">Статус синхронизации</span>
          <span class="kpi-value kpi-status">
            <span class="status-dot" :class="`status-${stats.lastSyncStatus.toLowerCase()}`"></span>
            {{ stats.lastSyncStatus }}
          </span>
          <span class="kpi-sub">{{ formatDateTime(stats.lastSyncDate) }}</span>
        </div>
      </section>

      <section class="sync-row">
        <h2 class="section-title">Центр синхронизации</h2>
        <div class="sync-grid">
          <!-- Sync Courses -->
          <div class="sync-card sync-amber" :class="{ 'sync-card--loading': syncingCourses }">
            <div v-if="syncingCourses" class="sync-overlay">
              <div class="sync-spinner"></div>
              <span class="sync-text">Синхронизация курсов...</span>
            </div>
            <div class="sync-content">
              <div class="sync-header">
                <div class="sync-icon sync-icon-courses">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
                    <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
                  </svg>
                </div>
                <h3>Синхронизировать курсы</h3>
              </div>
              <p class="sync-desc">
                Загрузка всех курсов из Moodle с автоматическим анализом тем, тегов и определением уровня сложности.
              </p>
              <button class="btn-sync btn-sync-amber" :disabled="syncingCourses" @click="syncCourses">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <polyline points="23 4 23 10 17 10" />
                  <polyline points="1 20 1 14 7 14" />
                  <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
                </svg>
                Синхронизировать
              </button>
            </div>
          </div>

          <div class="sync-card sync-amber-alt" :class="{ 'sync-card--loading': syncingGrades }">
            <div v-if="syncingGrades" class="sync-overlay">
              <div class="sync-spinner"></div>
              <span class="sync-text">Синхронизация оценок...</span>
            </div>
            <div class="sync-content">
              <div class="sync-header">
                <div class="sync-icon sync-icon-grades">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
                  </svg>
                </div>
                <h3>Синхронизировать оценки</h3>
              </div>
              <p class="sync-desc">
                Загрузка студентов, их оценок за задания и итоговых баллов из всех курсов в базе данных.
              </p>
              <button class="btn-sync btn-sync-amber-alt" :disabled="syncingGrades" @click="syncGrades">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <polyline points="23 4 23 10 17 10" />
                  <polyline points="1 20 1 14 7 14" />
                  <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
                </svg>
                Синхронизировать
              </button>
            </div>
          </div>
        </div>
      </section>

      <section class="analytics-row">
        <h2 class="section-title">AI Монитор & Аналитика</h2>
        <div class="analytics-grid">
          <!-- AI Monitor -->
          <div class="monitor-card">
            <div class="monitor-header">
              <div class="monitor-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path d="M12 2a10 10 0 0 1 10 10 10 10 0 0 1-10 10A10 10 0 0 1 2 12 10 10 0 0 1 12 2z" />
                  <path d="M8 14s1.5 2 4 2 4-2 4-2" />
                  <line x1="9" y1="9" x2="9.01" y2="9" />
                  <line x1="15" y1="9" x2="15.01" y2="9" />
                </svg>
              </div>
              <h3>AI Service</h3>
              <span class="status-badge" :class="stats.pythonServiceOnline ? 'status-online' : 'status-offline'">
                {{ stats.pythonServiceOnline ? 'Online' : 'Offline' }}
              </span>
            </div>
          </div>

          <div class="chart-card">
            <h3>Активность за 7 дней</h3>
            <div class="chart-wrapper">
              <Line v-if="activityData.length > 0" :key="chartKey" :data="chartData" :options="chartOptions" />
              <div v-else class="chart-empty">Нет данных для отображения</div>
            </div>
          </div>
        </div>
      </section>

      <section class="courses-section">
        <h2 class="section-title">Управление курсами</h2>
        <div class="table-wrapper">
          <table class="courses-table">
            <thead>
              <tr>
                <th>Title</th>
                <th>Platform</th>
                <th>Topics</th>
                <th>Difficulty</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="course in courses" :key="course.id">
                <td class="cell-title">{{ course.title }}</td>
                <td>
                  <span class="platform-badge">{{ course.platform }}</span>
                </td>
                <td class="cell-topics">
                  <span v-for="(topic, i) in course.topics.slice(0, 3)" :key="i" class="topic-tag">
                    {{ topic }}
                  </span>
                  <span v-if="course.topics.length > 3" class="topic-more">+{{ course.topics.length - 3 }}</span>
                </td>
                <td>
                  <span class="difficulty-badge" :style="{ borderColor: difficultyColor(course.difficulty), color: difficultyColor(course.difficulty) }">
                    {{ difficultyLabel(course.difficulty) }}
                  </span>
                </td>
                <td>
                  <button class="btn-edit" @click="openEditCourse(course)">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                      <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                      <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
                    </svg>
                    Edit
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
          <div v-if="courses.length === 0" class="empty-table">
            Нет курсов. Выполните синхронизацию для загрузки данных.
          </div>
        </div>
      </section>
    </div>

    <Transition name="modal">
      <div v-if="editingCourse" class="modal-backdrop" @click.self="closeEditCourse">
        <div class="modal">
          <div class="modal-header">
            <h3>Редактировать курс</h3>
            <button class="modal-close" @click="closeEditCourse">&times;</button>
          </div>
          <div class="modal-body">
            <div class="form-group">
              <label>Название</label>
              <input type="text" :value="editingCourse.title" disabled class="input-disabled" />
            </div>
            <div class="form-group">
              <label>Сложность</label>
              <select v-model="editDifficulty" class="input-select">
                <option value="Beginner">Beginner</option>
                <option value="Standard">Standard</option>
                <option value="Advanced">Advanced</option>
              </select>
            </div>
            <div class="form-group">
              <label>Теги (через запятую)</label>
              <textarea v-model="editTopics" rows="3" class="input-textarea" placeholder="Python, Data Structures, Algorithms" />
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn-modal-cancel" @click="closeEditCourse">Отмена</button>
            <button class="btn-modal-save" :disabled="isSavingCourse" @click="saveCourse">
              <svg v-if="isSavingCourse" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" class="spinner-icon">
                <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
              </svg>
              {{ isSavingCourse ? 'Сохранение...' : 'Сохранить' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.admin-page {
  min-height: 100vh;
  background-color: var(--bg-body);
  color: var(--text-main);
  font-size: var(--text-base);
}

.admin-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: var(--space-xl) var(--space-lg);
}

.page-header {
  margin-bottom: var(--space-2xl);
}

.page-header h1 {
  font-family: var(--font-display);
  font-size: var(--text-4xl);
  font-weight: 800;
  margin-bottom: var(--space-xs);
}

.subtitle {
  color: var(--text-muted);
  font-size: var(--text-lg);
}

.section-title {
  font-family: var(--font-display);
  font-size: var(--text-2xl);
  font-weight: 700;
  margin-bottom: var(--space-lg);
  color: var(--text-main);
}

.skeleton-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-lg);
  padding: var(--space-xl) var(--space-lg);
  max-width: 1400px;
  margin: 0 auto;
}

.skeleton-card {
  background: var(--bg-surface);
  border-radius: var(--radius-xl);
  padding: var(--space-xl);
  border: 1px solid var(--border-color);
}

.skeleton-line {
  height: 20px;
  border-radius: 8px;
  background: linear-gradient(90deg, var(--bg-surface-hover) 25%, var(--border-color) 50%, var(--bg-surface-hover) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
}

.skeleton-short {
  width: 40%;
  margin-bottom: var(--space-md);
}

.skeleton-long {
  width: 80%;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.kpi-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-lg);
  margin-bottom: var(--space-2xl);
}

@media (max-width: 1100px) {
  .kpi-row {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 640px) {
  .kpi-row {
    grid-template-columns: 1fr;
  }
}

.kpi-card {
  background: var(--bg-surface);
  backdrop-filter: var(--glass-blur);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-xl);
  padding: var(--space-xl);
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--space-sm);
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.kpi-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-glow);
}

.kpi-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
}

.kpi-indigo::before { background: linear-gradient(90deg, #6366f1, #8b5cf6); }
.kpi-indigo:hover { border-color: #6366f1; }

.kpi-mint::before { background: linear-gradient(90deg, #10b981, #34d399); }
.kpi-mint:hover { border-color: #10b981; }

.kpi-purple::before { background: linear-gradient(90deg, #8b5cf6, #a855f7); }
.kpi-purple:hover { border-color: #8b5cf6; }

.kpi-emerald::before { background: linear-gradient(90deg, #10b981, #34d399); }
.kpi-emerald:hover { border-color: #10b981; }

.kpi-amber::before { background: linear-gradient(90deg, #f59e0b, #fbbf24); }
.kpi-amber:hover { border-color: #f59e0b; }

.kpi-icon {
  color: var(--text-muted);
  margin-bottom: var(--space-xs);
}

.kpi-label {
  font-size: var(--text-sm);
  color: var(--text-muted);
  font-weight: 500;
}

.kpi-value {
  font-size: 2rem;
  font-weight: 800;
  font-family: var(--font-display);
  line-height: 1.1;
}

.kpi-status {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.status-success { background: #10b981; box-shadow: 0 0 8px rgba(16, 185, 129, 0.4); }
.status-error { background: #ef4444; box-shadow: 0 0 8px rgba(239, 68, 68, 0.4); }
.status-never { background: #9ca3af; }

.kpi-sub {
  font-size: var(--text-xs);
  color: var(--text-muted);
}

.sync-row {
  margin-bottom: var(--space-2xl);
}

.sync-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-lg);
}

@media (max-width: 768px) {
  .sync-grid {
    grid-template-columns: 1fr;
  }
}

.sync-card {
  background: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-xl);
  padding: var(--space-xl);
  position: relative;
  overflow: hidden;
  transition: all 0.3s ease;
}

.sync-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
}

.sync-amber::before { background: linear-gradient(90deg, #f59e0b, #fbbf24); }
.sync-amber-alt::before { background: linear-gradient(90deg, #ef4444, #f59e0b); }

.sync-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-md);
}

.sync-card--loading .sync-content {
  opacity: 0.3;
  pointer-events: none;
}

.sync-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 10;
  gap: var(--space-md);
}

.sync-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid var(--border-color);
  border-top-color: #f59e0b;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.sync-text {
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--text-main);
}

.sync-content {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.sync-header {
  display: flex;
  align-items: center;
  gap: var(--space-md);
}

.sync-icon {
  width: 56px;
  height: 56px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.sync-icon-courses {
  background: rgba(245, 158, 11, 0.15);
  color: #f59e0b;
}

.sync-icon-grades {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
}

.sync-header h3 {
  font-family: var(--font-display);
  font-size: var(--text-xl);
  font-weight: 700;
}

.sync-desc {
  color: var(--text-muted);
  font-size: var(--text-sm);
  line-height: 1.6;
}

.btn-sync {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-sm);
  padding: var(--space-md);
  border: none;
  border-radius: var(--radius-md);
  font-weight: 700;
  font-size: var(--text-base);
  cursor: pointer;
  transition: all 0.2s;
  color: #000;
}

.btn-sync-amber {
  background: linear-gradient(135deg, #f59e0b, #fbbf24);
}

.btn-sync-amber:hover:not(:disabled) {
  box-shadow: 0 4px 12px rgba(245, 158, 11, 0.3);
  transform: translateY(-1px);
}

.btn-sync-amber-alt {
  background: linear-gradient(135deg, #ef4444, #f59e0b);
}

.btn-sync-amber-alt:hover:not(:disabled) {
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
  transform: translateY(-1px);
}

.btn-sync:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.analytics-row {
  margin-bottom: var(--space-2xl);
}

.analytics-grid {
  display: grid;
  grid-template-columns: 1fr 3fr;
  gap: var(--space-lg);
}

@media (max-width: 1024px) {
  .analytics-grid {
    grid-template-columns: 1fr;
  }
}

.monitor-card {
  background: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-xl);
  padding: var(--space-xl);
  transition: all 0.3s ease;
}

.monitor-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-glow);
}

.monitor-header {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  margin-bottom: var(--space-lg);
}

.monitor-icon {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-md);
  background: rgba(139, 92, 246, 0.15);
  color: #8b5cf6;
  display: flex;
  align-items: center;
  justify-content: center;
}

.monitor-header h3 {
  font-family: var(--font-display);
  font-size: var(--text-lg);
  font-weight: 700;
}

.status-badge {
  margin-left: auto;
  font-size: 12px;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 20px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.status-online {
  background: rgba(16, 185, 129, 0.15);
  color: #10b981;
}

.status-offline {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
}

.chart-card {
  background: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-xl);
  padding: var(--space-xl);
  transition: all 0.3s ease;
}

.chart-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-md);
}

.chart-card h3 {
  font-family: var(--font-display);
  font-size: var(--text-lg);
  font-weight: 700;
  margin-bottom: var(--space-lg);
}

.chart-wrapper {
  height: 280px;
}

.chart-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--text-muted);
  font-size: var(--text-base);
}

.courses-section {
  margin-bottom: var(--space-2xl);
}

.table-wrapper {
  background: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-xl);
  overflow: hidden;
}

.courses-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--text-base);
}

.courses-table thead {
  background: var(--bg-surface-hover);
}

.courses-table th {
  padding: var(--space-md) var(--space-lg);
  text-align: left;
  font-weight: 700;
  font-size: var(--text-sm);
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.courses-table td {
  padding: var(--space-md) var(--space-lg);
  border-top: 1px solid var(--border-color);
  vertical-align: middle;
}

.courses-table tbody tr {
  transition: background 0.2s;
}

.courses-table tbody tr:hover {
  background: var(--bg-surface-hover);
}

.cell-title {
  font-weight: 600;
  color: var(--text-main);
}

.platform-badge {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 700;
  background: rgba(99, 102, 241, 0.15);
  color: #6366f1;
}

.cell-topics {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.topic-tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
  background: var(--bg-surface-hover);
  color: var(--text-muted);
}

.topic-more {
  font-size: 11px;
  color: var(--text-muted);
  font-weight: 600;
}

.difficulty-badge {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 700;
  border: 1px solid;
  background: transparent;
}

.btn-edit {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border: 1px solid var(--accent-indigo);
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--accent-indigo);
  font-size: var(--text-sm);
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-edit:hover {
  background: var(--accent-indigo);
  color: white;
}

.empty-table {
  text-align: center;
  padding: var(--space-2xl);
  color: var(--text-muted);
  font-size: var(--text-lg);
}

.toast {
  position: fixed;
  bottom: var(--space-xl);
  right: var(--space-xl);
  display: flex;
  align-items: flex-start;
  gap: var(--space-md);
  padding: var(--space-lg);
  border-radius: var(--radius-lg);
  background: var(--bg-surface);
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-lg);
  z-index: 9999;
  max-width: 420px;
}

.toast-success { border-left: 4px solid #10b981; }
.toast-error { border-left: 4px solid #ef4444; }
.toast-info { border-left: 4px solid #6366f1; }

.toast-icon {
  flex-shrink: 0;
  margin-top: 2px;
}

.toast-success .toast-icon { color: #10b981; }
.toast-error .toast-icon { color: #ef4444; }

.toast-message {
  margin: 0;
  font-size: var(--text-sm);
  color: var(--text-main);
  white-space: pre-wrap;
  font-family: var(--font-base);
  line-height: 1.5;
}

.toast-close {
  flex-shrink: 0;
  background: none;
  border: none;
  color: var(--text-muted);
  font-size: var(--text-xl);
  cursor: pointer;
  padding: 0;
  line-height: 1;
}

.toast-close:hover {
  color: var(--text-main);
}

.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from {
  opacity: 0;
  transform: translateX(40px);
}

.toast-leave-to {
  opacity: 0;
  transform: translateX(40px);
}

.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9000;
}

.modal {
  background: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-xl);
  width: 100%;
  max-width: 500px;
  box-shadow: var(--shadow-lg);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-lg) var(--space-xl);
  border-bottom: 1px solid var(--border-color);
}

.modal-header h3 {
  font-family: var(--font-display);
  font-size: var(--text-xl);
  font-weight: 700;
}

.modal-close {
  background: none;
  border: none;
  color: var(--text-muted);
  font-size: var(--text-2xl);
  cursor: pointer;
  line-height: 1;
}

.modal-close:hover {
  color: var(--text-main);
}

.modal-body {
  padding: var(--space-xl);
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.form-group label {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text-muted);
}

.input-disabled {
  padding: var(--space-sm) var(--space-md);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  background: var(--bg-surface-hover);
  color: var(--text-muted);
  font-size: var(--text-base);
  cursor: not-allowed;
}

.input-select,
.input-textarea {
  padding: var(--space-sm) var(--space-md);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  background: var(--bg-card);
  color: var(--text-main);
  font-size: var(--text-base);
  font-family: var(--font-base);
  outline: none;
  transition: border-color 0.2s;
}

.input-select:focus,
.input-textarea:focus {
  border-color: var(--accent-indigo);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15);
}

.input-textarea {
  resize: vertical;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-md);
  padding: var(--space-lg) var(--space-xl);
  border-top: 1px solid var(--border-color);
}

.btn-modal-cancel {
  padding: var(--space-sm) var(--space-lg);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-muted);
  font-weight: 600;
  font-size: var(--text-base);
  cursor: pointer;
  transition: all 0.2s;
}

.btn-modal-cancel:hover {
  background: var(--bg-surface-hover);
  color: var(--text-main);
}

.btn-modal-save {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  padding: var(--space-sm) var(--space-lg);
  border: none;
  border-radius: var(--radius-sm);
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: white;
  font-weight: 700;
  font-size: var(--text-base);
  cursor: pointer;
  transition: all 0.2s;
}

.btn-modal-save:hover:not(:disabled) {
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
  transform: translateY(-1px);
}

.btn-modal-save:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.spinner-icon {
  animation: spin 1s linear infinite;
}

.modal-enter-active,
.modal-leave-active {
  transition: all 0.3s ease;
}

.modal-enter-from {
  opacity: 0;
  transform: scale(0.95);
}

.modal-leave-to {
  opacity: 0;
  transform: scale(0.95);
}

@media (max-width: 768px) {
  .page-header h1 {
    font-size: var(--text-3xl);
  }

  .kpi-value {
    font-size: 1.75rem;
  }

  .courses-table {
    font-size: var(--text-sm);
  }

  .courses-table th,
  .courses-table td {
    padding: var(--space-sm) var(--space-md);
  }
}
</style>
