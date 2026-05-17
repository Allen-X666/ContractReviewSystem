/**
 * 文件预览组件库
 * 提供统一的文件预览功能
 */

export { default as FilePreviewDialog } from './FilePreviewDialog.vue'
export { default as PdfPreview } from './PdfPreview.vue'
export { default as DocxPreview } from './DocxPreview.vue'
export { default as TxtPreview } from './TxtPreview.vue'

// 文件预览工具函数
export {
  previewFile,
  closePreview,
  getFileType,
  isPreviewable,
  formatFileSize
} from '@/utils/filePreview'

// 组合式函数
export {
  useFilePreview,
  getFileType as useGetFileType,
  isPreviewable as useIsPreviewable,
  formatFileSize as useFormatFileSize
} from '@/composables/useFilePreview'
