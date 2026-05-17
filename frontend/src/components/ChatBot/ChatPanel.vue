<template>
  <div class="chat-panel">
    <div v-if="showBackBtn" class="chat-header">
      <el-button
        type="primary"
        text
        class="back-btn"
        @click="emit('back')"
      >
        <el-icon><ArrowLeft /></el-icon>
        <span>返回</span>
      </el-button>
      <div class="header-title">
        {{ store.currentConversation?.name || '新对话' }}
      </div>
      <div class="header-actions">
        <el-tooltip content="导出对话" placement="top">
          <el-button
            type="primary"
            text
            class="export-btn"
            @click="handleExport"
            :disabled="!store.currentConversation"
          >
            <el-icon><Download /></el-icon>
          </el-button>
        </el-tooltip>
      </div>
    </div>
    <div class="messages-container" ref="messagesContainer">
      <div v-if="messages.length === 0" class="empty-chat">
        <el-icon :size="48" class="empty-icon"><ChatDotRound /></el-icon>
        <p class="empty-text">开始您的对话</p>
        <p class="empty-desc">输入问题，智能客服将为您解答</p>
      </div>
      <div
        v-for="msg in messages"
        :key="msg.id"
        :class="['message-row', msg.role]"
      >
        <div v-if="msg.role === 'assistant'" class="avatar-wrapper">
          <el-avatar :size="32" class="ai-avatar">
            <el-icon><Service /></el-icon>
          </el-avatar>
        </div>
        <div :class="['message-bubble', msg.role]">
          <div
            class="message-content"
            v-html="formatMessage(msg.content)"
          ></div>
          <!-- AI思考中提示 -->
          <div
            v-if="isStreaming && msg.role === 'assistant' && msg.id === lastAssistantMsgId && !msg.content"
            class="thinking-indicator"
          >
            <span class="thinking-dots">
              <span></span>
              <span></span>
              <span></span>
            </span>
            <span class="thinking-text">AI正在思考中</span>
          </div>
          <span
            v-if="isStreaming && msg.role === 'assistant' && msg.id === lastAssistantMsgId && msg.content"
            class="streaming-cursor"
          ></span>
          <span class="message-time">{{ formatTime(msg.timestamp) }}</span>
        </div>
        <div v-if="msg.role === 'user'" class="avatar-wrapper">
          <el-avatar :size="32" class="user-avatar">
            <el-icon><User /></el-icon>
          </el-avatar>
        </div>
      </div>
    </div>
    <VoiceInputPanel
      ref="voiceInputPanelRef"
      v-model="inputText"
      :is-streaming="isStreaming"
      @send="handleSend"
      @stop="handleStop"
    />
  </div>
</template>

<script setup>
import { ref, computed, nextTick, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useChatbotStore } from '@/stores/chatbot'
import { formatMessage } from '@/utils/messageFormatter'
import { formatTime } from '@/utils/timeFormatter'
import VoiceInputPanel from './VoiceInputPanel.vue'

const props = defineProps({
  showBackBtn: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['back'])

const store = useChatbotStore()
const inputText = ref('')
const messagesContainer = ref(null)
const voiceInputPanelRef = ref(null)

const isStreaming = computed(() => store.sending)
const messages = computed(() => store.currentConversation?.messages || [])

// 监听当前对话变化，切换历史记录时滚动到底部
watch(
  () => store.currentConversation?.id,
  (newId, oldId) => {
    if (newId && newId !== oldId) {
      nextTick(scrollToBottom)
    }
  }
)

const lastAssistantMsgId = computed(() => {
  const msgs = messages.value
  for (let i = msgs.length - 1; i >= 0; i--) {
    if (msgs[i].role === 'assistant') return msgs[i].id
  }
  return null
})

// 监听消息列表长度变化（新消息添加时）
watch(
  () => store.currentConversation?.messages?.length,
  () => {
    nextTick(scrollToBottom)
  }
)

// 监听流式消息内容变化，自动滚动到底部
watch(
  () => {
    const msgs = store.currentConversation?.messages
    if (!msgs || msgs.length === 0) return ''
    const last = msgs[msgs.length - 1]
    return last.content || ''
  },
  () => {
    if (isStreaming.value) {
      nextTick(scrollToBottom)
    }
  },
  { flush: 'post' }
)

function scrollToBottom() {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

async function handleSend() {
  const text = inputText.value.trim()
  if (!text || store.sending) return

  inputText.value = ''
  await nextTick(scrollToBottom)

  try {
    await store.sendMessage(text)
  } catch {
    // onError 已在 store 中处理提示文案
  } finally {
    await nextTick(scrollToBottom)
  }
}

function handleStop() {
  store.cancelStream()
}

async function handleExport() {
  if (!store.currentConversation) return
  try {
    await store.exportConversationToExcel()
    ElMessage.success('对话已导出')
  } catch {
    // 错误已在 store 中处理
  }
}
</script>

<style scoped lang="scss">
.chat-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid $border-color;
  background: $bg-primary;

  .header-title {
    flex: 1;
    text-align: center;
    font-size: $font-size-md;
    font-weight: 500;
    color: $text-primary;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    padding: 0 16px;
  }

  .back-btn {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: $font-size-sm;
    color: $text-secondary;
    padding: 4px 8px;
    border-radius: $radius-sm;
    transition: all $transition-fast;

    &:hover {
      color: $primary-color;
      background: rgba($primary-color, 0.1);
    }

    .el-icon {
      font-size: 16px;
    }

    span {
      font-weight: 500;
    }
  }

  .header-actions {
    .export-btn {
      color: $text-secondary;
      padding: 6px;
      border-radius: $radius-sm;
      transition: all $transition-fast;

      &:hover {
        color: $primary-color;
        background: rgba($primary-color, 0.1);
      }

      .el-icon {
        font-size: 18px;
      }
    }
  }
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.empty-chat {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: $text-tertiary;

  .empty-icon {
    color: $primary-light;
    opacity: 0.5;
    margin-bottom: 12px;
  }

  .empty-text {
    font-size: $font-size-md;
    color: $text-secondary;
    margin-bottom: 4px;
  }

  .empty-desc {
    font-size: $font-size-sm;
  }
}

.message-row {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  max-width: 100%;

  &.user {
    justify-content: flex-end;
  }

  &.assistant {
    justify-content: flex-start;
  }
}

.avatar-wrapper {
  flex-shrink: 0;
}

.ai-avatar {
  background: linear-gradient(135deg, $primary-color, $primary-light);
  color: white;
}

.user-avatar {
  background: $secondary-color;
  color: white;
}

.message-bubble {
  max-width: 78%;
  padding: 10px 14px;
  border-radius: 12px;
  position: relative;
  word-break: break-word;
  line-height: 1.6;
  font-size: $font-size-base;

  &.assistant {
    background: $bg-tertiary;
    color: $text-primary;
    border-bottom-left-radius: 4px;
  }

  &.user {
    background: $primary-color;
    color: #fff;
    border-bottom-right-radius: 4px;

    .message-time {
      color: rgba(255, 255, 255, 0.65);
    }
  }

  .message-content {
    white-space: pre-wrap;

    :deep(strong) {
      font-weight: 600;
    }

    // Markdown 表格样式
    :deep(.markdown-table) {
      width: 100%;
      border-collapse: collapse;
      margin: 12px 0;
      font-size: 14px;
      background: #fff;
      border-radius: 8px;
      overflow: hidden;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);

      th, td {
        padding: 12px 16px;
        text-align: left;
        border-bottom: 1px solid #e4e7ed;
      }

      th {
        background: #f5f7fa;
        font-weight: 600;
        color: #303133;
        font-size: 13px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
      }

      td {
        color: #606266;
      }

      tr:last-child td {
        border-bottom: none;
      }

      tr:hover td {
        background: #f5f7fa;
      }
    }

    // Markdown 标题样式
    :deep(h1, h2, h3, h4, h5, h6) {
      margin: 16px 0 12px;
      font-weight: 600;
      color: #303133;
      line-height: 1.4;
    }

    :deep(h1) { font-size: 20px; }
    :deep(h2) { font-size: 18px; }
    :deep(h3) { font-size: 16px; }
    :deep(h4) { font-size: 15px; }
    :deep(h5) { font-size: 14px; }
    :deep(h6) { font-size: 13px; }

    // Markdown 列表样式
    :deep(ul, ol) {
      margin: 8px 0;
      padding-left: 20px;
    }

    :deep(li) {
      margin: 4px 0;
      line-height: 1.6;
    }

    // Markdown 代码样式
    :deep(code) {
      background: #f5f7fa;
      padding: 2px 6px;
      border-radius: 4px;
      font-family: 'Courier New', monospace;
      font-size: 13px;
      color: #e83e8c;
    }

    :deep(pre) {
      background: #282c34;
      padding: 16px;
      border-radius: 8px;
      overflow-x: auto;
      margin: 12px 0;

      code {
        background: transparent;
        color: #abb2bf;
        padding: 0;
      }
    }

    // Markdown 分隔线
    :deep(hr) {
      border: none;
      border-top: 1px solid #e4e7ed;
      margin: 16px 0;
    }

    // Markdown 斜体
    :deep(em) {
      font-style: italic;
      color: #606266;
    }
  }

  .message-time {
    display: block;
    font-size: $font-size-xs;
    color: $text-tertiary;
    margin-top: 4px;
    text-align: right;
  }
}

.streaming-cursor {
  display: inline-block;
  width: 2px;
  height: 1em;
  background: $primary-color;
  margin-left: 2px;
  vertical-align: text-bottom;
  animation: blink 1s step-end infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

// AI思考中提示样式
.thinking-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 0;
  color: $text-secondary;
  font-size: 14px;

  .thinking-dots {
    display: flex;
    gap: 4px;

    span {
      width: 8px;
      height: 8px;
      background: $primary-color;
      border-radius: 50%;
      animation: thinking-bounce 1.4s ease-in-out infinite both;

      &:nth-child(1) {
        animation-delay: -0.32s;
      }

      &:nth-child(2) {
        animation-delay: -0.16s;
      }
    }
  }

  .thinking-text {
    font-weight: 500;
  }
}

@keyframes thinking-bounce {
  0%, 80%, 100% {
    transform: scale(0);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}
</style>
