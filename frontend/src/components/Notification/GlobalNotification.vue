<template>
  <div class="notification-center">
    <el-badge :value="unreadCount" :hidden="unreadCount === 0" class="notification-badge">
      <el-button
        circle
        size="large"
        :type="isConnected ? 'primary' : 'info'"
        @click="showNotificationDrawer = true"
      >
        <el-icon><Bell /></el-icon>
      </el-button>
    </el-badge>

    <el-drawer
      v-model="showNotificationDrawer"
      title="通知中心"
      size="400px"
      :with-header="true"
    >
      <div class="notification-header">
        <el-radio-group v-model="filterType" size="small">
          <el-radio-button label="all">全部</el-radio-button>
          <el-radio-button label="unread">未读</el-radio-button>
        </el-radio-group>
        <el-button
          v-if="unreadCount > 0"
          link
          type="primary"
          size="small"
          @click="markAllAsRead"
        >
          全部已读
        </el-button>
      </div>

      <div class="notification-list">
        <el-empty v-if="filteredNotifications.length === 0" description="暂无通知" />

        <div
          v-for="notification in filteredNotifications"
          :key="notification.id"
          :class="['notification-item', { unread: !notification.isRead }]"
          @click="handleItemClick(notification)"
        >
          <div class="notification-icon">
            <el-icon :size="20" :color="getIconColor(notification.type)">
              <component :is="getIcon(notification.type)" />
            </el-icon>
          </div>
          <div class="notification-content">
            <div class="notification-title">{{ notification.title }}</div>
            <div class="notification-message">{{ notification.message }}</div>
            <div class="notification-time">{{ formatTime(notification.createTime) }}</div>
          </div>
          <div v-if="!notification.isRead" class="unread-dot" />
        </div>
      </div>

      <template #footer>
        <el-button link @click="clearAll">清空全部</el-button>
      </template>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useNotificationStore } from '@/stores/notification'
import { sseClient } from '@/utils/sse'
import { formatTime } from '@/utils/timeFormatter'
import { Bell, CircleCheck, WarningFilled, InfoFilled, Message } from '@element-plus/icons-vue'

const notificationStore = useNotificationStore()
const showNotificationDrawer = ref(false)
const filterType = ref('all')

const unreadCount = computed(() => notificationStore.unreadCount)
const isConnected = computed(() => notificationStore.isConnected)
const notifications = computed(() => notificationStore.notifications)

const filteredNotifications = computed(() => {
  if (filterType.value === 'unread') {
    return notifications.value.filter(n => !n.isRead)
  }
  return notifications.value
})

const getIcon = (type) => {
  const iconMap = {
    review_complete: CircleCheck,
    high_risk_warning: WarningFilled,
    system_announcement: InfoFilled,
    email_notification: Message
  }
  return iconMap[type] || InfoFilled
}

const getIconColor = (type) => {
  const colorMap = {
    review_complete: '#67C23A',
    high_risk_warning: '#E6A23C',
    system_announcement: '#909399',
    email_notification: '#409EFF'
  }
  return colorMap[type] || '#909399'
}

const handleItemClick = (notification) => {
  notificationStore.handleNotificationClick(notification)
  showNotificationDrawer.value = false
}

const markAllAsRead = () => {
  notificationStore.markAllAsRead()
}

const clearAll = () => {
  notificationStore.clearAll()
}

onMounted(() => {
  sseClient.connect()
})

onUnmounted(() => {
  sseClient.disconnect()
})
</script>

<style scoped lang="scss">
.notification-center {
  position: fixed;
  right: 24px;
  bottom: 24px;
  z-index: 2000;
}

.notification-badge {
  :deep(.el-badge__content) {
    z-index: 2001;
  }
}

.notification-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e4e7ed;
}

.notification-list {
  max-height: calc(100vh - 200px);
  overflow-y: auto;
}

.notification-item {
  display: flex;
  align-items: flex-start;
  padding: 12px;
  margin-bottom: 8px;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.2s;
  position: relative;

  &:hover {
    background-color: #f5f7fa;
  }

  &.unread {
    background-color: #f0f9ff;
  }
}

.notification-icon {
  margin-right: 12px;
  flex-shrink: 0;
}

.notification-content {
  flex: 1;
  min-width: 0;
}

.notification-title {
  font-weight: 500;
  color: #303133;
  margin-bottom: 4px;
}

.notification-message {
  font-size: 13px;
  color: #606266;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.notification-time {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.unread-dot {
  width: 8px;
  height: 8px;
  background-color: #f56c6c;
  border-radius: 50%;
  position: absolute;
  right: 12px;
  top: 12px;
}
</style>
