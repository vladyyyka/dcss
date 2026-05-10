<template>
  <div class="history-page">
    <div class="page-header">
      <h1>История выполнения заданий</h1>
      <p>Обзор вашей тренировочной активности и результатов</p>
    </div>

    <div class="history-controls">
      <div class="filter-group">
        <label for="status-filter">Фильтр по статусу:</label>
        <select id="status-filter" v-model="statusFilter" class="filter-select">
          <option value="all">Все задания</option>
          <option value="completed">Выполнено</option>
          <option value="aborted">Не завершено</option>
        </select>
      </div>
      
      <div class="filter-group">
        <label for="date-filter">Период:</label>
        <select id="date-filter" v-model="dateFilter" class="filter-select">
          <option value="all">За все время</option>
          <option value="week">За неделю</option>
          <option value="month">За месяц</option>
          <option value="3months">За 3 месяца</option>
        </select>
      </div>
    </div>

    <div v-if="loading" class="loading-spinner">Загрузка...</div>
    <div v-else class="history-table-container">
      <table class="history-table">
        <thead>
          <tr>
            <th @click="sortBy('questName')" class="sortable">
              Название задания
              <span class="sort-indicator" v-if="sortField === 'questName'">
                {{ sortDirection === 'asc' ? '↑' : '↓' }}
              </span>
            </th>
            <th @click="sortBy('startDate')" class="sortable">
              Дата начала
              <span class="sort-indicator" v-if="sortField === 'startDate'">
                {{ sortDirection === 'asc' ? '↑' : '↓' }}
              </span>
            </th>
            <th @click="sortBy('completedDate')" class="sortable">
              Дата завершения
              <span class="sort-indicator" v-if="sortField === 'completedDate'">
                {{ sortDirection === 'asc' ? '↑' : '↓' }}
              </span>
            </th>
            <th @click="sortBy('result')" class="sortable">
              Результат
              <span class="sort-indicator" v-if="sortField === 'result'">
                {{ sortDirection === 'asc' ? '↑' : '↓' }}
              </span>
            </th>
            <th>Статус</th>
            <th>Логи</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="attempt in filteredAttempts" :key="attempt.quest_guid" class="history-row">
            <td class="quest-name">
              <strong>{{ attempt.questName }}</strong>
            </td>
            <td class="date-cell">{{ formatDate(attempt.startDate) }}</td>
            <td class="date-cell">{{ formatDate(attempt.completedDate) }}</td>
            <td class="score-cell">
              <div v-if="attempt.result" class="score-display">
                <div class="score-value">{{ getResultText(attempt.result) }}</div>
              </div>
              <span v-else class="no-score">—</span>
            </td>
            <td class="status-cell">
              <span class="status-badge" :class="getStatusClass(attempt.status)">
                {{ getStatusText(attempt.status) }}
              </span>
            </td>
            <td class="log-cell">
              <button @click="viewLog(attempt.quest_guid)" class="log-btn">📋 Лог</button>
            </td>
          </tr>
        </tbody>
      </table>

      <div v-if="filteredAttempts.length === 0" class="no-data">
        <p>Нет данных для отображения</p>
        <p class="no-data-hint">Начните выполнение заданий на странице "Задания"</p>
        <router-link to="/quests" class="btn-primary">Перейти к заданиям</router-link>
      </div>
    </div>

    <div v-if="showLogModal" class="modal-overlay" @click.self="closeLogModal">
      <div class="modal-content">
        <div class="modal-header">
          <h3>Лог выполнения задания</h3>
          <button class="modal-close" @click="closeLogModal">×</button>
        </div>
        <div class="modal-body">
          <pre class="log-content">{{ currentLog }}</pre>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="closeLogModal">Закрыть</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'History',
  data() {
    return {
      loading: true,
      instances: [],
      questTypes: {},
      sortField: 'startDate',
      sortDirection: 'desc',
      statusFilter: 'all',
      dateFilter: 'all',
      showLogModal: false,
      currentLog: ''
    };
  },
  computed: {
    filteredAttempts() {
      let filtered = [...this.instances];
      if (this.statusFilter !== 'all') {
        filtered = filtered.filter(attempt => attempt.status === this.statusFilter);
      }
      if (this.dateFilter !== 'all') {
        const now = new Date();
        let cutoffDate = new Date();
        switch (this.dateFilter) {
          case 'week':
            cutoffDate.setDate(now.getDate() - 7);
            break;
          case 'month':
            cutoffDate.setMonth(now.getMonth() - 1);
            break;
          case '3months':
            cutoffDate.setMonth(now.getMonth() - 3);
            break;
        }
        filtered = filtered.filter(attempt => new Date(attempt.startDate) >= cutoffDate);
      }
      return filtered.sort((a, b) => {
        let aValue = a[this.sortField];
        let bValue = b[this.sortField];
        if (this.sortField.includes('Date')) {
          aValue = new Date(aValue || 0);
          bValue = new Date(bValue || 0);
        }
        if (aValue < bValue) return this.sortDirection === 'asc' ? -1 : 1;
        if (aValue > bValue) return this.sortDirection === 'asc' ? 1 : -1;
        return 0;
      });
    }
  },
  async created() {
    await this.loadQuestTypes();
    await this.loadHistory();
  },
  methods: {
    async loadQuestTypes() {
      try {
        const response = await axios.get('/quest/type?skip=0&take=100');
        if (response.data.success) {
          const types = response.data.data.types;
          types.forEach(type => {
            this.questTypes[type.type_id] = type.name;
          });
        }
      } catch (error) {
        console.error('Failed to load quest types:', error);
      }
    },
    async loadHistory() {
      this.loading = true;
      try {
        const response = await axios.get('/quest', {
          params: { skip: 0, take: 100 }
        });
        if (response.data.success) {
          const items = response.data.data.list;
          this.instances = items.map(item => ({
            quest_guid: item.quest_guid,
            type_id: item.type_id,
            questName: this.questTypes[item.type_id] || `Задание ${item.type_id}`,
            startDate: item.started,
            completedDate: item.completed,
            status: item.status,
            result: item.result
          }));
        }
      } catch (error) {
        console.error('Failed to load history:', error);
      } finally {
        this.loading = false;
      }
    },
    async viewLog(questGuid) {
      try {
        const response = await axios.get(`/quest/log/${questGuid}`);
        if (response.data.success) {
          this.currentLog = response.data.data.log || 'Лог пуст';
          this.showLogModal = true;
        } else {
          alert('Лог не найден');
        }
      } catch (error) {
        console.error('Failed to fetch log', error);
        alert('Ошибка получения лога');
      }
    },
    closeLogModal() {
      this.showLogModal = false;
      this.currentLog = '';
    },
    sortBy(field) {
      if (this.sortField === field) {
        this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
      } else {
        this.sortField = field;
        this.sortDirection = 'asc';
      }
    },
    formatDate(dateString) {
      if (!dateString) return '—';
      const date = new Date(dateString);
      return date.toLocaleDateString('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    },
    getResultText(result) {
      if (result === 'success') return 'Успешно';
      if (result === 'fail') return 'Не выполнено';
      return result;
    },
    getStatusClass(status) {
      return `status-${status}`;
    },
    getStatusText(status) {
      const statusMap = {
        'completed': 'Выполнено',
        'aborted': 'Не завершено',
        'running': 'В процессе'
      };
      return statusMap[status] || status;
    }
  }
};
</script>


<style scoped>
.history-page { display: grid; gap: 18px; }
.history-controls {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  padding: 18px;
  border-radius: 20px;
  background: #fff;
  border: 1px solid var(--line);
  box-shadow: var(--shadow-sm);
}
.filter-group { display: grid; gap: 8px; min-width: 220px; }
.loading-spinner {
  padding: 30px;
  border-radius: 20px;
  background: #fff;
  border: 1px solid var(--line);
  color: var(--muted);
}
.history-table-container {
  border-radius: 22px;
  overflow: hidden;
  background: #fff;
  border: 1px solid var(--line);
  box-shadow: var(--shadow-sm);
}
.history-table { width: 100%; border-collapse: collapse; min-width: 850px; }
.history-table th, .history-table td { padding: 16px; border-bottom: 1px solid var(--line); text-align: left; vertical-align: middle; }
.history-table th { background: var(--panel-2); font-size: 13px; color: var(--muted); text-transform: uppercase; letter-spacing: .04em; }
.history-table tbody tr:hover { background: #fbfdff; }
.sortable { cursor: pointer; user-select: none; }
.quest-name strong { color: var(--text); line-height: 1.45; }
.date-cell { white-space: nowrap; color: var(--text-2); }
.score-value { font-weight: 800; }
.no-score { color: var(--muted); }
.status-cell { width: 170px; min-width: 170px; white-space: nowrap; }
.log-cell { width: 120px; min-width: 120px; text-align: center; }
.no-data { padding: 40px 20px; text-align: center; color: var(--muted); }
.no-data p { margin: 0 0 10px; }
.no-data .btn-primary { margin-top: 12px; }
.modal-overlay {
  position: fixed; inset: 0; z-index: 10000; display: flex; align-items: center; justify-content: center;
  padding: 24px; background: rgba(15,23,42,.46); backdrop-filter: blur(5px);
}
.modal-content {
  width: min(980px, 100%); max-height: calc(100vh - 48px); display: flex; flex-direction: column;
  background: #fff; border: 1px solid var(--line); border-radius: 22px; box-shadow: var(--shadow); overflow: hidden;
}
.modal-header, .modal-footer { padding: 18px 22px; display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.modal-header { border-bottom: 1px solid var(--line); }
.modal-header h3 { margin: 0; }
.modal-close { width: 36px; height: 36px; border: 0; border-radius: 12px; background: transparent; font-size: 28px; color: var(--muted); }
.modal-close:hover { background: var(--panel-2); }
.modal-body { padding: 20px; overflow: auto; }
.log-content {
  margin: 0; max-height: 60vh; overflow: auto; padding: 16px; border-radius: 16px;
  border: 1px solid var(--line); background: #f8fafc; color: #0f172a;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 13px; line-height: 1.65;
  white-space: pre-wrap; word-break: break-word;
}
.modal-footer { justify-content: flex-end; border-top: 1px solid var(--line); background: var(--panel-2); }
@media (max-width: 760px) { .history-table-container { overflow-x: auto; } .filter-group { min-width: 100%; } }
</style>
