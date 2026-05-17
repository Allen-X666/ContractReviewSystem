<template>
  <div class="chat-history">
    <div class="history-header">
      <el-button
        v-if="showBackBtn"
        type="primary"
        text
        class="back-btn"
        @click="emit('back')"
      >
        <el-icon><ArrowLeft /></el-icon>
        <span>返回</span>
      </el-button>
      <span class="history-title">历史对话</span>
      <div class="history-actions">
        <el-tooltip content="新建对话" placement="top">
          <el-button type="primary" text size="small" @click="handleNew">
            <el-icon><Plus /></el-icon>
          </el-button>
        </el-tooltip>
      </div>
    </div>

    <div class="history-list" v-if="conversations.length > 0">
      <div
        v-for="conv in conversations"
        :key="conv.id"
        :class="['history-item', { active: conv.id === currentId }]"
        @click="handleSelect(conv.id)"
      >
        <div class="item-info">
          <div class="item-name" v-if="renamingId !== conv.id">{{ conv.name }}</div>
          <el-input
            v-else
            v-model="renameValue"
            size="small"
            @keyup.enter="confirmRename"
            @blur="confirmRename"
            ref="renameInputRef"
            @click.stop
          />
          <div class="item-time">{{ formatTime(conv.updatedAt) }}</div>
        </div>
        <div class="item-actions" @click.stop>
          <el-dropdown trigger="click" teleported popper-class="chatbot-dropdown-menu" @command="(cmd) => handleCommand(cmd, conv)">
            <el-button type="info" text size="small" class="more-btn">
              <el-icon><MoreFilled /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="rename">
                  <el-icon><Edit /></el-icon>重命名
                </el-dropdown-item>
                <el-dropdown-item command="export">
                  <el-icon><Download /></el-icon>导出
                </el-dropdown-item>
                <el-dropdown-item command="delete" divided>
                  <el-icon><Delete /></el-icon>
                  <span style="color: #dc2626">删除</span>
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
    </div>

    <div v-else class="empty-history">
      <el-icon :size="40" class="empty-icon"><Clock /></el-icon>
      <p>暂无历史对话</p>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useChatbotStore } from '@/stores/chatbot'

const props = defineProps({
  showBackBtn: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['back', 'select'])

const store = useChatbotStore()
const renamingId = ref(null)
const renameValue = ref('')
const renameInputRef = ref(null)

const conversations = store.sortedConversations
const currentId = store.currentConversationId

function formatTime(ts) {
  const d = new Date(ts)
  const now = new Date()
  const diff = now - d
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return Math.floor(diff / 60000) + '分钟前'
  if (d.toDateString() === now.toDateString()) return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  if (now.getFullYear() === d.getFullYear()) return d.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })
  return d.toLocaleDateString('zh-CN')
}

async function handleSelect(id) {
  await store.switchConversation(id)
  emit('select')
}

async function handleNew() {
  store.newChat()
  emit('back')
}

function handleExport() {
  const success = store.exportConversationToExcel()
  if (success) ElMessage.success('对话已导出')
}

function handleCommand(cmd, conv) {
  switch (cmd) {
    case 'rename':
      startRename(conv)
      break
    case 'export':
      const ok = store.exportConversationToExcel(conv)
      if (ok) ElMessage.success('对话已导出')
      break
    case 'delete':
      handleDelete(conv)
      break
  }
}

function startRename(conv) {
  renamingId.value = conv.id
  renameValue.value = conv.name
  nextTick(() => {
    if (renameInputRef.value) {
      const input = Array.isArray(renameInputRef.value) ? renameInputRef.value[0] : renameInputRef.value
      input?.focus()
    }
  })
}

async function confirmRename() {
  if (renamingId.value && renameValue.value.trim()) {
    try {
      await store.renameConversation(renamingId.value, renameValue.value.trim())
    } catch {
      /* request.js 统一处理错误提示 */
    }
  }
  renamingId.value = null
  renameValue.value = ''
}

async function handleDelete(conv) {
  try {
    await ElMessageBox.confirm(`确定要删除对话 "${conv.name}" 吗？`, '确认删除', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
      customClass: 'chatbot-message-box',
      appendTo: document.body,
      modal: true,
      lockScroll: false
    })
    await store.deleteConversation(conv.id)
    ElMessage.success('已删除')
  } catch {}
}
</script>

<style scoped lang="scss">
.chat-history {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.history-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  border-bottom: 1px solid $border-color;

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

  .history-title {
    font-size: $font-size-md;
    font-weight: 600;
    color: $text-primary;
  }

  .history-actions {
    display: flex;
    gap: 4px;
  }
}

.history-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.history-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  border-radius: $radius-md;
  cursor: pointer;
  transition: background $transition-fast;

  &:hover {
    background: $bg-tertiary;
  }

  &.active {
    background: rgba($primary-color, 0.08);
    border-left: 3px solid $primary-color;
    padding-left: 9px;
  }

  .item-info {
    flex: 1;
    min-width: 0;
    overflow: hidden;

    .item-name {
      font-size: $font-size-base;
      font-weight: 500;
      color: $text-primary;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .item-time {
      font-size: $font-size-xs;
      color: $text-tertiary;
      margin-top: 2px;
    }
  }

  .item-actions {
    flex-shrink: 0;
    margin-left: 8px;
    opacity: 0;
    transition: opacity $transition-fast;
  }

  &:hover .item-actions {
    opacity: 1;
  }

  .more-btn {
    padding: 4px;
  }
}

.empty-history {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: $text-tertiary;

  .empty-icon {
    opacity: 0.4;
    margin-bottom: 8px;
  }

  p {
    font-size: $font-size-sm;
  }
}
</style>

<style lang="scss">
/* 全局样式：确保 dropdown 菜单显示在最上层 */
.chatbot-dropdown-menu {
  z-index: 200 !important;
}

/* 全局样式：确保 MessageBox 显示在 ChatBot 面板之上 */
/* ChatBot 面板 z-index 为 101 */
.chatbot-message-box {
  z-index: 1000 !important;
}

/* 提高 MessageBox 的 overlay 层级 */
.el-overlay.el-overlay-message-box {
  z-index: 999 !important;
}

/* 确保 MessageBox 对话框本身层级最高 */
.el-overlay-message-box .el-message-box.chatbot-message-box {
  z-index: 1000 !important;
}
</style>
