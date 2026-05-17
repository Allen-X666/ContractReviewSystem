<template>
  <div class="chatbot-wrapper">
    <!-- 浮动按钮 -->
    <div
      class="chatbot-fab"
      :style="fabStyle"
      @mousedown="onMouseDown"
      @touchstart.prevent="onTouchStart"
      @click="onFabClick"
      :class="{ dragging: isDragging, opened: panelVisible }"
    >
      <transition name="fab-icon" mode="out-in">
        <el-icon v-if="!panelVisible" :size="28" key="open"><ChatDotRound /></el-icon>
        <el-icon v-else :size="28" key="close"><Close /></el-icon>
      </transition>
    </div>

    <!-- 对话弹窗 -->
    <transition name="panel-slide">
      <div
        v-if="panelVisible"
        class="chatbot-panel"
        :style="panelStyle"
      >
        <!-- 顶部标题栏 -->
        <div
          class="panel-header"
          @mousedown="onPanelMouseDown"
          @touchstart.prevent="onPanelTouchStart"
        >
          <div class="panel-title" v-if="currentView === 'chat'">
            <el-icon><Service /></el-icon>
            <span>智能客服</span>
          </div>
          <div class="panel-title" v-else>
            <el-icon><Clock /></el-icon>
            <span>历史对话</span>
          </div>
          <div class="panel-header-actions">
            <el-tooltip content="导出当前对话" placement="top" v-if="currentView === 'chat'">
              <el-button text class="header-btn" @click="handleExport" :disabled="!store.currentConversation">
                <el-icon><Download /></el-icon>
              </el-button>
            </el-tooltip>
            <el-tooltip content="历史对话" placement="top" v-if="currentView === 'chat'">
              <el-button text class="header-btn" @click="currentView = 'history'">
                <el-icon><Clock /></el-icon>
              </el-button>
            </el-tooltip>
            <el-tooltip content="返回对话" placement="top" v-if="currentView === 'history'">
              <el-button text class="header-btn" @click="currentView = 'chat'">
                <el-icon><ChatDotRound /></el-icon>
              </el-button>
            </el-tooltip>
            <el-tooltip content="新对话" placement="top">
              <el-button text class="header-btn" @click="handleNewChat">
                <el-icon><Plus /></el-icon>
              </el-button>
            </el-tooltip>
          </div>
        </div>

        <!-- 内容区 -->
        <div class="panel-body">
          <ChatPanel 
            v-if="currentView === 'chat' || currentView === 'historyDetail'" 
            :show-back-btn="currentView === 'historyDetail'"
            @back="currentView = 'history'"
          />
          <ChatHistory 
            v-else 
            :show-back-btn="currentView === 'history'"
            @select="currentView = 'historyDetail'"
            @back="currentView = 'chat'"
          />
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { useChatbotStore } from '@/stores/chatbot'
import ChatPanel from './ChatPanel.vue'
import ChatHistory from './ChatHistory.vue'

const store = useChatbotStore()

const panelVisible = ref(false)
const currentView = ref('chat')
const isDragging = ref(false)

const DEFAULT_POS = { x: null, y: null }
const fabPos = ref(store.buttonPosition || { ...DEFAULT_POS })

let dragTimer = null
let startPos = { x: 0, y: 0 }
let hasMoved = false

const FAB_SIZE = 56
const PANEL_WIDTH = 460
const PANEL_HEIGHT = 600
const MARGIN = 32

const fabStyle = computed(() => {
  if (fabPos.value.x !== null && fabPos.value.y !== null) {
    return {
      right: 'auto',
      bottom: 'auto',
      left: fabPos.value.x + 'px',
      top: fabPos.value.y + 'px'
    }
  }
  return {
    right: MARGIN + 'px',
    bottom: MARGIN + 'px'
  }
})

// 面板固定位置（右下角）
const panelFixedPos = ref({ right: MARGIN, bottom: MARGIN + FAB_SIZE + 12 })

const panelStyle = computed(() => {
  const vw = window.innerWidth
  const vh = window.innerHeight

  // 如果设置了固定位置，使用固定位置
  if (panelFixedPos.value.right !== null && panelFixedPos.value.bottom !== null) {
    return {
      right: panelFixedPos.value.right + 'px',
      bottom: panelFixedPos.value.bottom + 'px',
      width: PANEL_WIDTH + 'px',
      height: PANEL_HEIGHT + 'px'
    }
  }

  // 否则基于按钮位置计算（拖动后的情况）
  let panelRight, panelBottom

  if (fabPos.value.x !== null && fabPos.value.y !== null) {
    const fabRight = vw - fabPos.value.x - FAB_SIZE
    const fabBottom = vh - fabPos.value.y - FAB_SIZE
    panelRight = Math.max(MARGIN, fabRight - (PANEL_WIDTH - FAB_SIZE) / 2)
    panelBottom = Math.min(vh - MARGIN, fabBottom + FAB_SIZE + 12)

    if (panelRight + PANEL_WIDTH > vw - MARGIN) {
      panelRight = vw - PANEL_WIDTH - MARGIN
    }
    if (panelRight < MARGIN) {
      panelRight = MARGIN
    }
    if (panelBottom + PANEL_HEIGHT > vh - MARGIN) {
      panelBottom = fabPos.value.y - PANEL_HEIGHT - 12
      if (panelBottom < MARGIN) panelBottom = MARGIN
    }
  } else {
    panelRight = MARGIN
    panelBottom = MARGIN + FAB_SIZE + 12
  }

  return {
    right: panelRight + 'px',
    bottom: (vh - panelBottom - PANEL_HEIGHT) + 'px',
    width: PANEL_WIDTH + 'px',
    height: PANEL_HEIGHT + 'px'
  }
})

async function onFabClick() {
  if (hasMoved) return
  panelVisible.value = !panelVisible.value
  if (panelVisible.value) {
    // 点击后固定面板到右下角，按钮位置根据面板位置计算
    const vw = window.innerWidth
    const vh = window.innerHeight

    // 面板固定在右下角
    const targetPanelRight = MARGIN
    const targetPanelBottom = MARGIN + FAB_SIZE + 12

    panelFixedPos.value = {
      right: targetPanelRight,
      bottom: targetPanelBottom
    }

    // 计算按钮位置：按钮在面板右下角外侧
    // 按钮右边缘与面板右边缘对齐，按钮上边缘与面板下边缘相距 12px
    fabPos.value = {
      x: vw - targetPanelRight - FAB_SIZE,
      y: vh - targetPanelBottom + 12
    }
    store.updateButtonPosition({ ...fabPos.value })

    currentView.value = 'chat'
    if (store.conversations.length === 0) {
      await store.loadConversations()
    }
    if (!store.currentConversationId && !store.currentConversationClientId) {
      store.newChat()
    }
  } else {
    // 关闭面板时清除固定位置
    panelFixedPos.value = { right: null, bottom: null }
  }
}

function onMouseDown(e) {
  if (e.button !== 0) return
  startPos = { x: e.clientX, y: e.clientY }
  hasMoved = false

  dragTimer = setTimeout(() => {
    isDragging.value = true
    document.addEventListener('mousemove', onMouseMove)
    document.addEventListener('mouseup', onMouseUp)
  }, 300)

  document.addEventListener('mouseup', onMouseUpImmediate, { once: true })
}

function onMouseUpImmediate() {
  clearTimeout(dragTimer)
  if (!isDragging.value) {
    document.removeEventListener('mousemove', onMouseMove)
    document.removeEventListener('mouseup', onMouseUp)
  }
}

function onMouseMove(e) {
  if (!isDragging.value) return
  hasMoved = true
  updatePosition(e.clientX, e.clientY)
}

function onMouseUp() {
  isDragging.value = false
  clearTimeout(dragTimer)
  document.removeEventListener('mousemove', onMouseMove)
  document.removeEventListener('mouseup', onMouseUp)
  if (hasMoved) {
    store.updateButtonPosition({ ...fabPos.value })
  }
}

function onTouchStart(e) {
  const touch = e.touches[0]
  startPos = { x: touch.clientX, y: touch.clientY }
  hasMoved = false

  dragTimer = setTimeout(() => {
    isDragging.value = true
    document.addEventListener('touchmove', onTouchMove, { passive: false })
    document.addEventListener('touchend', onTouchEnd)
  }, 300)

  document.addEventListener('touchend', onTouchEndImmediate, { once: true })
}

function onTouchEndImmediate() {
  clearTimeout(dragTimer)
  if (!isDragging.value) {
    document.removeEventListener('touchmove', onTouchMove)
    document.removeEventListener('touchend', onTouchEnd)
  }
}

function onTouchMove(e) {
  if (!isDragging.value) return
  e.preventDefault()
  hasMoved = true
  const touch = e.touches[0]
  updatePosition(touch.clientX, touch.clientY)
}

function onTouchEnd() {
  isDragging.value = false
  clearTimeout(dragTimer)
  document.removeEventListener('touchmove', onTouchMove)
  document.removeEventListener('touchend', onTouchEnd)
  if (hasMoved) {
    store.updateButtonPosition({ ...fabPos.value })
  }
}

// 面板拖动相关变量
let panelDragTimer = null
let panelStartPos = { x: 0, y: 0 }
let panelHasMoved = false
let isPanelDragging = false

function onPanelMouseDown(e) {
  if (e.button !== 0) return
  // 如果点击的是按钮区域，不触发拖动
  if (e.target.closest('.panel-header-actions')) return

  panelStartPos = { x: e.clientX, y: e.clientY }
  panelHasMoved = false
  isPanelDragging = false

  panelDragTimer = setTimeout(() => {
    isPanelDragging = true
    isDragging.value = true
    document.addEventListener('mousemove', onPanelMouseMove)
    document.addEventListener('mouseup', onPanelMouseUp)
  }, 300)

  document.addEventListener('mouseup', onPanelMouseUpImmediate, { once: true })
}

function onPanelMouseUpImmediate() {
  clearTimeout(panelDragTimer)
  if (!isPanelDragging) {
    document.removeEventListener('mousemove', onPanelMouseMove)
    document.removeEventListener('mouseup', onPanelMouseUp)
  }
}

function onPanelMouseMove(e) {
  if (!isPanelDragging) return
  panelHasMoved = true
  updatePanelPosition(e.clientX, e.clientY)
}

function onPanelMouseUp() {
  isPanelDragging = false
  isDragging.value = false
  clearTimeout(panelDragTimer)
  document.removeEventListener('mousemove', onPanelMouseMove)
  document.removeEventListener('mouseup', onPanelMouseUp)
  if (panelHasMoved) {
    store.updateButtonPosition({ ...fabPos.value })
  }
}

function onPanelTouchStart(e) {
  // 如果触摸的是按钮区域，不触发拖动
  if (e.target.closest('.panel-header-actions')) return

  const touch = e.touches[0]
  panelStartPos = { x: touch.clientX, y: touch.clientY }
  panelHasMoved = false
  isPanelDragging = false

  panelDragTimer = setTimeout(() => {
    isPanelDragging = true
    isDragging.value = true
    document.addEventListener('touchmove', onPanelTouchMove, { passive: false })
    document.addEventListener('touchend', onPanelTouchEnd)
  }, 300)

  document.addEventListener('touchend', onPanelTouchEndImmediate, { once: true })
}

function onPanelTouchEndImmediate() {
  clearTimeout(panelDragTimer)
  if (!isPanelDragging) {
    document.removeEventListener('touchmove', onPanelTouchMove)
    document.removeEventListener('touchend', onPanelTouchEnd)
  }
}

function onPanelTouchMove(e) {
  if (!isPanelDragging) return
  e.preventDefault()
  panelHasMoved = true
  const touch = e.touches[0]
  updatePanelPosition(touch.clientX, touch.clientY)
}

function onPanelTouchEnd() {
  isPanelDragging = false
  isDragging.value = false
  clearTimeout(panelDragTimer)
  document.removeEventListener('touchmove', onPanelTouchMove)
  document.removeEventListener('touchend', onPanelTouchEnd)
  if (panelHasMoved) {
    store.updateButtonPosition({ ...fabPos.value })
  }
}

function updatePanelPosition(clientX, clientY) {
  const vw = window.innerWidth
  const vh = window.innerHeight

  // 计算面板的新位置（基于鼠标/触摸位置居中）
  let newRight = vw - clientX - PANEL_WIDTH / 2
  let newBottom = vh - clientY - 26 // 26 是标题栏高度的一半

  // 边界限制
  newRight = Math.max(MARGIN, Math.min(newRight, vw - PANEL_WIDTH - MARGIN))
  newBottom = Math.max(MARGIN, Math.min(newBottom, vh - PANEL_HEIGHT - MARGIN))

  // 转换为 left/top 存储
  fabPos.value = {
    x: vw - newRight - PANEL_WIDTH,
    y: vh - newBottom - PANEL_HEIGHT
  }
}

function updatePosition(clientX, clientY) {
  const vw = window.innerWidth
  const vh = window.innerHeight

  let x = clientX - FAB_SIZE / 2
  let y = clientY - FAB_SIZE / 2

  x = Math.max(MARGIN / 2, Math.min(x, vw - FAB_SIZE - MARGIN / 2))
  y = Math.max(MARGIN / 2, Math.min(y, vh - FAB_SIZE - MARGIN / 2))

  fabPos.value = { x, y }
}

async function handleNewChat() {
  store.newChat()
  currentView.value = 'chat'
}

async function handleExport() {
  const success = await store.exportConversationToExcel()
  if (success) {
    ElMessage.success('对话记录已导出')
  } else {
    ElMessage.warning('当前没有可导出的对话')
  }
}
</script>

<style scoped lang="scss">
.chatbot-wrapper {
  position: fixed;
  top: 0;
  left: 0;
  width: 0;
  height: 0;
  z-index: 100;
  pointer-events: none;
}

.chatbot-fab {
  position: fixed;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: linear-gradient(135deg, $primary-color 0%, $primary-light 100%);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  pointer-events: auto;
  box-shadow: 0 4px 16px rgba($primary-color, 0.4);
  transition: transform $transition-base, box-shadow $transition-base, opacity $transition-base;
  user-select: none;

  &:hover:not(.dragging) {
    transform: scale(1.08);
    box-shadow: 0 6px 24px rgba($primary-color, 0.5);
  }

  &:active {
    transform: scale(0.95);
  }

  &.dragging {
    cursor: grabbing;
    transform: scale(1.12);
    box-shadow: 0 8px 32px rgba($primary-color, 0.5);
    transition: none;
  }

  &.opened {
    background: linear-gradient(135deg, $text-secondary 0%, $text-tertiary 100%);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  }
}

.fab-icon-enter-active,
.fab-icon-leave-active {
  transition: all 0.2s ease;
}

.fab-icon-enter-from {
  opacity: 0;
  transform: rotate(-90deg) scale(0.6);
}

.fab-icon-leave-to {
  opacity: 0;
  transform: rotate(90deg) scale(0.6);
}

.chatbot-panel {
  position: fixed;
  pointer-events: auto;
  background: $bg-primary;
  border-radius: $radius-xl;
  box-shadow: 0 12px 48px rgba(0, 0, 0, 0.15), 0 0 0 1px rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  z-index: 101;
}

.panel-slide-enter-active {
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.panel-slide-leave-active {
  transition: all 0.2s ease-in;
}

.panel-slide-enter-from {
  opacity: 0;
  transform: translateY(20px) scale(0.95);
}

.panel-slide-leave-to {
  opacity: 0;
  transform: translateY(10px) scale(0.98);
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  height: 52px;
  min-height: 52px;
  background: linear-gradient(135deg, $primary-color 0%, $primary-light 100%);
  color: #fff;

  .panel-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: $font-size-md;
    font-weight: 600;

    .el-icon {
      font-size: 20px;
      color: $secondary-color;
    }
  }

  .panel-header-actions {
    display: flex;
    gap: 2px;

    .header-btn {
      color: rgba(255, 255, 255, 0.8);
      padding: 6px;
      border-radius: $radius-md;

      &:hover {
        color: #fff;
        background: rgba(255, 255, 255, 0.12);
      }

      .el-icon {
        font-size: 18px;
      }
    }
  }
}

.panel-body {
  flex: 1;
  overflow: hidden;
}
</style>
