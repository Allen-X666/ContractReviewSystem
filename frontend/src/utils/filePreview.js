import { createApp, h } from 'vue'
import FilePreviewDialog from '@/components/preview/FilePreviewDialog.vue'

/**
 * 文件预览服务
 * 提供全局文件预览功能，无需在组件中引入对话框组件
 * 
 * 使用示例：
 * import { previewFile } from '@/utils/filePreview'
 * 
 * // 预览文件
 * previewFile(fileUrl, '合同.pdf')
 * previewFile(fileBlob, '文档.docx')
 */

let previewInstance = null
let previewApp = null

/**
 * 创建预览对话框实例
 */
function createPreviewInstance() {
  if (previewInstance) return previewInstance

  // 创建容器
  const container = document.createElement('div')
  container.id = 'global-file-preview-container'
  document.body.appendChild(container)

  // 创建 Vue 应用实例
  previewApp = createApp({
    render() {
      return h(FilePreviewDialog, {
        ref: 'dialogRef'
      })
    }
  })

  // 挂载应用
  const vm = previewApp.mount(container)
  previewInstance = vm.$refs.dialogRef

  return previewInstance
}

/**
 * 销毁预览实例
 */
function destroyPreviewInstance() {
  if (previewApp) {
    previewApp.unmount()
    previewApp = null
  }
  if (previewInstance) {
    previewInstance = null
  }
  const container = document.getElementById('global-file-preview-container')
  if (container) {
    document.body.removeChild(container)
  }
}

/**
 * 预览文件
 * @param {string|Blob} source - 文件URL或Blob对象
 * @param {string} fileName - 文件名
 * @param {string} [fileType] - 可选，强制指定文件类型
 */
export function previewFile(source, fileName, fileType = null) {
  const dialog = createPreviewInstance()
  
  if (!dialog) {
    console.error('[filePreview] 无法创建预览对话框')
    return
  }

  // 自动检测文件类型
  const type = fileType || getFileType(fileName)
  
  dialog.open(source, fileName, type)
}

/**
 * 关闭预览
 */
export function closePreview() {
  if (previewInstance) {
    previewInstance.close()
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

// 清理函数（可选，在应用卸载时调用）
export function cleanup() {
  destroyPreviewInstance()
}
