<template>
  <div class="review-page">
    <!-- 页面头部 -->
    <div class="review-header">
      <div class="header-left">
        <el-button link @click="$router.back()">
          <el-icon><ArrowLeft /></el-icon>
        </el-button>
        <div class="contract-info">
          <h1 class="contract-name">{{ contractInfo.fileName || '加载中...' }}</h1>
          <div class="contract-meta">
            <span class="file-size">{{ formatFileSize(contractInfo.fileSize) }}</span>
            <el-divider direction="vertical" />
            <span class="upload-time">上传于 {{ formatDate(contractInfo.uploadTime) }}</span>
          </div>
        </div>
      </div>
      
      <div class="header-right">
        <template v-if="reviewStore.isCompleted">
          <el-button @click="showReportPreview">
            <el-icon><View /></el-icon>
            <span>预览报告</span>
          </el-button>
          <el-button type="primary" @click="exportPdf">
            <el-icon><Download /></el-icon>
            <span>导出 PDF</span>
          </el-button>
          <el-button @click="retryReview">
            <el-icon><RefreshRight /></el-icon>
            <span>重新审查</span>
          </el-button>
        </template>
        <template v-else-if="reviewStore.hasFailed">
          <el-button type="danger" @click="retryReview">
            <el-icon><RefreshRight /></el-icon>
            <span>重新审查</span>
          </el-button>
        </template>
        <template v-else-if="reviewStore.isReviewing">
          <el-button @click="cancelReview">
            <el-icon><CircleClose /></el-icon>
            <span>取消</span>
          </el-button>
        </template>
      </div>
    </div>
    
    <!-- 审查进度 -->
    <div v-if="reviewStore.isReviewing" class="progress-section">
      <div class="progress-header">
        <div class="progress-title">
          <el-icon class="rotating"><Loading /></el-icon>
          <span>正在审查中...</span>
        </div>
        <div class="progress-percent">{{ reviewStore.reviewProgress }}%</div>
      </div>
      <el-progress
        :percentage="reviewStore.reviewProgress"
        :stroke-width="8"
        :show-text="false"
        status="primary"
      />
      <div class="progress-stages">
        <div
          v-for="(label, stage) in stageLabels"
          :key="stage"
          class="stage-item"
          :class="getStageClass(stage)"
        >
          <el-icon v-if="isStageCompleted(stage)"><CircleCheck /></el-icon>
          <el-icon v-else-if="isStageActive(stage)"><Loading /></el-icon>
          <span v-else class="stage-dot"></span>
          <span class="stage-label">{{ label }}</span>
        </div>
      </div>
      <div v-if="reviewStore.currentReview?.message" class="progress-message">
        {{ reviewStore.currentReview.message }}
      </div>
    </div>
    
    <!-- 主内容区 -->
    <div class="review-main">
      <!-- 左侧：合同原文 -->
      <div class="contract-panel">
        <div class="panel-header">
          <h3 class="panel-title">
            <el-icon><Document /></el-icon>
            <span>合同原文</span>
          </h3>
          <div class="panel-actions">
            <el-button link size="small" @click="zoomOut" title="缩小">
              <el-icon><ZoomOut /></el-icon>
            </el-button>
            <span class="zoom-level">{{ Math.round(zoomLevel * 100) }}%</span>
            <el-button link size="small" @click="zoomIn" title="放大">
              <el-icon><ZoomIn /></el-icon>
            </el-button>
            <el-divider direction="vertical" />
            <el-button link size="small" @click="resetZoom" title="重置">
              <el-icon><RefreshLeft /></el-icon>
            </el-button>
          </div>
        </div>
        <div ref="contractViewer" class="contract-viewer">
          <div v-if="loadingContract" class="viewer-placeholder">
            <el-icon class="placeholder-icon is-loading"><Loading /></el-icon>
            <p>合同文件加载中...</p>
          </div>
          <div v-else-if="contractBlobUrl" class="contract-file-preview" :style="previewContainerStyle">
            <!-- PDF 文件预览 -->
            <iframe
              v-if="isPdfFile"
              :src="contractBlobUrl"
              class="file-iframe"
              :style="iframeStyle"
              frameborder="0"
            ></iframe>
            <!-- 图片文件预览 -->
            <img
              v-else-if="isImageFile"
              :src="contractBlobUrl"
              class="file-image"
              :style="imageStyle"
              alt="合同文件"
            />
            <!-- 其他文件类型显示下载链接 -->
            <div v-else class="file-download">
              <el-icon class="file-icon"><Document /></el-icon>
              <p>该文件类型暂不支持在线预览</p>
              <el-button type="primary" @click="downloadContractFile">
                <el-icon><Download /></el-icon>
                下载文件查看
              </el-button>
            </div>
          </div>
          <div v-else class="viewer-placeholder">
            <el-icon class="placeholder-icon"><Document /></el-icon>
            <p>暂无合同文件</p>
          </div>
        </div>
      </div>
      
      <!-- 右侧：审查结果 -->
      <div class="result-panel">
        <div class="panel-header">
          <h3 class="panel-title">
            <el-icon><Warning /></el-icon>
            <span>审查结果</span>
          </h3>
          <el-tag v-if="reviewStore.isCompleted" :type="overallScoreType">
            总体评分：{{ overallScore }}分
          </el-tag>
        </div>
        
        <div v-if="!reviewStore.isCompleted && !reviewStore.hasFailed" class="result-placeholder">
          <el-icon class="placeholder-icon"><Loading /></el-icon>
          <p>正在分析合同内容，请稍候...</p>
        </div>
        
        <div v-else-if="reviewStore.hasFailed" class="result-error">
          <el-icon class="error-icon"><CircleClose /></el-icon>
          <p>审查失败，请重试</p>
          <el-button type="primary" @click="retryReview">重新审查</el-button>
        </div>
        
        <div v-else class="result-content">
          <!-- 风险概览 -->
          <div class="risk-summary">
            <div class="summary-title">风险概览</div>
            <div class="summary-cards">
              <div class="summary-card high">
                <div class="card-value">{{ reviewStore.riskSummary.high }}</div>
                <div class="card-label">高风险</div>
              </div>
              <div class="summary-card medium">
                <div class="card-value">{{ reviewStore.riskSummary.medium }}</div>
                <div class="card-label">中风险</div>
              </div>
              <div class="summary-card low">
                <div class="card-value">{{ reviewStore.riskSummary.low }}</div>
                <div class="card-label">低风险</div>
              </div>
            </div>
          </div>
          
          <!-- 风险筛选 -->
          <div class="risk-filter">
            <el-radio-group v-model="riskFilter" size="small">
              <el-radio-button label="all">全部</el-radio-button>
              <el-radio-button label="high">高风险</el-radio-button>
              <el-radio-button label="medium">中风险</el-radio-button>
              <el-radio-button label="low">低风险</el-radio-button>
            </el-radio-group>
          </div>
          
          <!-- 风险列表 -->
          <div class="risk-list">
            <div
              v-for="risk in filteredRisks"
              :key="risk.id"
              class="risk-card"
              :class="`risk-${risk.level}`"
              @click="locateRisk(risk)"
            >
              <div class="risk-header">
                <el-tag
                  :type="getRiskTagType(risk.level)"
                  size="small"
                  effect="dark"
                >
                  {{ getRiskLevelText(risk.level) }}
                </el-tag>
                <span class="risk-clause">{{ risk.clause }}</span>
              </div>
              
              <div class="risk-body">
                <div class="risk-location">
                  <el-icon><Location /></el-icon>
                  <span>位置：{{ risk.location?.text || '第 X 条' }}</span>
                </div>

                <div class="risk-problem">
                  <div class="section-label">问题描述</div>
                  <div class="section-content">{{ risk.description }}</div>
                </div>

                <div v-if="risk.lawReferences?.length" class="risk-laws">
                  <div class="section-label">
                    <el-icon><Collection /></el-icon>
                    <span>关联法条</span>
                  </div>
                  <div class="laws-list">
                    <div
                      v-for="law in risk.lawReferences"
                      :key="law.id"
                      class="law-item"
                    >
                      <div class="law-content">{{ truncateText(law.content, 100) }}</div>
                    </div>
                  </div>
                </div>

                <div class="risk-suggestion">
                  <div class="section-label">
                    <el-icon><EditPen /></el-icon>
                    <span>修改建议</span>
                  </div>
                  <div class="section-content">{{ risk.suggestion }}</div>
                  <el-button
                    type="primary"
                    link
                    size="small"
                    class="copy-btn"
                    @click.stop="copySuggestion(risk.suggestion)"
                  >
                    <el-icon><CopyDocument /></el-icon>
                    <span>复制建议</span>
                  </el-button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    


    <!-- 审查配置弹框 -->
    <ReviewOptionsDialog
      v-model:visible="reviewOptionsVisible"
      :loading="isStartingReview"
      @confirm="handleRetryConfirm"
    />

    <!-- 页面切换拦截弹框 -->
    <el-dialog
      v-model="pageSwitchDialogVisible"
      title="提示"
      width="400px"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      :show-close="false"
    >
      <div class="page-switch-warning">
        <el-icon class="warning-icon" :size="48" color="#e6a23c"><Warning /></el-icon>
        <p class="warning-text">合同条款正在分析中，请勿切换页面</p>
      </div>
      <template #footer>
        <el-button type="primary" @click="pageSwitchDialogVisible = false">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { onBeforeRouteLeave } from 'vue-router'
import { useRoute, useRouter } from 'vue-router'
import { useReviewStore } from '@/stores/review'
import { useContractStore } from '@/stores/contract'
import { ElMessage, ElMessageBox } from 'element-plus'
import ReviewOptionsDialog from '@/components/ReviewOptionsDialog.vue'
import {
  formatDate,
  formatFileSize,
  formatRiskLevel,
  truncateText,
  copyToClipboard,
  calculateOverallScore
} from '@/utils/helpers'
import { RISK_LEVEL_TAG_TYPE, REVIEW_STAGE } from '@/utils/constants'
import { exportPdfReport } from '@/api/report'
import { getContractPreview, getContractFileBlob } from '@/api/contract'

const route = useRoute()
const router = useRouter()
const reviewStore = useReviewStore()
const contractStore = useContractStore()

const contractId = computed(() => {
  const id = route.params.contractId
  console.log('[Review] route.params:', route.params)
  console.log('[Review] route.params.contractId:', id)
  return id ? Number(id) : null
})

// 合同信息
const contractInfo = ref({
  fileName: '',
  fileSize: 0,
  uploadTime: null,
  fileUrl: ''
})
const loadingContract = ref(false)
const contractBlobUrl = ref('')
const contractContent = ref('')
const contractParagraphs = ref([])

// 审查状态
const riskFilter = ref('all')
const highlightedParagraph = ref(-1)
const zoomLevel = ref(1)
const isExporting = ref(false)
const isStartingReview = ref(false)
const reviewOptionsVisible = ref(false)

// 页面切换拦截
const pageSwitchDialogVisible = ref(false)

// Wake Lock - 屏幕常亮
let wakeLock = null

async function requestWakeLock() {
  try {
    if ('wakeLock' in navigator) {
      wakeLock = await navigator.wakeLock.request('screen')
      console.log('[WakeLock] 屏幕常亮已激活')
    } else {
      console.warn('[WakeLock] 当前浏览器不支持 Screen Wake Lock API')
    }
  } catch (err) {
    console.error('[WakeLock] 无法激活屏幕常亮:', err.name, err.message)
  }
}

function releaseWakeLock() {
  if (wakeLock !== null) {
    wakeLock.release()
      .then(() => {
        console.log('[WakeLock] 屏幕常亮已释放')
        wakeLock = null
      })
      .catch(err => console.error('[WakeLock] 释放屏幕常亮失败:', err))
  }
}

function handleWakeLockVisibilityChange() {
  if (document.visibilityState === 'visible' && reviewStore.isReviewing) {
    requestWakeLock()
  }
}

// 阶段标签
const stageLabels = {
  [REVIEW_STAGE.PARSING]: '解析文档',
  [REVIEW_STAGE.RETRIEVING]: '检索法条',
  [REVIEW_STAGE.ANALYZING]: 'AI 分析',
  [REVIEW_STAGE.GENERATING]: '生成报告'
}

// 监听审查状态变化，自动请求/释放屏幕常亮
watch(() => reviewStore.isReviewing, (isReviewing) => {
  if (isReviewing) {
    requestWakeLock()
  } else {
    releaseWakeLock()
  }
}, { immediate: true })

// 处理页面可见性变化
function handleVisibilityChange() {
  console.log('[handleVisibilityChange] 触发, document.hidden:', document.hidden, 'isReviewing:', reviewStore.isReviewing)
  // 只有在审查进行中且页面变为隐藏时才显示弹框
  if (reviewStore.isReviewing && document.hidden) {
    console.log('[handleVisibilityChange] 显示弹框')
    pageSwitchDialogVisible.value = true
  }
}

// 处理窗口失去焦点
function handleWindowBlur() {
  console.log('[handleWindowBlur] 触发, isReviewing:', reviewStore.isReviewing)
  // 暂时移除 isReviewing 检查，直接显示弹框用于测试
  console.log('[handleWindowBlur] 显示弹框')
  pageSwitchDialogVisible.value = true
}

// 路由守卫取消函数
let removeRouterGuard = null

// 路由离开守卫
const beforeEachGuard = (to, from, next) => {
  console.log('[路由守卫] 触发, isReviewing:', reviewStore.isReviewing)
  if (reviewStore.isReviewing) {
    console.log('[路由守卫] 阻止路由切换, 显示弹框')
    pageSwitchDialogVisible.value = true
    next(false)
  } else {
    next()
  }
}

// 计算属性
const viewerStyle = computed(() => ({
  transform: `scale(${zoomLevel.value})`,
  transformOrigin: 'top left'
}))

// 预览容器样式
const previewContainerStyle = computed(() => ({
  width: '100%',
  height: '100%',
  overflow: 'auto'
}))

// iframe样式（PDF预览放大）
const iframeStyle = computed(() => ({
  width: '100%',
  height: '100%',
  transform: `scale(${zoomLevel.value})`,
  transformOrigin: 'top left'
}))

// 图片样式（图片预览放大）
const imageStyle = computed(() => ({
  maxWidth: '100%',
  transform: `scale(${zoomLevel.value})`,
  transformOrigin: 'top left',
  transition: 'transform 0.2s ease'
}))

// 判断是否为PDF文件
const isPdfFile = computed(() => {
  const fileName = contractInfo.value.fileName || ''
  return fileName.toLowerCase().endsWith('.pdf')
})

// 判断是否为图片文件
const isImageFile = computed(() => {
  const fileName = contractInfo.value.fileName || ''
  const imageExts = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
  return imageExts.some(ext => fileName.toLowerCase().endsWith(ext))
})

const overallScore = computed(() => {
  const apiScore = reviewStore.currentReview?.overallScore
  if (apiScore !== undefined && apiScore !== null) {
    return apiScore
  }
  return calculateOverallScore(reviewStore.riskList)
})

const overallScoreType = computed(() => {
  if (overallScore.value >= 80) return 'success'
  if (overallScore.value >= 60) return 'warning'
  return 'danger'
})

const filteredRisks = computed(() => {
  if (riskFilter.value === 'all') {
    return reviewStore.riskList
  }
  return reviewStore.riskList.filter(risk => risk.level === riskFilter.value)
})

// 获取风险标签类型
function getRiskTagType(level) {
  return RISK_LEVEL_TAG_TYPE[level] || 'info'
}

// 获取风险等级文本
function getRiskLevelText(level) {
  return formatRiskLevel(level)
}

// 获取阶段样式
function getStageClass(stage) {
  const stages = Object.values(REVIEW_STAGE)
  const currentIndex = stages.indexOf(reviewStore.reviewStage)
  const stageIndex = stages.indexOf(stage)
  
  if (stageIndex < currentIndex) return 'completed'
  if (stageIndex === currentIndex) return 'active'
  return ''
}

// 判断阶段是否完成
function isStageCompleted(stage) {
  const stages = Object.values(REVIEW_STAGE)
  const currentIndex = stages.indexOf(reviewStore.reviewStage)
  const stageIndex = stages.indexOf(stage)
  return stageIndex < currentIndex
}

// 判断阶段是否激活
function isStageActive(stage) {
  return stage === reviewStore.reviewStage
}

// 定位风险
function locateRisk(risk) {
  if (risk.location?.paragraph !== undefined) {
    highlightedParagraph.value = risk.location.paragraph
    // 滚动到对应段落
    const element = document.getElementById(`para-${risk.location.paragraph}`)
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
    // 3秒后取消高亮
    setTimeout(() => {
      highlightedParagraph.value = -1
    }, 3000)
  }
}

// 处理段落点击
function handleParagraphClick(index) {
  // 查找关联的风险
  const relatedRisks = reviewStore.riskList.filter(
    risk => risk.location?.paragraph === index
  )
  if (relatedRisks.length > 0) {
    // 滚动到第一个关联风险
    console.log('关联风险:', relatedRisks)
  }
}

// 缩放
function zoomIn() {
  zoomLevel.value = Math.min(zoomLevel.value + 0.2, 3.0)
}

function zoomOut() {
  zoomLevel.value = Math.max(zoomLevel.value - 0.2, 0.5)
}

// 重置缩放
function resetZoom() {
  zoomLevel.value = 1.0
}

// 复制建议
async function copySuggestion(text) {
  const success = await copyToClipboard(text)
  if (success) {
    ElMessage.success('已复制到剪贴板')
  } else {
    ElMessage.error('复制失败')
  }
}

// 显示报告预览
function showReportPreview() {
  const reviewId = reviewStore.currentReview?.reviewId || reviewStore.currentReview?.review_id

  console.log('[showReportPreview] currentReview:', reviewStore.currentReview)
  console.log('[showReportPreview] reviewId:', reviewId)

  if (reviewId) {
    router.push(`/report/${reviewId}`)
  } else {
    ElMessage.error('报告ID不存在，请等待审查完成')
  }
}

// 导出 PDF
async function exportPdf() {
  isExporting.value = true
  try {
    const reviewId = reviewStore.currentReview?.reviewId || reviewStore.currentReview?.review_id
    if (!reviewId) {
      ElMessage.error('报告ID不存在')
      return
    }
    
    await exportPdfReport(reviewId, `审查报告_${contractInfo.value.fileName}.pdf`)
    ElMessage.success('导出成功')
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败')
  } finally {
    isExporting.value = false
  }
}

// 重新审查 - 显示配置弹框
function retryReview() {
  reviewOptionsVisible.value = true
}

// 处理重新审查确认
async function handleRetryConfirm(reviewOptions) {
  isStartingReview.value = true
  try {
    const reviewId = reviewStore.currentReview?.reviewId || reviewStore.currentReview?.review_id
    if (reviewId) {
      const fileBlob = await getContractFileBlob(contractId.value)
      await reviewStore.restart(reviewId, contractId.value, fileBlob, contractInfo.value.fileName, reviewOptions)
    } else {
      const fileBlob = await getContractFileBlob(contractId.value)
      await reviewStore.start(contractId.value, fileBlob, contractInfo.value.fileName, reviewOptions)
    }
    reviewOptionsVisible.value = false
  } catch (error) {
    console.error('[retryReview] 启动审查失败:', error)
    ElMessage.error('启动审查失败: ' + (error.message || '未知错误'))
  } finally {
    isStartingReview.value = false
  }
}

// 取消审查
async function cancelReview() {
  try {
    await ElMessageBox.confirm(
      '确定要取消当前审查吗？取消后将无法恢复。',
      '确认取消审查',
      {
        confirmButtonText: '确定',
        cancelButtonText: '继续审查',
        type: 'warning'
      }
    )
    // 用户点击确定，执行取消
    const reviewId = reviewStore.currentReview?.reviewId ||
                     reviewStore.currentReview?.review_id ||
                     reviewStore.currentReview?.id

    console.log('[cancelReview] currentReview:', reviewStore.currentReview)
    console.log('[cancelReview] reviewId:', reviewId)

    if (reviewId) {
      await reviewStore.cancel(reviewId)
    } else {
      console.warn('[cancelReview] 未找到 reviewId，无法取消审查')
      ElMessage.warning('未找到审查ID，无法取消')
    }
  } catch (error) {
    // 用户点击取消或关闭弹框，继续审查
    console.log('[cancelReview] 用户取消操作，继续审查')
  }
}

// 加载合同信息
async function loadContractInfo() {
  loadingContract.value = true
  try {
    const res = await getContractPreview(contractId.value)
    if (res.code === 200 && res.data) {
      contractInfo.value = {
        fileName: res.data.fileName || '',
        fileSize: res.data.fileSize || 0,
        uploadTime: res.data.createdAt || res.data.created_at || res.data.uploadTime,
        fileUrl: ''
      }
      // 加载合同文件blob
      await loadContractFile()
    }
  } catch (error) {
    console.error('加载合同信息失败:', error)
    ElMessage.error('加载合同信息失败')
  } finally {
    loadingContract.value = false
  }
}

// 加载合同文件blob
async function loadContractFile() {
  try {
    const blob = await getContractFileBlob(contractId.value)
    // 释放之前的blob URL
    if (contractBlobUrl.value) {
      URL.revokeObjectURL(contractBlobUrl.value)
    }
    // 创建新的blob URL
    contractBlobUrl.value = URL.createObjectURL(blob)
  } catch (error) {
    console.error('加载合同文件失败:', error)
    ElMessage.error('加载合同文件失败：' + error.message)
  }
}

// 下载合同文件
function downloadContractFile() {
  if (contractBlobUrl.value) {
    const link = document.createElement('a')
    link.href = contractBlobUrl.value
    link.download = contractInfo.value.fileName || '合同文件'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }
}

onMounted(async () => {
  console.log('[Review] 页面挂载，contractId:', contractId.value)

  // 检查是否已经有正在进行的审查（从配置页面跳转过来时已启动）
  const currentReviewId = sessionStorage.getItem('currentReviewId')
  console.log('[Review] 从sessionStorage读取currentReviewId:', currentReviewId)

  if (currentReviewId) {
    // 配置页面已经启动了审查，直接使用现有的reviewId
    console.log('[Review] 检测到已有审查ID，跳过启动审查')
    // 清除sessionStorage中的reviewId，避免重复
    sessionStorage.removeItem('currentReviewId')
    // 清除reviewOptions
    sessionStorage.removeItem('reviewOptions')
    // 设置审查状态为进行中，确保进度条显示
    reviewStore.setProcessingStatus()
    // 设置currentReview，确保cancelReview等方法可以获取到reviewId
    reviewStore.currentReview = { reviewId: parseInt(currentReviewId, 10) }
    // 连接到现有的审查进度
    reviewStore.connectProgress(currentReviewId)
    // 异步加载合同信息（不阻塞）
    loadContractInfo()
    return
  }

  // 检查是否已有完成的审查（页面刷新后直接访问时）
  console.log('[Review] 检查是否已有审查记录')
  const existingReview = await reviewStore.loadExistingReview(contractId.value)
  if (existingReview) {
    console.log('[Review] 已加载已有审查记录:', existingReview)
    // 异步加载合同信息（不阻塞）
    loadContractInfo()
    return
  }

  // 启动审查（直接访问审查页面时）
  console.log('[Review] 检查审查状态 - isReviewing:', reviewStore.isReviewing, 'isCompleted:', reviewStore.isCompleted)
  if (!reviewStore.isReviewing && !reviewStore.isCompleted) {
    // 从 sessionStorage 读取审查选项
    let reviewOptions = {}
    try {
      const storedOptions = sessionStorage.getItem('reviewOptions')
      console.log('[Review] 从sessionStorage读取选项:', storedOptions)
      if (storedOptions) {
        reviewOptions = JSON.parse(storedOptions)
        // 使用后清除，避免刷新页面时重复使用
        sessionStorage.removeItem('reviewOptions')
      }
    } catch (e) {
      console.warn('[Review] 读取审查选项失败:', e)
    }

    // 并行加载合同信息和获取文件Blob，加快启动速度
    try {
      console.log('[Review] 开始并行加载合同信息和获取文件Blob')
      const [contractRes, fileBlob] = await Promise.all([
        getContractPreview(contractId.value),
        getContractFileBlob(contractId.value)
      ])
      
      // 设置合同信息
      if (contractRes.code === 200 && contractRes.data) {
        contractInfo.value = {
          fileName: contractRes.data.fileName || '',
          fileSize: contractRes.data.fileSize || 0,
          uploadTime: contractRes.data.createdAt || contractRes.data.created_at || contractRes.data.uploadTime,
          fileUrl: ''
        }
        // 异步加载合同文件预览（不阻塞审查）
        loadContractFile()
      }
      
      console.log('[Review] 获取到文件Blob:', fileBlob?.size, 'bytes')
      console.log('[Review] 开始调用reviewStore.start')
      await reviewStore.start(contractId.value, fileBlob, contractInfo.value.fileName, reviewOptions)
      console.log('[Review] reviewStore.start 调用成功')
    } catch (error) {
      console.error('[Review] 启动审查失败:', error)
      ElMessage.error('启动审查失败: ' + (error.message || '未知错误'))
    }
  } else {
    console.log('[Review] 跳过启动审查，当前状态:', { isReviewing: reviewStore.isReviewing, isCompleted: reviewStore.isCompleted })
    // 异步加载合同信息（不阻塞）
    loadContractInfo()
  }

  // 添加页面可见性变化监听
  document.addEventListener('visibilitychange', handleVisibilityChange)
  // 添加窗口失去焦点监听
  window.addEventListener('blur', handleWindowBlur)
  // 添加 Wake Lock 可见性恢复监听
  document.addEventListener('visibilitychange', handleWakeLockVisibilityChange)
  // 添加路由守卫
  removeRouterGuard = router.beforeEach(beforeEachGuard)
})

onUnmounted(() => {
  reviewStore.cleanup()
  // 释放屏幕常亮
  releaseWakeLock()
  // 释放blob URL
  if (contractBlobUrl.value) {
    URL.revokeObjectURL(contractBlobUrl.value)
  }
  // 移除页面可见性变化监听
  document.removeEventListener('visibilitychange', handleVisibilityChange)
  // 移除窗口失去焦点监听
  window.removeEventListener('blur', handleWindowBlur)
  // 移除 Wake Lock 可见性恢复监听
  document.removeEventListener('visibilitychange', handleWakeLockVisibilityChange)
  // 移除路由守卫
  if (removeRouterGuard) {
    removeRouterGuard()
  }
})

// 组件内路由离开守卫
onBeforeRouteLeave((to, from, next) => {
  console.log('[onBeforeRouteLeave] 触发, isReviewing:', reviewStore.isReviewing)
  if (reviewStore.isReviewing) {
    console.log('[onBeforeRouteLeave] 阻止路由切换, 显示弹框')
    pageSwitchDialogVisible.value = true
    next(false)
  } else {
    next()
  }
})
</script>

<style scoped lang="scss">
.review-page {
  display: flex;
  flex-direction: column;
  min-height: calc(100vh - 64px);
  background: $bg-secondary;
  overflow-y: auto;
}

.review-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px 32px;
  background: white;
  border-bottom: 1px solid $border-color;
  
  .header-left {
    display: flex;
    align-items: center;
    gap: 16px;
    
    .contract-info {
      .contract-name {
        font-size: $font-size-lg;
        font-weight: 600;
        color: $text-primary;
        margin: 0 0 4px 0;
      }
      
      .contract-meta {
        font-size: $font-size-sm;
        color: $text-secondary;
        display: flex;
        align-items: center;
        gap: 8px;
      }
    }
  }
  
  .header-right {
    display: flex;
    gap: 12px;
  }
}

.progress-section {
  background: white;
  padding: 24px 32px;
  border-bottom: 1px solid $border-color;
  
  .progress-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
    
    .progress-title {
      display: flex;
      align-items: center;
      gap: 8px;
      font-weight: 500;
      color: $primary-color;
      
      .rotating {
        animation: rotate 1s linear infinite;
      }
    }
    
    .progress-percent {
      font-size: $font-size-lg;
      font-weight: 600;
      color: $primary-color;
    }
  }
  
  .progress-stages {
    display: flex;
    justify-content: space-between;
    margin-top: 16px;
    padding: 0 20px;
    
    .stage-item {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: $font-size-sm;
      color: $text-tertiary;
      
      &.completed {
        color: $success-color;
      }
      
      &.active {
        color: $primary-color;
        font-weight: 500;
        
        .el-icon {
          animation: rotate 1s linear infinite;
        }
      }
      
      .stage-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: $border-color;
      }
    }
  }
  
  .progress-message {
    margin-top: 12px;
    padding: 8px 12px;
    background: $bg-secondary;
    border-radius: $radius-sm;
    font-size: $font-size-sm;
    color: $text-secondary;
  }
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.review-main {
  display: flex;
  flex: 1;
  min-height: 800px;
  padding: 32px;
  gap: 32px;
}

.contract-panel,
.result-panel {
  display: flex;
  flex-direction: column;
  background: white;
  border-radius: $radius-lg;
  box-shadow: $shadow-sm;
  overflow: hidden;
}

.contract-panel {
  width: 45%;
  min-width: 400px;
  min-height: 700px;
}

.result-panel {
  flex: 1;
  min-width: 450px;
  min-height: 700px;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid $border-light;
  background: $bg-secondary;
  
  .panel-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: $font-size-base;
    font-weight: 600;
    color: $text-primary;
    margin: 0;
    
    .el-icon {
      color: $primary-color;
    }
  }
  
  .panel-actions {
    display: flex;
    align-items: center;
    gap: 4px;
    
    .zoom-level {
      font-size: 12px;
      color: $text-secondary;
      min-width: 40px;
      text-align: center;
    }
  }
}

.contract-viewer {
  flex: 1;
  overflow: auto;
  padding: 32px;
  background: $bg-secondary;
  min-height: 900px;
  
  .viewer-placeholder {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 900px;
    color: $text-tertiary;
    
    .placeholder-icon {
      font-size: 48px;
      margin-bottom: 12px;
    }
  }
  
  .contract-file-preview {
    width: 100%;
    min-height: 1000px;
    height: calc(100vh - 300px);
    display: flex;
    align-items: flex-start;
    justify-content: center;
    
    .file-iframe {
      width: 100%;
      height: 100%;
      min-height: 1000px;
      border: none;
      background: white;
    }
    
    .file-image {
      max-width: 100%;
      height: auto;
      box-shadow: $shadow-md;
    }
    
    .file-download {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      height: 100%;
      color: $text-tertiary;
      
      .file-icon {
        font-size: 64px;
        margin-bottom: 16px;
      }
      
      p {
        margin-bottom: 20px;
      }
    }
  }
}

.contract-content {
  background: white;
  padding: 32px;
  min-height: 100%;
  box-shadow: $shadow-sm;
  
  .paragraph {
    display: flex;
    gap: 12px;
    padding: 8px 12px;
    margin-bottom: 4px;
    border-radius: $radius-sm;
    cursor: pointer;
    transition: all $transition-fast;
    line-height: 1.8;
    
    &:hover {
      background: $bg-secondary;
    }
    
    &.highlighted {
      background: rgba($secondary-color, 0.15);
      border-left: 3px solid $secondary-color;
    }
    
    .para-number {
      color: $text-tertiary;
      font-size: $font-size-xs;
      min-width: 24px;
      text-align: right;
      flex-shrink: 0;
    }
    
    .para-text {
      color: $text-primary;
      flex: 1;
    }
  }
}

.result-content {
  flex: 1;
  overflow: auto;
  padding: 32px;
  min-height: 600px;
}

.result-placeholder,
.result-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 600px;
  color: $text-tertiary;
  
  .placeholder-icon,
  .error-icon {
    font-size: 48px;
    margin-bottom: 12px;
  }
  
  .error-icon {
    color: $danger-color;
  }
}

.risk-summary {
  margin-bottom: 20px;
  
  .summary-title {
    font-size: $font-size-sm;
    font-weight: 600;
    color: $text-primary;
    margin-bottom: 12px;
  }
  
  .summary-cards {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
  }
  
  .summary-card {
    text-align: center;
    padding: 16px;
    border-radius: $radius-md;
    
    &.high {
      background: rgba($risk-high, 0.08);
      .card-value { color: $risk-high; }
    }
    
    &.medium {
      background: rgba($risk-medium, 0.08);
      .card-value { color: $risk-medium; }
    }
    
    &.low {
      background: rgba($risk-low, 0.08);
      .card-value { color: $risk-low; }
    }
    
    .card-value {
      font-size: 28px;
      font-weight: 700;
      line-height: 1;
      margin-bottom: 4px;
    }
    
    .card-label {
      font-size: $font-size-sm;
      color: $text-secondary;
    }
  }
}

.risk-filter {
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid $border-light;
}

.risk-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.risk-card {
  background: $bg-secondary;
  border-radius: $radius-md;
  padding: 16px;
  cursor: pointer;
  transition: all $transition-fast;
  border-left: 3px solid transparent;
  
  &:hover {
    box-shadow: $shadow-md;
    transform: translateY(-2px);
  }
  
  &.risk-high {
    border-left-color: $risk-high;
  }
  
  &.risk-medium {
    border-left-color: $risk-medium;
  }
  
  &.risk-low {
    border-left-color: $risk-low;
  }
  
  .risk-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 12px;
    
    .risk-clause {
      font-weight: 600;
      color: $text-primary;
    }
  }
  
  .risk-body {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  
  .section-label {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: $font-size-xs;
    font-weight: 600;
    color: $text-secondary;
    margin-bottom: 4px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  
  .section-content {
    font-size: $font-size-sm;
    color: $text-primary;
    line-height: 1.6;
  }
  
  .risk-location {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: $font-size-xs;
    color: $text-tertiary;
    
    .el-icon {
      font-size: 12px;
    }
  }
  
  .risk-laws {
    .laws-list {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    
    .law-item {
      background: white;
      padding: 10px 12px;
      border-radius: $radius-sm;
      border: 1px solid $border-light;
      
      .law-title {
        font-size: $font-size-sm;
        font-weight: 500;
        color: $primary-color;
        margin-bottom: 4px;
      }
      
      .law-content {
        font-size: $font-size-xs;
        color: $text-secondary;
        line-height: 1.5;
      }
    }
  }
  
  .risk-suggestion {
    background: rgba($success-color, 0.05);
    padding: 12px;
    border-radius: $radius-sm;
    border: 1px solid rgba($success-color, 0.1);
    
    .copy-btn {
      margin-top: 8px;
    }
  }
}

.export-options {
  .export-desc {
    margin-bottom: 16px;
    color: $text-secondary;
  }

  .el-radio {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 12px;

    .el-icon {
      font-size: 20px;
    }
  }
}

// 页面切换警告弹框样式
.page-switch-warning {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px 0;

  .warning-icon {
    margin-bottom: 16px;
  }

  .warning-text {
    font-size: 16px;
    color: $text-primary;
    text-align: center;
    margin: 0;
  }
}
</style>
