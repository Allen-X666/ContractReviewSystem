<template>
  <div class="knowledge-page">
    <div class="page-header">
      <h1 class="page-title">法律知识库</h1>
      <div class="header-actions">
        <el-input
          v-model="searchQuery"
          placeholder="搜索法律法规、条款..."
          clearable
          style="width: 320px"
          @keyup.enter="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>
    </div>
    
    <!-- 知识库统计 -->
    <div class="knowledge-stats">
      <div class="stat-card">
        <div class="stat-icon">
          <el-icon><Collection /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.totalLaws }}</div>
          <div class="stat-label">法律法规</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">
          <el-icon><Document /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.totalArticles }}</div>
          <div class="stat-label">法条条款</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">
          <el-icon><Files /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.totalTemplates }}</div>
          <div class="stat-label">合同模板</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">
          <el-icon><Refresh /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.lastUpdate }}</div>
          <div class="stat-label">最近更新</div>
        </div>
      </div>
    </div>
    
    <!-- 分类标签 -->
    <div class="category-tabs">
      <el-tabs v-model="activeCategory" @tab-change="handleCategoryChange">
        <el-tab-pane
          v-for="cat in categories"
          :key="cat.id"
          :label="cat.name"
          :name="cat.id"
        >
          <div class="law-list">
            <div
              v-for="law in filteredLaws"
              :key="law.id"
              class="law-card"
              @click="showLawDetail(law)"
            >
              <div class="law-header">
                <h3 class="law-title">《{{ law.name }}》</h3>
                <el-tag size="small" :type="law.isNew ? 'success' : 'info'">
                  {{ law.isNew ? '最新' : '现行有效' }}
                </el-tag>
              </div>
              <div class="law-meta">
                <span>发布机关：{{ law.issuer }}</span>
                <el-divider direction="vertical" />
                <span>发布日期：{{ law.publishDate }}</span>
              </div>
              <div class="law-desc">{{ law.description }}</div>
              <div class="law-footer">
                <span class="article-count">共 {{ law.articleCount }} 条</span>
                <el-button type="primary" link size="small">
                  查看详情
                  <el-icon class="el-icon--right"><ArrowRight /></el-icon>
                </el-button>
              </div>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>
    
    <!-- 法条详情弹窗 -->
    <el-dialog
      v-model="detailDialogVisible"
      :title="selectedLaw?.name"
      width="800px"
      class="law-detail-dialog"
    >
      <div v-if="selectedLaw" class="law-detail">
        <div class="detail-header">
          <div class="detail-meta">
            <p><strong>发布机关：</strong>{{ selectedLaw.issuer }}</p>
            <p><strong>发布日期：</strong>{{ selectedLaw.publishDate }}</p>
            <p><strong>施行日期：</strong>{{ selectedLaw.effectiveDate }}</p>
          </div>
        </div>
        
        <el-divider />
        
        <div class="detail-content">
          <h4>相关条款</h4>
          <div class="article-list">
            <div
              v-for="article in selectedLaw.articles"
              :key="article.id"
              class="article-item"
            >
              <div class="article-number">{{ article.articleNo }}</div>
              <div class="article-title">{{ article.title }}</div>
              <div class="article-content">{{ article.content }}</div>
              <div v-if="article.interpretation" class="article-interpretation">
                <strong>司法解释：</strong>{{ article.interpretation }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getKnowledgeStats, getLawCategories, searchLaws, getLawDetail } from '@/api/knowledge'

const searchQuery = ref('')
const activeCategory = ref('')
const detailDialogVisible = ref(false)
const selectedLaw = ref(null)
const loading = ref(false)

// 统计数据
const stats = ref({
  totalLaws: 0,
  totalArticles: 0,
  totalTemplates: 0,
  lastUpdate: '-'
})

// 分类 - 使用真实API
const categories = ref([])

// 法律法规数据 - 使用真实API
const laws = ref([])

// 过滤后的法律
const filteredLaws = computed(() => {
  return laws.value
})

// 获取统计数据 - 使用真实API
async function fetchStats() {
  try {
    const res = await getKnowledgeStats()
    if (res.code === 200 && res.data) {
      stats.value = {
        totalLaws: res.data.totalLaws || 0,
        totalArticles: res.data.totalArticles || 0,
        totalTemplates: res.data.totalTemplates || 0,
        lastUpdate: res.data.lastUpdate || '-'
      }
    }
  } catch (error) {
    console.error('获取知识库统计失败:', error)
  }
}

// 获取分类列表 - 使用真实API
async function fetchCategories() {
  try {
    const res = await getLawCategories()
    if (res.code === 200 && res.data) {
      categories.value = res.data.map(cat => ({
        id: cat.id,
        name: cat.name
      }))
      // 默认选中第一个分类
      if (categories.value.length > 0 && !activeCategory.value) {
        activeCategory.value = categories.value[0].id
        await fetchLaws()
      }
    }
  } catch (error) {
    console.error('获取分类列表失败:', error)
  }
}

// 获取法律列表 - 使用真实API（处理分组数据格式）
async function fetchLaws() {
  if (!activeCategory.value) return

  loading.value = true
  try {
    const res = await searchLaws(searchQuery.value, activeCategory.value, 1, 10)
    if (res.code === 200 && res.data) {
      // 处理分组数据格式
      if (Array.isArray(res.data)) {
        // 查找当前选中的分类对应的分组
        const group = res.data.find(g => g.categoryId === activeCategory.value)
        if (group && group.laws) {
          laws.value = group.laws
        } else {
          laws.value = []
        }
      } else {
        laws.value = res.data
      }
    }
  } catch (error) {
    console.error('获取法律列表失败:', error)
    ElMessage.error('获取法律列表失败')
  } finally {
    loading.value = false
  }
}

// 搜索
function handleSearch() {
  fetchLaws()
}

// 分类变化
function handleCategoryChange() {
  fetchLaws()
}

// 显示法律详情 - 使用真实API
async function showLawDetail(law) {
  try {
    const res = await getLawDetail(law.id)
    if (res.code === 200 && res.data) {
      selectedLaw.value = {
        ...res.data,
        articles: res.data.articles || []
      }
      detailDialogVisible.value = true
    }
  } catch (error) {
    console.error('获取法律详情失败:', error)
    ElMessage.error('获取法律详情失败')
  }
}

// 初始化
onMounted(() => {
  fetchStats()
  fetchCategories()
})
</script>

<style scoped lang="scss">
.knowledge-page {
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
}

.knowledge-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  background: white;
  padding: 20px 24px;
  border-radius: $radius-lg;
  box-shadow: $shadow-sm;
  
  .stat-icon {
    width: 48px;
    height: 48px;
    background: rgba($primary-color, 0.1);
    border-radius: $radius-md;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
    color: $primary-color;
  }
  
  .stat-info {
    .stat-value {
      font-size: 24px;
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

.category-tabs {
  background: white;
  border-radius: $radius-lg;
  padding: 20px 24px;
  box-shadow: $shadow-sm;
}

.law-list {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  padding: 16px 0;
}

.law-card {
  background: $bg-secondary;
  border-radius: $radius-lg;
  padding: 20px;
  cursor: pointer;
  transition: all $transition-fast;
  border: 1px solid transparent;
  
  &:hover {
    border-color: $primary-color;
    box-shadow: $shadow-md;
    transform: translateY(-2px);
  }
  
  .law-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
    
    .law-title {
      font-size: $font-size-md;
      font-weight: 600;
      color: $text-primary;
      margin: 0;
    }
  }
  
  .law-meta {
    font-size: $font-size-xs;
    color: $text-tertiary;
    margin-bottom: 12px;
  }
  
  .law-desc {
    font-size: $font-size-sm;
    color: $text-secondary;
    line-height: 1.6;
    margin-bottom: 16px;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
  
  .law-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    
    .article-count {
      font-size: $font-size-xs;
      color: $text-tertiary;
    }
  }
}

.law-detail-dialog {
  .law-detail {
    .detail-header {
      .detail-meta {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 12px;
        
        p {
          margin: 0;
          font-size: $font-size-sm;
          color: $text-secondary;
          
          strong {
            color: $text-primary;
          }
        }
      }
    }
    
    .detail-content {
      h4 {
        font-size: $font-size-base;
        font-weight: 600;
        color: $primary-color;
        margin: 0 0 16px 0;
      }
    }
    
    .article-list {
      display: flex;
      flex-direction: column;
      gap: 16px;
    }
    
    .article-item {
      background: $bg-secondary;
      padding: 16px;
      border-radius: $radius-md;
      
      .article-number {
        font-size: $font-size-sm;
        font-weight: 600;
        color: $primary-color;
        margin-bottom: 4px;
      }
      
      .article-title {
        font-weight: 600;
        color: $text-primary;
        margin-bottom: 8px;
      }
      
      .article-content {
        font-size: $font-size-sm;
        color: $text-primary;
        line-height: 1.8;
        margin-bottom: 8px;
      }
      
      .article-interpretation {
        font-size: $font-size-xs;
        color: $text-secondary;
        padding-top: 8px;
        border-top: 1px dashed $border-color;
      }
    }
  }
}

@media (max-width: 1200px) {
  .knowledge-stats {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .law-list {
    grid-template-columns: 1fr;
  }
}
</style>
