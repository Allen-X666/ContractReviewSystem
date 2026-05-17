import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ElNotification } from 'element-plus'

export const useNotificationStore = defineStore('notification', () => {
  const notifications = ref([])
  const unreadCount = ref(0)
  const isConnected = ref(false)

  const notificationTypes = {
    review_complete: {
      title: '审查完成',
      type: 'success',
      icon: 'CircleCheck',
      duration: 5000
    },
    high_risk_warning: {
      title: '高风险预警',
      type: 'warning',
      icon: 'WarningFilled',
      duration: 0
    },
    system_announcement: {
      title: '系统公告',
      type: 'info',
      icon: 'InfoFilled',
      duration: 8000
    },
    email_notification: {
      title: '邮件通知',
      type: 'info',
      icon: 'Message',
      duration: 6000
    }
  }

  const addNotification = (notification) => {
    const config = notificationTypes[notification.type] || notificationTypes.system_announcement

    ElNotification({
      title: notification.title || config.title,
      message: notification.message,
      type: config.type,
      duration: config.duration,
      position: 'bottom-right',
      showClose: true,
      onClick: () => handleNotificationClick(notification),
      onClose: () => removeNotification(notification.id)
    })

    notifications.value.unshift({
      id: notification.id || Date.now(),
      type: notification.type,
      title: notification.title || config.title,
      message: notification.message,
      data: notification.data,
      isRead: false,
      createTime: new Date().toISOString()
    })

    unreadCount.value++
  }

  const handleNotificationClick = (notification) => {
    switch (notification.type) {
      case 'review_complete':
        if (notification.data?.reviewId) {
          window.location.href = `/review/${notification.data.reviewId}`
        }
        break
      case 'high_risk_warning':
        if (notification.data?.contractId) {
          window.location.href = `/contract/${notification.data.contractId}`
        }
        break
      case 'system_announcement':
        showAnnouncementDetail(notification)
        break
      default:
        break
    }
    markAsRead(notification.id)
  }

  const showAnnouncementDetail = (notification) => {
    ElNotification.info({
      title: notification.data?.title || '系统公告',
      message: notification.data?.content || notification.message,
      duration: 0
    })
  }

  const markAsRead = (notificationId) => {
    const notification = notifications.value.find(n => n.id === notificationId)
    if (notification && !notification.isRead) {
      notification.isRead = true
      unreadCount.value = Math.max(0, unreadCount.value - 1)
    }
  }

  const markAllAsRead = () => {
    notifications.value.forEach(n => n.isRead = true)
    unreadCount.value = 0
  }

  const removeNotification = (notificationId) => {
    const index = notifications.value.findIndex(n => n.id === notificationId)
    if (index > -1) {
      const notification = notifications.value[index]
      if (!notification.isRead) {
        unreadCount.value = Math.max(0, unreadCount.value - 1)
      }
      notifications.value.splice(index, 1)
    }
  }

  const clearAll = () => {
    notifications.value = []
    unreadCount.value = 0
  }

  return {
    notifications,
    unreadCount,
    isConnected,
    addNotification,
    handleNotificationClick,
    markAsRead,
    markAllAsRead,
    removeNotification,
    clearAll
  }
})
