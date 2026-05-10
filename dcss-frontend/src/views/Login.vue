<template>
  <div class="login-page">
    <div class="login-container">
      <div class="login-card">
        <div class="login-header">
          <h2>Вход в систему</h2>
        </div>
        <form @submit.prevent="handleLogin">
          <div class="form-group">
            <label>Логин</label>
            <input type="text" v-model="loginData.login" required>
          </div>
          <div class="form-group">
            <label>Пароль</label>
            <input type="password" v-model="loginData.password" required>
          </div>
          <button type="submit" :disabled="loading">{{ loading ? 'Вход...' : 'Войти' }}</button>
        </form>
        <div class="login-links">
          <router-link to="/register">Регистрация</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
export default {
  data() {
    return { loading: false, loginData: { login: '', password: '' } };
  },
  methods: {
    async handleLogin() {
      this.loading = true;
      try {
        let res;
        try {
          res = await axios.post('/auth', {
            login: this.loginData.login,
            password: this.loginData.password
          });
        } catch (postError) {
          // Временная совместимость со старым backend, где авторизация была GET /auth.
          if (postError.response && [404, 405, 422].includes(postError.response.status)) {
            res = await axios.get('/auth', { params: this.loginData });
          } else {
            throw postError;
          }
        }

        if (res.data.success) {
          this.$emit('user-logged-in', { token: res.data.data.auth_token, user: res.data.data.user });
          this.$router.push('/');
        } else {
          alert('Ошибка входа');
        }
      } catch (e) {
        alert('Неверный логин или пароль');
      } finally {
        this.loading = false;
      }
    }
  }
};
</script>


<style scoped>
.login-page {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 24px;
  background: radial-gradient(circle at top left, rgba(37,99,235,.12), transparent 32rem), var(--page);
}
.login-container { width: min(440px, 100%); }
.login-card {
  padding: 32px;
  border-radius: 26px;
  background: rgba(255,255,255,.92);
  border: 1px solid var(--line);
  box-shadow: var(--shadow);
}
.login-header { text-align: left; margin-bottom: 24px; }
.login-header h2 { margin: 0; font-size: 2rem; letter-spacing: -.04em; }
form { display: grid; gap: 16px; }
.form-group { display: grid; gap: 8px; margin: 0; }
button[type="submit"] { width: 100%; margin-top: 4px; }
.login-links { margin-top: 18px; text-align: center; color: var(--muted); }
.login-links a { color: var(--blue-2); font-weight: 800; }
</style>
