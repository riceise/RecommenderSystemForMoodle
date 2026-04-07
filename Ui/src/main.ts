// src/main.ts
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from './stores/auth'

import './style.css'
import App from './App.vue'

import AuthView from './views/AuthView.vue'
import DashboardView from './views/DashboardView.vue'
import CourseDetailsView from './views/CourseDetailsView.vue'
import StatisticsView from './views/StatisticsView.vue'
import AdminView from './views/AdminView.vue'

const MainLayout = () => import('./layouts/MainLayout.vue')

const routes: Array<RouteRecordRaw> = [
    {
        path: '/login',
        name: 'Login',
        component: AuthView,
        meta: { requiresAuth: false, public: true }
    },

    {
        path: '/',
        component: MainLayout,
        meta: { requiresAuth: true },
        children: [
            {
                path: '',
                redirect: '/dashboard'
            },
            {
                path: 'dashboard',
                name: 'Dashboard',
                component: DashboardView,
                meta: { title: 'Dashboard', requiresAuth: true }
            },
            {
                path: 'statistics',
                name: 'Statistics',
                component: StatisticsView,
                meta: { title: 'Statistics', requiresAuth: true }
            },
            {
                path: 'course/:id',
                name: 'CourseDetails',
                component: CourseDetailsView,
                meta: { title: 'Course Details', requiresAuth: true }
            },
            {
                path: 'admin',
                name: 'Admin',
                component: AdminView,
                meta: { title: 'Admin Panel', requiresAuth: true, adminOnly: true }
            }
        ]
    },

    {
        path: '/:pathMatch(.*)*',
        name: 'NotFound',
        redirect: '/dashboard'
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes,
    scrollBehavior(to, _from, savedPosition) {
        if (to.hash) {
            return {
                el: to.hash,
                behavior: 'smooth',
                top: 80 
            }
        }
        return savedPosition || { top: 0, behavior: 'smooth' }
    }
})

router.beforeEach((to, _from, next) => {
    const authStore = useAuthStore()
    const token = authStore.token
    const requiresAuth = to.meta.requiresAuth
    const isAdminRoute = to.meta.adminOnly

    if (to.meta.public) {
        if (token && to.path === '/login') {
            next('/dashboard')
        } else {
            next()
        }
        return
    }

    if (requiresAuth && !token) {
        next('/login')
        return
    }

    if (isAdminRoute) {
        // Пример: if (authStore.user?.role !== 'admin') next('/dashboard')
        // Пока просто пропускаем, но можно расширить
    }

    if (to.meta.title) {
        document.title = `${to.meta.title} • NeuroTutor`
    }

    next()
})

const app = createApp(App)

app.use(createPinia())
app.use(router)

app.mount('#app')