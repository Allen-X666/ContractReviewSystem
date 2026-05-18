import { useNotificationStore } from '@/stores/notification'
import { useUserStore } from '@/stores/user'
import { inject } from 'vue'

let toastInstance = null

export const setToastInstance = (instance) => {
  toastInstance = instance
}

class SSEClient {
  constructor() {
    this.eventSource = null
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = 5
    this.reconnectInterval = 3000
    this.heartbeatInterval = 30000
    this.heartbeatTimer = null
    this.notificationStore = null
    this.baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080'
  }

  showToastNotification(notification) {
    if (toastInstance) {
      toastInstance.showToast({
        type: notification.type,
        title: notification.title,
        message: notification.message,
        duration: 60000
      })
    }
  }

  connect() {
    const userStore = useUserStore()
    const token = userStore.token

    if (!token) {
      console.warn('SSE: 未登录，跳过连接')
      return
    }

    this.disconnect()

    // 移除 Bearer 前缀，后端会自动添加
    const cleanToken = token.replace('Bearer ', '')
    // 注意：后端配置了 context-path: /api，所以路径是 /api/notifications/stream
    // 开发环境直接访问后端，不走 Vite 代理
    const sseUrl = `http://localhost:8080/api/notifications/stream?token=${encodeURIComponent(cleanToken)}`

    try {
      this.eventSource = new EventSource(sseUrl)
      this.notificationStore = useNotificationStore()

      this.eventSource.onopen = () => {
        console.log('SSE: 连接成功')
        this.reconnectAttempts = 0
        this.notificationStore.isConnected = true
        this.startHeartbeat()
      }

      this.eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          this.handleMessage(data)
        } catch (error) {
          console.error('SSE: 消息解析失败', error)
        }
      }

      this.eventSource.addEventListener('review_complete', (event) => {
        const data = JSON.parse(event.data)
        this.handleReviewComplete(data)
      })

      this.eventSource.addEventListener('high_risk_warning', (event) => {
        const data = JSON.parse(event.data)
        this.handleHighRiskWarning(data)
      })

      this.eventSource.addEventListener('system_announcement', (event) => {
        const data = JSON.parse(event.data)
        this.handleSystemAnnouncement(data)
      })

      this.eventSource.addEventListener('email_notification', (event) => {
        const data = JSON.parse(event.data)
        this.handleEmailNotification(data)
      })

      this.eventSource.onerror = (error) => {
        console.error('SSE: 连接错误', error)
        this.notificationStore.isConnected = false
        this.stopHeartbeat()
        this.reconnect()
      }

    } catch (error) {
      console.error('SSE: 连接失败', error)
      this.reconnect()
    }
  }

  handleMessage(data) {
    if (data.type === 'heartbeat') {
      console.debug('SSE: 收到心跳')
      return
    }

    if (data.type && this.notificationStore) {
      const notification = {
        type: data.type,
        title: data.title,
        message: data.message,
        data: data.data
      }
      this.notificationStore.addNotification(notification)
      this.showToastNotification(notification)
    }
  }

  handleReviewComplete(data) {
    const notification = {
      type: 'review_complete',
      title: '审查完成',
      message: `合同 "${data.contractName}" 审查已完成，综合评分: ${data.score}分`,
      data: {
        reviewId: data.reviewId,
        contractId: data.contractId,
        contractName: data.contractName,
        score: data.score
      }
    }
    this.notificationStore.addNotification(notification)
    this.showToastNotification(notification)
  }

  handleHighRiskWarning(data) {
    const notification = {
      type: 'high_risk_warning',
      title: '高风险预警',
      message: `检测到高风险合同 "${data.contractName}"，存在 ${data.riskCount} 个高风险项，请立即查看！`,
      data: {
        contractId: data.contractId,
        contractName: data.contractName,
        riskCount: data.riskCount,
        riskLevel: data.riskLevel
      }
    }
    this.notificationStore.addNotification(notification)
    this.showToastNotification(notification)
  }

  handleSystemAnnouncement(data) {
    const notification = {
      type: 'system_announcement',
      title: `系统公告: ${data.title}`,
      message: data.content,
      data: {
        announcementId: data.announcementId,
        title: data.title,
        content: data.content
      }
    }
    this.notificationStore.addNotification(notification)
    this.showToastNotification(notification)
  }

  handleEmailNotification(data) {
    const notification = {
      type: 'email_notification',
      title: '邮件通知',
      message: data.message,
      data: {
        emailId: data.emailId,
        subject: data.subject
      }
    }
    this.notificationStore.addNotification(notification)
    this.showToastNotification(notification)
  }

  startHeartbeat() {
    this.heartbeatTimer = setInterval(() => {
      if (this.eventSource && this.eventSource.readyState === EventSource.CLOSED) {
        console.warn('SSE: 连接已断开，尝试重连')
        this.reconnect()
      }
    }, this.heartbeatInterval)
  }

  stopHeartbeat() {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
  }

  reconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      console.log(`SSE: ${this.reconnectInterval}ms 后尝试第 ${this.reconnectAttempts} 次重连`)
      setTimeout(() => this.connect(), this.reconnectInterval)
    } else {
      console.error('SSE: 重连次数已达上限')
    }
  }

  disconnect() {
    this.stopHeartbeat()
    if (this.eventSource) {
      this.eventSource.close()
      this.eventSource = null
    }
    if (this.notificationStore) {
      this.notificationStore.isConnected = false
    }
  }
}

export const sseClient = new SSEClient()
