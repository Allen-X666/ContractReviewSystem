<template>
  <div class="pdf-preview">
    <div v-if="loading" class="loading-state">
      <el-icon class="loading-icon"><Loading /></el-icon>
      <span>正在加载 PDF...</span>
    </div>
    
    <div v-else-if="error" class="error-state">
      <el-icon><CircleClose /></el-icon>
      <span>{{ error }}</span>
    </div>
    
    <template v-else>
      <div class="pdf-toolbar">
        <div class="toolbar-left">
          <el-button-group>
            <el-button size="small" @click="prevPage" :disabled="currentPage <= 1">
              <el-icon><ArrowLeft /></el-icon>
            </el-button>
            <el-button size="small" @click="nextPage" :disabled="currentPage >= totalPages">
              <el-icon><ArrowRight /></el-icon>
            </el-button>
          </el-button-group>
          <span class="page-info">{{ currentPage }} / {{ totalPages }}</span>
        </div>
        
        <div class="toolbar-right">
          <el-button-group>
            <el-button size="small" @click="zoomOut" :disabled="scale <= 0.5">
              <el-icon><ZoomOut /></el-icon>
            </el-button>
            <el-button size="small" @click="zoomIn" :disabled="scale >= 3">
              <el-icon><ZoomIn /></el-icon>
            </el-button>
          </el-button-group>
          <span class="zoom-info">{{ Math.round(scale * 100) }}%</span>
        </div>
      </div>
      
      <div ref="containerRef" class="pdf-container" @scroll="handleScroll">
        <canvas ref="canvasRef" class="pdf-canvas"></canvas>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import * as pdfjsLib from 'pdfjs-dist'
import { 
  Loading, 
  CircleClose, 
  ArrowLeft, 
  ArrowRight, 
  ZoomIn, 
  ZoomOut 
} from '@element-plus/icons-vue'

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
const currentPage = ref(1)
const totalPages = ref(0)
const scale = ref(1.5)
const canvasRef = ref(null)
const containerRef = ref(null)
let pdfDoc = null
let renderTask = null

// 初始化 PDF.js worker
// 使用 CDN 版本的 worker（版本需与 pdfjs-dist 一致）
pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.10.38/pdf.worker.min.mjs'

const loadPDF = async () => {
  try {
    loading.value = true
    error.value = ''
    
    let url = props.fileUrl
    
    if (props.fileBlob) {
      url = URL.createObjectURL(props.fileBlob)
    }
    
    if (!url) {
      throw new Error('未提供文件 URL 或 Blob')
    }
    
    console.log('Loading PDF from URL:', url)
    pdfDoc = await pdfjsLib.getDocument(url).promise
    totalPages.value = pdfDoc.numPages
    currentPage.value = 1
    loading.value = false

    await nextTick()
    await renderPage(currentPage.value)
  } catch (err) {
    console.error('PDF加载失败:', err)
    error.value = 'PDF 文件加载失败: ' + (err.message || err.toString())
    loading.value = false
  }
}

const renderPage = async (pageNum) => {
  if (!pdfDoc) return

  await nextTick()
  if (!canvasRef.value) {
    console.error('Canvas 元素未找到')
    return
  }

  try {
    if (renderTask) {
      renderTask.cancel()
    }

    const page = await pdfDoc.getPage(pageNum)
    const canvas = canvasRef.value
    const ctx = canvas.getContext('2d')

    const viewport = page.getViewport({ scale: scale.value })
    canvas.height = viewport.height
    canvas.width = viewport.width

    renderTask = page.render({
      canvasContext: ctx,
      viewport: viewport
    })

    await renderTask.promise
    renderTask = null
  } catch (err) {
    if (err.name !== 'RenderingCancelledException') {
      console.error('页面渲染失败:', err)
    }
  }
}

const prevPage = async () => {
  if (currentPage.value > 1) {
    currentPage.value--
    await renderPage(currentPage.value)
  }
}

const nextPage = async () => {
  if (currentPage.value < totalPages.value) {
    currentPage.value++
    await renderPage(currentPage.value)
  }
}

const zoomIn = async () => {
  if (scale.value < 3) {
    scale.value += 0.25
    await renderPage(currentPage.value)
  }
}

const zoomOut = async () => {
  if (scale.value > 0.5) {
    scale.value -= 0.25
    await renderPage(currentPage.value)
  }
}

const handleScroll = () => {
  // 可以在这里实现虚拟滚动或懒加载
}

onMounted(() => {
  nextTick(() => {
    loadPDF()
  })
})

// 监听 props 变化，当 fileUrl 或 fileBlob 变化时重新加载
watch(() => [props.fileUrl, props.fileBlob], ([newUrl, newBlob]) => {
  if (newUrl || newBlob) {
    loadPDF()
  }
})

onUnmounted(() => {
  if (renderTask) {
    renderTask.cancel()
  }
  if (pdfDoc) {
    pdfDoc.destroy()
  }
})
</script>

<style scoped lang="scss">
.pdf-preview {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #f5f5f5;
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

.pdf-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
}

.toolbar-left,
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.page-info,
.zoom-info {
  font-size: 14px;
  color: #606266;
  min-width: 60px;
  text-align: center;
}

.pdf-container {
  flex: 1;
  overflow: auto;
  padding: 20px;
  display: flex;
  justify-content: center;
}

.pdf-canvas {
  background: #fff;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}
</style>
