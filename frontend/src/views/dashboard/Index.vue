<template>
  <div class="dashboard-page">
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">仪表盘</h1>
        <p class="page-subtitle">欢迎回来，{{ userStore.userInfo?.nickName || userStore.username || '法务专员' }}</p>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="$router.push('/contract/upload')">
          <el-icon><Plus /></el-icon>
          <span>上传合同</span>
        </el-button>
      </div>
    </div>
    
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
    
    <!-- 快捷操作 -->
    <div class="quick-actions">
      <h3 class="section-title">快捷操作</h3>
      <div class="actions-grid">
        <div class="action-card" @click="$router.push('/contract/upload')">
          <div class="action-icon upload">
            <el-icon><Upload /></el-icon>
          </div>
          <div class="action-info">
            <div class="action-title">上传合同</div>
            <div class="action-desc">上传 PDF 或 Word 格式合同</div>
          </div>
          <el-icon class="action-arrow"><ArrowRight /></el-icon>
        </div>
        
        <div class="action-card" @click="$router.push('/contract/list')">
          <div class="action-icon list">
            <el-icon><DocumentCopy /></el-icon>
          </div>
          <div class="action-info">
            <div class="action-title">合同列表</div>
            <div class="action-desc">查看和管理所有合同</div>
          </div>
          <el-icon class="action-arrow"><ArrowRight /></el-icon>
        </div>
        
        <div class="action-card" @click="$router.push('/history')">
          <div class="action-icon history">
            <el-icon><Clock /></el-icon>
          </div>
          <div class="action-info">
            <div class="action-title">审查历史</div>
            <div class="action-desc">查看历史审查记录</div>
          </div>
          <el-icon class="action-arrow"><ArrowRight /></el-icon>
        </div>
        
        <div class="action-card" @click="$router.push('/knowledge')">
          <div class="action-icon knowledge">
            <el-icon><Collection /></el-icon>
          </div>
          <div class="action-info">
            <div class="action-title">法律知识库</div>
            <div class="action-desc">查询相关法律法规</div>
          </div>
          <el-icon class="action-arrow"><ArrowRight /></el-icon>
        </div>
      </div>
    </div>
    
    <!-- 下方内容区 -->
    <div class="dashboard-grid">
      <!-- 最近审查 -->
      <div class="dashboard-card recent-reviews">
        <div class="card-header">
          <h3 class="card-title">
            <el-icon><Clock /></el-icon>
            <span>最近审查</span>
          </h3>
          <el-button link type="primary" @click="$router.push('/history')">
            查看全部
          </el-button>
        </div>
        <div class="card-content">
          <div v-if="loadingReviews" class="empty-state">
            <el-icon class="empty-icon"><Loading /></el-icon>
            <p>加载中...</p>
          </div>
          <div v-else-if="recentReviews.length === 0" class="empty-state">
            <el-icon class="empty-icon"><Document /></el-icon>
            <p>暂无审查记录</p>
          </div>
          <div v-else class="review-list">
            <div
              v-for="review in recentReviews"
              :key="review.id"
              class="review-item"
              @click="viewReview(review)"
            >
              <div class="review-icon">
                <el-icon><Document /></el-icon>
              </div>
              <div class="review-info">
                <div class="review-name">{{ review.contractName }}</div>
                <div class="review-meta">
                  <span>{{ formatDate(review.reviewTime) }}</span>
                  <el-divider direction="vertical" />
                  <span>评分：{{ review.score }}分</span>
                </div>
              </div>
              <div class="review-status">
                <el-tag :type="getRiskType(review.riskLevel)" size="small">
                  {{ getRiskText(review.riskLevel) }}
                </el-tag>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 风险统计 -->
      <div class="dashboard-card risk-stats">
        <div class="card-header">
          <h3 class="card-title">
            <el-icon><PieChart /></el-icon>
            <span>风险统计</span>
          </h3>
        </div>
        <div class="card-content">
          <div ref="riskChart" class="chart-wrapper"></div>
          <div class="risk-legend">
            <div class="legend-item">
              <span class="legend-dot high"></span>
              <span class="legend-label">高风险</span>
              <span class="legend-value">{{ riskStats.high }}</span>
            </div>
            <div class="legend-item">
              <span class="legend-dot medium"></span>
              <span class="legend-label">中风险</span>
              <span class="legend-value">{{ riskStats.medium }}</span>
            </div>
            <div class="legend-item">
              <span class="legend-dot low"></span>
              <span class="legend-label">低风险</span>
              <span class="legend-value">{{ riskStats.low }}</span>
            </div>
            <div class="legend-item">
              <span class="legend-dot no-risk"></span>
              <span class="legend-label">无风险</span>
              <span class="legend-value">{{ riskStats.noRisk }}</span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 系统公告 -->
      <div class="dashboard-card announcements">
        <div class="card-header">
          <h3 class="card-title">
            <el-icon><Bell /></el-icon>
            <span>系统公告</span>
          </h3>
          <el-tag v-if="announcements.length > 0" type="info" size="small" effect="plain">
            共 {{ announcements.length }} 条
          </el-tag>
        </div>
        <div class="card-content">
          <div class="announcement-list" v-loading="loadingAnnouncements">
            <div v-if="announcements.length === 0" class="empty-announcements">
              <el-icon><InfoFilled /></el-icon>
              <span>暂无公告</span>
            </div>
            <div v-for="item in announcements" :key="item.id" class="announcement-item" :class="{ 'is-expanded': expandedItems[item.id] }">
              <div class="announcement-header" @click="toggleExpand(item.id)">
                <div class="announcement-dot" :class="getAnnouncementTypeClass(item.type)"></div>
                <div class="announcement-title-wrap">
                  <div class="announcement-title">{{ item.title }}</div>
                  <div class="announcement-meta">
                    <el-tag :type="getAnnouncementTypeTag(item.type)" size="small" effect="plain">
                      {{ getAnnouncementTypeText(item.type) }}
                    </el-tag>
                    <span class="announcement-time">{{ formatDate(item.publishTime) }}</span>
                  </div>
                </div>
                <el-icon class="expand-icon" :class="{ 'is-expanded': expandedItems[item.id] }">
                  <ArrowDown />
                </el-icon>
              </div>
              <div class="announcement-body" v-show="expandedItems[item.id]">
                <div class="announcement-desc markdown-content" v-html="processAnnouncementContent(item.content)"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { formatDate } from '@/utils/helpers'
import { processAnnouncementContent } from '@/utils/markdown'
import { getContractStats } from '@/api/contract'
import { getNoticeList } from '@/api/admin'
import { getReviewHistory } from '@/api/review'
import * as echarts from 'echarts'

const router = useRouter()
const userStore = useUserStore()
const riskChart = ref(null)

// 统计数据
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
  // 趋势数据
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
      
      // 更新风险统计数据用于图表
      riskStats.value.high = data.highRisk || 0
      riskStats.value.medium = data.mediumRisk || 0
      riskStats.value.low = data.lowRisk || 0
      riskStats.value.noRisk = data.none || 0
      
      // 更新图表
      updateChart()
    }
  } catch (error) {
    console.error('获取统计数据失败:', error)
  }
}

// 风险统计
const riskStats = ref({
  high: 0,
  medium: 0,
  low: 0,
  noRisk: 0
})

// 公告列表
const announcements = ref([])
const loadingAnnouncements = ref(false)
const expandedItems = ref({})

function toggleExpand(id) {
  expandedItems.value[id] = !expandedItems.value[id]
}

function getAnnouncementTypeClass(type) {
  const classMap = {
    system: 'type-system',
    feature: 'type-feature',
    maintenance: 'type-maintenance',
    other: 'type-other'
  }
  return classMap[type] || 'type-other'
}

function getAnnouncementTypeTag(type) {
  const tagMap = {
    system: '',
    feature: 'success',
    maintenance: 'warning',
    other: 'info'
  }
  return tagMap[type] || 'info'
}

function getAnnouncementTypeText(type) {
  const textMap = {
    system: '系统公告',
    feature: '功能更新',
    maintenance: '维护通知',
    other: '其他'
  }
  return textMap[type] || '其他'
}

// 获取公告列表
async function fetchAnnouncements() {
  loadingAnnouncements.value = true
  try {
    const res = await getNoticeList()
    if (res.code === 200 && res.data) {
      announcements.value = res.data
    }
  } catch (error) {
    console.error('获取公告列表失败:', error)
  } finally {
    loadingAnnouncements.value = false
  }
}

// 最近审查记录
const recentReviews = ref([])
const loadingReviews = ref(false)

// 加载最近审查记录
async function loadRecentReviews() {
  loadingReviews.value = true
  try {
    const res = await getReviewHistory({ page: 1, pageSize: 5 })
    if (res.code === 200 && res.data) {
      const list = res.data.list || res.data || []
      recentReviews.value = list.map(item => ({
        id: parseInt(item.reviewNo, 10) || item.reviewId || item.id,
        contractName: item.contractName || '未命名合同',
        reviewTime: item.reviewTime || item.createdAt,
        score: item.overallScore || item.score || 0,
        riskLevel: item.riskLevel || getRiskLevelFromScore(item.overallScore || item.score)
      }))
    }
  } catch (error) {
    console.error('加载最近审查记录失败:', error)
  } finally {
    loadingReviews.value = false
  }
}

// 根据分数获取风险等级
function getRiskLevelFromScore(score) {
  if (score > 90) return 'none'
  if (score >= 80) return 'low'
  if (score >= 60) return 'medium'
  return 'high'
}

// 获取风险类型
function getRiskType(level) {
  const map = {
    none: 'success',
    high: 'danger',
    medium: 'warning',
    low: 'info'
  }
  return map[level] || 'info'
}

// 获取风险文本
function getRiskText(level) {
  const map = {
    none: '无风险',
    high: '高风险',
    medium: '中风险',
    low: '低风险'
  }
  return map[level] || level
}

// 获取趋势样式类
function getTrendClass(trend) {
  if (trend > 0) return 'up'
  if (trend < 0) return 'down'
  return ''
}

// 格式化趋势值 - 显示周环比变化
function formatTrend(trend, currentValue) {
  if (trend === 0) return '环比持平'

  const sign = trend > 0 ? '+' : ''

  // 显示 "周环比 ±X%"
  return `周环比 ${sign}${trend}%`
}

// 查看审查详情
function viewReview(review) {
  router.push(`/report/${review.id}`)
}

// 初始化图表
function initChart() {
  if (!riskChart.value) return
  
  const chart = echarts.init(riskChart.value)
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)'
    },
    series: [
      {
        type: 'pie',
        radius: ['45%', '70%'],
        center: ['50%', '50%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 6,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: false
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 14,
            fontWeight: 'bold'
          }
        },
        data: [
          { value: riskStats.value.high, name: '高风险', itemStyle: { color: '#dc2626' } },
          { value: riskStats.value.medium, name: '中风险', itemStyle: { color: '#d97706' } },
          { value: riskStats.value.low, name: '低风险', itemStyle: { color: '#059669' } },
          { value: riskStats.value.noRisk, name: '无风险', itemStyle: { color: '#6b7280' } }
        ]
      }
    ]
  }
  
  chart.setOption(option)
  
  window.addEventListener('resize', () => chart.resize())
  
  // 将 chart 实例保存到 ref，以便后续更新
  riskChart._chartInstance = chart
}

// 更新图表数据
function updateChart() {
  if (riskChart._chartInstance) {
    riskChart._chartInstance.setOption({
      series: [{
        data: [
          { value: riskStats.value.high, name: '高风险', itemStyle: { color: '#dc2626' } },
          { value: riskStats.value.medium, name: '中风险', itemStyle: { color: '#d97706' } },
          { value: riskStats.value.low, name: '低风险', itemStyle: { color: '#059669' } },
          { value: riskStats.value.noRisk, name: '无风险', itemStyle: { color: '#6b7280' } }
        ]
      }]
    })
  }
}

onMounted(() => {
  fetchStats()
  fetchAnnouncements()
  loadRecentReviews()
  initChart()
})
</script>

<style scoped lang="scss">
.dashboard-page {
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
    .page-title {
      font-size: $font-size-2xl;
      font-weight: 600;
      color: $text-primary;
      margin: 0 0 4px 0;
    }
    
    .page-subtitle {
      font-size: $font-size-base;
      color: $text-secondary;
      margin: 0;
    }
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

// 快捷操作
.quick-actions {
  margin-bottom: 24px;
  
  .section-title {
    font-size: $font-size-lg;
    font-weight: 600;
    color: $text-primary;
    margin: 0 0 16px 0;
  }
}

.actions-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.action-card {
  display: flex;
  align-items: center;
  gap: 16px;
  background: white;
  padding: 20px;
  border-radius: $radius-lg;
  box-shadow: $shadow-sm;
  cursor: pointer;
  transition: all $transition-base;
  
  &:hover {
    box-shadow: $shadow-md;
    transform: translateY(-2px);
    
    .action-arrow {
      transform: translateX(4px);
    }
  }
  
  .action-icon {
    width: 48px;
    height: 48px;
    border-radius: $radius-md;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
    
    &.upload {
      background: rgba($primary-color, 0.1);
      color: $primary-color;
    }
    
    &.list {
      background: rgba($info-color, 0.1);
      color: $info-color;
    }
    
    &.history {
      background: rgba($warning-color, 0.1);
      color: $warning-color;
    }
    
    &.knowledge {
      background: rgba($success-color, 0.1);
      color: $success-color;
    }
  }
  
  .action-info {
    flex: 1;
    
    .action-title {
      font-weight: 600;
      color: $text-primary;
      margin-bottom: 2px;
    }
    
    .action-desc {
      font-size: $font-size-xs;
      color: $text-tertiary;
    }
  }
  
  .action-arrow {
    color: $text-tertiary;
    transition: transform $transition-fast;
  }
}

// 下方网格
.dashboard-grid {
  display: grid;
  grid-template-columns: 1.5fr 1fr;
  grid-template-rows: auto auto;
  gap: 20px;
}

.dashboard-card {
  background: white;
  border-radius: $radius-lg;
  box-shadow: $shadow-sm;
  overflow: hidden;
  
  .card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 20px;
    border-bottom: 1px solid $border-light;
    
    .card-title {
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
  }
  
  .card-content {
    padding: 16px 20px;
  }
}

.recent-reviews {
  grid-row: span 2;
  
  .review-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  
  .review-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px;
    background: $bg-secondary;
    border-radius: $radius-md;
    cursor: pointer;
    transition: all $transition-fast;
    
    &:hover {
      background: $bg-tertiary;
    }
    
    .review-icon {
      width: 40px;
      height: 40px;
      background: white;
      border-radius: $radius-sm;
      display: flex;
      align-items: center;
      justify-content: center;
      color: $primary-color;
      font-size: 20px;
    }
    
    .review-info {
      flex: 1;
      min-width: 0;
      
      .review-name {
        font-weight: 500;
        color: $text-primary;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
      
      .review-meta {
        font-size: $font-size-xs;
        color: $text-tertiary;
        margin-top: 2px;
      }
    }
  }
}

.risk-stats {
  .chart-wrapper {
    height: 180px;
  }
  
  .risk-legend {
    display: flex;
    justify-content: center;
    gap: 24px;
    margin-top: 16px;
    
    .legend-item {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: $font-size-sm;
      
      .legend-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        
        &.high { background: $risk-high; }
        &.medium { background: $risk-medium; }
        &.low { background: $success-color; }
        &.no-risk { background: #6b7280; }
      }
      
      .legend-label {
        color: $text-secondary;
      }
      
      .legend-value {
        font-weight: 600;
        color: $text-primary;
      }
    }
  }
}

.announcements {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .announcement-list {
    display: flex;
    flex-direction: column;
    gap: 12px;

    .empty-announcements {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 8px;
      color: $text-tertiary;
      padding: 40px 0;
      font-size: $font-size-sm;

      .el-icon {
        font-size: 32px;
        opacity: 0.5;
      }
    }
  }

  .announcement-item {
    background: #fff;
    border-radius: 8px;
    border: 1px solid #e4e7ed;
    overflow: hidden;
    transition: all 0.3s ease;

    &:hover {
      border-color: $primary-color;
      box-shadow: 0 2px 8px rgba($primary-color, 0.1);
    }

    &.is-expanded {
      border-color: $primary-color;
      box-shadow: 0 2px 12px rgba($primary-color, 0.15);
    }

    .announcement-header {
      display: flex;
      align-items: flex-start;
      gap: 12px;
      padding: 14px 16px;
      cursor: pointer;
      transition: background-color 0.2s ease;

      &:hover {
        background-color: #f8f9fa;
      }
    }

    .announcement-dot {
      width: 10px;
      height: 10px;
      border-radius: 50%;
      margin-top: 4px;
      flex-shrink: 0;
      transition: transform 0.2s ease;

      &.type-system {
        background: $primary-color;
        box-shadow: 0 0 0 3px rgba($primary-color, 0.2);
      }

      &.type-feature {
        background: $success-color;
        box-shadow: 0 0 0 3px rgba($success-color, 0.2);
      }

      &.type-maintenance {
        background: $warning-color;
        box-shadow: 0 0 0 3px rgba($warning-color, 0.2);
      }

      &.type-other {
        background: #909399;
        box-shadow: 0 0 0 3px rgba(144, 147, 153, 0.2);
      }
    }

    .announcement-title-wrap {
      flex: 1;
      min-width: 0;

      .announcement-title {
        font-weight: 600;
        color: $text-primary;
        font-size: 15px;
        line-height: 1.4;
        margin-bottom: 6px;
      }

      .announcement-meta {
        display: flex;
        align-items: center;
        gap: 12px;

        .announcement-time {
          font-size: $font-size-xs;
          color: $text-tertiary;
        }
      }
    }

    .expand-icon {
      font-size: 16px;
      color: $text-tertiary;
      transition: transform 0.3s ease, color 0.2s ease;
      margin-top: 4px;
      flex-shrink: 0;

      &.is-expanded {
        transform: rotate(180deg);
        color: $primary-color;
      }
    }

    .announcement-body {
      padding: 0 16px 16px 38px;
      animation: slideDown 0.3s ease;
    }

    .announcement-desc {
      font-size: $font-size-sm;
      color: $text-secondary;
      line-height: 1.6;
      padding-top: 12px;
      border-top: 1px solid #f0f0f0;

      &.markdown-content {
        h1, h2, h3, h4, h5, h6 {
          margin: 12px 0 8px;
          font-weight: 600;
          color: $text-primary;
        }
        h1 { font-size: 18px; }
        h2 { font-size: 16px; }
        h3 { font-size: 15px; }
        h4, h5, h6 { font-size: 14px; }

        strong { font-weight: 600; color: $text-primary; }
        em { font-style: italic; }
        del { text-decoration: line-through; }

        code {
          background: rgba($primary-color, 0.08);
          padding: 2px 6px;
          border-radius: 4px;
          font-family: 'Courier New', monospace;
          font-size: 12px;
          color: $primary-color;
        }

        pre {
          background: #f5f7fa;
          padding: 12px;
          border-radius: 8px;
          overflow-x: auto;
          margin: 8px 0;
          code {
            background: none;
            padding: 0;
            color: #333;
          }
        }

        a {
          color: $primary-color;
          text-decoration: none;
          &:hover { text-decoration: underline; }
        }

        ul, ol {
          margin: 8px 0;
          padding-left: 24px;
        }

        ul {
          list-style: disc;
        }

        ol {
          list-style: decimal;
        }

        li {
          margin: 4px 0;
          line-height: 1.6;
        }

        blockquote {
          border-left: 3px solid $primary-color;
          padding-left: 12px;
          margin: 8px 0;
          color: $text-secondary;
          font-style: italic;
        }

        hr {
          border: none;
          border-top: 1px solid #e4e7ed;
          margin: 12px 0;
        }

        p {
          margin: 8px 0;
        }

        br {
          display: block;
          content: "";
          margin-top: 4px;
        }
      }
    }
  }
}

@keyframes slideDown {
  from {
    opacity: 0;
    max-height: 0;
  }
  to {
    opacity: 1;
    max-height: 1000px;
  }
}

.empty-state {
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
}

@media (max-width: 1200px) {
  .stats-section {
    .stats-row {
      grid-template-columns: repeat(2, 1fr);
    }
  }
  
  .actions-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
  
  .recent-reviews {
    grid-row: span 1;
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
