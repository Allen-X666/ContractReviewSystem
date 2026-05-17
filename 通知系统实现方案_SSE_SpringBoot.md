# 合同审查系统通知功能实现方案 (SSE + Spring Boot)

## 需求概述

实现以下通知功能：
1. **审查完成通知** - 合同审查完成后发送通知
2. **高风险预警** - 检测到高风险合同时发送预警通知
3. **系统公告** - 接收系统更新和功能公告
4. **邮件通知** - 通过邮件接收重要通知

---

## 技术选型

- **前端**: Vue 3 + Element Plus + EventSource (SSE)
- **后端**: Spring Boot 3.x + SSE (Server-Sent Events)
- **邮件**: Spring Mail + 异步线程池
- **数据存储**: MySQL + Redis (可选，用于多实例部署)

**为什么选择 SSE 而不是 WebSocket？**
- SSE 是单向通信（服务器→客户端），适合通知推送场景
- 基于 HTTP，更容易穿透防火墙和代理
- 自动重连机制，实现简单
- 不需要像 WebSocket 那样维护长连接状态

---

## 一、前端实现方案

### 1.1 目录结构

```
frontend/src/
├── components/
│   └── Notification/
│       ├── GlobalNotification.vue    # 全局通知容器组件
│       └── NotificationToast.vue     # 单个通知弹窗组件
├── stores/
│   └── notification.js               # 通知状态管理
├── composables/
│   └── useNotification.js            # 通知组合式函数
├── api/
│   └── notification.js               # 通知相关 API
└── utils/
    └── sse.js                        # SSE 连接工具
```

### 1.2 代码实现

#### 1.2.1 SSE 连接工具 (utils/sse.js)

```javascript
import { useNotificationStore } from '@/stores/notification'
import { useUserStore } from '@/stores/user'

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

  connect() {
    const userStore = useUserStore()
    const token = userStore.token

    if (!token) {
      console.warn('SSE: 未登录，跳过连接')
      return
    }

    // 关闭现有连接
    this.disconnect()

    const sseUrl = `${this.baseUrl}/api/notifications/stream?token=${token}`

    try {
      this.eventSource = new EventSource(sseUrl)
      this.notificationStore = useNotificationStore()

      // 连接打开
      this.eventSource.onopen = () => {
        console.log('SSE: 连接成功')
        this.reconnectAttempts = 0
        this.notificationStore.isConnected = true
        this.startHeartbeat()
      }

      // 接收消息
      this.eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          this.handleMessage(data)
        } catch (error) {
          console.error('SSE: 消息解析失败', error)
        }
      }

      // 处理特定事件类型
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

      // 连接错误
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
    // 处理心跳消息
    if (data.type === 'heartbeat') {
      console.debug('SSE: 收到心跳')
      return
    }

    // 处理普通消息
    if (data.type && this.notificationStore) {
      this.notificationStore.addNotification({
        type: data.type,
        title: data.title,
        message: data.message,
        data: data.data
      })
    }
  }

  handleReviewComplete(data) {
    this.notificationStore.addNotification({
      type: 'review_complete',
      title: '审查完成',
      message: `合同 "${data.contractName}" 审查已完成，综合评分: ${data.score}分`,
      data: {
        reviewId: data.reviewId,
        contractId: data.contractId,
        contractName: data.contractName,
        score: data.score
      }
    })
  }

  handleHighRiskWarning(data) {
    this.notificationStore.addNotification({
      type: 'high_risk_warning',
      title: '高风险预警',
      message: `检测到高风险合同 "${data.contractName}"，存在 ${data.riskCount} 个高风险项，请立即查看！`,
      data: {
        contractId: data.contractId,
        contractName: data.contractName,
        riskCount: data.riskCount,
        riskLevel: data.riskLevel
      }
    })
  }

  handleSystemAnnouncement(data) {
    this.notificationStore.addNotification({
      type: 'system_announcement',
      title: `系统公告: ${data.title}`,
      message: data.content,
      data: {
        announcementId: data.announcementId,
        title: data.title,
        content: data.content
      }
    })
  }

  handleEmailNotification(data) {
    this.notificationStore.addNotification({
      type: 'email_notification',
      title: '邮件通知',
      message: data.message,
      data: {
        emailId: data.emailId,
        subject: data.subject
      }
    })
  }

  startHeartbeat() {
    // SSE 本身有连接保持机制，这里主要用于检测连接状态
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
```

#### 1.2.2 通知状态管理 (stores/notification.js)

```javascript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ElNotification } from 'element-plus'

export const useNotificationStore = defineStore('notification', () => {
  // 状态
  const notifications = ref([])
  const unreadCount = ref(0)
  const isConnected = ref(false)

  // 通知类型配置
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
      duration: 0  // 不自动关闭
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

  // 添加通知
  const addNotification = (notification) => {
    const config = notificationTypes[notification.type] || notificationTypes.system_announcement

    // 显示 Element Plus 通知（右下角）
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

    // 添加到通知列表
    notifications.value.unshift({
      id: notification.id || Date.now(),
      type: notification.type,
      title: notification.title || config.title,
      message: notification.message,
      data: notification.data,
      isRead: false,
      createTime: new Date().toISOString()
    })

    // 更新未读数
    unreadCount.value++
  }

  // 处理通知点击
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

  // 显示公告详情
  const showAnnouncementDetail = (notification) => {
    // 可以使用 ElMessageBox 或自定义弹窗
    ElNotification.info({
      title: notification.data?.title || '系统公告',
      message: notification.data?.content || notification.message,
      duration: 0
    })
  }

  // 标记为已读
  const markAsRead = (notificationId) => {
    const notification = notifications.value.find(n => n.id === notificationId)
    if (notification && !notification.isRead) {
      notification.isRead = true
      unreadCount.value = Math.max(0, unreadCount.value - 1)
    }
  }

  // 标记全部已读
  const markAllAsRead = () => {
    notifications.value.forEach(n => n.isRead = true)
    unreadCount.value = 0
  }

  // 删除通知
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

  // 清空所有通知
  const clearAll = () => {
    notifications.value = []
    unreadCount.value = 0
  }

  return {
    notifications,
    unreadCount,
    isConnected,
    addNotification,
    markAsRead,
    markAllAsRead,
    removeNotification,
    clearAll
  }
})
```

#### 1.2.3 全局通知组件 (components/Notification/GlobalNotification.vue)

```vue
<template>
  <!-- 通知中心入口 - 固定在右下角 -->
  <div class="notification-center">
    <!-- 通知铃铛按钮 -->
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

    <!-- 通知列表面板 -->
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
import { formatTimeAgo } from '@/utils/timeFormatter'

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
    review_complete: 'CircleCheck',
    high_risk_warning: 'WarningFilled',
    system_announcement: 'InfoFilled',
    email_notification: 'Message'
  }
  return iconMap[type] || 'InfoFilled'
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

const formatTime = (time) => formatTimeAgo(time)

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
```

#### 1.2.4 修改 App.vue 引入全局通知

```vue
<template>
  <router-view />
  <!-- 全局通知组件 - 固定在右下角 -->
  <GlobalNotification v-if="userStore.isLoggedIn" />
</template>

<script setup>
import { onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { useTokenRefresh } from '@/composables/useTokenRefresh'
import GlobalNotification from '@/components/Notification/GlobalNotification.vue'

const userStore = useUserStore()

useTokenRefresh()

onMounted(() => {
  userStore.loadUserFromStorage()
})
</script>
```

#### 1.2.5 通知相关 API (api/notification.js)

```javascript
import request from '@/utils/request'

// 获取通知列表
export const getNotifications = (params) => {
  return request({
    url: '/api/notifications',
    method: 'get',
    params
  })
}

// 标记通知已读
export const markNotificationRead = (notificationId) => {
  return request({
    url: `/api/notifications/${notificationId}/read`,
    method: 'put'
  })
}

// 标记全部已读
export const markAllNotificationsRead = () => {
  return request({
    url: '/api/notifications/read-all',
    method: 'put'
  })
}

// 删除通知
export const deleteNotification = (notificationId) => {
  return request({
    url: `/api/notifications/${notificationId}`,
    method: 'delete'
  })
}

// 获取通知设置
export const getNotificationSettings = () => {
  return request({
    url: '/api/notifications/settings',
    method: 'get'
  })
}

// 更新通知设置
export const updateNotificationSettings = (data) => {
  return request({
    url: '/api/notifications/settings',
    method: 'put',
    data
  })
}
```

---

## 二、后端实现方案 (Spring Boot)

### 2.1 项目结构

```
src/main/java/com/contractreview/
├── config/
│   ├── AsyncConfig.java              # 异步线程池配置
│   ├── MailConfig.java               # 邮件配置
│   └── WebMvcConfig.java             # Web配置
├── controller/
│   └── NotificationController.java   # 通知控制器
├── service/
│   ├── NotificationService.java      # 通知服务接口
│   ├── NotificationServiceImpl.java  # 通知服务实现
│   ├── EmailService.java             # 邮件服务接口
│   └── EmailServiceImpl.java         # 邮件服务实现
├── repository/
│   ├── NotificationRepository.java   # 通知数据访问
│   └── NotificationSettingRepository.java # 通知设置数据访问
├── entity/
│   ├── Notification.java             # 通知实体
│   └── NotificationSetting.java      # 通知设置实体
├── dto/
│   ├── NotificationDTO.java          # 通知DTO
│   └── NotificationRequest.java      # 通知请求
├── enums/
│   └── NotificationType.java         # 通知类型枚举
└── sse/
    ├── SseEmitterManager.java        # SSE 连接管理器
    └── SseHeartbeatTask.java         # SSE 心跳任务
```

### 2.2 代码实现

#### 2.2.1 通知类型枚举 (enums/NotificationType.java)

```java
package com.contractreview.enums;

public enum NotificationType {
    REVIEW_COMPLETE("review_complete", "审查完成"),
    HIGH_RISK_WARNING("high_risk_warning", "高风险预警"),
    SYSTEM_ANNOUNCEMENT("system_announcement", "系统公告"),
    EMAIL_NOTIFICATION("email_notification", "邮件通知");

    private final String code;
    private final String description;

    NotificationType(String code, String description) {
        this.code = code;
        this.description = description;
    }

    public String getCode() {
        return code;
    }

    public String getDescription() {
        return description;
    }
}
```

#### 2.2.2 通知实体 (entity/Notification.java)

```java
package com.contractreview.entity;

import com.contractreview.enums.NotificationType;
import jakarta.persistence.*;
import lombok.Data;
import org.hibernate.annotations.CreationTimestamp;

import java.time.LocalDateTime;

@Data
@Entity
@Table(name = "notifications")
public class Notification {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "user_id", nullable = false)
    private Long userId;

    @Enumerated(EnumType.STRING)
    @Column(name = "type", nullable = false)
    private NotificationType type;

    @Column(name = "title", nullable = false, length = 200)
    private String title;

    @Column(name = "message", nullable = false, columnDefinition = "TEXT")
    private String message;

    @Column(name = "data", columnDefinition = "TEXT")
    private String data; // JSON格式存储附加数据

    @Column(name = "is_read")
    private Boolean isRead = false;

    @Column(name = "is_email_sent")
    private Boolean isEmailSent = false;

    @CreationTimestamp
    @Column(name = "create_time")
    private LocalDateTime createTime;

    @Column(name = "read_time")
    private LocalDateTime readTime;
}
```

#### 2.2.3 通知设置实体 (entity/NotificationSetting.java)

```java
package com.contractreview.entity;

import jakarta.persistence.*;
import lombok.Data;
import org.hibernate.annotations.UpdateTimestamp;

import java.time.LocalDateTime;

@Data
@Entity
@Table(name = "notification_settings")
public class NotificationSetting {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "user_id", unique = true, nullable = false)
    private Long userId;

    // 审查完成通知设置
    @Column(name = "review_complete_web")
    private Boolean reviewCompleteWeb = true;

    @Column(name = "review_complete_email")
    private Boolean reviewCompleteEmail = true;

    // 高风险预警通知设置
    @Column(name = "high_risk_warning_web")
    private Boolean highRiskWarningWeb = true;

    @Column(name = "high_risk_warning_email")
    private Boolean highRiskWarningEmail = true;

    // 系统公告通知设置
    @Column(name = "system_announcement_web")
    private Boolean systemAnnouncementWeb = true;

    @Column(name = "system_announcement_email")
    private Boolean systemAnnouncementEmail = false;

    @UpdateTimestamp
    @Column(name = "update_time")
    private LocalDateTime updateTime;
}
```

#### 2.2.4 SSE 连接管理器 (sse/SseEmitterManager.java)

```java
package com.contractreview.sse;

import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.io.IOException;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@Slf4j
@Component
public class SseEmitterManager {

    // 用户ID到SseEmitter的映射
    private final Map<Long, SseEmitter> emitters = new ConcurrentHashMap<>();

    // SSE超时时间（毫秒）
    private static final long SSE_TIMEOUT = 0L; // 0表示不超时

    /**
     * 创建SSE连接
     */
    public SseEmitter createEmitter(Long userId) {
        // 如果已存在连接，先移除
        removeEmitter(userId);

        SseEmitter emitter = new SseEmitter(SSE_TIMEOUT);

        // 连接完成回调
        emitter.onCompletion(() -> {
            log.info("SSE连接完成 - 用户ID: {}", userId);
            emitters.remove(userId);
        });

        // 连接超时回调
        emitter.onTimeout(() -> {
            log.warn("SSE连接超时 - 用户ID: {}", userId);
            emitters.remove(userId);
        });

        // 连接错误回调
        emitter.onError((e) -> {
            log.error("SSE连接错误 - 用户ID: {}, 错误: {}", userId, e.getMessage());
            emitters.remove(userId);
        });

        emitters.put(userId, emitter);
        log.info("SSE连接建立 - 用户ID: {}", userId);

        return emitter;
    }

    /**
     * 移除SSE连接
     */
    public void removeEmitter(Long userId) {
        SseEmitter emitter = emitters.remove(userId);
        if (emitter != null) {
            emitter.complete();
            log.info("SSE连接移除 - 用户ID: {}", userId);
        }
    }

    /**
     * 向指定用户发送消息
     */
    public void sendToUser(Long userId, String eventName, Object data) {
        SseEmitter emitter = emitters.get(userId);
        if (emitter == null) {
            log.debug("用户 {} 不在线，跳过发送", userId);
            return;
        }

        try {
            SseEmitter.SseEventBuilder event = SseEmitter.event()
                    .name(eventName)
                    .data(data);
            emitter.send(event);
            log.debug("SSE消息发送成功 - 用户ID: {}, 事件: {}", userId, eventName);
        } catch (IOException e) {
            log.error("SSE消息发送失败 - 用户ID: {}, 错误: {}", userId, e.getMessage());
            removeEmitter(userId);
        }
    }

    /**
     * 向指定用户发送普通消息
     */
    public void sendMessageToUser(Long userId, Object data) {
        SseEmitter emitter = emitters.get(userId);
        if (emitter == null) {
            return;
        }

        try {
            emitter.send(data);
        } catch (IOException e) {
            log.error("SSE消息发送失败 - 用户ID: {}", userId, e);
            removeEmitter(userId);
        }
    }

    /**
     * 广播消息给所有在线用户
     */
    public void broadcast(String eventName, Object data) {
        emitters.forEach((userId, emitter) -> {
            try {
                SseEmitter.SseEventBuilder event = SseEmitter.event()
                        .name(eventName)
                        .data(data);
                emitter.send(event);
            } catch (IOException e) {
                log.error("广播消息失败 - 用户ID: {}", userId, e);
                removeEmitter(userId);
            }
        });
    }

    /**
     * 检查用户是否在线
     */
    public boolean isUserOnline(Long userId) {
        return emitters.containsKey(userId);
    }

    /**
     * 获取在线用户数量
     */
    public int getOnlineCount() {
        return emitters.size();
    }
}
```

#### 2.2.5 异步配置 (config/AsyncConfig.java)

```java
package com.contractreview.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;

import java.util.concurrent.Executor;
import java.util.concurrent.ThreadPoolExecutor;

@Configuration
@EnableAsync
public class AsyncConfig {

    /**
     * 邮件发送线程池
     */
    @Bean("emailTaskExecutor")
    public Executor emailTaskExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(5);
        executor.setMaxPoolSize(20);
        executor.setQueueCapacity(100);
        executor.setThreadNamePrefix("email-");
        executor.setRejectedExecutionHandler(new ThreadPoolExecutor.CallerRunsPolicy());
        executor.initialize();
        return executor;
    }

    /**
     * 通知发送线程池
     */
    @Bean("notificationTaskExecutor")
    public Executor notificationTaskExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(10);
        executor.setMaxPoolSize(50);
        executor.setQueueCapacity(200);
        executor.setThreadNamePrefix("notification-");
        executor.setRejectedExecutionHandler(new ThreadPoolExecutor.CallerRunsPolicy());
        executor.initialize();
        return executor;
    }
}
```

#### 2.2.6 邮件服务实现 (service/EmailServiceImpl.java)

```java
package com.contractreview.service.impl;

import com.contractreview.enums.NotificationType;
import com.contractreview.service.EmailService;
import jakarta.mail.MessagingException;
import jakarta.mail.internet.MimeMessage;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.mail.javamail.MimeMessageHelper;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

@Slf4j
@Service
@RequiredArgsConstructor
public class EmailServiceImpl implements EmailService {

    private final JavaMailSender mailSender;

    @Value("${spring.mail.username}")
    private String fromEmail;

    @Value("${app.mail.sender-name:合同审查系统}")
    private String senderName;

    @Override
    @Async("emailTaskExecutor")
    public void sendNotificationEmail(String toEmail, NotificationType type, String title, String message) {
        try {
            MimeMessage mimeMessage = mailSender.createMimeMessage();
            MimeMessageHelper helper = new MimeMessageHelper(mimeMessage, true, "UTF-8");

            helper.setFrom(fromEmail, senderName);
            helper.setTo(toEmail);
            helper.setSubject("【" + senderName + "】" + title);
            helper.setText(buildEmailContent(type, title, message), true);

            mailSender.send(mimeMessage);
            log.info("邮件发送成功 - 收件人: {}, 主题: {}", toEmail, title);

        } catch (Exception e) {
            log.error("邮件发送失败 - 收件人: {}, 错误: {}", toEmail, e.getMessage(), e);
        }
    }

    @Override
    public String buildEmailContent(NotificationType type, String title, String message) {
        String time = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"));

        String headerColor;
        String icon;

        switch (type) {
            case REVIEW_COMPLETE:
                headerColor = "#67C23A";
                icon = "✓";
                break;
            case HIGH_RISK_WARNING:
                headerColor = "#E6A23C";
                icon = "⚠";
                break;
            default:
                headerColor = "#409EFF";
                icon = "ℹ";
        }

        return String.format(
            "<div style=\"font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;\">" +
            "<h2 style=\"color: %s;\">%s %s</h2>" +
            "<div style=\"background: #f5f7fa; padding: 20px; border-radius: 8px;\">" +
            "<h3>%s</h3>" +
            "<p>%s</p>" +
            "</div>" +
            "<p style=\"color: #909399; font-size: 12px; margin-top: 20px;\">" +
            "此邮件由%s自动发送，请勿回复。<br>" +
            "发送时间: %s" +
            "</p>" +
            "</div>",
            headerColor, icon, type.getDescription(),
            title, message,
            senderName, time
        );
    }
}
```

#### 2.2.7 通知服务实现 (service/NotificationServiceImpl.java)

```java
package com.contractreview.service.impl;

import com.contractreview.dto.NotificationDTO;
import com.contractreview.entity.Notification;
import com.contractreview.entity.NotificationSetting;
import com.contractreview.entity.User;
import com.contractreview.enums.NotificationType;
import com.contractreview.repository.NotificationRepository;
import com.contractreview.repository.NotificationSettingRepository;
import com.contractreview.repository.UserRepository;
import com.contractreview.service.EmailService;
import com.contractreview.service.NotificationService;
import com.contractreview.sse.SseEmitterManager;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Slf4j
@Service
@RequiredArgsConstructor
public class NotificationServiceImpl implements NotificationService {

    private final NotificationRepository notificationRepository;
    private final NotificationSettingRepository settingRepository;
    private final UserRepository userRepository;
    private final SseEmitterManager sseEmitterManager;
    private final EmailService emailService;
    private final ObjectMapper objectMapper;

    @Override
    @Transactional
    public Notification createNotification(Long userId, NotificationType type,
                                           String title, String message,
                                           Map<String, Object> data, boolean sendEmail) {
        // 检查用户通知设置
        NotificationSetting settings = getOrCreateSettings(userId);

        // 检查是否应该发送页面通知
        if (!shouldSendWeb(type, settings)) {
            log.debug("用户 {} 关闭了 {} 的页面通知", userId, type);
            return null;
        }

        // 创建通知记录
        Notification notification = new Notification();
        notification.setUserId(userId);
        notification.setType(type);
        notification.setTitle(title);
        notification.setMessage(message);

        try {
            if (data != null) {
                notification.setData(objectMapper.writeValueAsString(data));
            }
        } catch (Exception e) {
            log.error("序列化通知数据失败", e);
        }

        notificationRepository.save(notification);

        // 发送SSE通知
        sendSseNotification(userId, type, title, message, data);

        // 异步发送邮件
        if (sendEmail && shouldSendEmail(type, settings)) {
            sendEmailNotification(userId, type, title, message);
            notification.setIsEmailSent(true);
            notificationRepository.save(notification);
        }

        return notification;
    }

    @Override
    public void notifyReviewComplete(Long userId, Long reviewId, Long contractId,
                                     String contractName, Double score) {
        Map<String, Object> data = new HashMap<>();
        data.put("reviewId", reviewId);
        data.put("contractId", contractId);
        data.put("contractName", contractName);
        data.put("score", score);

        createNotification(
            userId,
            NotificationType.REVIEW_COMPLETE,
            "审查完成",
            String.format("合同 \"%s\" 审查已完成，综合评分: %.1f分", contractName, score),
            data,
            true
        );
    }

    @Override
    public void notifyHighRiskWarning(Long userId, Long contractId, String contractName,
                                      Integer riskCount, String riskLevel) {
        Map<String, Object> data = new HashMap<>();
        data.put("contractId", contractId);
        data.put("contractName", contractName);
        data.put("riskCount", riskCount);
        data.put("riskLevel", riskLevel);

        createNotification(
            userId,
            NotificationType.HIGH_RISK_WARNING,
            "高风险预警",
            String.format("检测到高风险合同 \"%s\"，存在 %d 个高风险项，请立即查看！", contractName, riskCount),
            data,
            true
        );
    }

    @Override
    public void notifySystemAnnouncement(List<Long> userIds, Long announcementId,
                                         String title, String content) {
        for (Long userId : userIds) {
            Map<String, Object> data = new HashMap<>();
            data.put("announcementId", announcementId);
            data.put("title", title);
            data.put("content", content);

            String shortContent = content.length() > 200
                ? content.substring(0, 200) + "..."
                : content;

            createNotification(
                userId,
                NotificationType.SYSTEM_ANNOUNCEMENT,
                "系统公告: " + title,
                shortContent,
                data,
                false  // 系统公告通常不发送邮件
            );
        }
    }

    @Async("notificationTaskExecutor")
    protected void sendSseNotification(Long userId, NotificationType type,
                                       String title, String message, Map<String, Object> data) {
        if (!sseEmitterManager.isUserOnline(userId)) {
            return;
        }

        Map<String, Object> payload = new HashMap<>();
        payload.put("type", type.getCode());
        payload.put("title", title);
        payload.put("message", message);
        payload.put("data", data);

        sseEmitterManager.sendToUser(userId, type.getCode(), payload);
    }

    @Async("emailTaskExecutor")
    protected void sendEmailNotification(Long userId, NotificationType type,
                                         String title, String message) {
        User user = userRepository.findById(userId).orElse(null);
        if (user == null || user.getEmail() == null || user.getEmail().isEmpty()) {
            log.warn("用户 {} 未设置邮箱，跳过邮件发送", userId);
            return;
        }

        emailService.sendNotificationEmail(user.getEmail(), type, title, message);
    }

    private boolean shouldSendWeb(NotificationType type, NotificationSetting settings) {
        if (settings == null) return true;

        return switch (type) {
            case REVIEW_COMPLETE -> settings.getReviewCompleteWeb();
            case HIGH_RISK_WARNING -> settings.getHighRiskWarningWeb();
            case SYSTEM_ANNOUNCEMENT -> settings.getSystemAnnouncementWeb();
            default -> true;
        };
    }

    private boolean shouldSendEmail(NotificationType type, NotificationSetting settings) {
        if (settings == null) return false;

        return switch (type) {
            case REVIEW_COMPLETE -> settings.getReviewCompleteEmail();
            case HIGH_RISK_WARNING -> settings.getHighRiskWarningEmail();
            case SYSTEM_ANNOUNCEMENT -> settings.getSystemAnnouncementEmail();
            default -> false;
        };
    }

    private NotificationSetting getOrCreateSettings(Long userId) {
        return settingRepository.findByUserId(userId)
            .orElseGet(() -> {
                NotificationSetting setting = new NotificationSetting();
                setting.setUserId(userId);
                return settingRepository.save(setting);
            });
    }

    // ==================== 查询方法 ====================

    @Override
    public Page<Notification> getUserNotifications(Long userId, Boolean isRead,
                                                    NotificationType type, Pageable pageable) {
        if (isRead != null && type != null) {
            return notificationRepository.findByUserIdAndIsReadAndType(userId, isRead, type, pageable);
        } else if (isRead != null) {
            return notificationRepository.findByUserIdAndIsRead(userId, isRead, pageable);
        } else if (type != null) {
            return notificationRepository.findByUserIdAndType(userId, type, pageable);
        }
        return notificationRepository.findByUserIdOrderByCreateTimeDesc(userId, pageable);
    }

    @Override
    public Long getUnreadCount(Long userId) {
        return notificationRepository.countByUserIdAndIsRead(userId, false);
    }

    @Override
    @Transactional
    public boolean markAsRead(Long notificationId, Long userId) {
        Notification notification = notificationRepository.findByIdAndUserId(notificationId, userId);
        if (notification == null || notification.getIsRead()) {
            return false;
        }

        notification.setIsRead(true);
        notification.setReadTime(LocalDateTime.now());
        notificationRepository.save(notification);
        return true;
    }

    @Override
    @Transactional
    public int markAllAsRead(Long userId) {
        List<Notification> unreadNotifications = notificationRepository
            .findByUserIdAndIsRead(userId, false);

        LocalDateTime now = LocalDateTime.now();
        for (Notification notification : unreadNotifications) {
            notification.setIsRead(true);
            notification.setReadTime(now);
        }

        notificationRepository.saveAll(unreadNotifications);
        return unreadNotifications.size();
    }

    @Override
    public NotificationSetting getUserSettings(Long userId) {
        return getOrCreateSettings(userId);
    }

    @Override
    @Transactional
    public NotificationSetting updateSettings(Long userId, NotificationSetting settings) {
        NotificationSetting existing = getOrCreateSettings(userId);

        if (settings.getReviewCompleteWeb() != null) {
            existing.setReviewCompleteWeb(settings.getReviewCompleteWeb());
        }
        if (settings.getReviewCompleteEmail() != null) {
            existing.setReviewCompleteEmail(settings.getReviewCompleteEmail());
        }
        if (settings.getHighRiskWarningWeb() != null) {
            existing.setHighRiskWarningWeb(settings.getHighRiskWarningWeb());
        }
        if (settings.getHighRiskWarningEmail() != null) {
            existing.setHighRiskWarningEmail(settings.getHighRiskWarningEmail());
        }
        if (settings.getSystemAnnouncementWeb() != null) {
            existing.setSystemAnnouncementWeb(settings.getSystemAnnouncementWeb());
        }
        if (settings.getSystemAnnouncementEmail() != null) {
            existing.setSystemAnnouncementEmail(settings.getSystemAnnouncementEmail());
        }

        return settingRepository.save(existing);
    }
}
```

#### 2.2.8 通知控制器 (controller/NotificationController.java)

```java
package com.contractreview.controller;

import com.contractreview.dto.ApiResponse;
import com.contractreview.entity.Notification;
import com.contractreview.entity.NotificationSetting;
import com.contractreview.enums.NotificationType;
import com.contractreview.security.CurrentUser;
import com.contractreview.security.UserPrincipal;
import com.contractreview.service.NotificationService;
import com.contractreview.sse.SseEmitterManager;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

@Slf4j
@RestController
@RequestMapping("/api/notifications")
@RequiredArgsConstructor
public class NotificationController {

    private final NotificationService notificationService;
    private final SseEmitterManager sseEmitterManager;

    /**
     * SSE 实时通知流
     */
    @GetMapping(value = "/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public SseEmitter streamNotifications(@RequestParam String token) {
        // 从token中解析用户ID（这里简化处理，实际应该验证token）
        Long userId = extractUserIdFromToken(token);
        return sseEmitterManager.createEmitter(userId);
    }

    /**
     * 获取通知列表
     */
    @GetMapping
    public ApiResponse<Page<Notification>> getNotifications(
            @CurrentUser UserPrincipal user,
            @RequestParam(required = false) Boolean isRead,
            @RequestParam(required = false) String type,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {

        Pageable pageable = PageRequest.of(page, size);
        NotificationType notificationType = null;

        if (type != null && !type.isEmpty()) {
            try {
                notificationType = NotificationType.valueOf(type.toUpperCase());
            } catch (IllegalArgumentException e) {
                log.warn("无效的通知类型: {}", type);
            }
        }

        Page<Notification> notifications = notificationService.getUserNotifications(
            user.getId(), isRead, notificationType, pageable);

        return ApiResponse.success(notifications);
    }

    /**
     * 获取未读通知数量
     */
    @GetMapping("/unread-count")
    public ApiResponse<Long> getUnreadCount(@CurrentUser UserPrincipal user) {
        Long count = notificationService.getUnreadCount(user.getId());
        return ApiResponse.success(count);
    }

    /**
     * 标记通知为已读
     */
    @PutMapping("/{notificationId}/read")
    public ApiResponse<Boolean> markAsRead(
            @CurrentUser UserPrincipal user,
            @PathVariable Long notificationId) {
        boolean success = notificationService.markAsRead(notificationId, user.getId());
        return ApiResponse.success(success);
    }

    /**
     * 标记所有通知为已读
     */
    @PutMapping("/read-all")
    public ApiResponse<Integer> markAllAsRead(@CurrentUser UserPrincipal user) {
        int count = notificationService.markAllAsRead(user.getId());
        return ApiResponse.success(count);
    }

    /**
     * 获取通知设置
     */
    @GetMapping("/settings")
    public ApiResponse<NotificationSetting> getSettings(@CurrentUser UserPrincipal user) {
        NotificationSetting settings = notificationService.getUserSettings(user.getId());
        return ApiResponse.success(settings);
    }

    /**
     * 更新通知设置
     */
    @PutMapping("/settings")
    public ApiResponse<NotificationSetting> updateSettings(
            @CurrentUser UserPrincipal user,
            @RequestBody NotificationSetting settings) {
        NotificationSetting updated = notificationService.updateSettings(user.getId(), settings);
        return ApiResponse.success(updated);
    }

    private Long extractUserIdFromToken(String token) {
        // 实际项目中应该使用JWT解析
        // 这里简化处理
        return 1L;
    }
}
```

#### 2.2.9 邮件配置 (application.yml)

```yaml
spring:
  mail:
    host: smtp.qq.com
    port: 465
    username: your-email@qq.com
    password: your-authorization-code
    protocol: smtp
    default-encoding: UTF-8
    properties:
      mail:
        smtp:
          auth: true
          ssl:
            enable: true
          starttls:
            enable: true

app:
  mail:
    sender-name: 合同审查系统
```

#### 2.2.10 在审查流程中触发通知

```java
package com.contractreview.service.impl;

import com.contractreview.service.NotificationService;
import com.contractreview.service.ReviewService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

@Slf4j
@Service
@RequiredArgsConstructor
public class ReviewServiceImpl implements ReviewService {

    private final NotificationService notificationService;
    // ... 其他依赖

    @Override
    public void completeReview(Long reviewId) {
        // ... 原有审查完成逻辑

        // 获取审查结果
        ReviewResult result = getReviewResult(reviewId);

        // 发送审查完成通知
        notificationService.notifyReviewComplete(
            result.getUserId(),
            reviewId,
            result.getContractId(),
            result.getContractName(),
            result.getOverallScore()
        );

        // 检查是否有高风险项
        long highRiskCount = result.getRisks().stream()
            .filter(risk -> "HIGH".equals(risk.getRiskLevel()))
            .count();

        if (highRiskCount > 0) {
            notificationService.notifyHighRiskWarning(
                result.getUserId(),
                result.getContractId(),
                result.getContractName(),
                (int) highRiskCount,
                "HIGH"
            );
        }
    }
}
```

---

## 三、Maven 依赖

```xml
<dependencies>
    <!-- Spring Boot Web -->
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-web</artifactId>
    </dependency>

    <!-- Spring Boot Data JPA -->
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-data-jpa</artifactId>
    </dependency>

    <!-- Spring Boot Mail -->
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-mail</artifactId>
    </dependency>

    <!-- Spring Boot Validation -->
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-validation</artifactId>
    </dependency>

    <!-- MySQL Connector -->
    <dependency>
        <groupId>com.mysql</groupId>
        <artifactId>mysql-connector-j</artifactId>
        <scope>runtime</scope>
    </dependency>

    <!-- Lombok -->
    <dependency>
        <groupId>org.projectlombok</groupId>
        <artifactId>lombok</artifactId>
        <optional>true</optional>
    </dependency>

    <!-- JSON 处理 -->
    <dependency>
        <groupId>com.fasterxml.jackson.core</groupId>
        <artifactId>jackson-databind</artifactId>
    </dependency>
</dependencies>
```

---

## 四、功能总结

| 功能 | 实现方式 | 触发时机 |
|------|----------|----------|
| 审查完成通知 | SSE实时推送 + 邮件 | 审查任务完成时 |
| 高风险预警 | SSE实时推送 + 邮件 | 检测到高风险合同时 |
| 系统公告 | SSE实时推送 | 管理员发布公告时 |
| 邮件通知 | 异步线程池 | 根据用户设置自动触发 |

### 前端特性
- 右下角固定通知中心入口
- 支持实时 SSE 推送（自动重连）
- 通知分类展示（全部/未读）
- 点击通知跳转对应页面
- 支持标记已读、清空通知

### 后端特性
- SSE 服务器推送（比 WebSocket 更简单）
- 通知持久化存储
- 用户个性化通知设置
- 异步邮件发送（Spring Mail + 线程池）
- 支持邮件模板定制
