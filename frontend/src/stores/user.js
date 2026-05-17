import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { SecureStorage } from '@/utils/secureStorage'

export const useUserStore = defineStore('user', () => {
  // State
  const token = ref(SecureStorage.getToken() || '')
  const userInfo = ref(null)
  const settings = ref({
    theme: 'light',
    language: 'zh-CN',
    notifications: true
  })

  // Getters
  const isLoggedIn = computed(() => !!token.value)
  
  const username = computed(() => userInfo.value?.username || '')

  const nickName = computed(() => userInfo.value?.nickName || '')

  const displayName = computed(() => nickName.value || username.value || '法务专员')

  const avatar = computed(() => userInfo.value?.avatar || '')

  const role = computed(() => userInfo.value?.role || '')

  // Actions
  // 设置 token
  function setToken(newToken) {
    token.value = newToken
    if (newToken) {
      SecureStorage.setToken(newToken)
    } else {
      SecureStorage.removeToken()
    }
  }

  // 设置用户信息
  function setUserInfo(info) {
    userInfo.value = info
    if (info) {
      SecureStorage.setUserInfo(info)
    } else {
      SecureStorage.removeUserInfo()
    }
  }

  // 加载本地存储的用户信息
  function loadUserFromStorage() {
    // 加载 Token（从 SecureStorage）
    const storedToken = SecureStorage.getToken()
    if (storedToken) {
      token.value = storedToken
    }
    
    // 加载用户信息
    const storedUser = SecureStorage.getUserInfo()
    if (storedUser) {
      userInfo.value = storedUser
    }
    
    // 加载设置
    const storedSettings = SecureStorage.getSettings()
    if (storedSettings) {
      settings.value = { ...settings.value, ...storedSettings }
    }
  }

  // 更新设置
  function updateSettings(newSettings) {
    settings.value = { ...settings.value, ...newSettings }
    SecureStorage.setSettings(settings.value)
  }

  // 登出
  function logout() {
    setToken('')
    setUserInfo(null)
  }

  return {
    // State
    token,
    userInfo,
    settings,
    // Getters
    isLoggedIn,
    username,
    nickName,
    displayName,
    avatar,
    role,
    // Actions
    setToken,
    setUserInfo,
    loadUserFromStorage,
    updateSettings,
    logout
  }
})
