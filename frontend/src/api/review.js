import { get, post, del } from '@/utils/request'
import { STORAGE_KEYS } from '@/utils/constants'
import { SecureStorage } from '@/utils/secureStorage'

// 发起审查 - 通过 SpringBoot 转发到 FastAPI
export async function startReview(contractId, fileBlob, fileName, options = {}) {
  const formData = new FormData()
  formData.append('contractId', contractId)

  if (fileBlob && fileName) {
    formData.append('file', fileBlob, fileName)
  }

  const reviewOptions = {
    checkInvalidClause: options.checkInvalidClause ?? true,
    checkMissingClause: options.checkMissingClause ?? true,
    checkUnreasonableClause: options.checkUnreasonableClause ?? true,
    checkLegalRisk: options.checkLegalRisk ?? true
  }
  formData.append('reviewOptions', JSON.stringify(reviewOptions))

  return post('/review/start', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}



// 获取审查进度 - 使用 SSE EventSource 连接后端 SSE 接口
export function connectReviewProgress(reviewId, onMessage, onError) {
  try {
    // 检查 EventSource 是否可用
    if (typeof EventSource === 'undefined') {
      console.error('[API] EventSource 不被浏览器支持')
      onError?.(new Error('浏览器不支持 EventSource'))
      return { close: () => {} }
    }

    const baseURL = import.meta.env.VITE_API_BASE_URL || '/api'
    const token = SecureStorage.getToken()
    
    // 确保 reviewId 是数字类型
    const numericReviewId = parseInt(reviewId, 10)
    console.log('[API] connectReviewProgress - 原始 reviewId:', reviewId, '转换后:', numericReviewId, 'token exists:', !!token)
    
    // 构建 SSE URL，将 token 作为查询参数传递
    // 移除 Bearer 前缀（如果存在）
    const cleanToken = token ? token.replace('Bearer ', '') : ''
    const sseUrl = `${baseURL}/review/${numericReviewId}/progress?token=${encodeURIComponent(cleanToken)}`
    console.log('[API] SSE URL:', sseUrl.replace(cleanToken, '***'))
    
    // 创建 EventSource 连接
    console.log('[API] 正在创建 EventSource...')
    let eventSource
    try {
      eventSource = new EventSource(sseUrl)
    } catch (e) {
      console.error('[API] 创建 EventSource 失败:', e)
      onError?.(e)
      return { close: () => {} }
    }
    console.log('[API] EventSource 创建成功, readyState:', eventSource.readyState)
  
  // 监听进度事件
  eventSource.addEventListener('progress', (event) => {
    try {
      const data = JSON.parse(event.data)
      console.log('[API] SSE progress event:', data)
      onMessage(data)
      
      // 审查完成或失败时关闭连接
      if (data.status === 'completed' || data.status === 'failed') {
        eventSource.close()
      }
    } catch (error) {
      console.error('[API] 解析 SSE 数据失败:', error, event.data)
      onError?.(error)
    }
  })
  
  // 监听错误事件
  eventSource.addEventListener('error', (event) => {
    console.error('[API] SSE error event:', event)
    onError?.(new Error('SSE 连接错误'))
  })
  
  // 监听连接打开
  eventSource.onopen = () => {
    console.log('[API] SSE 连接已建立')
  }
  
  // 监听连接错误
  eventSource.onerror = (error) => {
    console.error('[API] SSE 连接错误:', error)
    onError?.(error)
    
    // 如果连接已关闭且不是正常完成，则尝试重连
    if (eventSource.readyState === EventSource.CLOSED) {
      console.log('[API] SSE 连接已关闭')
    }
  }
  
  // 返回控制对象
  return {
    close: () => {
      console.log('[API] 关闭 SSE 连接')
      eventSource.close()
    }
  }
  } catch (error) {
    console.error('[API] connectReviewProgress 发生错误:', error)
    onError?.(error)
    return {
      close: () => {
        console.log('[API] 关闭 SSE 连接（创建失败）')
      }
    }
  }
}

// 获取审查结果 - 通过 SpringBoot 转发到 FastAPI
export function getReviewResult(reviewId) {
  return get(`/review/${reviewId}/result`)
}

// 获取审查报告 PDF - 用于下载或预览 PDF
export function getReviewReportPdf(reviewId) {
  return get(`/review/${reviewId}/report/view`, {}, { responseType: 'blob' })
}

// 获取风险列表 - 通过 SpringBoot
export function getRiskList(reviewId, params = {}) {
  return get(`/review/${reviewId}/risks`, params)
}

// 获取审查历史 - 通过 SpringBoot
export function getReviewHistory(params) {
  return get('/review/history', params)
}

// 重新审查 - 通过 SpringBoot 转发到 FastAPI
export async function reReview(reviewId, contractId, fileBlob, fileName, options = {}) {
  const formData = new FormData()
  formData.append('contractId', contractId)

  if (fileBlob && fileName) {
    formData.append('file', fileBlob, fileName)
  }

  const reviewOptions = {
    checkInvalidClause: options.checkInvalidClause ?? true,
    checkMissingClause: options.checkMissingClause ?? true,
    checkUnreasonableClause: options.checkUnreasonableClause ?? true,
    checkLegalRisk: options.checkLegalRisk ?? true
  }
  formData.append('reviewOptions', JSON.stringify(reviewOptions))

  return post(`/review/${reviewId}/re-review`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

// 取消审查 - 通过 SpringBoot 转发到 FastAPI
export function cancelReview(reviewId) {
  return post(`/review/${reviewId}/cancel`)
}

// 获取审查历史统计 - 通过 SpringBoot
export function getReviewHistoryStats() {
  return get('/review/history/stats')
}

// 根据合同ID获取最新的审查记录 - 通过 SpringBoot
export function getLatestReviewByContractId(contractId) {
  return get(`/review/contract/${contractId}/latest`)
}

// 删除审查记录 - 通过 SpringBoot
export function deleteReview(reviewId) {
  return del(`/review/${reviewId}`)
}
