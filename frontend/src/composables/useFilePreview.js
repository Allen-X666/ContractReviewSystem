import { ref } from 'vue'

/**
 * 文件预览组合式函数
 * 提供统一的文件预览功能
 * 
 * 使用示例：
 * const { previewFile, previewDialogRef } = useFilePreview()
 * 
 * // 在模板中使用
 * <FilePreviewDialog ref="previewDialogRef" />
 * 
 * // 调用预览
 * previewFile(fileUrl, fileName)
 * previewFile(fileBlob, fileName, fileType)
 */
export function useFilePreview() {
  const previewDialogRef = ref(null)

  /**
   * 预览文件
   * @param {string|Blob} source - 文件URL或Blob对象
   * @param {string} fileName - 文件名（用于识别文件类型）
   * @param {string} [fileType] - 可选，强制指定文件类型
   */
  const previewFile = (source, fileName, fileType = null) => {
    if (!previewDialogRef.value) {
      console.error('[useFilePreview] FilePreviewDialog 组件未挂载')
      return
    }

    // 自动检测文件类型
    const type = fileType || getFileType(fileName)
    
    if (!type) {
      console.warn('[useFilePreview] 无法识别文件类型:', fileName)
    }

    previewDialogRef.value.open(source, fileName, type)
  }

  /**
   * 关闭预览
   */
  const closePreview = () => {
    if (previewDialogRef.value) {
      previewDialogRef.value.close()
    }
  }

  return {
    previewDialogRef,
    previewFile,
    closePreview
  }
}

/**
 * 获取文件类型
 * @param {string} fileName - 文件名
 * @returns {string|null} 文件类型
 */
export function getFileType(fileName) {
  if (!fileName) return null
  
  const ext = fileName.split('.').pop()?.toLowerCase()
  
  const typeMap = {
    // PDF
    'pdf': 'pdf',
    
    // Word 文档
    'doc': 'docx',
    'docx': 'docx',
    
    // 文本文件
    'txt': 'txt',
    'text': 'txt',
    'md': 'txt',
    'markdown': 'txt',
    'json': 'txt',
    'xml': 'txt',
    'yaml': 'txt',
    'yml': 'txt',
    'ini': 'txt',
    'conf': 'txt',
    'log': 'txt',
    'csv': 'txt',
    'tsv': 'txt',
    
    // 代码文件
    'js': 'txt',
    'ts': 'txt',
    'jsx': 'txt',
    'tsx': 'txt',
    'vue': 'txt',
    'html': 'txt',
    'htm': 'txt',
    'css': 'txt',
    'scss': 'txt',
    'sass': 'txt',
    'less': 'txt',
    'py': 'txt',
    'java': 'txt',
    'c': 'txt',
    'cpp': 'txt',
    'h': 'txt',
    'hpp': 'txt',
    'cs': 'txt',
    'php': 'txt',
    'rb': 'txt',
    'go': 'txt',
    'rs': 'txt',
    'swift': 'txt',
    'kt': 'txt',
    'sql': 'txt',
    'sh': 'txt',
    'bash': 'txt',
    'zsh': 'txt',
    'ps1': 'txt',
    'bat': 'txt',
    'cmd': 'txt'
  }
  
  return typeMap[ext] || null
}

/**
 * 检查文件是否可预览
 * @param {string} fileName - 文件名
 * @returns {boolean}
 */
export function isPreviewable(fileName) {
  return getFileType(fileName) !== null
}

/**
 * 获取文件图标
 * @param {string} fileName - 文件名
 * @returns {string} 图标类名
 */
export function getFileIcon(fileName) {
  const type = getFileType(fileName)
  
  const iconMap = {
    'pdf': 'Document',
    'docx': 'Document',
    'txt': 'Document-Copy'
  }
  
  return iconMap[type] || 'Document'
}

/**
 * 格式化文件大小
 * @param {number} bytes - 字节数
 * @returns {string}
 */
export function formatFileSize(bytes) {
  if (bytes === 0 || bytes == null) return '0 B'
  
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}
