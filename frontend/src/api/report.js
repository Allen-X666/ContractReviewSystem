import { get, post } from '@/utils/request'
import { ElMessage } from 'element-plus'

// 生成报告
export function generateReport(reviewId, options = {}) {
  return post('/report/generate', {
    reviewId,
    ...options
  })
}

// 获取报告详情
export function getReportDetail(reportId) {
  return get(`/report/${reportId}`)
}

// 导出 Word 报告
export function exportWordReport(reportId, filename) {
  ElMessage.info('文件正在下载中...')
  return get(`/report/${reportId}/export/word`, {}, {
    responseType: 'blob'
  }).then(blob => {
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = filename || `审查报告_${reportId}.docx`
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

// 导出 PDF 报告
export function exportPdfReport(reviewId, filename) {
  ElMessage.info('文件正在下载中...')
  return get(`/review/${reviewId}/report/pdf`, {}, {
    responseType: 'blob'
  }).then(response => {
    const blob = response.data || response
    const headers = response.headers || {}
    
    // 从Content-Disposition头中提取文件名
    let downloadFilename = filename
    if (!downloadFilename) {
      const contentDisposition = headers['content-disposition']
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/)
        if (filenameMatch) {
          downloadFilename = filenameMatch[1]
        }
      }
      if (!downloadFilename) {
        downloadFilename = `审查报告_${reviewId}.pdf`
      }
    }
    
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = downloadFilename
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

// 获取报告列表
export function getReportList(params) {
  return get('/report/list', params)
}

// 删除报告
export function deleteReport(reportId) {
  return post(`/report/${reportId}/delete`)
}
