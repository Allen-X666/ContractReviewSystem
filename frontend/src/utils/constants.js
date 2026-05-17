// 常量定义

// 文件上传配置
export const UPLOAD_CONFIG = {
  MAX_SIZE: 50 * 1024 * 1024, // 50MB
  ACCEPT_TYPES: ['.pdf', '.docx'],
  MIME_TYPES: {
    'application/pdf': '.pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx'
  }
}

// 审查状态
export const REVIEW_STATUS = {
  PENDING: 'pending',
  PROCESSING: 'processing',
  COMPLETED: 'completed',
  FAILED: 'failed',
  CANCELLED: 'cancelled'
}

export const REVIEW_STATUS_TEXT = {
  [REVIEW_STATUS.PENDING]: '待审查',
  [REVIEW_STATUS.PROCESSING]: '审查中',
  [REVIEW_STATUS.COMPLETED]: '已完成',
  [REVIEW_STATUS.FAILED]: '审查失败',
  [REVIEW_STATUS.CANCELLED]: '取消审查'
}

export const REVIEW_STATUS_TYPE = {
  [REVIEW_STATUS.PENDING]: 'info',
  [REVIEW_STATUS.PROCESSING]: 'warning',
  [REVIEW_STATUS.COMPLETED]: 'success',
  [REVIEW_STATUS.FAILED]: 'danger',
  [REVIEW_STATUS.CANCELLED]: 'info'
}

// 风险等级
export const RISK_LEVEL = {
  HIGH: 'high',
  MEDIUM: 'medium',
  LOW: 'low'
}

export const RISK_LEVEL_TEXT = {
  [RISK_LEVEL.HIGH]: '高风险',
  [RISK_LEVEL.MEDIUM]: '中风险',
  [RISK_LEVEL.LOW]: '低风险',
  // 支持后端返回的大写格式
  'HIGH': '高风险',
  'MEDIUM': '中风险',
  'LOW': '低风险',
  'EMPTY': '无风险',
  '': '无风险'
}

export const RISK_LEVEL_TAG_TYPE = {
  [RISK_LEVEL.HIGH]: 'danger',
  [RISK_LEVEL.MEDIUM]: 'warning',
  [RISK_LEVEL.LOW]: 'info'
}

export const RISK_LEVEL_COLOR = {
  [RISK_LEVEL.HIGH]: '#dc2626',
  [RISK_LEVEL.MEDIUM]: '#d97706',
  [RISK_LEVEL.LOW]: '#2563eb'
}

// 风险类型
export const RISK_TYPE = {
  INVALID_CLAUSE: 'invalid_clause',
  MISSING_CLAUSE: 'missing_clause',
  UNREASONABLE_CLAUSE: 'unreasonable_clause',
  LEGAL_RISK: 'legal_risk'
}

export const RISK_TYPE_TEXT = {
  [RISK_TYPE.INVALID_CLAUSE]: '无效条款',
  [RISK_TYPE.MISSING_CLAUSE]: '缺失条款',
  [RISK_TYPE.UNREASONABLE_CLAUSE]: '不合理条款',
  [RISK_TYPE.LEGAL_RISK]: '法律风险'
}

// 审查阶段
export const REVIEW_STAGE = {
  PARSING: 'parsing',
  RETRIEVING: 'retrieving',
  ANALYZING: 'analyzing',
  GENERATING: 'generating'
}

export const REVIEW_STAGE_TEXT = {
  [REVIEW_STAGE.PARSING]: '解析文档',
  [REVIEW_STAGE.RETRIEVING]: '检索法条',
  [REVIEW_STAGE.ANALYZING]: 'AI 分析',
  [REVIEW_STAGE.GENERATING]: '生成报告'
}

// 报告导出格式
export const EXPORT_FORMAT = {
  WORD: 'word',
  PDF: 'pdf'
}

export const EXPORT_FORMAT_TEXT = {
  [EXPORT_FORMAT.WORD]: 'Word 文档',
  [EXPORT_FORMAT.PDF]: 'PDF 文档'
}

// 分页配置
export const PAGINATION = {
  PAGE_SIZE: 10,
  PAGE_SIZES: [10, 20, 50, 100]
}

// 本地存储键名
export const STORAGE_KEYS = {
  TOKEN: 'contract_review_token',
  USER_INFO: 'contract_review_user',
  SETTINGS: 'contract_review_settings'
}

// 路由名称
export const ROUTE_NAMES = {
  DASHBOARD: 'Dashboard',
  CONTRACT_UPLOAD: 'ContractUpload',
  CONTRACT_LIST: 'ContractList',
  CONTRACT_DETAIL: 'ContractDetail',
  REVIEW: 'Review',
  REPORT_PREVIEW: 'ReportPreview',
  HISTORY: 'History',
  KNOWLEDGE: 'Knowledge',
  TEMPLATE: 'Template',
  SETTINGS: 'Settings',
  ADMIN: 'Admin'
}
