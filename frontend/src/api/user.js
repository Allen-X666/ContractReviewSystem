import { get, post, put } from '@/utils/request'
import axios from 'axios'

/**
 * 获取图形验证码
 * @param {string} source - 来源: login/register
 * @returns {Promise<{captchaId: string, imageBase64: string}>} 验证码ID和图片base64
 */
export function getCaptcha(source = 'login') {
  return axios.get('/api/auth/captcha', { 
    params: { source },
    timeout: 5000,
    headers: {
      'Content-Type': 'application/json'
    }
  }).then(res => res.data)
}

/**
 * 用户注册
 * @param {Object} data - 注册数据
 * @param {string} data.username - 用户名
 * @param {string} data.password - 密码
 * @param {string} data.confirmPassword - 确认密码
 * @param {string} data.email - 邮箱
 * @param {string} data.phone - 手机号
 * @param {string} data.code - 验证码
 * @param {string} data.captchaId - 验证码ID
 * @param {string} data.registerType - 注册类型: account/phone/email
 */
export function register(data) {
  return post('/auth/register', data)
}

/**
 * 用户登录
 * @param {Object} data - 登录数据
 * @param {string} data.username - 用户名/手机号/邮箱
 * @param {string} data.password - 密码
 * @param {string} data.loginType - 登录类型: account/phone/email
 * @param {string} data.code - 图形验证码
 */
export function login(data) {
  return post('/auth/login', data)
}

/**
 * 发送验证码
 * @param {string} target - 手机号或邮箱
 * @param {string} targetType - 目标类型: phone/email
 * @param {string} type - 业务类型: login/register/reset_password
 */
export function sendVerificationCode(target, targetType, type = 'register') {
  return post('/auth/send-code', {
    target,
    targetType,
    type
  })
}

/**
 * 用户登出
 */
export function logout() {
  return post('/auth/logout')
}

/**
 * 获取当前用户信息
 */
export function getUserInfo() {
  return post('/auth/info')
}

/**
 * 修改密码
 * @param {Object} data - 密码数据
 * @param {string} data.oldPassword - 旧密码
 * @param {string} data.newPassword - 新密码
 * @param {string} data.confirmPassword - 确认新密码
 */
export function changePassword(data) {
  return post('/auth/change-password', data)
}

/**
 * 更新用户信息
 * @param {Object} data - 用户信息数据
 * @param {string} data.nickName - 昵称
 * @param {string} data.email - 邮箱
 * @param {string} data.phone - 手机号
 */
export function updateProfile(data) {
  return put('/user/profile', data)
}

/**
 * 上传头像
 * @param {FormData} formData - 包含头像文件的 FormData 对象
 * @param {File} formData.file - 头像文件
 * @returns {Promise<{avatarUrl: string}>} 头像URL
 */
export function uploadAvatar(formData) {
  return put('/user/avatar', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

/**
 * 获取通知设置
 * @returns {Promise<{reviewComplete: boolean, riskAlert: boolean, systemNotice: boolean, emailNotification: boolean}>}
 */
export function getNotificationSetting() {
  return get('/user/notification-settings')
}

/**
 * 更新通知设置
 * @param {Object} data - 通知设置数据
 * @param {boolean} data.reviewComplete - 审查完成通知
 * @param {boolean} data.riskAlert - 高风险预警
 * @param {boolean} data.systemNotice - 系统公告
 * @param {boolean} data.emailNotification - 邮件通知
 */
export function updateNotificationSetting(data) {
  return put('/user/notification-settings', data)
}

/**
 * 获取存储路径配置
 * @returns {Promise<{uploadPath: string, reviewPath: string}>}
 */
export function getStorageConfig() {
  return get('/system/config/storage')
}

/**
 * 保存存储路径配置
 * @param {Object} data - 存储配置数据
 * @param {string} data.uploadPath - 上传文件路径
 * @param {string} data.reviewPath - 审查文件路径
 */
export function saveStorageConfig(data) {
  return post('/system/config/storage', data)
}

/**
 * 验证路径是否有效
 * @param {string} path - 要验证的路径
 * @returns {Promise<boolean>}
 */
export function validatePath(path) {
  return post('/system/config/validate-path', { path })
}

/**
 * 重置密码（忘记密码）
 * @param {Object} data - 重置密码数据
 * @param {string} data.email - 邮箱
 * @param {string} data.code - 验证码
 * @param {string} data.newPassword - 新密码
 * @param {string} data.confirmPassword - 确认新密码
 */
export function resetPassword(data) {
  // 使用 axios 直接请求，不经过 request 拦截器（无需 token）
  const baseURL = import.meta.env.VITE_API_BASE_URL || '/api'
  return axios.post(`${baseURL}/auth/reset-password`, data, {
    headers: {
      'Content-Type': 'application/json'
    }
  }).then(response => response.data)
}
