<template>
  <div class="contract-detail-page">
    <div class="page-header">
      <div class="header-left">
        <el-button link @click="$router.back()">
          <el-icon><ArrowLeft /></el-icon>
        </el-button>
        <div class="contract-title">
          <h1>{{ contract?.fileName || '合同详情' }}</h1>
          <div class="contract-meta">
            <span>{{ formatFileSize(contract?.fileSize) }}</span>
            <el-divider direction="vertical" />
            <span>上传于 {{ formatDate(contract?.createdAt) }}</span>
          </div>
        </div>
      </div>
      <div class="header-actions">
        <el-button @click="downloadContract">
          <el-icon><Download /></el-icon>
          <span>下载</span>
        </el-button>
        <el-button type="primary" @click="startReview">
          <el-icon><VideoPlay /></el-icon>
          <span>开始审查</span>
        </el-button>
      </div>
    </div>
    
    <div class="detail-content">
      <!-- 左侧：合同预览 -->
      <div class="preview-section">
        <div class="section-header">
          <h3>合同预览</h3>
        </div>
        <div class="preview-container">
          <div v-if="loading" class="preview-placeholder">
            <el-icon class="placeholder-icon"><Loading /></el-icon>
            <p>合同内容加载中...</p>
          </div>
          <div v-else-if="error" class="preview-placeholder">
            <el-icon class="placeholder-icon"><DocumentDelete /></el-icon>
            <p>{{ error }}</p>
          </div>
          <div v-else-if="fileType === 'pdf'" class="pdf-preview-wrapper">
            <PdfPreview :file-blob="fileBlob" />
          </div>
          <div v-else-if="fileType === 'docx' || fileType === 'doc'" class="docx-preview-wrapper">
            <DocxPreview :file-blob="fileBlob" />
          </div>
          <div v-else-if="['txt', 'md', 'json', 'xml', 'yaml', 'yml', 'csv', 'log'].includes(fileType)" class="text-preview-wrapper">
            <TxtPreview :file-blob="fileBlob" />
          </div>
          <div v-else class="preview-placeholder">
            <el-icon class="placeholder-icon"><Document /></el-icon>
            <p>该文件格式暂不支持在线预览，但可以进行审查</p>
            <p class="sub-text">支持的审查格式：PDF、Word、TXT 等</p>
          </div>
        </div>
      </div>
      
      <!-- 右侧：审查信息 -->
      <div class="info-section">
        <div class="section-header">
          <h3>审查信息</h3>
        </div>
        <div class="info-content">
          <div v-if="!contract?.lastReviewId" class="empty-review">
            <el-icon class="empty-icon"><DocumentDelete /></el-icon>
            <p>该合同尚未进行审查</p>
            <el-button type="primary" @click="startReview">
              立即审查
            </el-button>
          </div>
          <div v-else class="review-info">
            <div class="info-item">
              <span class="info-label">审查编号</span>
              <span class="info-value">{{ contract.lastReviewId }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">审查状态</span>
              <el-tag :type="getStatusType(contract.reviewStatus)">
                {{ getStatusText(contract.reviewStatus) }}
              </el-tag>
            </div>
            <div class="info-item">
              <span class="info-label">审查得分</span>
              <span class="info-value score">{{ contract.reviewScore || '-' }} 分</span>
            </div>
            <div class="info-item">
              <span class="info-label">风险统计</span>
              <div class="risk-tags">
                <el-tag type="danger" size="small" v-if="contract.riskSummary?.high">
                  高 {{ contract.riskSummary.high }}
                </el-tag>
                <el-tag type="warning" size="small" v-if="contract.riskSummary?.medium">
                  中 {{ contract.riskSummary.medium }}
                </el-tag>
                <el-tag type="info" size="small" v-if="contract.riskSummary?.low">
                  低 {{ contract.riskSummary.low }}
                </el-tag>
              </div>
            </div>
            <div class="info-actions">
              <el-button type="primary" @click="viewReport">
                查看审查报告
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 审查选项对话框 -->
    <ReviewOptionsDialog
      v-model:visible="reviewOptionsVisible"
      :loading="startingReview"
      @confirm="handleReviewConfirm"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { formatDate, formatFileSize } from '@/utils/helpers'
import { REVIEW_STATUS_TEXT, REVIEW_STATUS_TYPE } from '@/utils/constants'
import { getContractPreview, getContractFileBlob, downloadContract as downloadContractApi } from '@/api/contract'
import { useReviewStarter } from '@/composables/useReviewStarter'
import PdfPreview from '@/components/preview/PdfPreview.vue'
import DocxPreview from '@/components/preview/DocxPreview.vue'
import TxtPreview from '@/components/preview/TxtPreview.vue'
import ReviewOptionsDialog from '@/components/ReviewOptionsDialog.vue'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()

const contract = ref({
  id: route.params.id,
  fileName: '',
  fileSize: 0,
  createdAt: null,
  reviewStatus: 'pending',
  lastReviewId: null,
  lastReviewNo: null,
  reviewScore: null,
  riskSummary: null
})

const loading = ref(false)
const error = ref('')
const fileBlob = ref(null)

// 使用审查启动组合式函数
const {
  reviewOptionsVisible,
  startingReview,
  startReview: startReviewAction,
  handleReviewConfirm
} = useReviewStarter()

function startReview() {
  startReviewAction(contract.value)
}

const fileType = computed(() => {
  const fileName = contract.value.fileName || ''
  const ext = fileName.split('.').pop()?.toLowerCase()
  return ext
})

// 获取状态文本
function getStatusText(status) {
  return REVIEW_STATUS_TEXT[status] || status
}

// 获取状态类型
function getStatusType(status) {
  return REVIEW_STATUS_TYPE[status] || 'info'
}

// 下载合同
async function downloadContract() {
  try {
    await downloadContractApi(contract.value.id, contract.value.fileName)
  } catch (error) {
    console.error('下载合同失败:', error)
  }
}

// 辅助函数：从 reviewNo 中提取数字ID
function extractReviewId(reviewNo) {
  if (!reviewNo) return null
  // 统一转为字符串后提取数字部分
  const match = String(reviewNo).match(/\d+/)
  return match ? parseInt(match[0], 10) : null
}

// 查看报告
function viewReport() {
  // 优先使用 lastReviewId
  if (contract.value.lastReviewId) {
    router.push(`/report/${contract.value.lastReviewId}`)
  } else {
    ElMessage.warning('暂无审查报告')
  }
}

// 加载合同内容和文件
async function loadContractContent() {
  loading.value = true
  error.value = ''
  
  try {
    // 1. 获取合同预览信息
    const previewRes = await getContractPreview(route.params.id)
    if (previewRes.code === 200) {
      const fileName = previewRes.data.fileName
      const fileSize = previewRes.data.fileSize
      const fileTypeFromServer = previewRes.data.fileType
      
      contract.value = {
        ...contract.value,
        fileName: fileName,
        fileSize: fileSize
      }
      
      console.log('loadContractContent - fileTypeFromServer:', fileTypeFromServer)
      
      // 2. 获取文件Blob（支持预览的文件类型）
      const previewableTypes = ['pdf', 'docx', 'doc', 'txt', 'md', 'json', 'xml', 'yaml', 'yml', 'csv', 'log']
      if (previewableTypes.includes(fileTypeFromServer)) {
        console.log(`开始获取${fileTypeFromServer}文件Blob`)
        fileBlob.value = await getContractFileBlob(route.params.id)
        console.log(`${fileTypeFromServer}文件Blob获取成功`)
      }
    } else {
      error.value = previewRes.message || '获取合同信息失败'
    }
  } catch (err) {
    console.error('加载合同失败:', err)
    error.value = err.message || '加载合同失败，请稍后重试'
    ElMessage.error(error.value)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadContractContent()
})
</script>

<style scoped lang="scss">
.contract-detail-page {
  padding: 24px;
  max-width: 1440px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
  
  .header-left {
    display: flex;
    align-items: center;
    gap: 16px;
    
    .contract-title {
      h1 {
        font-size: $font-size-xl;
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
  
  .header-actions {
    display: flex;
    gap: 12px;
  }
}

.detail-content {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 24px;
}

.preview-section,
.info-section {
  background: white;
  border-radius: $radius-lg;
  box-shadow: $shadow-sm;
  overflow: hidden;
}

.section-header {
  padding: 16px 20px;
  border-bottom: 1px solid $border-light;
  background: $bg-secondary;
  
  h3 {
    font-size: $font-size-base;
    font-weight: 600;
    color: $text-primary;
    margin: 0;
  }
}

.preview-container {
  height: 600px;
  overflow: auto;
  padding: 20px;
  background: $bg-secondary;
  
  .preview-placeholder {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: $text-tertiary;
    
    .placeholder-icon {
      font-size: 48px;
      margin-bottom: 12px;
    }
  }
  
  .pdf-preview-wrapper {
    height: 100%;
    background: white;
    box-shadow: $shadow-sm;
  }
  
  .docx-preview-wrapper {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100%;
    background: white;
    color: $text-secondary;
  }
  
  .preview-content {
    background: white;
    padding: 32px;
    min-height: 100%;
    box-shadow: $shadow-sm;
    
    .preview-paragraph {
      display: flex;
      gap: 12px;
      padding: 8px 0;
      line-height: 1.8;
      
      .para-number {
        color: $text-tertiary;
        font-size: $font-size-xs;
        min-width: 24px;
        text-align: right;
      }
      
      .para-text {
        color: $text-primary;
        flex: 1;
      }
    }
  }
}

.info-content {
  padding: 20px;
  
  .empty-review {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 40px;
    color: $text-tertiary;
    
    .empty-icon {
      font-size: 48px;
      margin-bottom: 12px;
    }
    
    p {
      margin-bottom: 16px;
    }
  }
  
  .review-info {
    .info-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px 0;
      border-bottom: 1px solid $border-light;
      
      &:last-child {
        border-bottom: none;
      }
      
      .info-label {
        color: $text-secondary;
        font-size: $font-size-sm;
      }
      
      .info-value {
        color: $text-primary;
        font-weight: 500;
        
        &.score {
          color: $primary-color;
          font-size: $font-size-lg;
        }
      }
      
      .risk-tags {
        display: flex;
        gap: 6px;
      }
    }
    
    .info-actions {
      margin-top: 20px;
      padding-top: 20px;
      border-top: 1px solid $border-light;
      
      .el-button {
        width: 100%;
      }
    }
  }
}

@media (max-width: 1200px) {
  .detail-content {
    grid-template-columns: 1fr;
  }
}
</style>
