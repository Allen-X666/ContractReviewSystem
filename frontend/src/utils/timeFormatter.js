/**
 * 时间格式化工具函数
 * 提供时间戳的格式化和处理功能
 */

/**
 * 检查给定日期是否为今天
 * @param {Date} date - 要检查的日期
 * @returns {boolean} 是否为今天
 */
function isToday(date) {
  const now = new Date()
  return date.toDateString() === now.toDateString()
}

/**
 * 检查给定日期是否为昨天
 * @param {Date} date - 要检查的日期
 * @returns {boolean} 是否为昨天
 */
function isYesterday(date) {
  const now = new Date()
  const yesterday = new Date(now)
  yesterday.setDate(yesterday.getDate() - 1)
  return date.toDateString() === yesterday.toDateString()
}

/**
 * 格式化时间为 HH:mm 格式
 * @param {Date} date - 日期对象
 * @returns {string} 格式化后的时间字符串
 */
function formatTimeOnly(date) {
  return date.toLocaleTimeString('zh-CN', { 
    hour: '2-digit', 
    minute: '2-digit' 
  })
}

/**
 * 格式化日期为 MM-dd 格式
 * @param {Date} date - 日期对象
 * @returns {string} 格式化后的日期字符串
 */
function formatDateOnly(date) {
  return date.toLocaleDateString('zh-CN', { 
    month: '2-digit', 
    day: '2-digit' 
  })
}

/**
 * 格式化时间戳为易读的时间格式
 * - 今天：显示 HH:mm
 * - 昨天：显示 "昨天 HH:mm"
 * - 其他：显示 MM-dd HH:mm
 * @param {number|string|Date} timestamp - 时间戳或日期对象
 * @returns {string} 格式化后的时间字符串
 * @example
 * formatTime(Date.now()) // '14:30'
 * formatTime(1640995200000) // '01-01 00:00'
 */
export function formatTime(timestamp) {
  if (!timestamp) return ''
  
  const date = timestamp instanceof Date ? timestamp : new Date(timestamp)
  
  if (isNaN(date.getTime())) {
    return ''
  }
  
  const time = formatTimeOnly(date)
  
  if (isToday(date)) {
    return time
  }
  
  if (isYesterday(date)) {
    return `昨天 ${time}`
  }
  
  return `${formatDateOnly(date)} ${time}`
}

/**
 * 格式化日期为完整格式
 * @param {number|string|Date} timestamp - 时间戳或日期对象
 * @returns {string} 格式化后的日期时间字符串
 * @example
 * formatDateTime(Date.now()) // '2024年01月01日 14:30'
 */
export function formatDateTime(timestamp) {
  if (!timestamp) return ''
  
  const date = timestamp instanceof Date ? timestamp : new Date(timestamp)
  
  if (isNaN(date.getTime())) {
    return ''
  }
  
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

/**
 * 格式化相对时间（几分钟前、几小时前等）
 * @param {number|string|Date} timestamp - 时间戳或日期对象
 * @returns {string} 相对时间字符串
 * @example
 * formatRelativeTime(Date.now() - 60000) // '1分钟前'
 */
export function formatRelativeTime(timestamp) {
  if (!timestamp) return ''
  
  const date = timestamp instanceof Date ? timestamp : new Date(timestamp)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  const minute = 60 * 1000
  const hour = 60 * minute
  const day = 24 * hour
  
  if (diff < minute) {
    return '刚刚'
  }
  
  if (diff < hour) {
    const minutes = Math.floor(diff / minute)
    return `${minutes}分钟前`
  }
  
  if (diff < day) {
    const hours = Math.floor(diff / hour)
    return `${hours}小时前`
  }
  
  if (diff < 7 * day) {
    const days = Math.floor(diff / day)
    return `${days}天前`
  }
  
  return formatDateOnly(date)
}
