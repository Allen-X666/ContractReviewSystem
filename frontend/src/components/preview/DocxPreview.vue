<template>
  <div class="docx-preview">
    <div v-if="loading" class="loading-state">
      <el-icon class="loading-icon"><Loading /></el-icon>
      <span>正在加载文档...</span>
    </div>
    
    <div v-else-if="error" class="error-state">
      <el-icon><CircleClose /></el-icon>
      <span>{{ error }}</span>
    </div>
    
    <div v-else ref="contentRef" class="docx-content"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import mammoth from 'mammoth'
import { Loading, CircleClose } from '@element-plus/icons-vue'

const props = defineProps({
  fileUrl: {
    type: String,
    default: ''
  },
  fileBlob: {
    type: Blob,
    default: null
  }
})

const loading = ref(true)
const error = ref('')
const contentRef = ref(null)

const loadDOCX = async () => {
  try {
    loading.value = true
    error.value = ''
    
    let arrayBuffer
    
    if (props.fileBlob) {
      // 使用Blob
      arrayBuffer = await props.fileBlob.arrayBuffer()
    } else if (props.fileUrl) {
      // 使用URL
      const response = await fetch(props.fileUrl)
      if (!response.ok) {
        throw new Error('文件加载失败')
      }
      arrayBuffer = await response.arrayBuffer()
    } else {
      throw new Error('未提供文件')
    }
    
    const result = await mammoth.convertToHtml(
      { arrayBuffer },
      {
        styleMap: [
          "p[style-name='Heading 1'] => h1",
          "p[style-name='Heading 2'] => h2",
          "p[style-name='Heading 3'] => h3",
          "p[style-name='Heading 4'] => h4",
          "p[style-name='Heading 5'] => h5",
          "p[style-name='Heading 6'] => h6",
          "p[style-name='Title'] => h1.title",
          "p[style-name='Subtitle'] => h2.subtitle"
        ],
        includeDefaultStyleMap: true
      }
    )
    
    // 等待 contentRef 元素可用
    let retries = 0
    while (!contentRef.value && retries < 50) {
      await new Promise(resolve => setTimeout(resolve, 100))
      retries++
    }
    
    if (contentRef.value) {
      contentRef.value.innerHTML = result.value
    } else {
      console.error('Content 元素未找到')
    }
    
    // 处理转换警告
    if (result.messages.length > 0) {
      console.warn('DOCX转换警告:', result.messages)
    }
  } catch (err) {
    console.error('DOCX加载失败:', err)
    error.value = '文档加载失败，请检查文件是否有效'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  nextTick(() => {
    loadDOCX()
  })
})
</script>

<style scoped lang="scss">
.docx-preview {
  height: 100%;
  background: #f5f5f5;
  overflow: hidden;
}

.loading-state,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 16px;
  color: #666;
  font-size: 14px;
}

.loading-icon {
  font-size: 32px;
  animation: rotating 2s linear infinite;
}

@keyframes rotating {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.docx-content {
  height: 100%;
  overflow-y: auto;
  padding: 40px;
  background: #fff;
  max-width: 900px;
  margin: 0 auto;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  line-height: 1.8;
  color: #333;
  
  :deep(*) {
    max-width: 100%;
  }
  
  :deep(h1) {
    font-size: 24px;
    font-weight: bold;
    margin: 24px 0 16px;
    color: #1a1a1a;
    
    &.title {
      text-align: center;
      font-size: 28px;
      margin-bottom: 8px;
    }
  }
  
  :deep(h2) {
    font-size: 20px;
    font-weight: bold;
    margin: 20px 0 12px;
    color: #1a1a1a;
    
    &.subtitle {
      text-align: center;
      font-size: 18px;
      color: #666;
      font-weight: normal;
      margin-top: 0;
    }
  }
  
  :deep(h3) {
    font-size: 18px;
    font-weight: bold;
    margin: 16px 0 10px;
    color: #1a1a1a;
  }
  
  :deep(h4, h5, h6) {
    font-size: 16px;
    font-weight: bold;
    margin: 14px 0 8px;
    color: #1a1a1a;
  }
  
  :deep(p) {
    margin: 12px 0;
    text-align: justify;
  }
  
  :deep(ul, ol) {
    margin: 12px 0;
    padding-left: 32px;
  }
  
  :deep(li) {
    margin: 6px 0;
  }
  
  :deep(table) {
    width: 100%;
    border-collapse: collapse;
    margin: 16px 0;
    font-size: 14px;
  }
  
  :deep(th, td) {
    border: 1px solid #ddd;
    padding: 10px 12px;
    text-align: left;
  }
  
  :deep(th) {
    background: #f5f5f5;
    font-weight: 600;
  }
  
  :deep(tr:nth-child(even)) {
    background: #fafafa;
  }
  
  :deep(strong, b) {
    font-weight: 600;
    color: #1a1a1a;
  }
  
  :deep(em, i) {
    font-style: italic;
  }
  
  :deep(u) {
    text-decoration: underline;
  }
  
  :deep(s, strike) {
    text-decoration: line-through;
  }
  
  :deep(a) {
    color: #409eff;
    text-decoration: none;
    
    &:hover {
      text-decoration: underline;
    }
  }
  
  :deep(img) {
    max-width: 100%;
    height: auto;
    display: block;
    margin: 16px auto;
  }
  
  :deep(blockquote) {
    border-left: 4px solid #ddd;
    padding-left: 16px;
    margin: 16px 0;
    color: #666;
  }
  
  :deep(pre, code) {
    background: #f5f5f5;
    padding: 2px 6px;
    border-radius: 3px;
    font-family: 'Courier New', monospace;
    font-size: 13px;
  }
  
  :deep(pre) {
    padding: 12px;
    overflow-x: auto;
    margin: 16px 0;
  }
}
</style>
