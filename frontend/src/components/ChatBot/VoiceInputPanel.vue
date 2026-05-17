<template>
  <div class="voice-input-panel">
    <div v-if="voice.isListening.value" class="voice-status-bar">
      <div class="voice-indicator" :class="{ paused: voice.isPaused.value }">
        <div class="voice-dots">
          <span
            v-for="i in 5"
            :key="i"
            class="voice-dot"
            :style="{ animationDelay: `${(i - 1) * 0.15}s`, transform: `scale(${0.4 + voice.volume.value * 1.8 * (1 + Math.sin(i * 1.2))})` }"
          ></span>
        </div>
        <span class="voice-status-text">{{ voice.statusText.value }}</span>
      </div>
      <div v-if="voice.interimText.value" class="voice-interim">
        <span class="interim-text">{{ voice.interimText.value }}</span>
        <span class="interim-cursor"></span>
      </div>
    </div>
    
    <div v-if="voice.error.value" class="voice-error-bar">
      <el-icon><WarningFilled /></el-icon>
      <span>{{ voice.error.value }}</span>
      <el-button text size="small" @click="voice.error.value = null">关闭</el-button>
    </div>
    
    <div class="input-area">
      <el-input
        ref="textareaRef"
        :model-value="modelValue"
        type="textarea"
        :rows="2"
        :autosize="{ minRows: 1, maxRows: 4 }"
        placeholder="输入您的问题..."
        resize="none"
        @update:model-value="$emit('update:modelValue', $event)"
        @keydown.enter.exact.prevent="$emit('send')"
      />
      <el-tooltip
        v-if="voice.isSupported"
        :content="voice.isListening.value ? (voice.isPaused.value ? '继续录音' : '暂停录音') : '语音输入'"
        placement="top"
      >
        <el-button
          class="voice-btn"
          :class="{ active: voice.isListening.value && !voice.isPaused.value, paused: voice.isPaused.value }"
          @click="voice.toggle"
        >
          <el-icon v-if="!voice.isListening.value"><Microphone /></el-icon>
          <el-icon v-else-if="voice.isPaused.value"><VideoPause /></el-icon>
          <el-icon v-else class="voice-pulse"><Microphone /></el-icon>
        </el-button>
      </el-tooltip>
      <el-button
        v-if="!isStreaming"
        type="primary"
        class="send-btn"
        :disabled="!modelValue.trim()"
        @click="$emit('send')"
      >
        <el-icon><Promotion /></el-icon>
      </el-button>
      <el-button
        v-else
        type="danger"
        class="send-btn"
        @click="$emit('stop')"
      >
        <el-icon><Close /></el-icon>
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { watch, ref } from 'vue'
import { useVoiceRecognition } from '@/composables/useVoiceRecognition'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  isStreaming: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'send', 'stop'])

const textareaRef = ref(null)

const voice = useVoiceRecognition({ lang: 'zh-CN', continuous: true, interimResults: true })

// 监听临时结果，实时显示到输入框
watch(
  () => voice.interimText.value,
  (newVal) => {
    const finalContent = voice.finalText.value
    emit('update:modelValue', finalContent + newVal)
  }
)

// 监听最终结果
watch(
  () => voice.finalText.value,
  (newVal) => {
    if (newVal) {
      const consumed = voice.consumeFinalText()
      if (consumed) {
        emit('update:modelValue', newVal + (voice.interimText.value || ''))
      }
    }
  }
)

// 暴露textareaRef给父组件
defineExpose({
  textareaRef
})
</script>

<style scoped lang="scss">
.voice-input-panel {
  display: flex;
  flex-direction: column;
}

.input-area {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  padding: 12px 16px;
  border-top: 1px solid $border-color;
  background: $bg-primary;

  :deep(.el-textarea__inner) {
    box-shadow: none !important;
    border: 1px solid $border-color;
    border-radius: $radius-md;
    padding: 8px 12px;
    font-size: $font-size-base;

    &:focus {
      border-color: $primary-color;
    }
  }

  .voice-btn {
    flex-shrink: 0;
    width: 40px;
    height: 40px;
    border-radius: $radius-md;
    padding: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 1px solid $border-color;
    color: $text-secondary;
    transition: all $transition-fast;

    &:hover {
      border-color: $primary-light;
      color: $primary-color;
      background: rgba($primary-color, 0.04);
    }

    &.active {
      border-color: $danger-color;
      color: $danger-color;
      background: rgba($danger-color, 0.06);
      animation: voice-btn-glow 1.5s ease-in-out infinite;
    }

    &.paused {
      border-color: $warning-color;
      color: $warning-color;
      background: rgba($warning-color, 0.06);
    }

    .voice-pulse {
      animation: voice-pulse 1.2s ease-in-out infinite;
    }
  }

  .send-btn {
    flex-shrink: 0;
    width: 40px;
    height: 40px;
    border-radius: $radius-md;
    padding: 0;
    display: flex;
    align-items: center;
    justify-content: center;
  }
}

.voice-status-bar {
  padding: 8px 16px;
  background: linear-gradient(to right, rgba($danger-color, 0.04), rgba($danger-color, 0.02));
  border-top: 1px solid rgba($danger-color, 0.12);
  display: flex;
  flex-direction: column;
  gap: 6px;

  .voice-indicator {
    display: flex;
    align-items: center;
    gap: 10px;

    &.paused {
      .voice-dot {
        animation: none !important;
        opacity: 0.3;
        transform: scale(0.4) !important;
      }
    }
  }

  .voice-dots {
    display: flex;
    align-items: center;
    gap: 3px;
  }

  .voice-dot {
    width: 4px;
    height: 16px;
    border-radius: 2px;
    background: $danger-color;
    animation: voice-wave 0.8s ease-in-out infinite alternate;
    transition: transform 0.1s ease;
  }

  .voice-status-text {
    font-size: $font-size-xs;
    color: $danger-color;
    font-weight: 500;
  }

  .voice-interim {
    font-size: $font-size-sm;
    color: $text-secondary;
    line-height: 1.5;
    max-height: 60px;
    overflow-y: auto;
    display: flex;
    align-items: flex-start;

    .interim-text {
      opacity: 0.7;
      font-style: italic;
    }

    .interim-cursor {
      display: inline-block;
      width: 2px;
      height: 1em;
      background: $danger-color;
      margin-left: 1px;
      vertical-align: text-bottom;
      animation: blink 1s step-end infinite;
    }
  }
}

.voice-error-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: rgba($danger-color, 0.06);
  border-top: 1px solid rgba($danger-color, 0.15);
  color: $danger-color;
  font-size: $font-size-xs;

  .el-icon {
    font-size: 14px;
    flex-shrink: 0;
  }

  span:nth-child(2) {
    flex: 1;
    min-width: 0;
  }
}

@keyframes voice-wave {
  0% {
    height: 4px;
  }
  100% {
    height: 18px;
  }
}

@keyframes voice-btn-glow {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba($danger-color, 0);
  }
  50% {
    box-shadow: 0 0 0 4px rgba($danger-color, 0.15);
  }
}

@keyframes voice-pulse {
  0%, 100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.15);
    opacity: 0.8;
  }
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}
</style>
