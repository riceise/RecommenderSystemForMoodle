import { defineStore } from 'pinia';
function getInitialTheme(): boolean {
    if (typeof window === 'undefined') return true;
    const stored = localStorage.getItem('theme');
    if (stored === 'light') return false;
    if (stored === 'dark') return true;
    return true;
}

export const useThemeStore = defineStore('theme', {
    state: () => ({
        isDark: getInitialTheme(),
    }),

    actions: {
        toggleTheme() {
            this.isDark = !this.isDark;
            this.persistAndApply();
        },

        setTheme(dark: boolean) {
            this.isDark = dark;
            this.persistAndApply();
        },

        persistAndApply() {
            if (typeof window !== 'undefined') {
                localStorage.setItem('theme', this.isDark ? 'dark' : 'light');
            }
            this.applyTheme();
        },

        applyTheme() {
            if (typeof document === 'undefined') return;
            const theme = this.isDark ? 'dark' : 'light';
            document.documentElement.setAttribute('data-theme', theme);
            if (this.isDark) {
                document.body.classList.remove('light-theme');
            } else {
                document.body.classList.add('light-theme');
            }
        },
    },
});
