import request from '@/utils/request'

export const getNotifications = (params) => {
  return request({
    url: '/api/notifications',
    method: 'get',
    params
  })
}

export const markNotificationRead = (notificationId) => {
  return request({
    url: `/api/notifications/${notificationId}/read`,
    method: 'put'
  })
}

export const markAllNotificationsRead = () => {
  return request({
    url: '/api/notifications/read-all',
    method: 'put'
  })
}

export const deleteNotification = (notificationId) => {
  return request({
    url: `/api/notifications/${notificationId}`,
    method: 'delete'
  })
}

export const getNotificationSettings = () => {
  return request({
    url: '/api/notifications/settings',
    method: 'get'
  })
}

export const updateNotificationSettings = (data) => {
  return request({
    url: '/api/notifications/settings',
    method: 'put',
    data
  })
}
