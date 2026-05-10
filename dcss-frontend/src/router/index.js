import { createRouter, createWebHistory } from 'vue-router';
import axios from 'axios';

import Home from '../views/Home.vue';
import Login from '../views/Login.vue';
import Register from '../views/Register.vue';
import Quests from '../views/Quests.vue';
import Profile from '../views/Profile.vue';
import History from '../views/History.vue';
import Admin from '../views/admin.vue';

const routes = [
  { path: '/', name: 'Home', component: Home, meta: { requiresAuth: true } },
  { path: '/quests', name: 'Quests', component: Quests, meta: { requiresAuth: true } },
  { path: '/history', name: 'History', component: History, meta: { requiresAuth: true } },
  { path: '/profile', name: 'Profile', component: Profile, meta: { requiresAuth: true } },
  { path: '/admin', name: 'Admin', component: Admin, meta: { requiresAuth: true, requiresInstructor: true } },
  { path: '/login', name: 'Login', component: Login },
  { path: '/register', name: 'Register', component: Register }
];

const router = createRouter({ history: createWebHistory(), routes });

function clearSession() {
  localStorage.removeItem('auth_token');
  localStorage.removeItem('user');
  delete axios.defaults.headers.common['Authorization'];
}

router.beforeEach(async (to, from, next) => {
  const token = localStorage.getItem('auth_token');
  const user = JSON.parse(localStorage.getItem('user') || '{}');

  if (!to.meta.requiresAuth) {
    next();
    return;
  }

  if (!token || !user.login) {
    clearSession();
    next('/login');
    return;
  }

  axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;

  try {
    const response = await axios.get('/user/me');
    if (!response.data || !response.data.success) {
      clearSession();
      next('/login');
      return;
    }

    const actualUser = response.data.data;
    localStorage.setItem('user', JSON.stringify(actualUser));

    if (to.meta.requiresInstructor && actualUser.role !== 'instructor') {
      next('/');
      return;
    }

    next();
  } catch (error) {
    clearSession();
    next('/login');
  }
});

export default router;
