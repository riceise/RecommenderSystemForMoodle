import { defineStore } from 'pinia';
import api from '../Api/index';

interface AuthUser {
    email: string;
    id: string;
}

interface AuthResponse {
    token: string;
    email: string;
    userId: string;
}

interface LoginCredentials {
    email: string;
    password: string;
}

interface RegisterData {
    email: string;
    password: string;
    fullName: string;
}

export const useAuthStore = defineStore('auth', {
    state: () => ({
        user: null as AuthUser | null,
        token: (typeof window !== 'undefined' && localStorage.getItem('jwt_token')) || null as string | null,
    }),
    actions: {
        async login(credentials: LoginCredentials) {
            const response = await api.post<AuthResponse>('/auth/login', credentials);
            this.setAuth(response.data);
        },
        async register(data: RegisterData) {
            const response = await api.post<AuthResponse>('/auth/register', data);
            this.setAuth(response.data);
        },
        setAuth(data: AuthResponse) {
            this.token = data.token;
            this.user = { email: data.email, id: data.userId };
            if (typeof window !== 'undefined') {
                localStorage.setItem('jwt_token', data.token);
            }
        },
        logout() {
            this.token = null;
            this.user = null;
            if (typeof window !== 'undefined') {
                localStorage.removeItem('jwt_token');
            }
        }
    }
});
