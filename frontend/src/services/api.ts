import axios from 'axios';
import { useAuthStore } from '@/store/authStore';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout();
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const authApi = {
  login: (email: string, password: string) =>
    api.post('/auth/login', { username: email, password }),
  register: (email: string, password: string, full_name: string) =>
    api.post('/auth/register', { email, password, full_name }),
  me: () => api.get('/auth/me'),
};

export const conversationApi = {
  list: () => api.get('/conversations'),
  create: (content: string, agent_type?: string) =>
    api.post('/conversations', { content, agent_type }),
  get: (id: number) => api.get(`/conversations/${id}`),
  sendMessage: (id: number, content: string) =>
    api.post(`/conversations/${id}/messages`, { content }),
  listAgents: () => api.get('/conversations/agents'),
};

export const reportApi = {
  list: () => api.get('/reports'),
  get: (uuid: string) => api.get(`/reports/${uuid}`),
};

export const paymentApi = {
  listPlans: () => api.get('/payments/plans'),
  checkout: (plan: string) => api.post(`/payments/checkout/${plan}`),
};
