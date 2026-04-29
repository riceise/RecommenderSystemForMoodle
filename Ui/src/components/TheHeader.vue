<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useThemeStore } from '../stores/theme'
import { useUiStore } from '../stores/ui'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const themeStore = useThemeStore()
const uiStore = useUiStore()

// ─── Search ──────────────────────────────────────────────────
const searchQuery = ref('')
let debounceTimer: ReturnType<typeof setTimeout> | null = null

/**
 * Debounce 300ms.
 * • На /dashboard — просто обновляем query-param (DashboardView фильтрует реактивно).
 * • На других страницах — переходим на /dashboard?search=...
 */
const onSearchInput = () => {
  if (debounceTimer) clearTimeout(debounceTimer)

  debounceTimer = setTimeout(() => {
    const q = searchQuery.value.trim()

    if (route.path === '/dashboard') {
      // Просто обновляем query-param, DashboardView подхватит через watch
      router.replace({ query: q ? { search: q } : {} })
    } else {
      // Переходим на dashboard с поиском
      if (q) {
        router.push({ path: '/dashboard', query: { search: q } })
      }
    }
  }, 300)
}

/** Синхронизируем input с query-param при навигации */
watch(
  () => route.query.search,
  (val) => {
    searchQuery.value = (val as string) ?? ''
  },
  { immediate: true },
)

// ─── Logout ──────────────────────────────────────────────────
const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}

const goBack = () => {
  if (window.history.length > 1) {
    router.back()
  } else {
    router.push('/dashboard')
  }
}

const showBackBtn = computed(() => route.path !== '/dashboard')

const handleThemeToggle = () => {
  themeStore.toggleTheme()
}
</script>

<template>
  <header class="main-header">
    <div class="header-left">
      <button class="mobile-menu-btn" @click="uiStore.toggleSidebar()">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>

      <button v-if="showBackBtn" class="back-btn" @click="goBack">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
        </svg>
      </button>

      <nav class="breadcrumb">
        <span class="crumb" @click="router.push('/dashboard')">Dashboard</span>
        <span class="separator">/</span>
        <span class="crumb active">{{ $route.meta.title || 'Page' }}</span>
      </nav>
    </div>

    <!-- Right actions -->
    <div class="user-actions">
      <!-- Global Search -->
      <div class="search-wrapper">
        <svg class="search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <circle cx="11" cy="11" r="8" />
          <path stroke-linecap="round" d="M21 21l-4.35-4.35" />
        </svg>
        <input
          v-model="searchQuery"
          @input="onSearchInput"
          type="text"
          placeholder="Поиск курсов..."
          class="search-input"
        />
        <kbd v-if="!searchQuery" class="search-shortcut">/</kbd>
      </div>

      <!-- Theme Toggle -->
      <button
        type="button"
        @click="handleThemeToggle"
        class="theme-toggle"
        :aria-pressed="!themeStore.isDark"
        :aria-label="themeStore.isDark ? 'Включить светлую тему' : 'Включить темную тему'"
        :title="themeStore.isDark ? 'Светлая тема' : 'Тёмная тема'"
      >
        {{ themeStore.isDark ? '☀️' : '🌙' }}
      </button>

      <!-- User Profile -->
      <div class="user-profile">
        <div class="avatar">{{ (authStore.user?.email?.[0] ?? 'U').toUpperCase() }}</div>
        <div class="user-info hide-mobile">
          <span class="status">Онлайн</span>
          <span class="email">{{ authStore.user?.email?.split('@')[0] || 'User' }}</span>
        </div>
      </div>

      <!-- Logout -->
      <button @click="handleLogout" class="logout-btn" title="Выйти">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
          <polyline points="16 17 21 12 16 7" />
          <line x1="21" y1="12" x2="9" y2="12" />
        </svg>
      </button>
    </div>
  </header>
</template>

<style scoped>
.main-header {
  background: var(--bg-surface);
  backdrop-filter: var(--glass-blur);
  border-bottom: 1px solid var(--border-color);
  padding: 0 var(--space-lg);
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: var(--shadow-sm);
}

.header-left {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.mobile-menu-btn,
.back-btn {
  background: none;
  border: none;
  color: var(--text-main);
  cursor: pointer;
  padding: 8px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  transition: background 0.2s;
}

.mobile-menu-btn:hover,
.back-btn:hover {
  background: var(--bg-surface-hover);
}

.breadcrumb {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  font-size: var(--text-sm);
  color: var(--text-muted);
}

@media (max-width: 768px) {
  .breadcrumb {
    display: none;
  }
}

.crumb {
  cursor: pointer;
  transition: color 0.2s;
}

.crumb:hover,
.crumb.active {
  color: var(--text-main);
}

.separator {
  color: var(--border-color);
}

/* ─── User Actions ───────────────────────────────────────── */
.user-actions {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

/* ─── Search ─────────────────────────────────────────────── */
.search-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 12px;
  color: var(--text-muted);
  pointer-events: none;
  transition: color 0.2s;
}

.search-input {
  width: 220px;
  height: 40px;
  padding: 0 36px 0 36px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  background: var(--bg-surface-hover);
  color: var(--text-main);
  font-size: var(--text-sm);
  outline: none;
  transition: all 0.2s;
  font-family: var(--font-base);
}

.search-input::placeholder {
  color: var(--text-muted);
  opacity: 0.6;
}

.search-input:focus {
  width: 280px;
  border-color: var(--accent-indigo);
  background: var(--bg-card);
  box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
}

.search-input:focus + .search-shortcut {
  opacity: 0;
}

.search-input:focus ~ .search-icon {
  color: var(--accent-indigo);
}

.search-shortcut {
  position: absolute;
  right: 10px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-muted);
  background: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: 5px;
  padding: 2px 6px;
  opacity: 0.7;
  pointer-events: none;
  transition: opacity 0.2s;
}

/* ─── Theme Toggle / Logout ──────────────────────────────── */
.theme-toggle,
.logout-btn {
  background: var(--bg-surface-hover);
  border: none;
  color: var(--text-main);
  cursor: pointer;
  width: 40px;
  height: 40px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: 0.2s;
}

.theme-toggle:hover,
.logout-btn:hover {
  background: var(--border-color);
}

.logout-btn:hover {
  color: #ef4444;
}

/* ─── User Profile ───────────────────────────────────────── */
.user-profile {
  display: flex;
  align-items: center;
  gap: 10px;
}

.avatar {
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, #6366f1, #a855f7);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  color: white;
  font-size: var(--text-sm);
}

.user-info {
  display: flex;
  flex-direction: column;
}

.status {
  font-size: 12px;
  color: #10b981;
  font-weight: 700;
  text-transform: uppercase;
}

.email {
  font-size: var(--text-sm);
  color: var(--text-muted);
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ─── Responsive ─────────────────────────────────────────── */
@media (max-width: 768px) {
  .hide-mobile {
    display: none;
  }

  .main-header {
    padding: 0 var(--space-md);
    height: 56px;
  }

  .search-wrapper {
    display: none;
  }

  .breadcrumb {
    font-size: 12px;
  }

  .avatar {
    width: 32px;
    height: 32px;
  }

  .theme-toggle,
  .logout-btn {
    width: 34px;
    height: 34px;
  }
}

@media (max-width: 1024px) {
  .search-input {
    width: 180px;
  }

  .search-input:focus {
    width: 220px;
  }
}
</style>
