import { defineStore } from 'pinia';
import api from '../api';

export const useAuthStore = defineStore('auth', {
    state: () => ({
        user: null,
        token: localStorage.getItem('jwt_token') || null,
    }),
    actions: {
        async login(credentials) {
            // credentials = { email, password }
            const response = await api.post('/auth/login', credentials);
            this.setAuth(response.data);
        },
        async register(data) {
            // data = { email, password, fullName }
            const response = await api.post('/auth/register', data);
            this.setAuth(response.data);
        },
        setAuth(data) {
            this.token = data.token;
            this.user = { email: data.email, id: data.userId };
            localStorage.setItem('jwt_token', data.token);
        },
        logout() {
            this.token = null;
            this.user = null;
            localStorage.removeItem('jwt_token');
        }
    }
});