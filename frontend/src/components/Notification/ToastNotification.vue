<template>
  <transition-group name="toast" tag="div" class="toast-container">
    <div
      v-for="toast in toasts"
      :key="toast.id"
      class="toast-item"
      :class="`toast-${toast.type}`"
    >
      <div class="toast-content">
        <div class="toast-icon">
          <el-icon :size="20">
            <component :is="getIcon(toast.type)" />
          </el-icon>
        </div>
        <div class="toast-body">
          <div class="toast-title">{{ toast.title }}</div>
          <div class="toast-message">{{ toast.message }}</div>
        </div>
      </div>
      <div class="toast-actions">
        <span class="toast-countdown">{{ formatCountdown(toast.remainingTime) }}</span>
        <button class="toast-close" @click="closeToast(toast.id)">
          <el-icon><Close /></el-icon>
        </button>
      </div>
    </div>
  </transition-group>
</template>

<script setup>
import { ref, computed, reactive } from 'vue'
import { CircleCheck, WarningFilled, InfoFilled, Message, Close } from '@element-plus/icons-vue'

const toasts = ref([])
const DEFAULT_DURATION = 60000

const getIcon = (type) => {
  const iconMap = {
    review_complete: CircleCheck,
    high_risk_warning: WarningFilled,
    system_announcement: InfoFilled,
    email_notification: Message,
    success: CircleCheck,
    warning: WarningFilled,
    info: InfoFilled,
    error: InfoFilled
  }
  return iconMap[type] || InfoFilled
}

const formatCountdown = (ms) => {
  const seconds = Math.ceil(ms / 1000)
  return `${seconds}s`
}

const showToast = (options) => {
  const id = Date.now() + Math.random()
  // 使用 reactive 让 remainingTime 变成响应式
  const toast = reactive({
    id,
    type: options.type || 'info',
    title: options.title || '',
    message: options.message || '',
    duration: options.duration || DEFAULT_DURATION,
    remainingTime: options.duration || DEFAULT_DURATION,
    timer: null,
    countdownInterval: null
  })

  toast.countdownInterval = setInterval(() => {
    toast.remainingTime -= 100
    if (toast.remainingTime <= 0) {
      closeToast(id)
    }
  }, 100)

  toast.timer = setTimeout(() => {
    closeToast(id)
  }, toast.duration)

  toasts.value.push(toast)
}

const closeToast = (id) => {
  const index = toasts.value.findIndex(t => t.id === id)
  if (index > -1) {
    const toast = toasts.value[index]
    clearTimeout(toast.timer)
    clearInterval(toast.countdownInterval)
    toasts.value.splice(index, 1)
  }
}

defineExpose({
  showToast,
  closeToast
})
</script>

<style scoped lang="scss">
.toast-container {
  position: fixed;
  bottom: 80px;
  right: 24px;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 12px;
  pointer-events: none;
}

.toast-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-width: 320px;
  max-width: 480px;
  padding: 16px 20px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  border-left: 4px solid;
  pointer-events: auto;
  transition: all 0.3s ease;

  &.toast-success {
    border-left-color: #67c23a;
    .toast-icon {
      color: #67c23a;
    }
  }

  &.toast-warning {
    border-left-color: #e6a23c;
    .toast-icon {
      color: #e6a23c;
    }
  }

  &.toast-info {
    border-left-color: #409eff;
    .toast-icon {
      color: #409eff;
    }
  }

  &.toast-error {
    border-left-color: #f56c6c;
    .toast-icon {
      color: #f56c6c;
    }
  }

  &.toast-review_complete {
    border-left-color: #67c23a;
    .toast-icon {
      color: #67c23a;
    }
  }

  &.toast-high_risk_warning {
    border-left-color: #f56c6c;
    .toast-icon {
      color: #f56c6c;
    }
  }

  &.toast-system_announcement {
    border-left-color: #409eff;
    .toast-icon {
      color: #409eff;
    }
  }

  &.toast-email_notification {
    border-left-color: #909399;
    .toast-icon {
      color: #909399;
    }
  }
}

.toast-content {
  display: flex;
  align-items: flex-start;
  flex: 1;
  gap: 12px;
}

.toast-icon {
  flex-shrink: 0;
  margin-top: 2px;
}

.toast-body {
  flex: 1;
  min-width: 0;
}

.toast-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
  line-height: 1.4;
}

.toast-message {
  font-size: 13px;
  color: #606266;
  line-height: 1.5;
  word-break: break-word;
}

.toast-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-left: 16px;
  flex-shrink: 0;
}

.toast-countdown {
  font-size: 12px;
  color: #909399;
  font-variant-numeric: tabular-nums;
  min-width: 30px;
  text-align: right;
}

.toast-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border: none;
  background: transparent;
  color: #909399;
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.2s;

  &:hover {
    background: #f5f7fa;
    color: #606266;
  }

  &:active {
    background: #e4e7ed;
  }
}

.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from {
  opacity: 0;
  transform: translateX(100%);
}

.toast-leave-to {
  opacity: 0;
  transform: translateX(100%);
}
</style>
