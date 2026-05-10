<template>
  <div class="app-shell">
    <template v-if="isLoggedIn">
      <header class="app-header">
        <div class="header-inner">
          <router-link to="/" class="brand">
            <div class="brand-icon">D</div>
            <div class="brand-text">
              <strong>DCSS</strong>
              <span>Drone Control Simulation Server</span>
            </div>
          </router-link>

          <nav class="main-nav">
            <router-link to="/" exact-active-class="active">Главная</router-link>
            <router-link to="/quests" active-class="active">Задания</router-link>
            <router-link to="/history" active-class="active">История</router-link>
            <router-link to="/profile" active-class="active">Профиль</router-link>
            <router-link v-if="user.role === 'instructor'" to="/admin" active-class="active">Администрирование</router-link>
          </nav>

          <div class="account" @click="toggleProfileDropdown">
            <div class="avatar">{{ userInitials }}</div>
            <div class="account-text">
              <strong>{{ user.login }}</strong>
              <span>{{ user.role === 'instructor' ? 'Инструктор' : 'Пилот' }}</span>
            </div>
            <span class="chevron">▾</span>

            <div v-if="showProfileDropdown" class="account-menu" @click.stop>
              <div class="account-card-head">
                <div class="avatar large">{{ userInitials }}</div>
                <div>
                  <strong>{{ user.login }}</strong>
                  <span>{{ user.email }}</span>
                </div>
              </div>
              <router-link to="/profile" @click="closeProfileDropdown">Профиль</router-link>
              <router-link to="/history" @click="closeProfileDropdown">История</router-link>
              <button @click="logout">Выйти</button>
            </div>
          </div>
        </div>
      </header>

      <main class="app-main">
        <router-view @profile-updated="updateUser" />
      </main>
    </template>

    <template v-else>
      <router-view @user-logged-in="handleUserLogin" @user-registered="handleUserLogin" />
    </template>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'App',
  data() {
    return {
      showProfileDropdown: false,
      isLoggedIn: false,
      user: { login: '', email: '', role: '' }
    };
  },
  computed: {
    userInitials() {
      return (this.user.login ? this.user.login[0] : '?').toUpperCase();
    }
  },
  async created() {
    await this.restoreSession();
  },
  mounted() {
    document.addEventListener('click', this.handleOutsideClick);
  },
  beforeUnmount() {
    document.removeEventListener('click', this.handleOutsideClick);
  },
  methods: {
    async restoreSession() {
      const token = localStorage.getItem('auth_token');
      const savedUser = localStorage.getItem('user');

      if (!token || !savedUser) {
        this.isLoggedIn = false;
        return;
      }

      try {
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
        const response = await axios.get('/user/me');
        if (response.data && response.data.success) {
          this.user = response.data.data;
          localStorage.setItem('user', JSON.stringify(response.data.data));
          this.isLoggedIn = true;
        } else {
          this.forceLogout();
        }
      } catch (error) {
        this.forceLogout();
      }
    },
    toggleProfileDropdown() {
      this.showProfileDropdown = !this.showProfileDropdown;
    },
    closeProfileDropdown() {
      this.showProfileDropdown = false;
    },
    handleOutsideClick(event) {
      if (!event.target.closest('.account')) this.showProfileDropdown = false;
    },
    handleUserLogin({ token, user }) {
      this.user = user;
      this.isLoggedIn = true;
      localStorage.setItem('auth_token', token);
      localStorage.setItem('user', JSON.stringify(user));
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      this.$router.push('/');
    },
    updateUser(updatedUser) {
      this.user = updatedUser;
      localStorage.setItem('user', JSON.stringify(updatedUser));
    },
    forceLogout() {
      this.isLoggedIn = false;
      this.user = { login: '', email: '', role: '' };
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user');
      delete axios.defaults.headers.common['Authorization'];
      if (this.$route && this.$route.path !== '/login' && this.$route.path !== '/register') {
        this.$router.push('/login');
      }
    },
    logout() {
      this.forceLogout();
    }
  }
};
</script>

<style>
.app-shell { min-height: 100vh; }
.app-header {
  position: sticky;
  top: 0;
  z-index: 100;
  background: rgba(255,255,255,.82);
  backdrop-filter: blur(18px);
  border-bottom: 1px solid rgba(226,232,240,.9);
}
.header-inner {
  max-width: 1440px;
  margin: 0 auto;
  min-height: 76px;
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: 24px;
  padding: 0 28px;
}
.brand { display: flex; align-items: center; gap: 14px; }
.brand-icon {
  width: 46px;
  height: 46px;
  border-radius: 16px;
  display: grid;
  place-items: center;
  background: linear-gradient(135deg, #2563eb, #0f172a);
  color: #fff;
  font-weight: 900;
  box-shadow: 0 14px 30px rgba(37,99,235,.25);
}
.brand-text { display: flex; flex-direction: column; line-height: 1.15; }
.brand-text strong { font-size: 1.35rem; letter-spacing: -.03em; }
.brand-text span { color: var(--muted); font-size: 13px; }
.main-nav {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 6px;
}
.main-nav a {
  padding: 10px 14px;
  border-radius: 999px;
  color: var(--muted);
  font-weight: 800;
  font-size: 14px;
}
.main-nav a:hover { background: var(--panel-2); color: var(--text); }
.main-nav a.active { background: var(--blue-soft); color: var(--blue-2); }
.account {
  position: relative;
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 210px;
  padding: 8px 10px;
  border: 1px solid var(--line);
  border-radius: 16px;
  background: #fff;
  box-shadow: var(--shadow-sm);
}
.avatar {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: var(--blue-soft);
  color: var(--blue-2);
  font-weight: 900;
}
.avatar.large { width: 50px; height: 50px; }
.account-text { display: flex; flex-direction: column; line-height: 1.15; min-width: 0; }
.account-text strong { font-size: 14px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.account-text span { font-size: 12px; color: var(--muted); }
.chevron { margin-left: auto; color: var(--muted); }
.account-menu {
  position: absolute;
  top: calc(100% + 12px);
  right: 0;
  width: 280px;
  padding: 12px;
  background: #fff;
  border: 1px solid var(--line);
  border-radius: 18px;
  box-shadow: var(--shadow);
}
.account-card-head {
  display: flex;
  gap: 12px;
  align-items: center;
  padding: 8px 8px 12px;
  border-bottom: 1px solid var(--line);
  margin-bottom: 8px;
}
.account-card-head div:last-child { display: flex; flex-direction: column; min-width: 0; }
.account-card-head span { color: var(--muted); font-size: 13px; word-break: break-word; }
.account-menu a, .account-menu button {
  display: block;
  width: 100%;
  padding: 11px 12px;
  border: 0;
  border-radius: 12px;
  background: transparent;
  text-align: left;
  color: var(--text-2);
  font-weight: 700;
}
.account-menu a:hover, .account-menu button:hover { background: var(--panel-2); }
.account-menu button { color: #b91c1c; }
.app-main {
  max-width: var(--container);
  margin: 0 auto;
  padding: 34px 24px 56px;
}
@media (max-width: 1100px) {
  .header-inner { grid-template-columns: 1fr; padding: 16px; gap: 14px; }
  .main-nav { justify-content: flex-start; flex-wrap: wrap; }
  .account { width: 100%; max-width: 360px; }
}
@media (max-width: 640px) {
  .brand-text span { display: none; }
  .main-nav a { padding: 9px 12px; font-size: 13px; }
  .app-main { padding: 24px 16px 40px; }
}
</style>
