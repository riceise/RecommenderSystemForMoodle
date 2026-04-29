import { defineStore } from 'pinia'

function getInitialTheme(): boolean {
  if (typeof window === 'undefined') return true
  const stored = localStorage.getItem('theme')
  if (stored === 'light') return false
  if (stored === 'dark') return true
  return true
}

export const useThemeStore = defineStore('theme', {
  state: () => ({
    isDark: getInitialTheme(),
  }),

  actions: {
    toggleTheme() {
      this.setTheme(!this.isDark)
    },

    setTheme(dark: boolean) {
      this.isDark = dark
      this.persistAndApply()
    },

    persistAndApply() {
      if (typeof window !== 'undefined') {
        localStorage.setItem('theme', this.isDark ? 'dark' : 'light')
      }
      this.applyTheme()
    },

    applyTheme() {
      if (typeof document === 'undefined') return

      const theme = this.isDark ? 'dark' : 'light'
      const root = document.documentElement
      const body = document.body

      root.setAttribute('data-theme', theme)
      root.classList.toggle('dark-theme', this.isDark)
      root.classList.toggle('light-theme', !this.isDark)
      root.style.colorScheme = theme

      body.classList.toggle('dark-theme', this.isDark)
      body.classList.toggle('light-theme', !this.isDark)
    },
  },
})
