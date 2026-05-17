import { get, post, del } from '@/utils/request'

// 搜索法条
export function searchLaws(keyword, params = {}) {
  return get('/knowledge/laws/search', {
    keyword,
    ...params
  })
}

// 获取法条详情
export function getLawDetail(lawId) {
  return get(`/knowledge/laws/${lawId}`)
}

// 获取法条分类列表
export function getLawCategories() {
  return get('/knowledge/laws/categories')
}

// 获取模板列表
export function getTemplateList(params) {
  return get('/knowledge/templates', params)
}

// 上传模板
export function uploadTemplate(file, data = {}) {
  const formData = new FormData()
  formData.append('file', file)
  Object.keys(data).forEach(key => {
    formData.append(key, data[key])
  })
  return post('/knowledge/templates/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

// 删除模板
export function deleteTemplate(templateId) {
  return del(`/knowledge/templates/${templateId}`)
}

// 获取知识库统计
export function getKnowledgeStats() {
  return get('/knowledge/stats')
}
