<template>
  <el-button
    :type="type"
    :size="size"
    :link="link"
    :disabled="!canPreview"
    @click="handlePreview"
  >
    <el-icon v-if="showIcon"><View /></el-icon>
    <span v-if="showText">{{ buttonText }}</span>
  </el-button>
</template>

<script setup>
import { computed } from 'vue'
import { View } from '@element-plus/icons-vue'
import { isPreviewable, getFileType } from '@/utils/filePreview'
import { ElMessage } from 'element-plus'

const props = defineProps({
  // 文件URL
  fileUrl: {
    type: String,
    default: ''
  },
  // 文件Blob（优先使用）
  fileBlob: {
    type: Blob,
    default: null
  },
  // 文件名（用于识别文件类型）
  fileName: {
    type: String,
    required: true
  },
  // 按钮类型
  type: {
    type: String,
    default: 'primary'
  },
  // 按钮大小
  size: {
    type: String,
    default: 'default'
  },
  // 是否为链接样式
  link: {
    type: Boolean,
    default: false
  },
  // 是否显示图标
  showIcon: {
    type: Boolean,
    default: true
  },
  // 是否显示文字
  showText: {
    type: Boolean,
    default: true
  },
  // 自定义按钮文字
  text: {
    type: String,
    default: ''
  },
  // 预览对话框实例（通过ref传入）
  previewRef: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['preview', 'error'])

// 是否可以预览
const canPreview = computed(() => {
  return isPreviewable(props.fileName)
})

// 按钮文字
const buttonText = computed(() => {
  if (props.text) return props.text
  return canPreview.value ? '预览' : '不可预览'
})

// 处理预览
const handlePreview = () => {
  if (!canPreview.value) {
    const fileType = getFileType(props.fileName)
    ElMessage.warning(`暂不支持 .${fileType} 文件的预览`)
    emit('error', { message: '不支持的文件类型', fileName: props.fileName })
    return
  }

  // 优先使用传入的预览对话框ref
  if (props.previewRef) {
    const source = props.fileBlob || props.fileUrl
    props.previewRef.open(source, props.fileName)
  }

  emit('preview', {
    fileUrl: props.fileUrl,
    fileBlob: props.fileBlob,
    fileName: props.fileName
  })
}
</script>
