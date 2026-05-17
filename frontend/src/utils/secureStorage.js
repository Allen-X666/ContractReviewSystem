/**
 * 安全存储工具
 * 提供比 localStorage 更安全的存储方式
 * 敏感信息使用内存存储，非敏感信息使用 localStorage
 */

import { STORAGE_KEYS } from './constants'

// 内存存储 - 用于敏感信息（页面刷新后丢失）
const memoryStorage = new Map()

// 会话存储 - 用于半敏感信息（标签页关闭后丢失）
const sessionStorage = window.sessionStorage

/**
 * 安全存储类
 */
export class SecureStorage {
  /**
   * 存储 Token（使用内存 + sessionStorage 双保险）
   * @param {string} token 
   */
  static setToken(token) {
    if (!token) {
      this.removeToken()
      return
    }
    // 主存储：内存
    memoryStorage.set(STORAGE_KEYS.TOKEN, token)
    // 备份存储：sessionStorage（页面刷新恢复用）
    try {
      sessionStorage.setItem(STORAGE_KEYS.TOKEN, token)
    } catch (e) {
      console.warn('sessionStorage 写入失败:', e)
    }
  }

  /**
   * 获取 Token
   * @returns {string|null}
   */
  static getToken() {
    // 优先从内存获取
    const memoryToken = memoryStorage.get(STORAGE_KEYS.TOKEN)
    if (memoryToken) {
      return memoryToken
    }
    // 内存没有，从 sessionStorage 恢复
    try {
      const sessionToken = sessionStorage.getItem(STORAGE_KEYS.TOKEN)
      if (sessionToken) {
        // 恢复到内存
        memoryStorage.set(STORAGE_KEYS.TOKEN, sessionToken)
        return sessionToken
      }
    } catch (e) {
      console.warn('sessionStorage 读取失败:', e)
    }
    return null
  }

  /**
   * 移除 Token
   */
  static removeToken() {
    memoryStorage.delete(STORAGE_KEYS.TOKEN)
    try {
      sessionStorage.removeItem(STORAGE_KEYS.TOKEN)
    } catch (e) {
      console.warn('sessionStorage 删除失败:', e)
    }
  }

  /**
   * 存储用户信息（非敏感，使用 localStorage）
   * @param {Object} userInfo 
   */
  static setUserInfo(userInfo) {
    if (!userInfo) {
      this.removeUserInfo()
      return
    }
    try {
      // 过滤敏感字段
      const safeUserInfo = this.filterSensitiveFields(userInfo)
      localStorage.setItem(STORAGE_KEYS.USER_INFO, JSON.stringify(safeUserInfo))
    } catch (e) {
      console.warn('localStorage 写入失败:', e)
    }
  }

  /**
   * 获取用户信息
   * @returns {Object|null}
   */
  static getUserInfo() {
    try {
      const data = localStorage.getItem(STORAGE_KEYS.USER_INFO)
      return data ? JSON.parse(data) : null
    } catch (e) {
      console.warn('localStorage 读取失败:', e)
      return null
    }
  }

  /**
   * 移除用户信息
   */
  static removeUserInfo() {
    try {
      localStorage.removeItem(STORAGE_KEYS.USER_INFO)
    } catch (e) {
      console.warn('localStorage 删除失败:', e)
    }
  }

  /**
   * 存储设置（非敏感，使用 localStorage）
   * @param {Object} settings 
   */
  static setSettings(settings) {
    if (!settings) {
      this.removeSettings()
      return
    }
    try {
      localStorage.setItem(STORAGE_KEYS.SETTINGS, JSON.stringify(settings))
    } catch (e) {
      console.warn('localStorage 写入失败:', e)
    }
  }

  /**
   * 获取设置
   * @returns {Object|null}
   */
  static getSettings() {
    try {
      const data = localStorage.getItem(STORAGE_KEYS.SETTINGS)
      return data ? JSON.parse(data) : null
    } catch (e) {
      console.warn('localStorage 读取失败:', e)
      return null
    }
  }

  /**
   * 移除设置
   */
  static removeSettings() {
    try {
      localStorage.removeItem(STORAGE_KEYS.SETTINGS)
    } catch (e) {
      console.warn('localStorage 删除失败:', e)
    }
  }

  /**
   * 清除所有存储
   */
  static clearAll() {
    this.removeToken()
    this.removeUserInfo()
    this.removeSettings()
  }

  /**
   * 过滤敏感字段
   * @param {Object} data 
   * @returns {Object}
   */
  static filterSensitiveFields(data) {
    if (!data || typeof data !== 'object') {
      return data
    }
    
    const sensitiveFields = ['password', 'token', 'secret', 'key', 'credential']
    const result = { ...data }
    
    sensitiveFields.forEach(field => {
      if (field in result) {
        delete result[field]
      }
    })
    
    return result
  }

  /**
   * 检查存储是否可用
   * @returns {Object}
   */
  static checkStorage() {
    const result = {
      localStorage: false,
      sessionStorage: false,
      memoryStorage: true
    }
    
    try {
      const testKey = '__storage_test__'
      localStorage.setItem(testKey, 'test')
      localStorage.removeItem(testKey)
      result.localStorage = true
    } catch (e) {
      result.localStorage = false
    }
    
    try {
      const testKey = '__storage_test__'
      sessionStorage.setItem(testKey, 'test')
      sessionStorage.removeItem(testKey)
      result.sessionStorage = true
    } catch (e) {
      result.sessionStorage = false
    }
    
    return result
  }
}

/**
 * 兼容旧版 API 的包装函数
 * 用于逐步迁移
 */
export const secureStorage = {
  getItem(key) {
    switch (key) {
      case STORAGE_KEYS.TOKEN:
        return SecureStorage.getToken()
      case STORAGE_KEYS.USER_INFO:
        return SecureStorage.getUserInfo()
      case STORAGE_KEYS.SETTINGS:
        return SecureStorage.getSettings()
      default:
        try {
          return localStorage.getItem(key)
        } catch (e) {
          return null
        }
    }
  },

  setItem(key, value) {
    switch (key) {
      case STORAGE_KEYS.TOKEN:
        SecureStorage.setToken(value)
        break
      case STORAGE_KEYS.USER_INFO:
        SecureStorage.setUserInfo(value)
        break
      case STORAGE_KEYS.SETTINGS:
        SecureStorage.setSettings(value)
        break
      default:
        try {
          localStorage.setItem(key, typeof value === 'object' ? JSON.stringify(value) : value)
        } catch (e) {
          console.warn('localStorage 写入失败:', e)
        }
    }
  },

  removeItem(key) {
    switch (key) {
      case STORAGE_KEYS.TOKEN:
        SecureStorage.removeToken()
        break
      case STORAGE_KEYS.USER_INFO:
        SecureStorage.removeUserInfo()
        break
      case STORAGE_KEYS.SETTINGS:
        SecureStorage.removeSettings()
        break
      default:
        try {
          localStorage.removeItem(key)
        } catch (e) {
          console.warn('localStorage 删除失败:', e)
        }
    }
  }
}

export default SecureStorage
