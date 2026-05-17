<template>
  <div class="txt-preview">
    <div v-if="loading" class="loading-state">
      <el-icon class="loading-icon"><Loading /></el-icon>
      <span>正在加载文本...</span>
    </div>
    
    <div v-else-if="error" class="error-state">
      <el-icon><CircleClose /></el-icon>
      <span>{{ error }}</span>
    </div>
    
    <template v-else>
      <div class="txt-toolbar">
        <div class="toolbar-left">
          <span class="file-info">{{ fileInfo }}</span>
        </div>
        <div class="toolbar-right">
          <el-button-group>
            <el-button size="small" @click="zoomOut" :disabled="fontSize <= 12">
              <el-icon><ZoomOut /></el-icon>
            </el-button>
            <el-button size="small" @click="zoomIn" :disabled="fontSize >= 24">
              <el-icon><ZoomIn /></el-icon>
            </el-button>
          </el-button-group>
          <span class="zoom-info">{{ fontSize }}px</span>
        </div>
      </div>
      
      <div ref="contentRef" class="txt-content" :style="contentStyle">
        <pre>{{ content }}</pre>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, nextTick } from 'vue'
import { Loading, CircleClose, ZoomIn, ZoomOut } from '@element-plus/icons-vue'

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
const content = ref('')
const fontSize = ref(14)
const contentRef = ref(null)
const lineCount = ref(0)
const charCount = ref(0)

const fileInfo = computed(() => {
  return `${lineCount.value} 行 | ${charCount.value} 字符`
})

const contentStyle = computed(() => ({
  fontSize: `${fontSize.value}px`,
  lineHeight: `${fontSize.value * 1.6}px`
}))

const zoomIn = () => {
  if (fontSize.value < 24) {
    fontSize.value += 2
  }
}

const zoomOut = () => {
  if (fontSize.value > 12) {
    fontSize.value -= 2
  }
}

const detectEncoding = (buffer) => {
  // 简单的编码检测
  const uint8Array = new Uint8Array(buffer)
  
  // 检查 BOM
  if (uint8Array.length >= 3 && uint8Array[0] === 0xEF && uint8Array[1] === 0xBB && uint8Array[2] === 0xBF) {
    return 'UTF-8'
  }
  if (uint8Array.length >= 2 && uint8Array[0] === 0xFE && uint8Array[1] === 0xFF) {
    return 'UTF-16BE'
  }
  if (uint8Array.length >= 2 && uint8Array[0] === 0xFF && uint8Array[1] === 0xFE) {
    return 'UTF-16LE'
  }
  
  // 检查是否包含 UTF-8 多字节字符
  let isUTF8 = true
  let i = 0
  while (i < Math.min(uint8Array.length, 1000)) {
    const byte = uint8Array[i]
    if (byte >= 0x80) {
      // 可能是多字节 UTF-8 字符
      if (byte >= 0xC0 && byte <= 0xDF) {
        // 2字节序列
        if (i + 1 >= uint8Array.length || (uint8Array[i + 1] & 0xC0) !== 0x80) {
          isUTF8 = false
          break
        }
        i += 2
      } else if (byte >= 0xE0 && byte <= 0xEF) {
        // 3字节序列
        if (i + 2 >= uint8Array.length || 
            (uint8Array[i + 1] & 0xC0) !== 0x80 || 
            (uint8Array[i + 2] & 0xC0) !== 0x80) {
          isUTF8 = false
          break
        }
        i += 3
      } else if (byte >= 0xF0 && byte <= 0xF7) {
        // 4字节序列
        if (i + 3 >= uint8Array.length || 
            (uint8Array[i + 1] & 0xC0) !== 0x80 || 
            (uint8Array[i + 2] & 0xC0) !== 0x80 || 
            (uint8Array[i + 3] & 0xC0) !== 0x80) {
          isUTF8 = false
          break
        }
        i += 4
      } else {
        isUTF8 = false
        break
      }
    } else {
      i++
    }
  }
  
  return isUTF8 ? 'UTF-8' : 'GBK'
}

const decodeText = (buffer, encoding) => {
  if (encoding === 'UTF-8') {
    // 跳过 BOM
    const start = buffer.byteLength >= 3 && 
      new Uint8Array(buffer)[0] === 0xEF && 
      new Uint8Array(buffer)[1] === 0xBB && 
      new Uint8Array(buffer)[2] === 0xBF ? 3 : 0
    return new TextDecoder('utf-8').decode(buffer.slice(start))
  } else if (encoding === 'UTF-16BE') {
    return new TextDecoder('utf-16be').decode(buffer.slice(2))
  } else if (encoding === 'UTF-16LE') {
    return new TextDecoder('utf-16le').decode(buffer.slice(2))
  } else {
    // GBK 或其他编码，尝试使用 TextDecoder
    try {
      return new TextDecoder('gbk').decode(buffer)
    } catch {
      // 如果 GBK 解码失败，尝试 UTF-8
      return new TextDecoder('utf-8').decode(buffer)
    }
  }
}

const loadTXT = async () => {
  try {
    loading.value = true
    error.value = ''
    
    let arrayBuffer
    
    if (props.fileBlob) {
      arrayBuffer = await props.fileBlob.arrayBuffer()
    } else if (props.fileUrl) {
      const response = await fetch(props.fileUrl)
      if (!response.ok) {
        throw new Error('文件加载失败')
      }
      arrayBuffer = await response.arrayBuffer()
    } else {
      throw new Error('未提供文件')
    }
    
    // 检测编码并解码
    const encoding = detectEncoding(arrayBuffer)
    console.log('[TxtPreview] 检测到编码:', encoding)
    
    content.value = decodeText(arrayBuffer, encoding)
    
    // 统计信息
    lineCount.value = content.value.split(/\r?\n/).length
    charCount.value = content.value.length
    
  } catch (err) {
    console.error('TXT加载失败:', err)
    error.value = '文本加载失败: ' + err.message
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  nextTick(() => {
    loadTXT()
  })
})
</script>

<style scoped lang="scss">
.txt-preview {
  height: 100%;
  display: flex;
  flex-direction: column;
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
  
  .el-icon {
    font-size: 48px;
    
    &.loading-icon {
      animation: rotating 2s linear infinite;
    }
  }
}

@keyframes rotating {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.txt-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  
  .toolbar-left,
  .toolbar-right {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  
  .file-info {
    font-size: 13px;
    color: #606266;
  }
  
  .zoom-info {
    font-size: 13px;
    color: #606266;
    min-width: 40px;
    text-align: center;
  }
}

.txt-content {
  flex: 1;
  overflow: auto;
  padding: 20px;
  background: #fff;
  
  pre {
    margin: 0;
    white-space: pre-wrap;
    word-wrap: break-word;
    font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
    color: #333;
    line-height: 1.6;
  }
}
</style>
