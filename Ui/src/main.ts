import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import AdminView from './views/AdminView.vue'
import './style.css'

import App from './App.vue'

import AuthView from './views/AuthView.vue'
import DashboardView from './views/DashboardView.vue'
import CourseDetailsView from './views/CourseDetailsView.vue'


const routes: Array<RouteRecordRaw> = [
    {
        path: '/',
        redirect: '/login'
    },
    {
        path: '/login',
        name: 'Login',
        component: AuthView
    },
    {
        path: '/dashboard',
        name: 'Dashboard',
        component: DashboardView,
        //добавить проверку авторизации (Navigation Guard)
        // meta: { requiresAuth: true }
    },
    {
        path: '/course/:id',
        name: 'CourseDetailsView',
        component: CourseDetailsView
    },
    {
        path: '/admin',
        name: 'admin',
        component: AdminView
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

const app = createApp(App)

app.use(createPinia()) 
app.use(router)       

app.mount('#app')