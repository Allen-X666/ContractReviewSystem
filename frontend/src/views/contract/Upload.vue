<template>
  <div class="upload-page">
    <div class="page-header">
      <div class="header-left">
        <el-button link @click="$router.back()">
          <el-icon><ArrowLeft /></el-icon>
        </el-button>
        <h1 class="page-title">上传合同</h1>
      </div>
      <el-button @click="$router.push('/contract/list')">
        返回列表
      </el-button>
    </div>
    
    <div class="upload-content">
      <!-- 拖拽上传区域 -->
      <div
        class="upload-area"
        :class="{ 'is-dragover': isDragover }"
        @dragenter.prevent="isDragover = true"
        @dragleave.prevent="isDragover = false"
        @dragover.prevent
        @drop.prevent="handleDrop"
        @click="triggerFileInput"
      >
        <input
          ref="fileInput"
          type="file"
          multiple
          accept=".pdf,.docx"
          style="display: none"
          @change="handleFileSelect"
        />
        
        <div class="upload-placeholder">
          <div class="upload-icon">
            <el-icon><UploadFilled /></el-icon>
          </div>
          <h3 class="upload-title">点击或拖拽文件至此处上传</h3>
          <p class="upload-desc">
            支持格式：PDF、DOCX（单个文件不超过 50MB）
          </p>
          <el-button type="primary" size="large" class="select-btn">
            <el-icon><FolderOpened /></el-icon>
            <span>选择文件</span>
          </el-button>
        </div>
      </div>
      
      <!-- 文件列表 -->
      <div v-if="contractStore.uploadQueue.length > 0" class="file-list-section">
        <div class="section-header">
          <h3 class="section-title">
            待上传文件
            <el-tag type="info" size="small">
              {{ pendingFileCount }} 个文件
            </el-tag>
          </h3>

        </div>
        
        <div class="file-list">
          <div
            v-for="item in contractStore.uploadQueue"
            :key="item.id"
            class="file-item"
            :class="`status-${item.status}`"
          >
            <div class="file-icon">
              <el-icon v-if="item.name.endsWith('.pdf')"><Document /></el-icon>
              <el-icon v-else><DocumentCopy /></el-icon>
            </div>
            
            <div class="file-info">
              <div class="file-name" :title="item.name">{{ item.name }}</div>
              <div class="file-size">{{ formatFileSize(item.size) }}</div>
            </div>
            
            <div class="file-progress" v-if="item.status === 'uploading'">
              <el-progress
                :percentage="item.progress"
                :stroke-width="6"
                :show-text="false"
              />
            </div>
            
            <div class="file-status">
              <el-icon v-if="item.status === 'success'" class="status-success">
                <CircleCheck />
              </el-icon>
              <el-icon v-else-if="item.status === 'error'" class="status-error">
                <CircleClose />
              </el-icon>
              <span v-else-if="item.status === 'pending'" class="status-pending">
                等待上传
              </span>
              <span v-else-if="item.status === 'uploading'" class="status-uploading">
                {{ item.progress }}%
              </span>
            </div>
            
            <div class="file-actions">
              <el-button
                v-if="item.status === 'pending'"
                type="primary"
                link
                size="small"
                @click="uploadFile(item.id)"
              >
                上传
              </el-button>
              <el-button
                v-if="item.status === 'error'"
                type="warning"
                link
                size="small"
                @click="retryUpload(item.id)"
              >
                重新上传
              </el-button>
              <el-button
                type="danger"
                link
                size="small"
                @click="removeFile(item.id)"
              >
                删除
              </el-button>
            </div>
          </div>
        </div>
        
        <div class="file-list-actions">
          <el-button @click="clearAllFiles">清空列表</el-button>
          <el-button
            type="primary"
            :disabled="!hasPendingFiles"
            :loading="contractStore.hasUploadingFiles"
            @click="uploadAllFiles"
          >
            全部上传
          </el-button>
        </div>
      </div>
      
      <!-- 空状态 -->
      <div v-else class="empty-tip">
        <el-icon class="tip-icon"><InfoFilled /></el-icon>
        <p>暂无待上传文件，请点击上方区域或拖拽文件进行上传</p>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useContractStore } from '@/stores/contract'
import { ElMessage } from 'element-plus'
import {
  formatFileSize,
  validateFileType,
  validateFileSize
} from '@/utils/helpers'
import { UPLOAD_CONFIG } from '@/utils/constants'

const contractStore = useContractStore()

const fileInput = ref(null)
const isDragover = ref(false)

// 计算属性
const pendingFileCount = computed(() => {
  return contractStore.uploadQueue.filter(item => item.status === 'pending').length
})

const hasPendingFiles = computed(() => {
  return contractStore.uploadQueue.some(item => item.status === 'pending')
})

// 触发文件选择
function triggerFileInput() {
  fileInput.value?.click()
}

// 处理文件选择
function handleFileSelect(event) {
  const files = Array.from(event.target.files)
  processFiles(files)
  // 清空 input 以便重复选择相同文件
  event.target.value = ''
}

// 处理拖拽文件
function handleDrop(event) {
  isDragover.value = false
  const files = Array.from(event.dataTransfer.files)
  processFiles(files)
}

// 处理文件
function processFiles(files) {
  const validFiles = []
  
  for (const file of files) {
    // 验证文件类型
    if (!validateFileType(file, UPLOAD_CONFIG.ACCEPT_TYPES)) {
      ElMessage.warning(`${file.name} 格式不支持，仅支持 PDF、DOCX 格式`)
      continue
    }
    
    // 验证文件大小
    if (!validateFileSize(file, UPLOAD_CONFIG.MAX_SIZE)) {
      ElMessage.warning(`${file.name} 超过 50MB 大小限制`)
      continue
    }
    
    validFiles.push(file)
  }
  
  if (validFiles.length > 0) {
    contractStore.addToUploadQueue(validFiles)
    ElMessage.success(`已添加 ${validFiles.length} 个文件`)
  }
}

// 上传单个文件
async function uploadFile(id) {
  try {
    await contractStore.uploadSingleFile(id)
  } catch (error) {
    console.error('上传失败:', error)
  }
}

// 重新上传
async function retryUpload(id) {
  contractStore.updateFileStatus(id, 'pending')
  await uploadFile(id)
}

// 上传所有文件
async function uploadAllFiles() {
  await contractStore.uploadAllFiles()
}

// 删除文件
function removeFile(id) {
  contractStore.removeFromQueue(id)
}

// 清空所有文件
function clearAllFiles() {
  contractStore.clearQueue()
}
</script>

<style scoped lang="scss">
.upload-page {
  padding: 24px;
  max-width: 1200px;
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
    gap: 12px;
    
    .page-title {
      font-size: $font-size-xl;
      font-weight: 600;
      color: $text-primary;
      margin: 0;
    }
  }
}

.upload-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.upload-area {
  background: white;
  border: 2px dashed $border-color;
  border-radius: $radius-xl;
  padding: 60px 40px;
  text-align: center;
  cursor: pointer;
  transition: all $transition-base;
  
  &:hover,
  &.is-dragover {
    border-color: $primary-color;
    background-color: rgba($primary-color, 0.02);
  }
  
  &.is-dragover {
    transform: scale(1.01);
  }
}

.upload-placeholder {
  .upload-icon {
    font-size: 64px;
    color: $primary-light;
    margin-bottom: 20px;
    
    .el-icon {
      animation: float 3s ease-in-out infinite;
    }
  }
  
  .upload-title {
    font-size: $font-size-lg;
    font-weight: 500;
    color: $text-primary;
    margin-bottom: 8px;
  }
  
  .upload-desc {
    font-size: $font-size-sm;
    color: $text-secondary;
    margin-bottom: 24px;
  }
  
  .select-btn {
    padding: 12px 32px;
    font-size: $font-size-md;
    
    .el-icon {
      margin-right: 6px;
    }
  }
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

.file-list-section {
  background: white;
  border-radius: $radius-lg;
  padding: 20px;
  box-shadow: $shadow-sm;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  
  .section-title {
    font-size: $font-size-md;
    font-weight: 600;
    color: $text-primary;
    margin: 0;
    display: flex;
    align-items: center;
    gap: 8px;
  }
}

.file-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 16px;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: $bg-secondary;
  border-radius: $radius-md;
  border: 1px solid transparent;
  transition: all $transition-fast;
  
  &:hover {
    border-color: $border-color;
  }
  
  &.status-success {
    background: rgba($success-color, 0.05);
    border-color: rgba($success-color, 0.2);
  }
  
  &.status-error {
    background: rgba($danger-color, 0.05);
    border-color: rgba($danger-color, 0.2);
  }
  
  .file-icon {
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: white;
    border-radius: $radius-sm;
    color: $primary-color;
    font-size: 20px;
  }
  
  .file-info {
    flex: 1;
    min-width: 0;
    
    .file-name {
      font-size: $font-size-base;
      color: $text-primary;
      font-weight: 500;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    
    .file-size {
      font-size: $font-size-xs;
      color: $text-tertiary;
      margin-top: 2px;
    }
  }
  
  .file-progress {
    width: 120px;
  }
  
  .file-status {
    width: 80px;
    text-align: center;
    
    .status-success {
      font-size: 20px;
      color: $success-color;
    }
    
    .status-error {
      font-size: 20px;
      color: $danger-color;
    }
    
    .status-pending {
      font-size: $font-size-xs;
      color: $text-tertiary;
    }
    
    .status-uploading {
      font-size: $font-size-sm;
      color: $primary-color;
      font-weight: 500;
    }
  }
  
  .file-actions {
    display: flex;
    gap: 4px;
  }
}

.file-list-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 16px;
  border-top: 1px solid $border-light;
}

.empty-tip {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 40px;
  color: $text-secondary;
  font-size: $font-size-sm;
  
  .tip-icon {
    font-size: 16px;
    color: $text-tertiary;
  }
}
</style>
