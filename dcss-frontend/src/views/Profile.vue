<template>
  <div class="profile-page">
    <div class="profile-header">
      <h1>Настройки профиля</h1>
      <p>Управление вашими персональными данными</p>
    </div>

    <div class="profile-content">
      <form @submit.prevent="saveProfile" class="profile-form">
        <div class="form-section">
          <h3>Личная информация</h3>
          <div class="form-group">
            <label>Логин</label>
            <input type="text" v-model="profile.login" disabled>
          </div>
          <div class="form-group">
            <label>Email</label>
            <input type="email" v-model="profile.email" required>
          </div>
        </div>

        <div class="form-section">
          <h3>Смена пароля</h3>
          <div class="form-group">
            <label>Текущий пароль</label>
            <input type="password" v-model="passwordData.currentPassword">
          </div>
          <div class="form-group">
            <label>Новый пароль</label>
            <input type="password" v-model="passwordData.newPassword">
          </div>
          <div class="form-group">
            <label>Подтверждение пароля</label>
            <input type="password" v-model="passwordData.confirmPassword">
          </div>
        </div>

        <div class="form-actions">
          <button type="submit" :disabled="loading">{{ loading ? 'Сохранение...' : 'Сохранить изменения' }}</button>
        </div>
      </form>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'Profile',
  data() {
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    return {
      loading: false,
      profile: {
        login: user.login || '',
        email: user.email || ''
      },
      passwordData: {
        currentPassword: '',
        newPassword: '',
        confirmPassword: ''
      }
    };
  },
  methods: {
    async saveProfile() {
      if (this.passwordData.newPassword && this.passwordData.newPassword !== this.passwordData.confirmPassword) {
        alert('Новый пароль и подтверждение не совпадают');
        return;
      }

      this.loading = true;
      try {
        const updatedUser = {
          ...JSON.parse(localStorage.getItem('user')),
          email: this.profile.email
        };
        localStorage.setItem('user', JSON.stringify(updatedUser));
        this.$emit('profile-updated', updatedUser);
        alert('Профиль обновлён');
        this.passwordData = { currentPassword: '', newPassword: '', confirmPassword: '' };
      } catch (error) {
        console.error('Save error', error);
        alert('Ошибка сохранения');
      } finally {
        this.loading = false;
      }
    }
  }
};
</script>


<style scoped>
.profile-page { max-width: 860px; margin: 0 auto; }
.profile-content { display: grid; gap: 18px; }
.profile-form { display: grid; gap: 18px; }
.form-section {
  padding: 24px;
  border-radius: 22px;
  background: #fff;
  border: 1px solid var(--line);
  box-shadow: var(--shadow-sm);
}
.form-section h3 { margin: 0 0 18px; font-size: 1.25rem; letter-spacing: -.02em; }
.form-group { display: grid; gap: 8px; margin-bottom: 16px; }
.form-group:last-child { margin-bottom: 0; }
.form-actions {
  display: flex;
  justify-content: flex-end;
  padding: 18px 0 0;
}
.form-actions button { min-width: 210px; }
@media (max-width: 640px) { .form-actions button { width: 100%; } }
</style>
