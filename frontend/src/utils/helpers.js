import dayjs from 'dayjs'
import { RISK_LEVEL_COLOR, RISK_LEVEL_TEXT, REVIEW_STATUS_TEXT } from './constants'

// 格式化日期
export function formatDate(date, format = 'YYYY-MM-DD HH:mm:ss') {
  if (!date) return '-'
  return dayjs(date).format(format)
}

export function formatDateShort(date) {
  return formatDate(date, 'YYYY-MM-DD')
}

// 格式化文件大小
export function formatFileSize(bytes) {
  if (!bytes || bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 获取文件图标
export function getFileIcon(filename) {
  if (!filename) return 'Document'
  const ext = filename.split('.').pop()?.toLowerCase()
  const iconMap = {
    pdf: 'Document',
    docx: 'Document',
    doc: 'Document'
  }
  return iconMap[ext] || 'Document'
}

// 验证文件类型
export function validateFileType(file, acceptTypes) {
  const ext = '.' + file.name.split('.').pop()?.toLowerCase()
  return acceptTypes.includes(ext)
}

// 验证文件大小
export function validateFileSize(file, maxSize) {
  return file.size <= maxSize
}

// 生成唯一ID
export function generateId() {
  return Date.now().toString(36) + Math.random().toString(36).substr(2)
}

// 深拷贝
export function deepClone(obj) {
  if (obj === null || typeof obj !== 'object') return obj
  if (obj instanceof Date) return new Date(obj.getTime())
  if (Array.isArray(obj)) return obj.map(item => deepClone(item))
  const cloned = {}
  for (const key in obj) {
    if (obj.hasOwnProperty(key)) {
      cloned[key] = deepClone(obj[key])
    }
  }
  return cloned
}

// 防抖
export function debounce(fn, delay = 300) {
  let timer = null
  return function (...args) {
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => {
      fn.apply(this, args)
    }, delay)
  }
}

// 节流
export function throttle(fn, limit = 300) {
  let inThrottle
  return function (...args) {
    if (!inThrottle) {
      fn.apply(this, args)
      inThrottle = true
      setTimeout(() => inThrottle = false, limit)
    }
  }
}

// 下载文件
export function downloadFile(url, filename) {
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

// 复制到剪贴板
export async function copyToClipboard(text) {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch (err) {
    console.error('复制失败:', err)
    return false
  }
}

// 获取风险等级样式
export function getRiskLevelStyle(level) {
  return {
    color: RISK_LEVEL_COLOR[level],
    backgroundColor: RISK_LEVEL_COLOR[level] + '15',
    borderColor: RISK_LEVEL_COLOR[level] + '30'
  }
}

// 计算总体评分
export function calculateOverallScore(risks) {
  if (!risks || risks.length === 0) return 100
  
  const weights = {
    high: 15,
    medium: 8,
    low: 3
  }
  
  let totalDeduction = 0
  risks.forEach(risk => {
    totalDeduction += weights[risk.level] || 0
  })
  
  return Math.max(0, 100 - totalDeduction)
}

// 格式化审查状态
export function formatReviewStatus(status) {
  if (!status || status === '') {
    return '-'
  }
  return REVIEW_STATUS_TEXT[status] || status
}

// 格式化风险等级
export function formatRiskLevel(level) {
  if (!level || level === '') {
    return '-'
  }
  return RISK_LEVEL_TEXT[level] || level
}

// 截断文本
export function truncateText(text, maxLength = 100) {
  if (!text || text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

// 高亮关键词
export function highlightKeyword(text, keyword) {
  if (!text || !keyword) return text
  const regex = new RegExp(`(${keyword})`, 'gi')
  return text.replace(regex, '<mark>$1</mark>')
}

// 平滑滚动到元素
export function scrollToElement(element, offset = 80) {
  if (!element) return
  const top = element.getBoundingClientRect().top + window.pageYOffset - offset
  window.scrollTo({ top, behavior: 'smooth' })
}
