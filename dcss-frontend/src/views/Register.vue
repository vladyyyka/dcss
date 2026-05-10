<template>
  <div class="register-page">
    <div class="register-container">
      <div class="register-card">
        <h2>Регистрация</h2>
        <form @submit.prevent="handleRegister">
          <div class="form-group">
            <label>Логин</label>
            <input type="text" v-model="form.login" required>
          </div>
          <div class="form-group">
            <label>Email</label>
            <input type="email" v-model="form.email" required>
          </div>
          <div class="form-group">
            <label>Пароль</label>
            <input type="password" v-model="form.password" required>
          </div>
          <div class="form-group">
            <label>Подтвердите пароль</label>
            <input type="password" v-model="form.confirmPassword" required>
          </div>
          <button type="submit" :disabled="loading">{{ loading ? 'Регистрация...' : 'Зарегистрироваться' }}</button>
        </form>
        <div class="register-links">
          <router-link to="/login">Уже есть аккаунт? Войти</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
export default {
  data() {
    return { loading: false, form: { login: '', email: '', password: '', confirmPassword: '' } };
  },
  methods: {
    async handleRegister() {
      if (this.form.password !== this.form.confirmPassword) {
        alert('Пароли не совпадают');
        return;
      }
      this.loading = true;
      try {
        const res = await axios.post('/auth/register', {
          login: this.form.login,
          email: this.form.email,
          password: this.form.password
        });
        if (res.data.success) {
          this.$emit('user-registered', { token: res.data.data.auth_token, user: res.data.data.user });
          this.$router.push('/');
        } else alert('Ошибка регистрации');
      } catch (e) {
        alert('Такой логин или email уже существует');
      } finally {
        this.loading = false;
      }
    }
  }
};
</script>


<style scoped>
.register-page {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 24px;
  background: radial-gradient(circle at top right, rgba(37,99,235,.12), transparent 32rem), var(--page);
}
.register-container { width: min(500px, 100%); }
.register-card {
  padding: 32px;
  border-radius: 26px;
  background: rgba(255,255,255,.92);
  border: 1px solid var(--line);
  box-shadow: var(--shadow);
}
.register-card h2 { margin: 0 0 24px; font-size: 2rem; letter-spacing: -.04em; }
form { display: grid; gap: 16px; }
.form-group { display: grid; gap: 8px; margin: 0; }
button[type="submit"] { width: 100%; margin-top: 4px; }
.register-links { margin-top: 18px; text-align: center; color: var(--muted); }
.register-links a { color: var(--blue-2); font-weight: 800; }
</style>
