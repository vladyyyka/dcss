<template>
  <Teleport to="body">
    <div v-if="visible" class="modal-overlay" @click.self="close">
      <div class="modal-card">
        <div class="modal-header">
          <h3>{{ title }}</h3>
          <button class="modal-x" @click="close">×</button>
        </div>
        <div class="modal-body">
          <p v-if="message">{{ message }}</p>
          <div v-if="htmlMessage" class="modal-html" v-html="htmlMessage"></div>
        </div>
        <div class="modal-footer">
          <button class="btn-primary" @click="confirm">{{ okText }}</button>
          <button v-if="showCancel" class="btn-secondary" @click="close">{{ cancelText }}</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script>
export default {
  name: 'Modal',
  props: {
    visible: Boolean,
    title: { type: String, default: 'Уведомление' },
    message: { type: String, default: '' },
    htmlMessage: { type: String, default: '' },
    okText: { type: String, default: 'OK' },
    cancelText: { type: String, default: 'Отмена' },
    showCancel: { type: Boolean, default: false }
  },
  emits: ['update:visible', 'confirm', 'close'],
  methods: {
    close() {
      this.$emit('update:visible', false);
      this.$emit('close');
    },
    confirm() {
      this.$emit('confirm');
      this.close();
    }
  }
};
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 10000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: rgba(15, 23, 42, .46);
  backdrop-filter: blur(5px);
}
.modal-card {
  width: min(560px, 100%);
  background: #fff;
  border: 1px solid var(--line);
  border-radius: 22px;
  box-shadow: var(--shadow);
  overflow: hidden;
}
.modal-header, .modal-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 18px 22px;
}
.modal-header { border-bottom: 1px solid var(--line); }
.modal-header h3 { margin: 0; font-size: 1.18rem; letter-spacing: -.02em; }
.modal-x {
  width: 36px;
  height: 36px;
  border: 0;
  border-radius: 12px;
  background: transparent;
  color: var(--muted);
  font-size: 28px;
  line-height: 1;
}
.modal-x:hover { background: var(--panel-2); }
.modal-body { padding: 22px; color: var(--text-2); line-height: 1.65; }
.modal-body p { margin: 0; }
.modal-html code {
  display: inline-block;
  margin-top: 6px;
  padding: 6px 10px;
  border-radius: 10px;
  background: var(--blue-soft) !important;
  color: var(--blue-2);
  border: 1px solid #bfdbfe;
}
.modal-footer { justify-content: flex-end; border-top: 1px solid var(--line); background: var(--panel-2); }
</style>
