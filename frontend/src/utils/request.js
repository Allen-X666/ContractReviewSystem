import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import { SecureStorage } from './secureStorage'

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json'
  }
})

const pendingRequests = new Map()

let isRefreshing = false
let refreshSubscribers = []

function subscribeTokenRefresh(callback) {
  refreshSubscribers.push(callback)
}

function onTokenRefreshed(newToken) {
  refreshSubscribers.forEach(callback => callback(newToken))
  refreshSubscribers = []
}

function generateRequestKey(config) {
  return `${config.method}_${config.url}_${JSON.stringify(config.params)}_${JSON.stringify(config.data)}`
}

function addPendingRequest(config) {
  const key = generateRequestKey(config)
  config.cancelToken = config.cancelToken || new axios.CancelToken(cancel => {
    if (!pendingRequests.has(key)) {
      pendingRequests.set(key, cancel)
    }
  })
}

function removePendingRequest(config) {
  const key = generateRequestKey(config)
  if (pendingRequests.has(key)) {
    const cancel = pendingRequests.get(key)
    cancel('取消重复请求')
    pendingRequests.delete(key)
  }
}

function handleTokenExpired(message) {
  SecureStorage.removeToken()

  ElMessageBox.alert(
    message || '登录已过期，请重新登录',
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

async function doRefreshToken() {
  const token = SecureStorage.getToken()
  if (!token) throw new Error('没有token')

  const baseURL = import.meta.env.VITE_API_BASE_URL || '/api'
  const response = await axios.post(`${baseURL}/auth/refresh-token`, null, {
    headers: { Authorization: `Bearer ${token}` }
  })

  if (response.data?.code === 200 && response.data?.data?.token) {
    return response.data.data.token
  }
  throw new Error('刷新失败')
}

request.interceptors.request.use(
  config => {
    removePendingRequest(config)
    addPendingRequest(config)

    const token = SecureStorage.getToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }

    if (config.headers['Content-Type'] === 'multipart/form-data') {
      delete config.headers['Content-Type']
    }

    return config
  },
  error => {
    return Promise.reject(error)
  }
)

request.interceptors.response.use(
  response => {
    removePendingRequest(response.config)

    const refreshedToken = response.headers['x-refresh-token']
    if (refreshedToken) {
      SecureStorage.setToken(refreshedToken)
      onTokenRefreshed(refreshedToken)
    }

    if (response.config.responseType === 'blob') {
      return response.data
    }

    const { code, message, data } = response.data

    if (code === 200) {
      return response.data
    }

    ElMessage.error(message || '请求失败')
    return Promise.reject(new Error(message))
  },
  async error => {
    if (error.config) {
      removePendingRequest(error.config)
    }

    if (axios.isCancel(error)) {
      return Promise.reject(error)
    }

    const { response } = error

    if (response) {
      const { status, data } = response
      const { config: originalConfig } = error

      if (originalConfig?.responseType === 'blob' && data instanceof Blob) {
        return Promise.reject(new Error(`请求失败 (${status}): 无法获取文件`))
      }

      if (status === 401 && !originalConfig._isRetry) {
        if (isRefreshing) {
          return new Promise(resolve => {
            subscribeTokenRefresh(newToken => {
              if (newToken) {
                originalConfig.headers.Authorization = `Bearer ${newToken}`
                originalConfig._isRetry = true
                resolve(request(originalConfig))
              } else {
                resolve(Promise.reject(error))
              }
            })
          })
        }

        isRefreshing = true
        try {
          const newToken = await doRefreshToken()
          SecureStorage.setToken(newToken)
          onTokenRefreshed(newToken)

          originalConfig.headers.Authorization = `Bearer ${newToken}`
          originalConfig._isRetry = true
          return request(originalConfig)
        } catch (refreshError) {
          onTokenRefreshed(null)
          handleTokenExpired(data?.message)
          return Promise.reject(refreshError)
        } finally {
          isRefreshing = false
        }
      }

      switch (status) {
        case 403:
          ElMessage.error('没有权限执行此操作')
          break
        case 404:
          ElMessage.error('请求的资源不存在')
          break
        case 500:
          ElMessage.error(data?.message || '服务器内部错误')
          break
        default:
          ElMessage.error(data?.message || `请求失败 (${status})`)
      }
    } else {
      ElMessage.error('网络连接异常，请检查网络')
    }

    return Promise.reject(error)
  }
)

export function get(url, params = {}, config = {}) {
  return request.get(url, { params, ...config })
}

export function post(url, data = {}, config = {}) {
  return request.post(url, data, config)
}

export function put(url, data = {}, config = {}) {
  return request.put(url, data, config)
}

export function del(url, config = {}) {
  return request.delete(url, config)
}

export function upload(url, file, onProgress, config = {}) {
  const formData = new FormData()
  formData.append('file', file)

  return request.post(url, formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    },
    onUploadProgress: (progressEvent) => {
      if (onProgress && progressEvent.total) {
        const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total)
        onProgress(percent)
      }
    },
    ...config
  })
}

export function download(url, params = {}, filename, config = {}) {
  return request.get(url, {
    params,
    responseType: 'blob',
    ...config
  }).then(blob => {
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(link.href)
  })
}

export default request
