<template>
  <div class="home-page">
    <div class="welcome-section">
      <h2>Добро пожаловать в DCSS!</h2>
      <p class="system-description">Система тренажерной подготовки пилотов БВС</p>
      
      <div class="description">
        <strong>DCSS (Drone Control Simulation Server)</strong> - это комплексная система 
        для обучения и оценки навыков пилотов беспилотных воздушных судов.
        Разработана для подготовки специалистов в области управления дронами с соблюдением
        всех требований безопасности и эффективности.
      </div>

      <div class="stats">
        <div class="stat-item">
          <span class="stat-label">Доступно заданий</span>
          <span class="stat-value">{{ totalQuestTypes }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">Выполнено вами</span>
          <span class="stat-value">{{ uniqueCompletedTypes }}</span>
        </div>
      </div>

      <div class="quick-actions">
        <router-link to="/quests" class="btn start-training-btn">
          Перейти к заданиям
        </router-link>
      </div>
    </div>

    <div class="system-info">
      <h3>Функциональные возможности системы</h3>
      <div class="info-grid">
        <div class="info-card">
          <h4>Реалистичная симуляция полетов</h4>
          <p>Полное воспроизведение физики полета и поведения беспилотных воздушных судов в различных условиях</p>
        </div>
        <div class="info-card">
          <h4>Оценка навыков пилотирования</h4>
          <p>Детальный анализ выполнения заданий с формированием отчетов и рекомендаций</p>
        </div>
        <div class="info-card">
          <h4>Учебные задания</h4>
          <p>Широкий спектр заданий от базового управления до сложных оперативных миссий</p>
        </div>
        <div class="info-card">
          <h4>Безопасность данных</h4>
          <p>Соответствие требованиям информационной безопасности государственных систем</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'Home',
  data() {
    return {
      totalQuestTypes: 0,
      uniqueCompletedTypes: 0
    };
  },
  async created() {
    await this.loadStats();
  },
  methods: {
    async loadStats() {
      try {
        // 1. Количество доступных типов заданий
        const typesRes = await axios.get('/quest/type?skip=0&take=1');
        if (typesRes.data.success) {
          this.totalQuestTypes = typesRes.data.data.total;
        }

        // 2. Загружаем все завершённые задания
        const completedRes = await axios.get('/quest', {
          params: { status: 'completed', skip: 0, take: 100 }
        });
        if (completedRes.data.success) {
          const items = completedRes.data.data.list;
          const uniqueTypes = new Set();
          items.forEach(item => {
            if (item.result === 'success') {
              uniqueTypes.add(item.type_id);
            }
          });
          this.uniqueCompletedTypes = uniqueTypes.size;
        }
      } catch (error) {
        console.error('Failed to load stats', error);
      }
    }
  }
}
</script>


<style scoped>
.home-page { display: grid; gap: 24px; }
.welcome-section {
  position: relative;
  overflow: hidden;
  padding: 34px;
  border-radius: 26px;
  background: linear-gradient(135deg, rgba(255,255,255,.95), rgba(239,246,255,.95));
  border: 1px solid var(--line);
  box-shadow: var(--shadow-sm);
}
.welcome-section::after {
  content: '';
  position: absolute;
  right: -70px;
  top: -70px;
  width: 260px;
  height: 260px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(37,99,235,.16), transparent 70%);
}
.welcome-section h2 {
  position: relative;
  margin: 0 0 8px;
  font-size: clamp(2rem, 4vw, 3.1rem);
  letter-spacing: -.05em;
  line-height: 1.06;
}
.system-description { margin: 0 0 22px; color: var(--muted); font-size: 1.12rem; }
.description {
  position: relative;
  max-width: 850px;
  margin-bottom: 26px;
  padding: 18px 20px;
  border-radius: 18px;
  background: #fff;
  border: 1px solid var(--line);
  color: var(--text-2);
  line-height: 1.75;
}
.stats {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 220px));
  gap: 16px;
  margin-bottom: 24px;
}
.stat-item {
  padding: 18px;
  border-radius: 18px;
  background: #fff;
  border: 1px solid var(--line);
}
.stat-label { display: block; color: var(--muted); font-size: 13px; font-weight: 800; text-transform: uppercase; margin-bottom: 8px; }
.stat-value { display: block; color: var(--text); font-size: 2rem; font-weight: 900; }
.quick-actions { display: flex; }
.system-info h3 { margin: 4px 0 16px; font-size: 1.35rem; }
.info-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}
.info-card {
  padding: 22px;
  border-radius: 20px;
  background: #fff;
  border: 1px solid var(--line);
  box-shadow: var(--shadow-sm);
}
.info-card h4 { margin: 0 0 10px; font-size: 1.08rem; }
.info-card p { margin: 0; color: var(--muted); line-height: 1.7; }
@media (max-width: 760px) { .welcome-section { padding: 24px; } .stats, .info-grid { grid-template-columns: 1fr; } }
</style>
