import { get, post, upload, del } from '@/utils/request'
import { STORAGE_KEYS } from '@/utils/constants'
import { ElMessage } from 'element-plus'
import { SecureStorage } from '@/utils/secureStorage'

// 上传合同
export function uploadContract(file, onProgress) {
  return upload('/contract/upload', file, onProgress)
}

// 批量上传合同
export function batchUploadContracts(files, onProgress) {
  const formData = new FormData()
  files.forEach(file => {
    formData.append('files', file)
  })
  return post('/contract/batch-upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: onProgress
  })
}

// 获取合同列表
export function getContractList(params) {
  return get('/contract/list', params)
}

// 获取合同统计数据
export function getContractStats() {
  return get('/contract/stats')
}

// 获取合同详情
export function getContractDetail(id) {
  return get(`/contract/${id}`)
}

// 删除合同
export function deleteContract(id) {
  return del(`/contract/${id}`)
}

// 批量删除合同
export function batchDeleteContracts(ids) {
  return post('/contract/batch-delete', { ids })
}

// 获取合同预览信息
export function getContractPreview(id) {
  return get(`/contract/preview/${id}`)
}

// 获取合同文件URL（用于预览和下载）
export function getContractFileUrl(id) {
  return `${import.meta.env.VITE_API_BASE_URL}/contract/file/${id}`
}

// 获取合同文件Blob（用于带认证的预览）
export async function getContractFileBlob(id) {
  const token = SecureStorage.getToken()
  console.log('getContractFileBlob - token:', token ? '存在' : '不存在')
  if (!token) {
    throw new Error('用户未登录')
  }
  const url = `${import.meta.env.VITE_API_BASE_URL}/contract/file/${id}`
  console.log('getContractFileBlob - url:', url)
  const response = await fetch(url, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  })
  console.log('getContractFileBlob - response status:', response.status)
  if (!response.ok) {
    if (response.status === 401) {
      throw new Error('登录已过期，请重新登录')
    }
    throw new Error('获取文件失败')
  }
  return await response.blob()
}

// 下载合同文件
export function downloadContract(id, filename) {
  ElMessage.info('文件正在下载中...')
  return get(`/contract/download/${id}`, {}, {
    responseType: 'blob'
  }).then(blob => {
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(link.href)
    ElMessage.success('文件下载完成')
  }).catch(error => {
    ElMessage.error('文件下载失败')
    throw error
  })
}
