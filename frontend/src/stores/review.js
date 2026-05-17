import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  startReview,
  connectReviewProgress,
  getReviewResult,
  getRiskList,
  getReviewHistory,
  reReview,
  cancelReview,
  getLatestReviewByContractId
} from '@/api/review'
import { ElMessage } from 'element-plus'
import { REVIEW_STATUS, REVIEW_STAGE } from '@/utils/constants'

export const useReviewStore = defineStore('review', () => {
  // State
  const currentReview = ref(null)
  const reviewProgress = ref(0)
  const reviewStage = ref('')
  const reviewStatus = ref('')
  const riskList = ref([])
  const historyList = ref([])
  const loading = ref(false)
  const eventSource = ref(null)
  const stageProgress = ref({
    [REVIEW_STAGE.PARSING]: 0,
    [REVIEW_STAGE.RETRIEVING]: 0,
    [REVIEW_STAGE.ANALYZING]: 0,
    [REVIEW_STAGE.GENERATING]: 0
  })

  // Getters
  const isReviewing = computed(() => {
    return reviewStatus.value === REVIEW_STATUS.PROCESSING
  })

  const isCompleted = computed(() => {
    return reviewStatus.value === REVIEW_STATUS.COMPLETED
  })

  const hasFailed = computed(() => {
    return reviewStatus.value === REVIEW_STATUS.FAILED
  })

  const riskSummary = computed(() => {
    const apiSummary = currentReview.value?.riskSummary
    if (apiSummary && (apiSummary.high || apiSummary.medium || apiSummary.low)) {
      return {
        high: apiSummary.high || 0,
        medium: apiSummary.medium || 0,
        low: apiSummary.low || 0,
        none: apiSummary.none || 0
      }
    }
    const summary = { high: 0, medium: 0, low: 0, none: 0 }
    riskList.value.forEach(risk => {
      if (summary[risk.level] !== undefined) {
        summary[risk.level]++
      }
    })
    return summary
  })

  const highRisks = computed(() => {
    return riskList.value.filter(risk => risk.level === 'high')
  })

  const mediumRisks = computed(() => {
    return riskList.value.filter(risk => risk.level === 'medium')
  })

  const lowRisks = computed(() => {
    return riskList.value.filter(risk => risk.level === 'low')
  })

  // Actions
  // 开始审查
  async function start(contractId, fileBlob, fileName, options = {}) {
    console.log('[ReviewStore] start 被调用:', { contractId, fileName, fileBlobSize: fileBlob?.size, options })
    loading.value = true
    try {
      console.log('[ReviewStore] 调用 startReview API')
      const response = await startReview(contractId, fileBlob, fileName, options)
      console.log('[ReviewStore] startReview API 返回:', response)

      // request.js 拦截器已解包，response 格式: { code, message, data }
      const result = response.data || response
      currentReview.value = result
      reviewStatus.value = REVIEW_STATUS.PROCESSING
      reviewProgress.value = 0
      
      // 获取 reviewId（后端返回的是整数类型）
      const reviewId = parseInt(result.reviewId || result.review_id, 10)
      console.log('[ReviewStore] 获取到 reviewId:', reviewId)
      
      if (!reviewId) {
        throw new Error('未获取到审查ID')
      }
      
      // 连接 SSE 获取实时进度
      connectProgress(reviewId)
      
      return result
    } catch (error) {
      console.error('[ReviewStore] 启动审查失败:', error)
      ElMessage.error('启动审查失败: ' + (error.message || '未知错误'))
      throw error
    } finally {
      loading.value = false
    }
  }

  // 连接进度推送
  function connectProgress(reviewId) {
    console.log('[ReviewStore] connectProgress 被调用, reviewId:', reviewId)
    // 关闭已有连接
    if (eventSource.value) {
      console.log('[ReviewStore] 关闭已有 SSE 连接')
      eventSource.value.close()
    }

    eventSource.value = connectReviewProgress(
      reviewId,
      (data) => {
        console.log('[ReviewStore] 收到进度更新:', data)
        // 更新进度
        reviewProgress.value = data.progress || 0
        reviewStage.value = data.stage || ''
        reviewStatus.value = data.status || REVIEW_STATUS.PROCESSING
        console.log('[ReviewStore] 状态已更新 - progress:', reviewProgress.value, 'stage:', reviewStage.value, 'status:', reviewStatus.value)
        
        // 更新阶段进度
        if (data.stageProgress) {
          stageProgress.value = { ...stageProgress.value, ...data.stageProgress }
        }
        
        // 更新当前消息
        if (data.message) {
          currentReview.value = {
            ...currentReview.value,
            message: data.message
          }
        }
        
        // 审查完成时获取结果
        if (data.status === REVIEW_STATUS.COMPLETED) {
          const reviewId = currentReview.value?.reviewId || currentReview.value?.review_id
          if (reviewId) {
            fetchResult(reviewId)
          } else {
            console.error('[ReviewStore] 审查完成但无法获取 reviewId')
            ElMessage.error('审查完成但获取审查ID失败')
          }
        }
      },
      (error) => {
        console.error('进度连接错误:', error)
        ElMessage.error('审查进度连接异常')
      }
    )
  }

  // 获取审查结果
  async function fetchResult(reviewId) {
    loading.value = true
    try {
      const response = await getReviewResult(reviewId)
      // 后端返回格式: { code, message, data }
      // response 是拦截器处理后的响应: { code, message, data }
      // 实际的审查结果在 response.data 中
      const result = response.data
      console.log('[fetchResult] 获取审查结果:', result)
      currentReview.value = { ...currentReview.value, ...result }
      reviewStatus.value = result.status || REVIEW_STATUS.COMPLETED
      reviewProgress.value = 100

      // 优先使用结果中的 risks（字段名与模板匹配）
      if (Array.isArray(result.risks) && result.risks.length > 0) {
        riskList.value = result.risks
      } else {
        // 兜底：从风险列表接口获取（使用 reviewId 整数）
        await fetchRisks(result.reviewId)
      }

      return result
    } catch (error) {
      console.error('获取审查结果失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  // 获取风险列表
  async function fetchRisks(reviewId, params = {}) {
    try {
      const response = await getRiskList(reviewId, params)
      // 后端返回格式: { code, message, data }
      // response 是拦截器处理后的响应: { code, message, data }
      // 实际的风险列表在 response.data 中
      const result = response.data
      console.log('[fetchRisks] 获取风险列表:', result)
      let list = []
      if (Array.isArray(result)) {
        list = result
      } else if (result && typeof result === 'object') {
        list = result.risks || result.list || result.data || []
      }
      // 映射字段名，使 /risks 接口返回的数据与模板一致
      riskList.value = list.map(item => ({
        id: item.id,
        level: item.level || item.riskLevel,
        clause: item.clause || item.clauseTitle,
        description: item.description || item.riskDescription,
        suggestion: item.suggestion,
        location: item.location || { text: item.clauseContent || '' },
        lawReferences: item.lawReferences || []
      }))
      return riskList.value
    } catch (error) {
      console.error('获取风险列表失败:', error)
      throw error
    }
  }

  // 获取审查历史
  async function fetchHistory(params = {}) {
    loading.value = true
    try {
      const response = await getReviewHistory(params)
      // 后端返回格式: { code, message, data }
      // response 是拦截器处理后的响应: { code, message, data }
      const result = response.data
      historyList.value = result.list || result || []
      return result
    } catch (error) {
      console.error('获取审查历史失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  // 根据合同ID加载已有的审查结果
  async function loadExistingReview(contractId) {
    try {
      const response = await getLatestReviewByContractId(contractId)
      // 后端返回格式: { code, message, data }
      // response 是拦截器处理后的响应: { code, message, data }
      const result = response.data

      // 使用 reviewNo 作为标识（字符串）
      if (result && result.reviewNo) {
        console.log('[loadExistingReview] 找到已有审查记录:', result)
        currentReview.value = result

        // 根据completedAt判断审查是否完成
        if (result.completedAt) {
          reviewStatus.value = REVIEW_STATUS.COMPLETED
          reviewProgress.value = 100
          // 加载风险列表（使用 reviewId 数字）
          await fetchRisks(result.reviewId)
        } else {
          reviewStatus.value = REVIEW_STATUS.PROCESSING
          // 连接到SSE获取进度（使用 reviewId 数字）
          connectProgress(result.reviewId)
        }
        return result
      }
      return null
    } catch (error) {
      console.log('[loadExistingReview] 没有找到已有审查记录:', error)
      return null
    }
  }

  // 重新审查
  async function restart(reviewId, contractId, fileBlob, fileName, options = {}) {
    try {
      await reReview(reviewId, contractId, fileBlob, fileName, options)
      ElMessage.success('已重新启动审查')
      reviewStatus.value = REVIEW_STATUS.PROCESSING
      reviewProgress.value = 0
      connectProgress(reviewId)
    } catch (error) {
      console.error('重新审查失败:', error)
      throw error
    }
  }

  // 取消审查
  async function cancel(reviewId) {
    console.log('[ReviewStore.cancel] 取消审查, reviewId:', reviewId)
    try {
      // 确保 reviewId 是数字类型
      const numericReviewId = parseInt(reviewId, 10)
      console.log('[ReviewStore.cancel] 转换后的 reviewId:', numericReviewId)
      
      if (!numericReviewId || isNaN(numericReviewId)) {
        throw new Error('无效的审查ID')
      }
      
      await cancelReview(numericReviewId)
      ElMessage.success('已取消审查')
      reviewStatus.value = REVIEW_STATUS.FAILED
      
      // 关闭 SSE 连接
      if (eventSource.value) {
        eventSource.value.close()
        eventSource.value = null
      }
    } catch (error) {
      console.error('[ReviewStore.cancel] 取消审查失败:', error)
      ElMessage.error('取消审查失败: ' + error.message)
      throw error
    }
  }

  // 清理连接
  function cleanup() {
    if (eventSource.value) {
      eventSource.value.close()
      eventSource.value = null
    }
  }

  // 设置处理中状态（用于页面跳转后恢复状态）
  function setProcessingStatus() {
    reviewStatus.value = REVIEW_STATUS.PROCESSING
    reviewProgress.value = 0
    console.log('[ReviewStore] 手动设置处理中状态')
  }

  // 重置状态
  function reset() {
    currentReview.value = null
    reviewProgress.value = 0
    reviewStage.value = ''
    reviewStatus.value = ''
    riskList.value = []
    stageProgress.value = {
      [REVIEW_STAGE.PARSING]: 0,
      [REVIEW_STAGE.RETRIEVING]: 0,
      [REVIEW_STAGE.ANALYZING]: 0,
      [REVIEW_STAGE.GENERATING]: 0
    }
    cleanup()
  }

  return {
    // State
    currentReview,
    reviewProgress,
    reviewStage,
    reviewStatus,
    riskList,
    historyList,
    loading,
    stageProgress,
    // Getters
    isReviewing,
    isCompleted,
    hasFailed,
    riskSummary,
    highRisks,
    mediumRisks,
    lowRisks,
    // Actions
    start,
    connectProgress,
    fetchResult,
    fetchRisks,
    fetchHistory,
    loadExistingReview,
    restart,
    cancel,
    cleanup,
    reset,
    setProcessingStatus
  }
})
