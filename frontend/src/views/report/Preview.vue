<template>
  <div class="report-preview-page">
    <!-- 页面头部 -->
    <div class="report-header">
      <div class="header-left">
        <el-button link @click="$router.back()">
          <el-icon><ArrowLeft /></el-icon>
        </el-button>
        <h1 class="page-title">审查报告</h1>
      </div>
      <div class="header-actions">
        <el-button @click="printReport">
          <el-icon><Printer /></el-icon>
          <span>打印</span>
        </el-button>
        <el-dropdown @command="handleExport">
          <el-button type="primary">
            <el-icon><Download /></el-icon>
            <span>导出报告</span>
            <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="pdf">
                <el-icon><DocumentChecked /></el-icon>
                <span>导出 PDF</span>
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>
    
    <!-- 报告内容 -->
    <div class="report-container" ref="reportContent">
      <div class="report-paper">
        <!-- 报告封面 -->
        <div class="report-cover">
          <div class="cover-header">
            <div class="company-logo">
              <el-icon><OfficeBuilding /></el-icon>
            </div>
            <h1 class="cover-title">{{ reportData.title || '合同审查报告' }}</h1>
            <div class="cover-subtitle">Contract Review Report</div>
          </div>
          
          <div class="cover-info">
            <div class="info-row">
              <span class="info-label">合同名称</span>
              <span class="info-value">{{ reportData.contractName }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">审查编号</span>
              <span class="info-value">{{ reportData.reviewNo }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">审查时间</span>
              <span class="info-value">{{ formatDate(reportData.completedAt) }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">审查机构</span>
              <span class="info-value">{{ reportData.reviewAgency || '智能合同审查系统' }}</span>
            </div>
          </div>
          
          <div class="cover-score">
            <div class="score-circle" :style="scoreCircleStyle">
              <div class="score-value">{{ reportData.overallScore }}</div>
              <div class="score-label">综合评分</div>
            </div>
            <div class="score-assessment" :class="assessmentLevel">
              {{ assessmentText }}
            </div>
          </div>
        </div>
        
        <!-- 分页：审查概览 -->
        <div class="report-section">
          <h2 class="section-title">
            <span class="section-number">一</span>
            审查概览
          </h2>
          
          <div class="overview-content">
            <div class="overview-stats">
              <div class="stat-box">
                <div class="stat-icon high">
                  <el-icon><Warning /></el-icon>
                </div>
                <div class="stat-info">
                  <div class="stat-value">{{ reportData.riskSummary?.high || 0 }}</div>
                  <div class="stat-label">高风险</div>
                </div>
              </div>
              <div class="stat-box">
                <div class="stat-icon medium">
                  <el-icon><WarningFilled /></el-icon>
                </div>
                <div class="stat-info">
                  <div class="stat-value">{{ reportData.riskSummary?.medium || 0 }}</div>
                  <div class="stat-label">中风险</div>
                </div>
              </div>
              <div class="stat-box">
                <div class="stat-icon low">
                  <el-icon><InfoFilled /></el-icon>
                </div>
                <div class="stat-info">
                  <div class="stat-value">{{ reportData.riskSummary?.low || 0 }}</div>
                  <div class="stat-label">低风险</div>
                </div>
              </div>
              <div class="stat-box">
                <div class="stat-icon none">
                  <el-icon><CircleCheck /></el-icon>
                </div>
                <div class="stat-info">
                  <div class="stat-value">{{ reportData.riskSummary?.none || 0 }}</div>
                  <div class="stat-label">无风险</div>
                </div>
              </div>
            </div>
            
            <div class="overview-chart">
              <div ref="riskChart" class="chart-container"></div>
            </div>
            
            <div class="overview-summary">
              <h4>审查结论</h4>
              <p>{{ reportData.conclusion || '经系统审查，本合同存在若干需要关注的风险点，建议根据修改建议进行调整后再签署。' }}</p>
            </div>
          </div>
        </div>
        
        <!-- 分页：风险详情 -->
        <div class="report-section">
          <h2 class="section-title">
            <span class="section-number">二</span>
            风险详情
          </h2>
          
          <div class="risks-content">
            <div
              v-for="(risk, index) in reportData.risks"
              :key="risk.id"
              class="risk-detail-item"
              :class="`risk-${risk.level}`"
            >
              <div class="risk-header">
                <div class="risk-number">{{ index + 1 }}</div>
                <el-tag :type="getRiskTagType(risk.level)" effect="dark" size="small">
                  {{ getRiskLevelText(risk.level) }}
                </el-tag>
                <span class="risk-clause">{{ risk.clause }}</span>
              </div>
              
              <div class="risk-body">
                <div class="risk-section">
                  <h5>涉及条款</h5>
                  <p class="clause-text">{{ risk.location?.text || '合同相关条款' }}</p>
                </div>

                <div class="risk-section">
                  <h5>问题描述</h5>
                  <p>{{ risk.description }}</p>
                </div>
                
                <div v-if="risk.lawReferences?.length" class="risk-section">
                  <h5>法律依据</h5>
                  <div class="law-list">
                    <div
                      v-for="law in risk.lawReferences"
                      :key="law.id"
                      class="law-reference"
                    >
                      <div class="law-content">{{ law.content }}</div>
                      <div v-if="law.interpretation" class="law-interpretation">
                        <strong>司法解释：</strong>{{ law.interpretation }}
                      </div>
                    </div>
                  </div>
                </div>
                
                <div class="risk-section suggestion">
                  <h5>修改建议</h5>
                  <div class="suggestion-box">
                    <p>{{ risk.suggestion }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 分页：修改建议汇总 -->
        <div class="report-section">
          <h2 class="section-title">
            <span class="section-number">三</span>
            修改建议汇总
          </h2>
          
          <div class="suggestions-summary">
            <table class="suggestions-table">
              <thead>
                <tr>
                  <th style="width: 60px">序号</th>
                  <th style="width: 100px">风险等级</th>
                  <th style="width: 150px">涉及条款</th>
                  <th>修改建议</th>
                  <th style="width: 80px">优先级</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(risk, index) in sortedRisks" :key="risk.id">
                  <td>{{ index + 1 }}</td>
                  <td>
                    <el-tag :type="getRiskTagType(risk.level)" size="small">
                      {{ getRiskLevelText(risk.level) }}
                    </el-tag>
                  </td>
                  <td>{{ risk.location?.text || risk.clause }}</td>
                  <td class="suggestion-cell">{{ risk.suggestion }}</td>
                  <td>{{ getPriorityText(risk.level) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        
        <!-- 报告页脚 -->
        <div class="report-footer">
          <p>本报告由智能合同审查系统自动生成，仅供参考</p>
          <p>报告生成时间：{{ formatDate(new Date()) }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
// 引入 ECharts 按需加载配置
import '@/utils/echarts'
import * as echarts from 'echarts/core'
import {
  formatDate,
  formatRiskLevel,
  calculateOverallScore
} from '@/utils/helpers'
import { RISK_LEVEL_TAG_TYPE } from '@/utils/constants'
import { exportPdfReport } from '@/api/report'
import { getReviewResult } from '@/api/review'

const route = useRoute()
const reportContent = ref(null)
const riskChart = ref(null)

// 报告数据
const reportData = ref({
  contractName: '采购合同_20240115.pdf',
  reviewId: 'REV-20240115-001',
  reviewTime: new Date(),
  overallScore: 72,
  conclusion: '经系统审查，本合同存在若干需要关注的风险点，建议根据修改建议进行调整后再签署。',
  riskSummary: {
    high: 2,
    medium: 3,
    low: 5
  },
  risks: [
    {
      id: '1',
      level: 'high',
      clause: '违约金条款',
      description: '违约金比例过高（30%），超出法定标准，可能被法院认定为无效条款。',
      location: { text: '第五条第2款' },
      lawReferences: [
        {
          id: 'law1',
          name: '民法典',
          article: '585',
          content: '当事人可以约定一方违约时应当根据违约情况向对方支付一定数额的违约金，也可以约定因违约产生的损失赔偿额的计算方法。约定的违约金过分高于造成的损失的，人民法院或者仲裁机构可以根据当事人的请求予以适当减少。',
          interpretation: '根据司法解释，违约金一般不应超过实际损失的30%。'
        }
      ],
      suggestion: '建议将违约金比例调整至不超过实际损失的130%，或约定为"按照实际损失计算"。'
    },
    {
      id: '2',
      level: 'high',
      clause: '争议解决条款',
      description: '争议解决方式约定不明确，未明确约定管辖法院或仲裁机构。',
      location: { text: '第六条' },
      lawReferences: [
        {
          id: 'law2',
          name: '民事诉讼法',
          article: '34',
          content: '合同或者其他财产权益纠纷的当事人可以书面协议选择被告住所地、合同履行地、合同签订地、原告住所地、标的物所在地等与争议有实际联系的地点的人民法院管辖，但不得违反本法对级别管辖和专属管辖的规定。'
        }
      ],
      suggestion: '建议明确约定争议解决方式，如"因本合同引起的争议，双方协商不成的，提交甲方所在地人民法院诉讼解决"。'
    },
    {
      id: '3',
      level: 'medium',
      clause: '付款方式条款',
      description: '付款时间约定过于宽泛，未明确具体付款节点和条件。',
      location: { text: '第四条' },
      suggestion: '建议明确付款节点，如"合同签订后5个工作日内支付30%预付款，货物验收合格后10个工作日内支付70%尾款"。'
    }
  ]
})

// 计算属性
const overallScore = computed(() => {
  return reportData.value.overallScore || calculateOverallScore(reportData.value.risks)
})

const scoreCircleStyle = computed(() => {
  const score = overallScore.value
  let color = '#059669'
  if (score < 60) color = '#dc2626'
  else if (score < 80) color = '#d97706'
  
  // 使用普通圆形代替锥形渐变（iText 不支持 conic-gradient）
  return {
    background: color,
    borderRadius: '50%'
  }
})

const assessmentLevel = computed(() => {
  const score = overallScore.value
  if (score >= 80) return 'excellent'
  if (score >= 60) return 'good'
  return 'poor'
})

const assessmentText = computed(() => {
  const score = overallScore.value
  if (score >= 80) return '优秀'
  if (score >= 60) return '合格'
  return '需改进'
})

const sortedRisks = computed(() => {
  const levelOrder = { high: 0, medium: 1, low: 2 }
  return [...(reportData.value.risks || [])]
    .filter(risk => risk.level !== 'none')  // 过滤无风险项
    .sort((a, b) => levelOrder[a.level] - levelOrder[b.level])
})

const uniqueLaws = computed(() => {
  const lawMap = new Map()
  
  reportData.value.risks?.forEach(risk => {
    risk.lawReferences?.forEach(law => {
      const key = `${law.name}-${law.article}`
      if (lawMap.has(key)) {
        lawMap.get(key).citationCount++
      } else {
        lawMap.set(key, { ...law, citationCount: 1 })
      }
    })
  })
  
  return Array.from(lawMap.values())
})

// 获取风险标签类型
function getRiskTagType(level) {
  return RISK_LEVEL_TAG_TYPE[level] || 'info'
}

// 获取风险等级文本
function getRiskLevelText(level) {
  return formatRiskLevel(level)
}

// 获取优先级文本
function getPriorityText(level) {
  const map = { high: '高', medium: '中', low: '低' }
  return map[level] || level
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
    legend: {
      orient: 'vertical',
      right: 10,
      top: 'center',
      data: ['高风险', '中风险', '低风险', '无风险']
    },
    series: [
      {
        type: 'pie',
        radius: ['50%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 8,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: false
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 16,
            fontWeight: 'bold'
          }
        },
        data: [
          { value: reportData.value.riskSummary?.high || 0, name: '高风险', itemStyle: { color: '#dc2626' } },
          { value: reportData.value.riskSummary?.medium || 0, name: '中风险', itemStyle: { color: '#d97706' } },
          { value: reportData.value.riskSummary?.low || 0, name: '低风险', itemStyle: { color: '#2563eb' } },
          { value: reportData.value.riskSummary?.none || 0, name: '无风险', itemStyle: { color: '#10b981' } }
        ]
      }
    ]
  }
  
  chart.setOption(option)
  
  window.addEventListener('resize', () => chart.resize())
}

// 打印报告
function printReport() {
  window.print()
}

// 处理导出
async function handleExport(command) {
  const reviewId = route.params.reviewId || route.query.reviewId

  if (!reviewId) {
    ElMessage.error('报告ID不存在，无法导出')
    return
  }

  const contractName = reportData.value.contractName || '未命名合同'
  const filename = `审查报告_${contractName}.pdf`

  try {
    await exportPdfReport(reviewId, filename)
    ElMessage.success('导出成功')
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败')
  }
}

// 加载报告数据
async function loadReportData() {
  const reviewId = route.params.reviewId || route.query.reviewId
  console.log('[Preview] route.params:', route.params)
  console.log('[Preview] route.query:', route.query)
  console.log('[Preview] reviewId from route:', reviewId)

  if (!reviewId) {
    ElMessage.error('报告ID不存在')
    return
  }

  try {
    console.log('[Preview] 加载报告数据, reviewId:', reviewId)
    const response = await getReviewResult(reviewId)
    console.log('[Preview] 报告数据:', response)

    if (response && response.code === 200 && response.data) {
      // 直接使用后端返回的数据
      reportData.value = response.data

      // 数据加载完成后初始化图表
      setTimeout(() => {
        initChart()
      }, 100)
    } else {
      ElMessage.error(response?.message || '获取报告数据失败')
    }
  } catch (error) {
    console.error('[Preview] 加载报告数据失败:', error)
    ElMessage.error('加载报告数据失败: ' + (error.response?.data?.message || error.message))
  }
}

onMounted(() => {
  loadReportData()
})
</script>

<style scoped lang="scss">
.report-preview-page {
  min-height: calc(100vh - 64px);
  background: $bg-secondary;
}

.report-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  background: white;
  border-bottom: 1px solid $border-color;
  position: sticky;
  top: 64px;
  z-index: 10;
  
  .header-left {
    display: flex;
    align-items: center;
    /* gap: 16px; iText 不支持 */
    
    .page-title {
      margin-left: 16px;
      font-size: $font-size-xl;
      font-weight: 600;
      color: $text-primary;
      margin: 0;
    }
  }
  
  .header-actions {
    display: flex;
    /* gap: 12px; iText 不支持 */
    
    .el-button + .el-button {
      margin-left: 12px;
    }
  }
}

.report-container {
  padding: 32px 24px;
  max-width: 900px;
  margin: 0 auto;
}

.report-paper {
  background: white;
  box-shadow: $shadow-lg;
  min-height: 1000px;
}

// 封面样式
.report-cover {
  padding: 80px 60px;
  text-align: center;
  border-bottom: 3px solid $primary-color;
  
  .cover-header {
    margin-bottom: 60px;
    
    .company-logo {
      width: 80px;
      height: 80px;
      margin: 0 auto 24px;
      background: linear-gradient(135deg, $primary-color, $primary-light);
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      
      .el-icon {
        font-size: 40px;
        color: white;
      }
    }
    
    .cover-title {
      font-size: 36px;
      font-weight: 700;
      color: $primary-color;
      margin: 0 0 8px 0;
      letter-spacing: 4px;
    }
    
    .cover-subtitle {
      font-size: $font-size-md;
      color: $text-secondary;
      text-transform: uppercase;
      letter-spacing: 2px;
    }
  }
  
  .cover-info {
    max-width: 400px;
    margin: 0 auto 60px;
    text-align: left;
    
    .info-row {
      display: flex;
      padding: 12px 0;
      border-bottom: 1px solid $border-light;
      
      .info-label {
        width: 100px;
        color: $text-secondary;
        font-size: $font-size-sm;
      }
      
      .info-value {
        flex: 1;
        color: $text-primary;
        font-weight: 500;
      }
    }
  }
  
  .cover-score {
    .score-circle {
      width: 140px;
      height: 140px;
      border-radius: 50%;
      margin: 0 auto 16px;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      background: white;
      box-shadow: inset 0 0 0 12px white;
      
      .score-value {
        font-size: 36px;
        font-weight: 700;
        color: $text-primary;
        line-height: 1;
      }
      
      .score-label {
        font-size: $font-size-sm;
        color: $text-secondary;
        margin-top: 4px;
      }
    }
    
    .score-assessment {
      font-size: $font-size-lg;
      font-weight: 600;
      
      &.excellent { color: $success-color; }
      &.good { color: $warning-color; }
      &.poor { color: $danger-color; }
    }
  }
}

// 章节样式
.report-section {
  padding: 40px 60px;
  border-bottom: 1px solid $border-light;
  page-break-inside: avoid;
  
  .section-title {
    display: flex;
    align-items: center;
    /* gap: 12px; iText 不支持 */
    font-size: $font-size-xl;
    font-weight: 600;
    color: $primary-color;
    margin: 0 0 24px 0;
    padding-bottom: 12px;
    border-bottom: 2px solid $primary-color;
    
    .section-number {
      width: 32px;
      height: 32px;
      background: $primary-color;
      color: white;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: $font-size-md;
    }
  }
}

// 概览样式
.overview-content {
  .overview-stats {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    /* gap: 20px; iText 不支持 */
    margin-bottom: 32px;
    
    .stat-box {
      margin-right: 20px;
    }
  }
  
  .stat-box {
    display: flex;
    align-items: center;
    /* gap: 16px; iText 不支持 */
    padding: 20px;
    background: $bg-secondary;
    border-radius: $radius-lg;
    
    .stat-info {
      margin-left: 16px;
    }
    
    .stat-icon {
      width: 48px;
      height: 48px;
      border-radius: $radius-md;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 24px;
      
      &.high {
        background: rgba($risk-high, 0.1);
        color: $risk-high;
      }
      
      &.medium {
        background: rgba($risk-medium, 0.1);
        color: $risk-medium;
      }
      
      &.low {
        background: rgba($risk-low, 0.1);
        color: $risk-low;
      }
      
      &.none {
        background: rgba(#10b981, 0.1);
        color: #10b981;
      }
    }
    
    .stat-info {
      .stat-value {
        font-size: 28px;
        font-weight: 700;
        color: $text-primary;
        line-height: 1;
      }
      
      .stat-label {
        font-size: $font-size-sm;
        color: $text-secondary;
        margin-top: 4px;
      }
    }
  }
  
  .overview-chart {
    margin-bottom: 32px;
    
    .chart-container {
      height: 280px;
    }
  }
  
  .overview-summary {
    background: rgba($primary-color, 0.03);
    border-left: 4px solid $primary-color;
    padding: 20px 24px;
    border-radius: 0 $radius-md $radius-md 0;
    
    h4 {
      font-size: $font-size-base;
      font-weight: 600;
      color: $primary-color;
      margin: 0 0 12px 0;
    }
    
    p {
      margin: 0;
      color: $text-primary;
      line-height: 1.8;
    }
  }
}

// 风险详情样式
.risks-content {
  display: flex;
  flex-direction: column;
  /* gap: 24px; iText 不支持 */
}

.risk-detail-item {
  margin-bottom: 24px;
  background: $bg-secondary;
  border-radius: $radius-lg;
  padding: 24px;
  border-left: 4px solid transparent;
  page-break-inside: avoid;
  
  &.risk-high { border-left-color: $risk-high; }
  &.risk-medium { border-left-color: $risk-medium; }
  &.risk-low { border-left-color: $risk-low; }
  
  .risk-header {
    display: flex;
    align-items: center;
    /* gap: 12px; iText 不支持 */
    margin-bottom: 20px;
    
    .risk-number {
      margin-right: 12px;
    }
    
    .el-tag {
      margin-right: 12px;
    }
    
    .risk-number {
      width: 28px;
      height: 28px;
      background: $primary-color;
      color: white;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: $font-size-sm;
      font-weight: 600;
    }
    
    .risk-clause {
      font-weight: 600;
      color: $text-primary;
      font-size: $font-size-md;
    }
  }
  
  .risk-section {
    margin-bottom: 16px;
    
    &:last-child {
      margin-bottom: 0;
    }
    
    h5 {
      font-size: $font-size-sm;
      font-weight: 600;
      color: $text-secondary;
      margin: 0 0 8px 0;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    
    p {
      margin: 0;
      color: $text-primary;
      line-height: 1.8;
    }
    
    .clause-text {
      background: white;
      padding: 12px 16px;
      border-radius: $radius-sm;
      border: 1px solid $border-color;
      font-style: italic;
    }
    
    &.suggestion {
      .suggestion-box {
        background: rgba($success-color, 0.05);
        border: 1px solid rgba($success-color, 0.2);
        padding: 16px;
        border-radius: $radius-md;
      }
    }
  }
  
  .law-list {
    display: flex;
    flex-direction: column;
    /* gap: 12px; iText 不支持 */
    
    .law-reference {
      margin-bottom: 12px;
    }
  }
  
  .law-reference {
    background: white;
    padding: 16px;
    border-radius: $radius-md;
    border: 1px solid $border-color;
    
    .law-title {
      font-weight: 600;
      color: $primary-color;
      margin-bottom: 8px;
    }
    
    .law-content {
      color: $text-primary;
      line-height: 1.8;
      margin-bottom: 8px;
    }
    
    .law-interpretation {
      font-size: $font-size-sm;
      color: $text-secondary;
      padding-top: 8px;
      border-top: 1px dashed $border-color;
    }
  }
}

// 表格样式
.laws-summary,
.suggestions-summary {
  overflow-x: auto;
}

.laws-table,
.suggestions-table {
  width: 100%;
  border-collapse: collapse;
  font-size: $font-size-sm;
  
  th,
  td {
    padding: 12px 16px;
    text-align: left;
    border-bottom: 1px solid $border-color;
  }
  
  th {
    background: $bg-tertiary;
    font-weight: 600;
    color: $text-primary;
  }
  
  td {
    color: $text-secondary;
  }
  
  tbody tr:hover {
    background: $bg-secondary;
  }
}

.suggestion-cell {
  max-width: 300px;
  line-height: 1.6;
}

// 页脚样式
.report-footer {
  padding: 40px 60px;
  text-align: center;
  color: $text-tertiary;
  font-size: $font-size-sm;
  
  p {
    margin: 4px 0;
  }
}

// 打印样式
@media print {
  .report-header {
    display: none;
  }
  
  .report-container {
    padding: 0;
  }
  
  .report-paper {
    box-shadow: none;
  }
  
  .report-section {
    page-break-inside: avoid;
  }
}
</style>
