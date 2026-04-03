<script setup lang="ts">
import {useRouter} from 'vue-router';
import {useAuthStore} from '../stores/auth';
import {useThemeStore} from '../stores/theme';

const router = useRouter();
const authStore = useAuthStore();
const themeStore = useThemeStore();

const handleLogout = () => {
  authStore.logout();
  router.push('/login');
};
</script>

<template>
  <header class="main-header">
    <div class="header-content">
      <!-- Логотип -->
      <div class="logo" @click="router.push('/dashboard')">
        <span class="logo-icon">🧠</span>
        <span class="logo-text">Neuro<span class="highlight">Tutor</span></span>
      </div>

      <div class="user-actions">
        <button @click="themeStore.toggleTheme" class="theme-toggle">
          {{ themeStore.isDark ? '☀️' : '🌙' }}
        </button>

        <div class="user-profile">
          <div class="avatar">{{ authStore.user?.email?.[0].toUpperCase() || 'U' }}</div>
          <div class="user-info hide-mobile">
            <span class="status">Online</span>
            <span class="email">{{ authStore.user?.email?.split('@')[0] || 'User' }}</span>
          </div>
        </div>

        <button @click="handleLogout" class="logout-btn" title="Выйти">
          <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none"
               stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
            <polyline points="16 17 21 12 16 7"></polyline>
            <line x1="21" y1="12" x2="9" y2="12"></line>
          </svg>
        </button>
      </div>
    </div>
  </header>
</template>

<style scoped>
.main-header {
  background: var(--header-bg);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--border-color);
  padding: 0 15px;
  height: 64px;
  display: flex;
  align-items: center;
  position: sticky;
  top: 0;
  z-index: 1000;
}

.header-content {
  max-width: 1200px;
  width: 100%;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.logo-icon {
  font-size: 20px;
}

.logo-text {
  font-size: 18px;
  font-weight: 800;
  color: var(--text-color);
}

.highlight {
  color: #2dd4bf;
}

.user-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.theme-toggle, .logout-btn {
  background: var(--hover-bg);
  border: none;
  color: var(--text-color);
  cursor: pointer;
  width: 38px;
  height: 38px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: 0.2s;
}

.logout-btn:hover {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
}

.user-profile {
  display: flex;
  align-items: center;
  gap: 10px;
}

.avatar {
  width: 34px;
  height: 34px;
  background: linear-gradient(135deg, #6366f1, #a855f7);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  color: white;
  font-size: 14px;
}

.user-info {
  display: flex;
  flex-direction: column;
}

.status {
  font-size: 9px;
  color: #10b981;
  font-weight: 800;
  text-transform: uppercase;
}

.email {
  font-size: 12px;
  color: var(--text-muted);
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
}

@media (max-width: 600px) {
  .hide-mobile {
    display: none;
  }

  .logo-text {
    font-size: 16px;
  }

  .user-actions {
    gap: 8px;
  }
}
</style>