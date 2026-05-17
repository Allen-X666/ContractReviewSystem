/**
 * 简单的Markdown解析器
 * 支持基本的Markdown语法：标题、加粗、斜体、链接、列表、代码块等
 */

/**
 * 检测文本是否包含Markdown语法
 * @param {string} text - 要检测的文本
 * @returns {boolean} - 是否包含Markdown
 */
export function isMarkdown(text) {
  if (!text || typeof text !== 'string') return false
  
  // Markdown特征模式
  const markdownPatterns = [
    /#{1,6}\s+/,           // 标题
    /\*\*.*?\*\*/,         // 加粗
    /\*.*?\*/,             // 斜体
    /`.*?`/,               // 行内代码
    /```[\s\S]*?```/,      // 代码块
    /\[.*?\]\(.*?\)/,      // 链接
    /^\s*[-*+]\s+/m,       // 无序列表
    /^\s*\d+\.\s+/m,        // 有序列表
    /^\s*>\s+/m,           // 引用
    /___|___|\*\*\*/,      // 分隔线
  ]
  
  return markdownPatterns.some(pattern => pattern.test(text))
}

/**
 * 将Markdown转换为HTML
 * @param {string} markdown - Markdown文本
 * @returns {string} - HTML字符串
 */
export function markdownToHtml(markdown) {
  if (!markdown || typeof markdown !== 'string') return ''
  
  let html = markdown
  
  // 转义HTML特殊字符
  html = html.replace(/&/g, '&amp;')
             .replace(/</g, '&lt;')
             .replace(/>/g, '&gt;')
  
  // 代码块 (```code```)
  html = html.replace(/```([\s\S]*?)```/g, '<pre class="markdown-code-block"><code>$1</code></pre>')
  
  // 行内代码 (`code`)
  html = html.replace(/`([^`]+)`/g, '<code class="markdown-inline-code">$1</code>')
  
  // 标题 (### Title)
  html = html.replace(/^######\s+(.*$)/gim, '<h6>$1</h6>')
             .replace(/^#####\s+(.*$)/gim, '<h5>$1</h5>')
             .replace(/^####\s+(.*$)/gim, '<h4>$1</h4>')
             .replace(/^###\s+(.*$)/gim, '<h3>$1</h3>')
             .replace(/^##\s+(.*$)/gim, '<h2>$1</h2>')
             .replace(/^#\s+(.*$)/gim, '<h1>$1</h1>')
  
  // 加粗 (**text**)
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
  
  // 斜体 (*text*)
  html = html.replace(/\*(.*?)\*/g, '<em>$1</em>')
  
  // 删除线 (~~text~~)
  html = html.replace(/~~(.*?)~~/g, '<del>$1</del>')
  
  // 链接 ([text](url))
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>')
  
  // 无序列表
  html = html.replace(/^\s*[-*+]\s+(.*$)/gim, '<li class="markdown-list-item">$1</li>')
  html = html.replace(/(<li class="markdown-list-item">.*<\/li>\n?)+/g, '<ul class="markdown-list">$&</ul>')
  
  // 有序列表
  html = html.replace(/^\s*\d+\.\s+(.*$)/gim, '<li class="markdown-ordered-item">$1</li>')
  html = html.replace(/(<li class="markdown-ordered-item">.*<\/li>\n?)+/g, '<ol class="markdown-ordered-list">$&</ol>')
  
  // 引用 (> text)
  html = html.replace(/^\s*>\s+(.*$)/gim, '<blockquote class="markdown-quote">$1</blockquote>')
  
  // 分隔线
  html = html.replace(/^\s*___\s*$/gim, '<hr class="markdown-hr">')
             .replace(/^\s*---\s*$/gim, '<hr class="markdown-hr">')
             .replace(/^\s*\*\*\*\s*$/gim, '<hr class="markdown-hr">')
  
  // 段落和换行
  html = html.replace(/\n\n/g, '</p><p>')
             .replace(/\n/g, '<br>')
  
  // 包装在段落中
  if (!html.startsWith('<')) {
    html = '<p>' + html + '</p>'
  }
  
  return html
}

/**
 * 处理公告内容，自动检测并转换Markdown
 * @param {string} content - 公告内容
 * @returns {string} - 处理后的HTML
 */
export function processAnnouncementContent(content) {
  if (!content) return ''
  
  // 检测是否为Markdown格式
  if (isMarkdown(content)) {
    return markdownToHtml(content)
  }
  
  // 普通文本，直接返回（保持原有换行）
  return content.replace(/\n/g, '<br>')
}
