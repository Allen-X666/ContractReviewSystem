<template>
  <div class="contract-list-page">
    <div class="page-header">
      <h1 class="page-title">合同列表</h1>
      <div class="header-actions">
        <el-button type="primary" @click="$router.push('/contract/upload')">
          <el-icon><Plus /></el-icon>
          <span>上传合同</span>
        </el-button>
      </div>
    </div>
    
    <!-- 文件预览对话框 -->
    <FilePreviewDialog ref="previewDialogRef" />
    
    <!-- 审查选项对话框 -->
    <ReviewOptionsDialog
      v-model:visible="reviewOptionsVisible"
      :loading="startingReview"
      @confirm="handleReviewConfirm"
    />
    
    <!-- 统计卡片 -->
    <div class="stats-section">
      <!-- 第一行：基础统计 -->
      <div class="stats-row">
        <div class="stat-card primary">
          <div class="stat-icon">
            <el-icon><Document /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.total }}</div>
            <div class="stat-label">合同总数</div>
            <div class="stat-trend" :class="getTrendClass(stats.totalTrend)">
              <el-icon>
                <ArrowUp v-if="stats.totalTrend > 0" />
                <ArrowDown v-else-if="stats.totalTrend < 0" />
                <Minus v-else />
              </el-icon>
              <span>{{ formatTrend(stats.totalTrend) }}</span>
            </div>
          </div>
        </div>
        <div class="stat-card success">
          <div class="stat-icon">
            <el-icon><CircleCheck /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.completed }}</div>
            <div class="stat-label">已审查</div>
            <div class="stat-trend" :class="getTrendClass(stats.completedTrend)">
              <el-icon>
                <ArrowUp v-if="stats.completedTrend > 0" />
                <ArrowDown v-else-if="stats.completedTrend < 0" />
                <Minus v-else />
              </el-icon>
              <span>{{ formatTrend(stats.completedTrend) }}</span>
            </div>
          </div>
        </div>
        <div class="stat-card warning">
          <div class="stat-icon">
            <el-icon><Timer /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.pending }}</div>
            <div class="stat-label">待审查</div>
            <div class="stat-trend" :class="getTrendClass(stats.pendingTrend)">
              <el-icon>
                <ArrowUp v-if="stats.pendingTrend > 0" />
                <ArrowDown v-else-if="stats.pendingTrend < 0" />
                <Minus v-else />
              </el-icon>
              <span>{{ formatTrend(stats.pendingTrend) }}</span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 第二行：风险等级统计 -->
      <div class="stats-row">
        <div class="stat-card danger">
          <div class="stat-icon">
            <el-icon><Warning /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.highRisk }}</div>
            <div class="stat-label">高风险合同</div>
            <div class="stat-trend" :class="getTrendClass(stats.highRiskTrend)">
              <el-icon>
                <ArrowUp v-if="stats.highRiskTrend > 0" />
                <ArrowDown v-else-if="stats.highRiskTrend < 0" />
                <Minus v-else />
              </el-icon>
              <span>{{ formatTrend(stats.highRiskTrend) }}</span>
            </div>
          </div>
        </div>
        <div class="stat-card medium">
          <div class="stat-icon">
            <el-icon><WarningFilled /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.mediumRisk }}</div>
            <div class="stat-label">中风险合同</div>
            <div class="stat-trend" :class="getTrendClass(stats.mediumRiskTrend)">
              <el-icon>
                <ArrowUp v-if="stats.mediumRiskTrend > 0" />
                <ArrowDown v-else-if="stats.mediumRiskTrend < 0" />
                <Minus v-else />
              </el-icon>
              <span>{{ formatTrend(stats.mediumRiskTrend) }}</span>
            </div>
          </div>
        </div>
        <div class="stat-card low">
          <div class="stat-icon">
            <el-icon><CircleCheck /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.lowRisk }}</div>
            <div class="stat-label">低风险合同</div>
            <div class="stat-trend" :class="getTrendClass(stats.lowRiskTrend)">
              <el-icon>
                <ArrowUp v-if="stats.lowRiskTrend > 0" />
                <ArrowDown v-else-if="stats.lowRiskTrend < 0" />
                <Minus v-else />
              </el-icon>
              <span>{{ formatTrend(stats.lowRiskTrend) }}</span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 第三行：无风险、平均得分和最高最低得分 -->
      <div class="stats-row">
        <div class="stat-card info">
          <div class="stat-icon">
            <el-icon><SuccessFilled /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.noRisk }}</div>
            <div class="stat-label">无风险合同</div>
            <div class="stat-trend" :class="getTrendClass(stats.noRiskTrend)">
              <el-icon>
                <ArrowUp v-if="stats.noRiskTrend > 0" />
                <ArrowDown v-else-if="stats.noRiskTrend < 0" />
                <Minus v-else />
              </el-icon>
              <span>{{ formatTrend(stats.noRiskTrend) }}</span>
            </div>
          </div>
        </div>
        <div class="stat-card purple">
          <div class="stat-icon">
            <el-icon><TrendCharts /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.avgScore }}</div>
            <div class="stat-label">平均得分</div>
            <div class="stat-trend" :class="getTrendClass(stats.avgScoreTrend)">
              <el-icon>
                <ArrowUp v-if="stats.avgScoreTrend > 0" />
                <ArrowDown v-else-if="stats.avgScoreTrend < 0" />
                <Minus v-else />
              </el-icon>
              <span>{{ formatTrend(stats.avgScoreTrend) }}</span>
            </div>
          </div>
        </div>
        <div class="stat-card score-range-card">
          <div class="score-range-content">
            <div class="score-item">
              <div class="score-icon-small score-icon-high">
                <el-icon><Trophy /></el-icon>
              </div>
              <div class="score-info">
                <div class="score-value">{{ stats.maxScore }}</div>
                <div class="score-label">最高得分</div>
                <div class="score-trend-mini" :class="getTrendClass(stats.maxScoreTrend)">
                  <el-icon>
                    <ArrowUp v-if="stats.maxScoreTrend > 0" />
                    <ArrowDown v-else-if="stats.maxScoreTrend < 0" />
                    <Minus v-else />
                  </el-icon>
                  <span>{{ formatTrend(stats.maxScoreTrend) }}</span>
                </div>
              </div>
            </div>
            <div class="score-divider"></div>
            <div class="score-item">
              <div class="score-icon-small score-icon-low">
                <el-icon><Warning /></el-icon>
              </div>
              <div class="score-info">
                <div class="score-value">{{ stats.minScore }}</div>
                <div class="score-label">最低得分</div>
                <div class="score-trend-mini" :class="getTrendClass(stats.minScoreTrend)">
                  <el-icon>
                    <ArrowUp v-if="stats.minScoreTrend > 0" />
                    <ArrowDown v-else-if="stats.minScoreTrend < 0" />
                    <Minus v-else />
                  </el-icon>
                  <span>{{ formatTrend(stats.minScoreTrend) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 合同列表 -->
    <div class="list-card">
      <!-- 列表工具栏 -->
      <div class="list-toolbar">
        <el-input
          v-model="searchQuery"
          placeholder="搜索合同名称"
          clearable
          style="width: 280px"
          @keyup.enter="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>
      <el-table
        v-loading="contractStore.loading"
        :data="contractStore.contractList"
        stripe
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="50" />

        <el-table-column label="合同编号" width="80">
          <template #default="{ row }">
            <span class="contract-id">{{ row.id }}</span>
          </template>
        </el-table-column>

        <el-table-column label="合同名称" min-width="200">
          <template #default="{ row }">
            <div class="contract-name-cell">
              <el-icon class="file-icon">
                <Document v-if="row.fileName?.endsWith('.pdf')" />
                <DocumentCopy v-else />
              </el-icon>
              <div class="contract-info">
                <div class="name" :title="row.fileName">{{ row.fileName }}</div>
                <div class="size">{{ formatFileSize(row.fileSize) }}</div>
              </div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="审查状态" width="120">
          <template #default="{ row }">
            <div v-if="row.reviewStatus" class="review-status">
              <el-tag
                :type="getReviewStatusType(row.reviewStatus)"
                size="small"
                effect="light"
              >
                {{ getReviewStatusText(row.reviewStatus) }}
              </el-tag>
            </div>
            <span v-else class="no-data">未审查</span>
          </template>
        </el-table-column>

        <el-table-column label="风险等级" width="120">
          <template #default="{ row }">
            <div v-if="row.riskLevel" class="risk-level">
              <el-tag
                :type="getRiskTagType(row.riskLevel)"
                size="small"
                effect="light"
              >
                {{ getRiskLevelDisplayText(row.riskLevel) }}
              </el-tag>
            </div>
            <span v-else class="no-data">未审查</span>
          </template>
        </el-table-column>

        <el-table-column label="审查得分" width="100">
          <template #default="{ row }">
            <div v-if="row.reviewScore !== undefined && row.reviewScore !== null" class="review-score">
              <el-progress
                :percentage="row.reviewScore"
                :color="getScoreColor(row.reviewScore)"
                :stroke-width="8"
                :show-text="true"
              />
            </div>
            <span v-else class="no-data">未审查</span>
          </template>
        </el-table-column>
        
        <el-table-column label="上传时间" width="160">
          <template #default="{ row }">
            {{ formatDate(row.createdAt) }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button
                v-if="row.reviewStatus === 'completed'"
                type="primary"
                link
                size="small"
                @click="viewReport(row)"
              >
                查看报告
              </el-button>
              <el-button
                v-else
                type="primary"
                link
                size="small"
                @click="startReview(row)"
              >
                开始审查
              </el-button>
              <el-button
                type="primary"
                link
                size="small"
                @click="previewContract(row)"
              >
                预览
              </el-button>
              <el-dropdown trigger="click" @command="(cmd) => handleCommand(cmd, row)">
                <el-button link size="small">
                  <el-icon><More /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="download">
                      <el-icon><Download /></el-icon>
                      <span>下载</span>
                    </el-dropdown-item>
                    <el-dropdown-item command="delete" divided>
                      <el-icon><Delete /></el-icon>
                      <span>删除</span>
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="contractStore.pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useContractStore } from '@/stores/contract'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  formatDate,
  formatFileSize,
  formatReviewStatus,
  formatRiskLevel
} from '@/utils/helpers'
import {
  REVIEW_STATUS,
  REVIEW_STATUS_TYPE,
  RISK_LEVEL_TAG_TYPE
} from '@/utils/constants'
import { getContractStats, getContractFileBlob, downloadContract as downloadContractApi } from '@/api/contract'
import { getLatestReviewByContractId } from '@/api/review'
import { useReviewStarter } from '@/composables/useReviewStarter'
import FilePreviewDialog from '@/components/preview/FilePreviewDialog.vue'
import ReviewOptionsDialog from '@/components/ReviewOptionsDialog.vue'

const router = useRouter()
const contractStore = useContractStore()
const previewDialogRef = ref(null)

const searchQuery = ref('')
const selectedContracts = ref([])
const pagination = reactive({
  page: 1,
  pageSize: 10
})

// 使用审查启动组合式函数
const {
  reviewOptionsVisible,
  startingReview,
  pendingContract: pendingReviewContract,
  startReview,
  handleReviewConfirm
} = useReviewStarter()

// 统计数据（从后端获取）
const stats = reactive({
  total: 0,
  pending: 0,
  completed: 0,
  highRisk: 0,
  mediumRisk: 0,
  lowRisk: 0,
  noRisk: 0,
  avgScore: 0,
  maxScore: 0,
  minScore: 0,
  // 趋势数据（本周vs上周）
  totalTrend: 0,
  pendingTrend: 0,
  completedTrend: 0,
  highRiskTrend: 0,
  mediumRiskTrend: 0,
  lowRiskTrend: 0,
  noRiskTrend: 0,
  avgScoreTrend: 0,
  maxScoreTrend: 0,
  minScoreTrend: 0
})

// 获取审查状态文本
function getReviewStatusText(status) {
  return formatReviewStatus(status)
}

// 获取审查状态标签类型
function getReviewStatusType(status) {
  return REVIEW_STATUS_TYPE[status] || 'info'
}

// 获取风险等级文本
function getRiskLevelText(level) {
  return formatRiskLevel(level)
}

// 获取风险标签类型
function getRiskTagType(level) {
  const typeMap = {
    'none': 'success',
    'NONE': 'success',
    'low': 'info',
    'LOW': 'info',
    'medium': 'warning',
    'MEDIUM': 'warning',
    'high': 'danger',
    'HIGH': 'danger'
  }
  return typeMap[level] || RISK_LEVEL_TAG_TYPE[level] || 'info'
}

// 根据分数获取风险等级文本
function getRiskLevelTextByScore(score) {
  if (score > 90) return '无风险'
  if (score >= 80) return '低风险'
  if (score >= 60) return '中风险'
  return '高风险'
}

// 根据分数获取风险标签类型
function getRiskTagTypeByScore(score) {
  if (score > 90) return 'success'
  if (score >= 80) return 'info'
  if (score >= 60) return 'warning'
  return 'danger'
}

// 将风险等级代码转换为显示文本
function getRiskLevelDisplayText(riskLevel) {
  const textMap = {
    'none': '无风险',
    'NONE': '无风险',
    'low': '低风险',
    'LOW': '低风险',
    'medium': '中风险',
    'MEDIUM': '中风险',
    'high': '高风险',
    'HIGH': '高风险'
  }
  return textMap[riskLevel] || riskLevel
}

// 获取分数颜色
function getScoreColor(score) {
  if (score >= 80) return '#059669'
  if (score >= 60) return '#d97706'
  return '#dc2626'
}

// 获取趋势样式类
function getTrendClass(trend) {
  if (trend > 0) return 'up'
  if (trend < 0) return 'down'
  return ''
}

// 格式化趋势值
function formatTrend(trend) {
  if (trend === 0) return '持平'
  const sign = trend > 0 ? '+' : ''
  return `${sign}${trend}%`
}

// 选择变化
function handleSelectionChange(selection) {
  selectedContracts.value = selection
}

// 搜索
function handleSearch() {
  pagination.page = 1
  loadData()
}

// 分页大小变化
function handleSizeChange(size) {
  pagination.pageSize = size
  pagination.page = 1
  loadData()
}

// 页码变化
function handlePageChange(page) {
  pagination.page = page
  loadData()
}

// 加载数据
async function loadData() {
  await contractStore.fetchContractList({
    page: pagination.page,
    pageSize: pagination.pageSize,
    keyword: searchQuery.value
  })
}

// 获取统计数据
async function fetchStats() {
  try {
    const res = await getContractStats()
    if (res.code === 200 && res.data) {
      const data = res.data
      stats.total = data.total || 0
      stats.pending = data.pending || 0
      stats.completed = data.completed || 0
      stats.highRisk = data.highRisk || 0
      stats.mediumRisk = data.mediumRisk || 0
      stats.lowRisk = data.lowRisk || 0
      stats.noRisk = data.noRisk || 0
      stats.avgScore = data.avgScore || 0
      stats.maxScore = data.maxScore || 0
      stats.minScore = data.minScore || 0
      // 趋势数据
      stats.totalTrend = data.totalTrend || 0
      stats.pendingTrend = data.pendingTrend || 0
      stats.completedTrend = data.completedTrend || 0
      stats.highRiskTrend = data.highRiskTrend || 0
      stats.mediumRiskTrend = data.mediumRiskTrend || 0
      stats.lowRiskTrend = data.lowRiskTrend || 0
      stats.noRiskTrend = data.noRiskTrend || 0
      stats.avgScoreTrend = data.avgScoreTrend || 0
      stats.maxScoreTrend = data.maxScoreTrend || 0
      stats.minScoreTrend = data.minScoreTrend || 0
    }
  } catch (error) {
    console.error('获取统计数据失败:', error)
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
async function viewReport(row) {
  console.log('[viewReport] row:', row)
  console.log('[viewReport] row.lastReviewId:', row.lastReviewId)
  console.log('[viewReport] row.id (contractId):', row.id)

  // 优先使用 row 中的 lastReviewId
  if (row.lastReviewId) {
    console.log('[viewReport] 使用 row.lastReviewId:', row.lastReviewId)
    router.push(`/report/${row.lastReviewId}`)
    return
  }

  // 调用 API 获取最新的审查记录
  try {
    console.log('[viewReport] 调用 getLatestReviewByContractId, contractId:', row.id)
    const res = await getLatestReviewByContractId(row.id)
    console.log('[viewReport] getLatestReviewByContractId 返回:', res)

    if (res.code === 200 && res.data) {
      // 使用 reviewId 作为路由参数
      const reviewId = res.data.reviewId
      console.log('[viewReport] 获取到 reviewId:', reviewId)
      if (reviewId) {
        router.push(`/report/${reviewId}`)
      } else {
        ElMessage.warning('暂无审查报告')
      }
    } else {
      ElMessage.warning('暂无审查报告')
    }
  } catch (error) {
    console.error('获取审查记录失败:', error)
    ElMessage.warning('暂无审查报告')
  }
}

// 预览合同（直接使用列表行数据，无需额外请求预览信息）
async function previewContract(row) {
  try {
    const fileName = row.fileName
    const fileType = row.fileType
    const previewableTypes = ['pdf', 'docx', 'doc', 'txt', 'text', 'md', 'json', 'xml', 'yaml', 'yml', 'csv', 'log']

    if (!previewableTypes.includes(fileType?.toLowerCase())) {
      ElMessage.warning('暂不支持该文件类型的预览，请下载后查看')
      return
    }

    const fileBlob = await getContractFileBlob(row.id)
    previewDialogRef.value?.open(fileBlob, fileName, fileType)
  } catch (error) {
    console.error('预览合同失败:', error)
    ElMessage.error(error.message || '预览失败，请稍后重试')
  }
}

// 处理下拉菜单命令
function handleCommand(command, row) {
  switch (command) {
    case 'download':
      downloadContract(row)
      break
    case 'delete':
      handleDelete(row)
      break
  }
}

// 下载合同
async function downloadContract(row) {
  try {
    await downloadContractApi(row.id, row.fileName)
  } catch (error) {
    console.error('下载合同失败:', error)
  }
}

// 删除合同
async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(
      `确定要删除合同 "${row.fileName}" 吗？删除后将无法恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await contractStore.removeContract(row.id)
    await loadData()
    await fetchStats()
  } catch {
    // 取消删除
  }
}

onMounted(() => {
  loadData()
  fetchStats()
})
</script>

<style scoped lang="scss">
.contract-list-page {
  padding: 24px;
  max-width: 1440px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
  
  .page-title {
    font-size: $font-size-xl;
    font-weight: 600;
    color: $text-primary;
    margin: 0;
  }
  
  .header-actions {
    display: flex;
    gap: 12px;
  }
}

// 统计卡片
.stats-section {
  margin-bottom: 24px;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-bottom: 20px;
  
  &:last-child {
    margin-bottom: 0;
  }
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  background: white;
  padding: 24px;
  border-radius: $radius-lg;
  box-shadow: $shadow-sm;
  transition: all $transition-base;
  
  &:hover {
    box-shadow: $shadow-md;
    transform: translateY(-2px);
  }
  
  &.primary .stat-icon {
    background: rgba($primary-color, 0.1);
    color: $primary-color;
  }
  
  &.success .stat-icon {
    background: rgba($success-color, 0.1);
    color: $success-color;
  }
  
  &.warning .stat-icon {
    background: rgba($warning-color, 0.1);
    color: $warning-color;
  }
  
  &.danger .stat-icon {
    background: rgba($danger-color, 0.1);
    color: $danger-color;
  }
  
  &.medium .stat-icon {
    background: rgba(#f97316, 0.1);
    color: #f97316;
  }
  
  &.low .stat-icon {
    background: rgba(#3b82f6, 0.1);
    color: #3b82f6;
  }
  
  &.info .stat-icon {
    background: rgba(#10b981, 0.1);
    color: #10b981;
  }
  
  &.purple .stat-icon {
    background: rgba(#8b5cf6, 0.1);
    color: #8b5cf6;
  }
  
  &.score-range-card {
    .score-range-content {
      display: flex;
      align-items: center;
      justify-content: space-around;
      flex: 1;
      
      .score-item {
        display: flex;
        align-items: center;
        gap: 12px;
        
        .score-icon-small {
          width: 40px;
          height: 40px;
          border-radius: $radius-md;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 20px;
          
          &.score-icon-high {
            background: rgba(#f59e0b, 0.1);
            color: #f59e0b;
          }
          
          &.score-icon-low {
            background: rgba(#ef4444, 0.1);
            color: #ef4444;
          }
        }
        
        .score-info {
          .score-value {
            font-size: 24px;
            font-weight: 700;
            color: $text-primary;
            line-height: 1;
          }
          
          .score-label {
            font-size: $font-size-xs;
            color: $text-secondary;
            margin-top: 2px;
          }
          
          .score-trend-mini {
            display: flex;
            align-items: center;
            gap: 2px;
            font-size: 11px;
            margin-top: 4px;
            
            &.up {
              color: $success-color;
            }
            
            &.down {
              color: $danger-color;
            }
          }
        }
      }
      
      .score-divider {
        width: 1px;
        height: 40px;
        background: $border-light;
      }
    }
  }
  
  &.placeholder {
    background: transparent;
    box-shadow: none;
    pointer-events: none;
  }
  
  .stat-icon {
    width: 56px;
    height: 56px;
    border-radius: $radius-lg;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 28px;
  }
  
  .stat-content {
    flex: 1;
    
    .stat-value {
      font-size: 32px;
      font-weight: 700;
      color: $text-primary;
      line-height: 1;
    }
    
    .stat-label {
      font-size: $font-size-sm;
      color: $text-secondary;
      margin-top: 4px;
    }
    
    .stat-trend {
      display: flex;
      align-items: center;
      gap: 4px;
      font-size: $font-size-xs;
      margin-top: 8px;
      
      &.up {
        color: $success-color;
      }
      
      &.down {
        color: $danger-color;
      }
    }
  }
}

.list-card {
  background: white;
  border-radius: $radius-lg;
  padding: 20px;
  box-shadow: $shadow-sm;

  .list-toolbar {
    display: flex;
    justify-content: flex-end;
    margin-bottom: 16px;
  }
}

.contract-name-cell {
  display: flex;
  align-items: center;
  gap: 12px;
  
  .file-icon {
    font-size: 24px;
    color: $primary-color;
  }
  
  .contract-info {
    .name {
      font-weight: 500;
      color: $text-primary;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      max-width: 200px;
    }
    
    .size {
      font-size: $font-size-xs;
      color: $text-tertiary;
      margin-top: 2px;
    }
  }
}

.risk-level {
  .el-tag {
    font-weight: 500;
  }
}

.review-score {
  width: 80px;
}

.no-data {
  color: $text-tertiary;
}

.action-buttons {
  display: flex;
  align-items: center;
  gap: 4px;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  padding-top: 20px;
  border-top: 1px solid $border-light;
  margin-top: 20px;
}

@media (max-width: 1200px) {
  .stats-section {
    .stats-row {
      grid-template-columns: repeat(2, 1fr);
    }
  }
}

@media (max-width: 768px) {
  .stats-section {
    .stats-row {
      grid-template-columns: 1fr;
    }
  }
  
  .score-range-content {
    flex-direction: column;
    gap: 16px;
    
    .score-divider {
      width: 100%;
      height: 1px;
    }
  }
}
</style>
