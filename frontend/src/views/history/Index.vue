<template>
  <div class="history-page">
    <div class="page-header">
      <h1 class="page-title">审查历史</h1>
      <div class="header-actions">
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          style="width: 260px"
          @change="handleDateChange"
        />
        <el-input
          v-model="searchQuery"
          placeholder="搜索合同名称"
          clearable
          style="width: 240px"
          @keyup.enter="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>
    </div>
    
    <!-- 统计概览 -->
    <div class="stats-bar">
      <div class="stat-item">
        <span class="stat-label">总审查次数</span>
        <span class="stat-value">{{ stats.total }}</span>
      </div>
      <el-divider direction="vertical" />
      <div class="stat-item">
        <span class="stat-label">本月审查</span>
        <span class="stat-value">{{ stats.thisMonth }}</span>
      </div>
      <el-divider direction="vertical" />
      <div class="stat-item">
        <span class="stat-label">平均评分</span>
        <span class="stat-value">{{ stats.avgScore }}</span>
      </div>
      <el-divider direction="vertical" />
      <div class="stat-item">
        <span class="stat-label">发现问题</span>
        <span class="stat-value">{{ stats.totalIssues }}</span>
      </div>
    </div>
    
    <!-- 历史列表 -->
    <div class="history-card">
      <el-table
        v-loading="loading"
        :data="historyList"
        stripe
        @row-click="handleRowClick"
      >
        <el-table-column label="合同名称" min-width="220">
          <template #default="{ row }">
            <div class="contract-cell">
              <el-icon class="file-icon">
                <Document v-if="row.contractName?.endsWith('.pdf')" />
                <DocumentCopy v-else />
              </el-icon>
              <div class="contract-info">
                <div class="name">{{ row.contractName }}</div>
                <div class="size">{{ formatFileSize(row.fileSize) }}</div>
              </div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="审查编号" width="160">
          <template #default="{ row }">
            <span class="review-id">{{ row.reviewNo }}</span>
          </template>
        </el-table-column>
        
        <el-table-column label="风险统计" width="200">
          <template #default="{ row }">
            <div class="risk-stats">
              <el-tag
                type="danger"
                size="small"
                effect="light"
              >
                高 {{ row.riskSummary?.high ?? 0 }}
              </el-tag>
              <el-tag
                type="warning"
                size="small"
                effect="light"
              >
                中 {{ row.riskSummary?.medium ?? 0 }}
              </el-tag>
              <el-tag
                type="info"
                size="small"
                effect="light"
              >
                低 {{ row.riskSummary?.low ?? 0 }}
              </el-tag>
              <el-tag
                type="success"
                size="small"
                effect="light"
              >
                无 {{ row.riskSummary?.none ?? 0 }}
              </el-tag>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="审查得分" width="120">
          <template #default="{ row }">
            <div class="score-cell">
              <el-progress
                :percentage="row.overallScore || 0"
                :color="getScoreColor(row.overallScore || 0)"
                :stroke-width="6"
                :show-text="true"
              />
            </div>
          </template>
        </el-table-column>

        <el-table-column label="审查时间" width="160">
          <template #default="{ row }">
            {{ formatDate(row.createdAt) }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <div class="action-btns">
              <el-button
                type="primary"
                link
                size="small"
                @click.stop="viewReport(row)"
              >
                查看报告
              </el-button>
              <el-dropdown trigger="click" @command="(cmd) => handleCommand(cmd, row)">
                <el-button link size="small" @click.stop>
                  <el-icon><More /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="reReview">
                      <el-icon><RefreshRight /></el-icon>
                      <span>重新审查</span>
                    </el-dropdown-item>
                    <el-dropdown-item command="export">
                      <el-icon><Download /></el-icon>
                      <span>导出 PDF</span>
                    </el-dropdown-item>
                    <el-dropdown-item command="delete" divided>
                      <el-icon><Delete /></el-icon>
                      <span>删除记录</span>
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
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </div>

    <!-- 审查配置对话框 -->
    <ReviewOptionsDialog
      v-model:visible="reviewOptionsVisible"
      :loading="startingReview"
      @confirm="handleReviewOptionsConfirm"
    />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { formatDate, formatDateShort, formatFileSize } from '@/utils/helpers'
import { getReviewHistory, getReviewHistoryStats, deleteReview, reReview } from '@/api/review'
import { exportPdfReport } from '@/api/report'
import { getContractFileBlob } from '@/api/contract'
import ReviewOptionsDialog from '@/components/ReviewOptionsDialog.vue'

const router = useRouter()

const loading = ref(false)
const searchQuery = ref('')
const dateRange = ref(null)

// 统计数据
const stats = reactive({
  total: 0,
  thisMonth: 0,
  avgScore: 0,
  totalIssues: 0
})

// 分页
const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

// 历史记录列表
const historyList = ref([])

// 审查配置对话框
const reviewOptionsVisible = ref(false)
const startingReview = ref(false)
const currentRow = ref(null)

// 获取分数颜色
function getScoreColor(score) {
  if (score >= 80) return '#059669'
  if (score >= 60) return '#d97706'
  return '#dc2626'
}

// 搜索
function handleSearch() {
  pagination.page = 1
  loadData()
}

// 日期变化
function handleDateChange() {
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

// 加载统计数据
async function fetchStats() {
  try {
    const res = await getReviewHistoryStats()
    if (res.code === 200 && res.data) {
      const data = res.data
      stats.total = data.total || 0
      stats.thisMonth = data.thisMonth || 0
      stats.avgScore = data.avgScore || 0
      stats.totalIssues = data.totalIssues || 0
    }
  } catch (error) {
    console.error('获取审查历史统计失败:', error)
  }
}

// 加载数据
async function loadData() {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      pageSize: pagination.pageSize,
      keyword: searchQuery.value || undefined,
      startDate: dateRange.value?.[0] ? formatDateShort(dateRange.value[0]) : undefined,
      endDate: dateRange.value?.[1] ? formatDateShort(dateRange.value[1]) : undefined
    }
    const res = await getReviewHistory(params)
    if (res.code === 200 && res.data) {
      // 后端直接返回数组，不是 { list, total } 结构
      const list = Array.isArray(res.data) ? res.data : (res.data.list || [])
      historyList.value = list
      pagination.total = Array.isArray(res.data) ? list.length : (res.data.total || 0)
    }
  } catch (error) {
    console.error('获取审查历史列表失败:', error)
    ElMessage.error('获取数据失败')
  } finally {
    loading.value = false
  }
}

// 点击行
function handleRowClick(row) {
  viewReport(row)
}

// 查看报告 - 使用 reviewNo 转为数字作为路由参数
function viewReport(row) {
  console.log('[viewReport] row:', row)
  console.log('[viewReport] row.reviewNo:', row.reviewNo)
  console.log('[viewReport] row.reviewId:', row.reviewId)

  // 优先使用 reviewId，如果没有则从 reviewNo 中提取数字部分
  let reviewId = row.reviewId
  if (!reviewId && row.reviewNo) {
    // 处理格式如 "REV-000123"，提取数字部分
    const match = String(row.reviewNo).match(/\d+/)
    reviewId = match ? parseInt(match[0], 10) : null
  }

  console.log('[viewReport] parsed reviewId:', reviewId)

  if (!reviewId || isNaN(reviewId)) {
    ElMessage.error('报告ID无效，无法查看报告')
    return
  }

  router.push(`/report/${reviewId}`)
}

// 处理命令
function handleCommand(command, row) {
  switch (command) {
    case 'reReview':
      handleReReview(row)
      break
    case 'export':
      handleExport(row)
      break
    case 'delete':
      handleDelete(row)
      break
  }
}

// 重新审查 - 显示确认弹框
async function handleReReview(row) {
  try {
    await ElMessageBox.confirm(
      `确定要重新审查合同 "${row.contractName}" 吗？`,
      '确认重新审查',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    // 保存当前行数据，显示审查配置对话框
    currentRow.value = row
    reviewOptionsVisible.value = true
  } catch (error) {
    // 取消确认，不做任何操作
  }
}

// 处理审查配置确认
async function handleReviewOptionsConfirm(reviewOptions) {
  if (!currentRow.value) return

  startingReview.value = true
  try {
    // 获取合同文件
    const fileBlob = await getContractFileBlob(currentRow.value.contractId)
    const fileName = currentRow.value.contractName

    const res = await reReview(currentRow.value.reviewId, currentRow.value.contractId, fileBlob, fileName, reviewOptions)
    if (res.code === 200) {
      ElMessage.success('重新审查已开始')
      reviewOptionsVisible.value = false
      
      // 保存 reviewId 到 sessionStorage，以便审查页面连接 SSE
      const newReviewId = res.data?.reviewId || res.data?.review_id
      if (newReviewId) {
        sessionStorage.setItem('currentReviewId', String(newReviewId))
      }
      
      router.push(`/review/${currentRow.value.contractId}`)
    } else {
      ElMessage.error(res.message || '重新审查失败')
    }
  } catch (error) {
    console.error('重新审查失败:', error)
    ElMessage.error('重新审查失败: ' + (error.message || '未知错误'))
  } finally {
    startingReview.value = false
  }
}

// 导出 PDF
async function handleExport(row) {
  try {
    const reviewId = parseInt(row.reviewNo, 10)
    await exportPdfReport(reviewId, `${row.contractName}_审查报告.pdf`)
  } catch (error) {
    console.error('导出 PDF 失败:', error)
  }
}

// 删除记录
async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(
      `确定要删除审查记录 "${row.reviewId}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const res = await deleteReview(row.reviewId)
    if (res.code === 200) {
      ElMessage.success('删除成功')
      loadData()
      fetchStats()
    } else {
      ElMessage.error(res.message || '删除失败')
    }
  } catch {
    // 取消删除
  }
}

onMounted(() => {
  fetchStats()
  loadData()
})
</script>

<style scoped lang="scss">
.history-page {
  padding: 24px;
  max-width: 1440px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  
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

.stats-bar {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 16px 24px;
  background: white;
  border-radius: $radius-lg;
  margin-bottom: 20px;
  box-shadow: $shadow-sm;
  
  .stat-item {
    display: flex;
    align-items: center;
    gap: 8px;
    
    .stat-label {
      font-size: $font-size-sm;
      color: $text-secondary;
    }
    
    .stat-value {
      font-size: $font-size-lg;
      font-weight: 700;
      color: $primary-color;
    }
  }
}

.history-card {
  background: white;
  border-radius: $radius-lg;
  padding: 20px;
  box-shadow: $shadow-sm;
}

.contract-cell {
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
    }
    
    .size {
      font-size: $font-size-xs;
      color: $text-tertiary;
      margin-top: 2px;
    }
  }
}

.review-id {
  font-family: monospace;
  font-size: $font-size-sm;
  color: $text-secondary;
  background: $bg-secondary;
  padding: 4px 8px;
  border-radius: $radius-sm;
}

.risk-stats {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  
  .el-tag {
    font-weight: 500;
  }
  
  .no-risk {
    font-size: $font-size-sm;
    color: $success-color;
  }
}

.score-cell {
  width: 80px;
}

.action-btns {
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
</style>
