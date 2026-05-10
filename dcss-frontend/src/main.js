import { createApp } from 'vue';
import App from './App.vue';
import router from './router';
import axios from 'axios';
import './assets/main.css';

axios.defaults.baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const token = localStorage.getItem('auth_token');
if (token) axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;

function clearSessionAndRedirectToLogin() {
  localStorage.removeItem('auth_token');
  localStorage.removeItem('user');
  delete axios.defaults.headers.common['Authorization'];
  if (window.location.pathname !== '/login' && window.location.pathname !== '/register') {
    window.location.href = '/login';
  }
}

axios.interceptors.response.use(
  response => response,
  error => {
    const isUnauthorized = error.response && error.response.status === 401;
    if (isUnauthorized) clearSessionAndRedirectToLogin();
    return Promise.reject(error);
  }
);

const app = createApp(App);
app.use(router);
app.mount('#app');
