<template>
    <div class="admin-page">
      <h1>Панель инструктора</h1>
  
      <div class="stats">
        <div class="stat-card">Всего пользователей: {{ stats.total_users }}</div>
        <div class="stat-card">Всего заданий: {{ stats.total_quests }}</div>
        <div class="stat-card">Выполнено: {{ stats.completed_quests }}</div>
        <div class="stat-card">Успешно: {{ stats.success_quests }}</div>
      </div>
  
      <div class="users-list">
        <h2>Пользователи</h2>
        <table>
          <thead>
            <tr>
              <th>ID</th><th>Логин</th><th>Email</th><th>Роль</th><th>Дата регистрации</th><th>Действия</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="user in users" :key="user.id">
              <td>{{ user.id }}</td>
              <td>{{ user.login }}</td>
              <td>{{ user.email }}</td>
              <td>{{ user.role }}</td>
              <td>{{ formatDate(user.created_at) }}</td>
              <td><button @click="viewUserQuests(user.id, user.login)">Задания</button></td>
            </tr>
          </tbody>
        </table>
        <button v-if="hasMoreUsers" @click="loadMoreUsers" class="load-more">Загрузить ещё</button>
      </div>
  
      <div v-if="selectedUserQuests" class="modal-overlay" @click.self="closeUserQuests">
        <div class="modal-content">
          <div class="modal-header">
            <h3>Задания пользователя: {{ selectedUserLogin }}</h3>
            <button class="modal-close" @click="closeUserQuests">×</button>
          </div>
          <div class="modal-body">
            <table class="quests-table">
              <thead>
                <tr><th>Тип</th><th>Статус</th><th>Результат</th><th>Начало</th><th>Окончание</th></tr>
              </thead>
              <tbody>
                <tr v-for="q in selectedUserQuests" :key="q.guid">
                  <td>{{ q.type_id }}</td>
                  <td>{{ q.status }}</td>
                  <td>{{ q.result || '—' }}</td>
                  <td>{{ formatDate(q.started_at) }}</td>
                  <td>{{ formatDate(q.completed_at) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="modal-footer">
            <button @click="closeUserQuests">Закрыть</button>
          </div>
        </div>
      </div>
    </div>
  </template>
  
  <script>
  import axios from 'axios';
  
  export default {
    name: 'Admin',
    data() {
      return {
        users: [],
        userSkip: 0,
        userTake: 20,
        totalUsers: 0,
        stats: {},
        selectedUserQuests: null,
        selectedUserLogin: ''
      };
    },
    computed: {
      hasMoreUsers() {
        return this.users.length < this.totalUsers;
      }
    },
    async created() {
      await this.loadStats();
      await this.loadUsers();
    },
    methods: {
      async loadStats() {
        try {
          const res = await axios.get('/admin/stats');
          if (res.data.success) this.stats = res.data.data;
        } catch (e) {
          console.error('Failed to load stats', e);
        }
      },
      async loadUsers(reset = true) {
        if (reset) {
          this.userSkip = 0;
          this.users = [];
        }
        try {
          const res = await axios.get('/admin/users', {
            params: { skip: this.userSkip, take: this.userTake }
          });
          if (res.data.success) {
            this.users.push(...res.data.data.list);
            this.totalUsers = res.data.data.total;
            this.userSkip += this.userTake;
          }
        } catch (e) {
          console.error('Failed to load users', e);
        }
      },
      loadMoreUsers() {
        this.loadUsers(false);
      },
      async viewUserQuests(userId, userLogin) {
        try {
          const res = await axios.get(`/admin/users/${userId}/quests`);
          if (res.data.success) {
            this.selectedUserQuests = res.data.data.list;
            this.selectedUserLogin = userLogin;
          }
        } catch (e) {
          console.error('Failed to load user quests', e);
        }
      },
      closeUserQuests() {
        this.selectedUserQuests = null;
      },
      formatDate(dateStr) {
        if (!dateStr) return '—';
        return new Date(dateStr).toLocaleString();
      }
    }
  };
  </script>


<style scoped>
.admin-page { display: grid; gap: 18px; }
.admin-page h1 { margin-bottom: 4px; }
.stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}
.stat-card {
  padding: 20px;
  border-radius: 20px;
  background: #fff;
  border: 1px solid var(--line);
  box-shadow: var(--shadow-sm);
  text-align: left;
  font-weight: 800;
}
.users-list {
  padding: 20px;
  border-radius: 22px;
  background: #fff;
  border: 1px solid var(--line);
  box-shadow: var(--shadow-sm);
  overflow: hidden;
}
.users-list h2 { margin: 0 0 14px; }
table { width: 100%; border-collapse: collapse; min-width: 780px; }
th, td { padding: 14px; border-bottom: 1px solid var(--line); text-align: left; }
th { background: var(--panel-2); color: var(--muted); font-size: 13px; text-transform: uppercase; letter-spacing: .04em; }
.users-list { overflow-x: auto; }
.modal-overlay {
  position: fixed; inset: 0; z-index: 10000; display: flex; align-items: center; justify-content: center;
  padding: 24px; background: rgba(15,23,42,.46); backdrop-filter: blur(5px);
}
.modal-content {
  width: min(980px, 100%); max-height: calc(100vh - 48px); display: flex; flex-direction: column;
  background: #fff; border: 1px solid var(--line); border-radius: 22px; box-shadow: var(--shadow); overflow: hidden;
}
.modal-header, .modal-footer { padding: 18px 22px; display: flex; justify-content: space-between; align-items: center; gap: 12px; }
.modal-header { border-bottom: 1px solid var(--line); }
.modal-header h3 { margin: 0; }
.modal-close { width: 36px; height: 36px; border: 0; border-radius: 12px; background: transparent; font-size: 28px; color: var(--muted); }
.modal-body { padding: 20px; overflow: auto; }
.modal-footer { justify-content: flex-end; border-top: 1px solid var(--line); background: var(--panel-2); }
@media (max-width: 900px) { .stats { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 560px) { .stats { grid-template-columns: 1fr; } }
</style>
