<template>
  <div class="template-page">
    <div class="page-header">
      <h1 class="page-title">模板管理</h1>
      <el-button type="primary" @click="showUploadDialog = true">
        <el-icon><Upload /></el-icon>
        <span>上传模板</span>
      </el-button>
    </div>
    
    <!-- 模板分类 -->
    <div class="template-categories">
      <el-radio-group v-model="selectedCategory" size="large">
        <el-radio-button label="all">全部</el-radio-button>
        <el-radio-button label="purchase">采购合同</el-radio-button>
        <el-radio-button label="service">服务协议</el-radio-button>
        <el-radio-button label="labor">劳动合同</el-radio-button>
        <el-radio-button label="lease">租赁合同</el-radio-button>
        <el-radio-button label="confidentiality">保密协议</el-radio-button>
        <el-radio-button label="cooperation">合作协议</el-radio-button>
      </el-radio-group>
    </div>
    
    <!-- 模板列表 -->
    <div class="template-grid">
      <div
        v-for="template in filteredTemplates"
        :key="template.id"
        class="template-card"
      >
        <div class="template-preview">
          <el-icon class="preview-icon"><Document /></el-icon>
          <div class="preview-overlay">
            <el-button type="primary" @click="previewTemplate(template)">
              <el-icon><View /></el-icon>
              <span>预览</span>
            </el-button>
          </div>
        </div>
        
        <div class="template-info">
          <h3 class="template-name">{{ template.name }}</h3>
          <p class="template-desc">{{ template.description }}</p>
          <div class="template-meta">
            <span class="meta-item">
              <el-icon><Calendar /></el-icon>
              {{ formatDate(template.updatedAt) }}
            </span>
            <span class="meta-item">
              <el-icon><Download /></el-icon>
              {{ template.downloadCount }} 次下载
            </span>
          </div>
        </div>
        
        <div class="template-actions">
          <el-button type="primary" link @click="useTemplate(template)">
            使用模板
          </el-button>
          <el-dropdown trigger="click">
            <el-button link>
              <el-icon><More /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="downloadTemplate(template)">
                  <el-icon><Download /></el-icon>
                  <span>下载</span>
                </el-dropdown-item>
                <el-dropdown-item @click="editTemplate(template)">
                  <el-icon><Edit /></el-icon>
                  <span>编辑</span>
                </el-dropdown-item>
                <el-dropdown-item divided @click="deleteTemplate(template)">
                  <el-icon><Delete /></el-icon>
                  <span>删除</span>
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
      
      <!-- 添加模板卡片 -->
      <div class="template-card add-card" @click="showUploadDialog = true">
        <div class="add-content">
          <el-icon class="add-icon"><Plus /></el-icon>
          <span>上传新模板</span>
        </div>
      </div>
    </div>
    
    <!-- 上传模板弹窗 -->
    <el-dialog
      v-model="showUploadDialog"
      title="上传模板"
      width="500px"
    >
      <el-form :model="uploadForm" label-width="80px">
        <el-form-item label="模板名称" required>
          <el-input v-model="uploadForm.name" placeholder="请输入模板名称" />
        </el-form-item>
        <el-form-item label="模板分类" required>
          <el-select v-model="uploadForm.category" placeholder="请选择分类" style="width: 100%">
            <el-option label="采购合同" value="purchase" />
            <el-option label="服务协议" value="service" />
            <el-option label="劳动合同" value="labor" />
            <el-option label="租赁合同" value="lease" />
            <el-option label="保密协议" value="confidentiality" />
            <el-option label="合作协议" value="cooperation" />
          </el-select>
        </el-form-item>
        <el-form-item label="模板描述">
          <el-input
            v-model="uploadForm.description"
            type="textarea"
            rows="3"
            placeholder="请输入模板描述"
          />
        </el-form-item>
        <el-form-item label="模板文件" required>
          <el-upload
            drag
            action="/api/template/upload"
            :auto-upload="false"
            :on-change="handleFileChange"
            accept=".docx,.doc"
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">
              将文件拖到此处，或<em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                支持 Word 格式文件（.docx, .doc）
              </div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showUploadDialog = false">取消</el-button>
        <el-button type="primary" :loading="uploading" @click="submitUpload">
          确认上传
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { formatDate } from '@/utils/helpers'

const selectedCategory = ref('all')
const showUploadDialog = ref(false)
const uploading = ref(false)

const uploadForm = ref({
  name: '',
  category: '',
  description: '',
  file: null
})

// 模板数据
const templates = ref([
  {
    id: '1',
    name: '标准采购合同模板',
    category: 'purchase',
    description: '适用于一般货物采购的标准合同模板，包含付款、交货、验收等条款',
    updatedAt: new Date(Date.now() - 86400000 * 5),
    downloadCount: 128
  },
  {
    id: '2',
    name: '技术服务协议模板',
    category: 'service',
    description: '适用于技术服务外包的合同模板，包含服务内容、验收标准等',
    updatedAt: new Date(Date.now() - 86400000 * 10),
    downloadCount: 86
  },
  {
    id: '3',
    name: '全日制劳动合同',
    category: 'labor',
    description: '符合劳动法规定的全日制劳动合同标准模板',
    updatedAt: new Date(Date.now() - 86400000 * 15),
    downloadCount: 256
  },
  {
    id: '4',
    name: '办公场地租赁合同',
    category: 'lease',
    description: '适用于办公场地租赁的合同模板，包含租金、押金、维修等条款',
    updatedAt: new Date(Date.now() - 86400000 * 20),
    downloadCount: 64
  },
  {
    id: '5',
    name: '员工保密协议',
    category: 'confidentiality',
    description: '员工入职时签署的保密协议模板',
    updatedAt: new Date(Date.now() - 86400000 * 25),
    downloadCount: 192
  },
  {
    id: '6',
    name: '战略合作协议',
    category: 'cooperation',
    description: '适用于企业间战略合作的标准协议模板',
    updatedAt: new Date(Date.now() - 86400000 * 30),
    downloadCount: 42
  }
])

// 过滤后的模板
const filteredTemplates = computed(() => {
  if (selectedCategory.value === 'all') {
    return templates.value
  }
  return templates.value.filter(t => t.category === selectedCategory.value)
})

// 文件变化
function handleFileChange(file) {
  uploadForm.value.file = file.raw
}

// 提交上传
async function submitUpload() {
  if (!uploadForm.value.name || !uploadForm.value.category) {
    ElMessage.warning('请填写完整信息')
    return
  }
  
  uploading.value = true
  
  // 模拟上传
  setTimeout(() => {
    templates.value.unshift({
      id: Date.now().toString(),
      name: uploadForm.value.name,
      category: uploadForm.value.category,
      description: uploadForm.value.description,
      updatedAt: new Date(),
      downloadCount: 0
    })
    
    uploading.value = false
    showUploadDialog.value = false
    ElMessage.success('上传成功')
    
    // 重置表单
    uploadForm.value = {
      name: '',
      category: '',
      description: '',
      file: null
    }
  }, 1500)
}

// 使用模板
function useTemplate(template) {
  ElMessage.success(`已选择模板：${template.name}`)
}

// 预览模板
function previewTemplate(template) {
  ElMessage.info(`预览模板：${template.name}`)
}

// 下载模板
function downloadTemplate(template) {
  ElMessage.info('文件正在下载中...')
  // 模拟下载延迟
  setTimeout(() => {
    ElMessage.success('文件下载完成')
    template.downloadCount++
  }, 1000)
}

// 编辑模板
function editTemplate(template) {
  ElMessage.info(`编辑模板：${template.name}`)
}

// 删除模板
async function deleteTemplate(template) {
  try {
    await ElMessageBox.confirm(
      `确定要删除模板 "${template.name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const index = templates.value.findIndex(t => t.id === template.id)
    if (index > -1) {
      templates.value.splice(index, 1)
    }
    
    ElMessage.success('删除成功')
  } catch {
    // 取消删除
  }
}
</script>

<style scoped lang="scss">
.template-page {
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

.template-categories {
  margin-bottom: 24px;
}

.template-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.template-card {
  background: white;
  border-radius: $radius-lg;
  box-shadow: $shadow-sm;
  overflow: hidden;
  transition: all $transition-base;
  
  &:hover {
    box-shadow: $shadow-md;
    transform: translateY(-4px);
    
    .preview-overlay {
      opacity: 1;
    }
  }
  
  &.add-card {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 280px;
    cursor: pointer;
    border: 2px dashed $border-color;
    background: transparent;
    
    &:hover {
      border-color: $primary-color;
      background: rgba($primary-color, 0.02);
    }
    
    .add-content {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 12px;
      color: $text-tertiary;
      
      .add-icon {
        font-size: 48px;
      }
      
      span {
        font-size: $font-size-base;
      }
    }
  }
}

.template-preview {
  height: 160px;
  background: linear-gradient(135deg, $bg-tertiary, $bg-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  
  .preview-icon {
    font-size: 64px;
    color: $text-tertiary;
  }
  
  .preview-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    opacity: 0;
    transition: opacity $transition-fast;
  }
}

.template-info {
  padding: 16px;
  
  .template-name {
    font-size: $font-size-base;
    font-weight: 600;
    color: $text-primary;
    margin: 0 0 8px 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  
  .template-desc {
    font-size: $font-size-sm;
    color: $text-secondary;
    line-height: 1.5;
    margin: 0 0 12px 0;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    height: 42px;
  }
  
  .template-meta {
    display: flex;
    gap: 16px;
    font-size: $font-size-xs;
    color: $text-tertiary;
    
    .meta-item {
      display: flex;
      align-items: center;
      gap: 4px;
      
      .el-icon {
        font-size: 12px;
      }
    }
  }
}

.template-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-top: 1px solid $border-light;
}
</style>
