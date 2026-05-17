import { get, put, del, post } from '@/utils/request'

/**
 * 获取用户列表
 * @param {Object} params - 查询参数
 * @param {number} params.pageNum - 页码，默认1
 * @param {number} params.pageSize - 每页大小，默认10
 * @returns {Promise<{code: number, message: string, data: {list: Array, total: number, pageNum: number, pageSize: number}}>}
 */
export function getUserList(params = {}) {
  return get('/admin/users', params)
}

/**
 * 编辑用户信息
 * @param {number} id - 用户ID
 * @param {Object} data - 用户数据
 * @param {string} data.username - 用户名
 * @param {string} data.nickName - 昵称
 * @param {string} data.email - 邮箱
 * @param {string} data.phone - 手机号
 * @param {string} data.role - 角色 (admin/user)
 * @returns {Promise<{code: number, message: string, data: string}>}
 */
export function updateUser(id, data) {
  return put(`/admin/users/${id}`, data)
}

/**
 * 更新用户状态（启用/禁用）
 * @param {number} id - 用户ID
 * @param {string} status - 状态 (ENABLED-启用，DISABLED-禁用)
 * @returns {Promise<{code: number, message: string, data: string}>}
 */
export function updateUserStatus(id, status) {
  return put(`/admin/users/${id}/status?status=${status}`)
}

/**
 * 删除用户
 * @param {number} id - 用户ID
 * @returns {Promise<{code: number, message: string, data: string}>}
 */
export function deleteUser(id) {
  return del(`/admin/users/${id}`)
}

/**
 * 上传法律文档
 * @param {FormData} formData - 表单数据，包含 file, type, effectiveDate, description
 * @returns {Promise<{code: number, message: string, data: Object}>}
 */
export function uploadLawDocument(formData) {
  return post('/admin/law/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

/**
 * 获取法律文档列表
 * @returns {Promise<{code: number, message: string, data: Array}>}
 */
export function getLawDocumentList() {
  return get('/admin/law/list')
}

/**
 * 删除法律文档
 * @param {number} id - 文档ID
 * @returns {Promise<{code: number, message: string, data: string}>}
 */
export function deleteLawDocument(id) {
  return del(`/admin/law/${id}`)
}

/**
 * 获取法律文档文件
 * @param {number} id - 文档ID
 * @returns {Promise<Blob>} - 文件Blob
 */
export function getLawDocumentFile(id) {
  return get(`/admin/law/${id}/file`, {
    responseType: 'blob'
  })
}

/**
 * 发布公告
 * @param {Object} data - 公告数据 {title, type, content, publishType, publishTime, isTop}
 * @returns {Promise<{code: number, message: string, data: Object}>}
 */
export function publishNotice(data) {
  return post('/admin/announcement', data)
}

/**
 * 获取公告列表
 * @returns {Promise<{code: number, message: string, data: Array}>}
 */
export function getNoticeList() {
  return get('/admin/announcement/list')
}

/**
 * 编辑公告
 * @param {number} id - 公告ID
 * @param {Object} data - 公告数据
 * @returns {Promise<{code: number, message: string, data: string}>}
 */
export function editNotice(id, data) {
  return put(`/admin/announcement/${id}`, data)
}

/**
 * 删除公告
 * @param {number} id - 公告ID
 * @returns {Promise<{code: number, message: string, data: string}>}
 */
export function deleteNotice(id) {
  return del(`/admin/announcement/${id}`)
}

/**
 * 置顶/取消置顶公告
 * @param {number} id - 公告ID
 * @param {boolean} isTop - 是否置顶
 * @returns {Promise<{code: number, message: string, data: string}>}
 */
export function toggleNoticeTop(id, isTop) {
  return put(`/admin/announcement/${id}/top`, { isTop })
}

/**
 * 上传系统文档
 * @param {FormData} formData - 表单数据，包含 file, category, tags, description
 * @returns {Promise<{code: number, message: string, data: Object}>}
 */
export function uploadSystemDocument(formData) {
  return post('/admin/system-docs/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

/**
 * 获取系统文档列表
 * @returns {Promise<{code: number, message: string, data: Array}>}
 */
export function getSystemDocList() {
  return get('/admin/system-docs/list')
}

/**
 * 删除系统文档
 * @param {number} id - 文档ID
 * @returns {Promise<{code: number, message: string, data: string}>}
 */
export function deleteSystemDocument(id) {
  return del(`/admin/system-docs/${id}`)
}

/**
 * 获取系统文档文件
 * @param {number} id - 文档ID
 * @returns {Promise<Blob>} - 文件Blob
 */
export function getSystemDocumentFile(id) {
  return get(`/admin/system-docs/${id}/file`, {
    responseType: 'blob'
  })
}
