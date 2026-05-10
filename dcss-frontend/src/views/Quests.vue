<template>
  <div class="quests-page">
    <div class="page-header">
      <h1>Тренировочные задания</h1>
      <p>Выберите задание для отработки навыков пилотирования</p>
    </div>

    <div class="quests-list">
      <div v-for="quest in questTypes" :key="quest.type_id" class="quest-card" :class="{ expanded: expandedQuest === quest.type_id }">
        <div class="quest-header" @click="toggleQuest(quest.type_id)">
          <div class="quest-main-info">
            <div class="status-indicator" :class="getQuestStatusClass(quest.type_id)"></div>
            <div class="quest-info">
              <h3>{{ quest.name }}</h3>
              <div class="quest-meta">
                <span class="quest-time">Время выполнения: {{ formatTime(quest.max_time_sec) }}</span>
                <span class="quest-difficulty">Сложность: {{ getDifficulty(quest.type_id) }}</span>
                <span class="quest-status">Статус: {{ getQuestStatusText(quest.type_id) }}</span>
              </div>
            </div>
          </div>
          <div class="quest-actions">
            <button class="btn-secondary" @click.stop="toggleQuest(quest.type_id)">Описание</button>
            <button 
              v-if="isQuestRunning(quest.type_id)"
              class="btn-danger" 
              @click.stop="requestStop(quest.type_id)"
            >
              Остановить
            </button>
            <button 
              class="btn-primary" 
              @click.stop="startQuest(quest.type_id)"
              :disabled="isQuestRunning(quest.type_id) || startingQuests[quest.type_id]"
            >
              {{ getActionButtonText(quest.type_id) }}
            </button>
          </div>
        </div>
        
        <div class="quest-tags">
          <span v-for="tag in getTags(quest.type_id)" :key="tag" class="quest-tag">{{ tag }}</span>
        </div>

        <div class="quest-content" v-if="expandedQuest === quest.type_id">
          <div class="quest-description">
            <h4> Описание задания</h4>
            <p>{{ quest.desc || 'Нет описания' }}</p>
            <div class="markdown" v-if="quest.markdown" v-html="renderedMarkdown(quest.markdown)"></div>
            
            <div class="description-details" v-if="quest.checklist && quest.checklist.length">
              <div class="detail-item">
                <strong> Критерии оценки</strong>
                <div class="criteria-list">
                  <div v-for="criterion in quest.checklist" :key="criterion.check_id" class="criterion-card">
                    <div class="criterion-header">
                      <span class="criterion-name">{{ criterion.name }}</span>
                      <span class="criterion-progress-value" v-if="currentProgress[quest.type_id] && currentProgress[quest.type_id][criterion.check_id] !== undefined">
                        {{ currentProgress[quest.type_id][criterion.check_id] }}%
                      </span>
                    </div>
                    <div class="criterion-desc">{{ criterion.desc }}</div>
                    <div class="progress-bar-container" v-if="currentProgress[quest.type_id] && currentProgress[quest.type_id][criterion.check_id] !== undefined">
                      <div class="progress-bar" :style="{ width: currentProgress[quest.type_id][criterion.check_id] + '%' }"></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <Modal
      :visible="modal.visible"
      :title="modal.title"
      :message="modal.message"
      :html-message="modal.htmlMessage"
      :show-cancel="modal.showCancel"
      :dark-mode="isDarkTheme"
      @update:visible="modal.visible = $event"
      @confirm="onModalConfirm"
    />
  </div>
</template>

<script>
import axios from 'axios';
import { marked } from 'marked';
import Modal from '@/components/Modal.vue';

export default {
  name: 'Quests',
  components: { Modal },
  data() {
    return {
      expandedQuest: null,
      questTypes: [],               
      activeQuests: {},            
      completedQuests: {},         
      currentProgress: {},         
      pollingIntervals: {},
      startingQuests: {},           
      isDarkTheme: false,
      modal: {
        visible: false,
        title: '',
        message: '',
        htmlMessage: '',
        callback: null,
        showCancel: false,
      },
    };
  },
  async created() {
    if (this.$root && typeof this.$root.isDarkTheme !== 'undefined') {
      this.isDarkTheme = this.$root.isDarkTheme;
    }
    await this.loadQuestTypes();
    await this.loadActiveQuestsFromServer();
    await this.loadCompletedQuestsFromServer();
  },
  beforeUnmount() {
    Object.values(this.pollingIntervals).forEach(clearInterval);
  },
  methods: {
    showModal(title, message, htmlMessage = '', callback = null, showCancel = false) {
      this.modal = {
        visible: true,
        title,
        message,
        htmlMessage,
        callback,
        showCancel,
      };
    },
    closeModal() {
      this.modal.visible = false;
      this.modal.callback = null;
    },
    onModalConfirm() {
      if (this.modal.callback) this.modal.callback();
      this.closeModal();
    },

    requestStop(typeId) {
      this.showModal(
        'Подтверждение',
        'Вы уверены, что хотите остановить выполнение задания?',
        '',
        () => this.performStop(typeId),
        true
      );
    },
    async performStop(typeId) {
      const quest = this.activeQuests[typeId];
      if (!quest || !quest.quest_guid) return;

      try {
        const response = await axios.post(`/quest/stop/${quest.quest_guid}`);
        if (response.data.success) {
          if (this.pollingIntervals[typeId]) {
            clearInterval(this.pollingIntervals[typeId]);
            delete this.pollingIntervals[typeId];
          }
          delete this.activeQuests[typeId];
          delete this.currentProgress[typeId];
          this.showModal('Задание остановлено', 'Выполнение задания успешно остановлено.');
        } else {
          this.showModal('Ошибка', 'Не удалось остановить задание. Сервер вернул ошибку.');
        }
      } catch (error) {
        console.error('Failed to stop quest:', error);
        this.showModal('Ошибка', 'Не удалось остановить задание. Проверьте соединение с сервером.');
      }
    },

    async loadQuestTypes() {
      try {
        const response = await axios.get('/quest/type?skip=0&take=100');
        if (response.data.success) {
          this.questTypes = response.data.data.types;
          for (const type of this.questTypes) {
            this.currentProgress[type.type_id] = {};
            await this.loadQuestTypeDetail(type.type_id);
          }
        }
      } catch (error) {
        console.error('Failed to load quest types:', error);
        this.showModal('Ошибка', 'Не удалось загрузить список заданий. Проверьте соединение с сервером.');
      }
    },
    async loadQuestTypeDetail(typeId) {
      try {
        const response = await axios.get(`/quest/type/${typeId}`);
        if (response.data.success) {
          const detail = response.data.data;
          const index = this.questTypes.findIndex(t => t.type_id === typeId);
          if (index !== -1) {
            this.questTypes[index].checklist = detail.checklist;
            this.questTypes[index].max_time_sec = detail.max_time_sec;
            this.questTypes[index].markdown = detail.markdown;
          }
        }
      } catch (error) {
        console.error(`Failed to load detail for quest type ${typeId}:`, error);
      }
    },
    async loadActiveQuestsFromServer() {
      try {
        const response = await axios.get('/quest', {
          params: { status: 'running', skip: 0, take: 50 }
        });
        if (response.data.success) {
          const items = response.data.data.list;
          for (const item of items) {
            const typeId = item.type_id;
            const questGuid = item.quest_guid;
            if (!this.activeQuests[typeId] || this.activeQuests[typeId].status !== 'running') {
              this.activeQuests[typeId] = {
                quest_guid: questGuid,
                link: item.link,
                status: item.status,
                result: item.result,
                progress: {},
                started_at: item.started,
                elapsed_time_sec: item.elapsed_time_sec
              };
              if (!this.currentProgress[typeId]) this.currentProgress[typeId] = {};
              this.startPolling(typeId, questGuid);
            }
          }
        }
      } catch (error) {
        console.error('Failed to load active quests from server', error);
      }
    },
    async loadCompletedQuestsFromServer() {
      try {
        const response = await axios.get('/quest', {
          params: { status: 'completed', skip: 0, take: 50 }
        });
        if (response.data.success) {
          const items = response.data.data.list;
          for (const item of items) {
            this.completedQuests[item.type_id] = {
              result: item.result,
              completed_at: item.completed
            };
          }
        }
      } catch (error) {
        console.error('Failed to load completed quests from server', error);
      }
    },

    async startQuest(typeId) {
      if (this.activeQuests[typeId] && this.activeQuests[typeId].status === 'running') return;
      if (this.startingQuests[typeId]) return;

      this.startingQuests[typeId] = true;   

      if (this.completedQuests[typeId]) {
        delete this.completedQuests[typeId];
      }

      if (this.activeQuests[typeId]) {
        delete this.activeQuests[typeId];
        delete this.currentProgress[typeId];
        if (this.pollingIntervals[typeId]) {
          clearInterval(this.pollingIntervals[typeId]);
          delete this.pollingIntervals[typeId];
        }
      }

      try {
        const response = await axios.post('/quest/start', { type_id: typeId });
        if (response.data.success) {
          const data = response.data.data;
          this.activeQuests[typeId] = {
            quest_guid: data.quest_guid,
            link: data.link,
            status: 'running',
            result: null,
            progress: {},
            started_at: new Date().toISOString()
          };
          this.currentProgress[typeId] = {};
          this.startPolling(typeId, data.quest_guid);
          
          const htmlMessage = `
            Задание <strong>${data.name}</strong> начато!<br><br>
            Для подключения к симулятору используйте:<br>
            <code style="background:#eee; padding:2px 6px; border-radius:4px;">${data.link}</code><br>
            (введите в Mission Planner как TCP)
          `;
          this.showModal('Задание запущено', '', htmlMessage);
        } else {
          this.showModal('Ошибка', 'Не удалось запустить задание. Сервер вернул ошибку.');
        }
      } catch (error) {
        console.error('Failed to start quest:', error);
        this.showModal('Ошибка', 'Не удалось запустить задание. Проверьте соединение с сервером.');
      } finally {
        this.startingQuests[typeId] = false; // Снимаем загрузку
      }
    },
    startPolling(typeId, questGuid) {
      if (this.pollingIntervals[typeId]) clearInterval(this.pollingIntervals[typeId]);
      const interval = setInterval(async () => {
        try {
          const response = await axios.get(`/quest/${questGuid}`);
          if (response.data.success) {
            const status = response.data.data;

            this.activeQuests[typeId] = {
              ...this.activeQuests[typeId],
              quest_guid: status.quest_guid,
              link: status.link,
              status: status.status,
              result: status.result,
              progress: status.checklist.reduce((acc, item) => {
                acc[item.check_id] = item.progress;
                return acc;
              }, {}),
              elapsed_time_sec: status.elapsed_time_sec,
              completed_at: status.completed
            };

            if (status.checklist) {
              this.currentProgress[typeId] = {};
              status.checklist.forEach(item => {
                this.currentProgress[typeId][item.check_id] = item.progress;
              });
            }

            if (status.status === 'completed' || status.status === 'aborted') {
              clearInterval(interval);
              delete this.pollingIntervals[typeId];

              if (status.status === 'completed') {
                this.completedQuests[typeId] = {
                  result: status.result,
                  completed_at: status.completed
                };
                const resultText = status.result === 'success' ? ' Успешно' : ' Не выполнено';
                this.showModal('Задание завершено', `Результат: ${resultText}`);
              } else {
                this.showModal('Задание остановлено', 'Задание было прервано.');
              }
            }
          }
        } catch (error) {
          console.error('Failed to fetch quest status:', error);
        }
      }, 2000);
      this.pollingIntervals[typeId] = interval;
    },

    isQuestRunning(typeId) {
      const quest = this.activeQuests[typeId];
      return quest && quest.status === 'running';
    },
    getQuestStatusClass(typeId) {
      if (this.activeQuests[typeId]) {
        if (this.activeQuests[typeId].status === 'running') return 'status-in-progress';
        if (this.activeQuests[typeId].status === 'completed') return 'status-completed';
        if (this.activeQuests[typeId].status === 'aborted') return 'status-failed';
      }
      if (this.completedQuests[typeId]) return 'status-completed';
      return 'status-not-started';
    },
    getQuestStatusText(typeId) {
      if (this.activeQuests[typeId]) {
        if (this.activeQuests[typeId].status === 'running') return 'В процессе';
        if (this.activeQuests[typeId].status === 'completed') return 'Выполнено';
        if (this.activeQuests[typeId].status === 'aborted') return 'Остановлено';
      }
      if (this.completedQuests[typeId]) return 'Выполнено';
      return 'Не начато';
    },
    getActionButtonText(typeId) {
      if (this.startingQuests[typeId]) return 'Запуск...';
      if (this.activeQuests[typeId]) {
        if (this.activeQuests[typeId].status === 'running') return 'В процессе...';
        if (this.activeQuests[typeId].status === 'completed') return 'Повторить';
        if (this.activeQuests[typeId].status === 'aborted') return 'Начать заново';
      }
      if (this.completedQuests[typeId]) return 'Повторить';
      return 'Начать задание';
    },
    formatTime(seconds) {
      const mins = Math.floor(seconds / 60);
      const secs = seconds % 60;
      return `${mins} мин ${secs} сек`;
    },
    getDifficulty(typeId) {
      const difficulties = { 1: 'Начальная', 2: 'Средняя', 3: 'Высокая', 4: 'Профессиональная' };
      return difficulties[typeId] || 'Средняя';
    },
    getTags(typeId) {
      const tagsMap = {
        1: ['Взлет', 'Высота 30м', 'Посадка'],
        2: ['Планирование', 'Маршрут', 'Сбор данных'],
        3: ['Ветер', 'Стабилизация', 'Экстренная посадка'],
        4: ['Координация', 'Группа', 'Синхронизация']
      };
      return tagsMap[typeId] || ['Задание'];
    },
    toggleQuest(typeId) {
      this.expandedQuest = this.expandedQuest === typeId ? null : typeId;
    },
    renderedMarkdown(markdown) {
      return marked.parse(markdown);
    }
  }
};
</script>


<style scoped>
.quests-page { display: grid; gap: 18px; }
.quests-list { display: grid; gap: 18px; }
.quest-card {
  background: #fff;
  border: 1px solid var(--line);
  border-radius: 24px;
  box-shadow: var(--shadow-sm);
  overflow: hidden;
  transition: transform .18s ease, box-shadow .18s ease;
}
.quest-card:hover { transform: translateY(-2px); box-shadow: var(--shadow); }
.quest-header {
  padding: 22px;
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 18px;
  align-items: start;
}
.quest-main-info { display: flex; gap: 14px; min-width: 0; }
.status-indicator { width: 12px; height: 12px; border-radius: 999px; margin-top: 9px; flex: 0 0 auto; }
.quest-info h3 { margin: 0 0 10px; font-size: 1.24rem; letter-spacing: -.02em; }
.quest-meta { display: flex; flex-wrap: wrap; gap: 10px; color: var(--muted); font-size: 14px; }
.quest-meta span { padding: 6px 10px; border-radius: 999px; background: var(--panel-2); }
.quest-actions { display: flex; flex-wrap: wrap; gap: 10px; justify-content: flex-end; }
.quest-tags { display: flex; flex-wrap: wrap; gap: 8px; padding: 0 22px 22px; }
.quest-tag { padding: 7px 11px; border-radius: 999px; background: var(--blue-soft); color: var(--blue-2); font-size: 12px; font-weight: 800; }
.quest-content { padding: 22px; border-top: 1px solid var(--line); background: #fbfdff; }
.quest-description h4 { margin: 0 0 10px; font-size: 1.08rem; }
.quest-description > p { color: var(--text-2); line-height: 1.7; }
.markdown {
  margin-top: 14px;
  padding: 16px 18px;
  border-radius: 18px;
  background: #fff;
  border: 1px solid var(--line);
  color: var(--text-2);
  line-height: 1.7;
}
.markdown ol, .markdown ul { padding-left: 22px; }
.description-details { margin-top: 18px; }
.detail-item strong { display: block; margin-bottom: 12px; }
.criteria-list { display: grid; gap: 12px; }
.criterion-card {
  padding: 16px;
  border: 1px solid var(--line);
  border-radius: 18px;
  background: #fff;
}
.criterion-header { display: flex; justify-content: space-between; gap: 12px; align-items: center; margin-bottom: 8px; }
.criterion-name { font-weight: 800; }
.criterion-progress-value { color: var(--blue-2); font-weight: 900; }
.criterion-desc { color: var(--muted); line-height: 1.6; }
.progress-bar-container { height: 9px; border-radius: 999px; background: #e2e8f0; overflow: hidden; margin-top: 12px; }
.progress-bar { height: 100%; border-radius: 999px; background: linear-gradient(90deg, var(--blue), #0ea5e9); }
@media (max-width: 900px) { .quest-header { grid-template-columns: 1fr; } .quest-actions { justify-content: flex-start; } }
</style>
