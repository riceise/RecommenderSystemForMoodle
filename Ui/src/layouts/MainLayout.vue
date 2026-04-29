<script setup lang="ts">
import { useRouter, useRoute } from 'vue-router'
import { computed } from 'vue'
import { useUiStore } from '../stores/ui'
import TheHeader from '../components/TheHeader.vue'

const router = useRouter()
const route = useRoute()
const uiStore = useUiStore()

const isSidebarCollapsed = computed(() => uiStore.isSidebarCollapsed)
const isSidebarMobileOpen = computed(() => uiStore.isSidebarMobileOpen)
const showText = computed(() => !isSidebarCollapsed.value)

const toggleSidebar = () => {
  uiStore.toggleSidebar()
}

const closeMobileSidebar = () => {
  uiStore.closeMobileSidebar()
}
</script>

<template>
  <div class="app-layout">
    <div
      v-if="isSidebarMobileOpen"
      class="sidebar-overlay"
      @click="closeMobileSidebar"
    ></div>

    <aside
      class="sidebar"
      :class="{
        'sidebar-collapsed': isSidebarCollapsed,
        'sidebar-mobile-open': isSidebarMobileOpen,
      }"
      :style="{ width: isSidebarMobileOpen ? '240px' : (isSidebarCollapsed ? '64px' : '240px') }"
    >
      <div class="sidebar-header">
        <div class="logo" @click="router.push('/dashboard')">
          <span class="logo-icon">NT</span>
          <span v-if="showText" class="logo-text">Neuro<span class="highlight">Tutor</span></span>
        </div>
        <p v-if="showText" class="tagline">AI learning dashboard</p>
      </div>

      <nav class="sidebar-nav">
        <button @click="router.push('/dashboard'); closeMobileSidebar()" class="nav-item" :class="{ active: route.path === '/dashboard' }">
          <svg class="nav-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"/>
          </svg>
          <span v-if="showText">Dashboard</span>
        </button>

        <button @click="router.push('/statistics'); closeMobileSidebar()" class="nav-item" :class="{ active: route.path === '/statistics' }">
          <svg class="nav-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
          </svg>
          <span v-if="showText">Statistics</span>
        </button>

        <button @click="router.push('/admin'); closeMobileSidebar()" class="nav-item" :class="{ active: route.path === '/admin' }">
          <svg class="nav-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/>
            <circle cx="12" cy="12" r="3"/>
          </svg>
          <span v-if="showText">Admin</span>
        </button>
      </nav>

      <button v-if="!isSidebarMobileOpen" class="collapse-btn" @click="toggleSidebar" :title="isSidebarCollapsed ? 'Expand' : 'Collapse'">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" :style="{ transform: isSidebarCollapsed ? 'rotate(180deg)' : '' }">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
        </svg>
      </button>
    </aside>

    <div class="main-area">
      <TheHeader @toggle-sidebar="toggleSidebar" />
      <main class="page-content">
        <router-view @toggle-sidebar="toggleSidebar"/>
      </main>
    </div>
  </div>
</template>

<style scoped>
.app-layout {
  display: flex;
  min-height: 100vh;
  font-family: var(--font-base);
}

.sidebar-overlay {
  display: none;
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 1000;
}

.sidebar {
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  padding: var(--space-lg) var(--space-md);
  position: sticky;
  top: 0;
  height: 100vh;
  flex-shrink: 0;
  transition: width 0.25s ease, left 0.3s ease;
  overflow: hidden;
  white-space: nowrap;
}

.sidebar-collapsed {
  padding-left: var(--space-sm);
  padding-right: var(--space-sm);
}

.sidebar-header {
  margin-bottom: var(--space-lg);
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
}

.logo-icon {
  align-items: center;
  background: rgba(139, 92, 246, 0.12);
  border: 1px solid rgba(139, 92, 246, 0.3);
  border-radius: var(--radius-sm);
  color: var(--accent-indigo);
  display: inline-flex;
  font-family: var(--font-display);
  font-size: var(--text-sm);
  font-weight: 800;
  flex-shrink: 0;
  height: 32px;
  justify-content: center;
  width: 32px;
}

.logo-text {
  font-size: var(--text-xl);
  font-weight: 800;
  color: var(--accent-indigo);
  font-family: var(--font-display);
}

.highlight {
  color: var(--text-main);
}

.tagline {
  font-size: var(--text-xs);
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 1px;
  margin: 4px 0 0 34px;
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.nav-item {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  background: none;
  border: none;
  border-radius: var(--radius-sm);
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.2s;
  font-size: var(--text-base);
  font-weight: 500;
  text-align: left;
  width: 100%;
}

.nav-item:hover {
  background: var(--bg-surface-hover);
  color: var(--text-main);
}

.nav-item.active {
  background: rgba(79, 70, 229, 0.1);
  color: var(--accent-indigo);
  font-weight: 600;
}

.nav-icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

.collapse-btn {
  margin-top: auto;
  margin-bottom: var(--space-sm);
  padding: var(--space-xs);
  background: none;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-muted);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  align-self: center;
}

.collapse-btn:hover {
  background: var(--bg-surface-hover);
  color: var(--text-main);
}

.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  overflow: hidden;
}

.page-content {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-lg);
}

@media (max-width: 1024px) {
  .sidebar-overlay {
    display: block;
  }

  .sidebar {
    position: fixed;
    top: 0;
    left: -260px;
    width: 240px !important;
    z-index: 1001;
    transition: left 0.3s ease, width 0.25s ease;
  }

  .sidebar-mobile-open {
    left: 0;
  }

  .sidebar-collapsed {
    left: -260px;
  }
}

@media (max-width: 600px) {
  .page-content {
    padding: 16px;
  }
}
</style>
