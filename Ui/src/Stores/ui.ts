import { defineStore } from 'pinia';

export const useUiStore = defineStore('ui', {
  state: () => ({
    isSidebarCollapsed: false,
    isSidebarMobileOpen: false,
  }),

  actions: {
    toggleSidebar() {
      if (typeof window !== 'undefined' && window.innerWidth >= 1024) {
        this.isSidebarCollapsed = !this.isSidebarCollapsed;
      } else {
        this.isSidebarMobileOpen = !this.isSidebarMobileOpen;
      }
    },

    closeMobileSidebar() {
      this.isSidebarMobileOpen = false;
    },

    setSidebarCollapsed(collapsed: boolean) {
      this.isSidebarCollapsed = collapsed;
    },
  },
});
