<template>
  <el-dialog
    v-model="visible"
    :title="title"
    width="90%"
    top="5vh"
    :close-on-click-modal="false"
    class="file-preview-dialog"
    destroy-on-close
  >
    <div class="preview-container">
      <!-- PDF 预览 -->
      <PdfPreview
        v-if="fileType === 'pdf'"
        :file-url="fileUrl"
        :file-blob="fileBlob"
      />
      
      <!-- DOCX 预览 -->
      <DocxPreview
        v-else-if="fileType === 'docx' || fileType === 'doc'"
        :file-url="fileUrl"
        :file-blob="fileBlob"
      />
      
      <!-- TXT 预览 -->
      <TxtPreview
        v-else-if="fileType === 'txt' || fileType === 'text'"
        :file-url="fileUrl"
        :file-blob="fileBlob"
      />
      
      <!-- 不支持的文件类型 -->
      <div v-else class="unsupported-type">
        <el-icon><Document /></el-icon>
        <p>暂不支持该文件类型的预览</p>
        <p class="file-type">文件类型: {{ fileType?.toUpperCase() }}</p>
        <el-button type="primary" @click="downloadFile">
          <el-icon><Download /></el-icon>
          下载文件查看
        </el-button>
      </div>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Document, Download } from '@element-plus/icons-vue'
import PdfPreview from './PdfPreview.vue'
import DocxPreview from './DocxPreview.vue'
import TxtPreview from './TxtPreview.vue'

const visible = ref(false)
const fileUrl = ref('')
const fileBlob = ref(null)
const fileName = ref('')
const fileType = ref('')

const title = computed(() => {
  return fileName.value || '文件预览'
})

// 打开预览对话框（支持URL或Blob）
const open = (urlOrBlob, name, type) => {
  if (urlOrBlob instanceof Blob) {
    fileBlob.value = urlOrBlob
    fileUrl.value = ''
  } else {
    fileUrl.value = urlOrBlob
    fileBlob.value = null
  }
  fileName.value = name
  fileType.value = (type || '').toLowerCase()
  visible.value = true
}

// 关闭预览对话框
const close = () => {
  visible.value = false
}

// 下载文件
const downloadFile = () => {
  const link = document.createElement('a')
  link.href = fileUrl.value
  link.download = fileName.value
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

// 暴露方法
defineExpose({
  open,
  close
})
</script>

<style scoped lang="scss">
.file-preview-dialog {
  :deep(.el-dialog__body) {
    padding: 0;
    height: calc(90vh - 120px);
  }
}

.preview-container {
  height: 100%;
  overflow: hidden;
}

.unsupported-type {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 16px;
  color: #666;
  
  .el-icon {
    font-size: 64px;
    color: #c0c4cc;
  }
  
  p {
    margin: 0;
    font-size: 16px;
  }
  
  .file-type {
    font-size: 14px;
    color: #999;
    background: #f5f5f5;
    padding: 4px 12px;
    border-radius: 4px;
  }
}
</style>
