/**
 * 消息格式化工具函数
 * 提供消息内容的格式化处理功能
 */

/**
 * 转义HTML特殊字符，防止XSS攻击
 * @param {string} text - 原始文本
 * @returns {string} 转义后的文本
 */
function escapeHtml(text) {
  if (!text) return ''
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
}

/**
 * 将Markdown格式的粗体转换为HTML strong标签
 * @param {string} text - 原始文本
 * @returns {string} 转换后的文本
 */
function formatBold(text) {
  if (!text) return ''
  return text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
}

/**
 * 将Markdown格式的斜体转换为HTML em标签
 * @param {string} text - 原始文本
 * @returns {string} 转换后的文本
 */
function formatItalic(text) {
  if (!text) return ''
  return text.replace(/\*(.*?)\*/g, '<em>$1</em>')
}

/**
 * 将Markdown格式的标题转换为HTML h标签
 * @param {string} text - 原始文本
 * @returns {string} 转换后的文本
 */
function formatHeaders(text) {
  if (!text) return ''
  return text
    .replace(/^###### (.*$)/gim, '<h6>$1</h6>')
    .replace(/^##### (.*$)/gim, '<h5>$1</h5>')
    .replace(/^#### (.*$)/gim, '<h4>$1</h4>')
    .replace(/^### (.*$)/gim, '<h3>$1</h3>')
    .replace(/^## (.*$)/gim, '<h2>$1</h2>')
    .replace(/^# (.*$)/gim, '<h1>$1</h1>')
}

/**
 * 将Markdown格式的列表转换为HTML列表
 * @param {string} text - 原始文本
 * @returns {string} 转换后的文本
 */
function formatLists(text) {
  if (!text) return ''
  
  // 处理无序列表
  const unorderedListRegex = /(^|\n)((?:\s*[-*+]\s+.*\n?)+)/g
  text = text.replace(unorderedListRegex, (match, prefix, listContent) => {
    const items = listContent
      .split('\n')
      .filter(line => line.trim())
      .map(line => {
        const content = line.replace(/^\s*[-*+]\s+/, '')
        return `<li>${content}</li>`
      })
      .join('')
    return `${prefix}<ul>${items}</ul>`
  })
  
  // 处理有序列表
  const orderedListRegex = /(^|\n)((?:\s*\d+\.\s+.*\n?)+)/g
  text = text.replace(orderedListRegex, (match, prefix, listContent) => {
    const items = listContent
      .split('\n')
      .filter(line => line.trim())
      .map(line => {
        const content = line.replace(/^\s*\d+\.\s+/, '')
        return `<li>${content}</li>`
      })
      .join('')
    return `${prefix}<ol>${items}</ol>`
  })
  
  return text
}

/**
 * 将Markdown格式的表格转换为HTML表格
 * @param {string} text - 原始文本
 * @returns {string} 转换后的文本
 */
function formatTables(text) {
  if (!text) return ''
  
  const tableRegex = /\|(.+)\|\n\|[-\s|:]+\|\n((?:\|.+\|\n?)+)/g
  
  return text.replace(tableRegex, (match, headerRow, bodyRows) => {
    // 处理表头
    const headers = headerRow
      .split('|')
      .filter(cell => cell.trim())
      .map(cell => `<th>${cell.trim()}</th>`)
      .join('')
    
    // 处理表体
    const rows = bodyRows
      .trim()
      .split('\n')
      .filter(row => row.trim())
      .map(row => {
        const cells = row
          .split('|')
          .filter(cell => cell.trim())
          .map(cell => `<td>${cell.trim()}</td>`)
          .join('')
        return `<tr>${cells}</tr>`
      })
      .join('')
    
    return `<table class="markdown-table"><thead><tr>${headers}</tr></thead><tbody>${rows}</tbody></table>`
  })
}

/**
 * 将Markdown格式的代码块转换为HTML
 * @param {string} text - 原始文本
 * @returns {string} 转换后的文本
 */
function formatCodeBlocks(text) {
  if (!text) return ''
  // 处理代码块 ```code```
  return text.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
}

/**
 * 将Markdown格式的行内代码转换为HTML
 * @param {string} text - 原始文本
 * @returns {string} 转换后的文本
 */
function formatInlineCode(text) {
  if (!text) return ''
  return text.replace(/`([^`]+)`/g, '<code>$1</code>')
}

/**
 * 将Markdown格式的分隔线转换为HTML hr
 * @param {string} text - 原始文本
 * @returns {string} 转换后的文本
 */
function formatHorizontalRules(text) {
  if (!text) return ''
  return text.replace(/\n---\n/g, '\n<hr>\n')
}

/**
 * 将换行符转换为HTML br标签
 * @param {string} text - 原始文本
 * @returns {string} 转换后的文本
 */
function formatNewlines(text) {
  if (!text) return ''
  return text.replace(/\n/g, '<br>')
}

/**
 * 格式化消息内容，处理HTML转义和Markdown格式
 * @param {string} content - 原始消息内容
 * @returns {string} 格式化后的HTML内容
 * @example
 * formatMessage('Hello **world**\nNew line')
 * // 返回: 'Hello <strong>world</strong><br>New line'
 */
export function formatMessage(content) {
  if (!content) return ''
  
  // 先转义HTML，防止XSS
  let formatted = escapeHtml(content)
  
  // 处理代码块（需要在其他处理之前）
  formatted = formatCodeBlocks(formatted)
  
  // 处理表格（需要在换行处理之前）
  formatted = formatTables(formatted)
  
  // 处理标题
  formatted = formatHeaders(formatted)
  
  // 处理列表
  formatted = formatLists(formatted)
  
  // 处理行内代码
  formatted = formatInlineCode(formatted)
  
  // 处理粗体
  formatted = formatBold(formatted)
  
  // 处理斜体
  formatted = formatItalic(formatted)
  
  // 处理分隔线
  formatted = formatHorizontalRules(formatted)
  
  // 处理换行（最后处理）
  formatted = formatNewlines(formatted)
  
  return formatted
}

/**
 * 截断文本到指定长度，添加省略号
 * @param {string} text - 原始文本
 * @param {number} maxLength - 最大长度
 * @returns {string} 截断后的文本
 */
export function truncateText(text, maxLength = 100) {
  if (!text || text.length <= maxLength) return text || ''
  return text.substring(0, maxLength) + '...'
}

/**
 * 提取纯文本（去除HTML标签）
 * @param {string} html - HTML内容
 * @returns {string} 纯文本
 */
export function stripHtml(html) {
  if (!html) return ''
  return html.replace(/<[^>]*>/g, '')
}
