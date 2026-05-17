import { ref, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import { useUserStore } from '@/stores/user'
import { STORAGE_KEYS } from '@/utils/constants'
import { ElMessage, ElMessageBox } from 'element-plus'
import { SecureStorage } from '@/utils/secureStorage'

const REFRESH_THRESHOLD = 5 * 60 * 1000
const CHECK_INTERVAL = 60 * 1000

let isRefreshing = false
let refreshSubscribers = []

function subscribeTokenRefresh(callback) {
  refreshSubscribers.push(callback)
}

function onTokenRefreshed(newToken) {
  refreshSubscribers.forEach(cb => cb(newToken))
  refreshSubscribers = []
}

function parseJwtPayload(token) {
  try {
    const parts = token.split('.')
    if (parts.length !== 3) return null
    const payload = parts[1]
    const decoded = atob(payload.replace(/-/g, '+').replace(/_/g, '/'))
    return JSON.parse(decoded)
  } catch {
    return null
  }
}

function getTokenRemainingTime(token) {
  const payload = parseJwtPayload(token)
  if (!payload || !payload.exp) return null
  return payload.exp * 1000 - Date.now()
}

export async function refreshTokenRequest() {
  const token = SecureStorage.getToken()
  if (!token) return null

  const baseURL = import.meta.env.VITE_API_BASE_URL || '/api'
  const response = await axios.post(`${baseURL}/auth/refresh-token`, null, {
    headers: { Authorization: `Bearer ${token}` }
  })

  if (response.data?.code === 200 && response.data?.data?.token) {
    return response.data.data.token
  }
  return null
}

export async function refreshTokenIfNeeded() {
  const token = SecureStorage.getToken()
  if (!token) return false

  const remaining = getTokenRemainingTime(token)
  if (remaining === null || remaining <= 0) return false
  if (remaining > REFRESH_THRESHOLD) return false

  if (isRefreshing) {
    return new Promise(resolve => {
      subscribeTokenRefresh(newToken => {
        resolve(!!newToken)
      })
    })
  }

  isRefreshing = true
  try {
    const newToken = await refreshTokenRequest()
    if (newToken) {
      const userStore = useUserStore()
      userStore.setToken(newToken)
      onTokenRefreshed(newToken)
      console.log('[TokenRefresh] Token已自动刷新，剩余时间:', Math.round(remaining / 1000), '秒')
      return true
    }
    onTokenRefreshed(null)
    return false
  } catch (error) {
    console.error('[TokenRefresh] 刷新Token失败:', error.message)
    onTokenRefreshed(null)
    return false
  } finally {
    isRefreshing = false
  }
}

export async function forceRefreshToken() {
  if (isRefreshing) {
    return new Promise(resolve => {
      subscribeTokenRefresh(newToken => resolve(newToken))
    })
  }

  isRefreshing = true
  try {
    const newToken = await refreshTokenRequest()
    if (newToken) {
      const userStore = useUserStore()
      userStore.setToken(newToken)
      onTokenRefreshed(newToken)
      return newToken
    }
    onTokenRefreshed(null)
    return null
  } catch (error) {
    console.error('[TokenRefresh] 强制刷新Token失败:', error.message)
    onTokenRefreshed(null)
    return null
  } finally {
    isRefreshing = false
  }
}

export function useTokenRefresh() {
  const userStore = useUserStore()
  let timer = null
  let loggedOut = false

  function handleRefreshFailure() {
    if (loggedOut) return
    loggedOut = true

    userStore.logout()
    ElMessageBox.alert(
      '登录已过期，请重新登录',
      '登录提示',
      {
        confirmButtonText: '重新登录',
        showClose: false,
        closeOnClickModal: false,
        closeOnPressEscape: false,
        type: 'warning',
        callback: () => {
          window.location.href = '/login'
        }
      }
    )
  }

  async function checkAndRefresh() {
    if (!userStore.isLoggedIn) return

    const token = SecureStorage.getToken()
    if (!token) return

    const remaining = getTokenRemainingTime(token)
    if (remaining === null) return

    if (remaining <= 0) {
      handleRefreshFailure()
      return
    }

    if (remaining <= REFRESH_THRESHOLD) {
      const success = await refreshTokenIfNeeded()
      if (!success) {
        handleRefreshFailure()
      }
    }
  }

  onMounted(() => {
    checkAndRefresh()
    timer = setInterval(checkAndRefresh, CHECK_INTERVAL)
  })

  onUnmounted(() => {
    if (timer) {
      clearInterval(timer)
      timer = null
    }
  })

  return {
    checkAndRefresh,
    refreshTokenIfNeeded,
    forceRefreshToken
  }
}
