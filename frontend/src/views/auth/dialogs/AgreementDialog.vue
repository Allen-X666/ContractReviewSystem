<template>
  <el-dialog
    v-model="visible"
    :title="title"
    width="600px"
    class="agreement-dialog"
    @close="handleClose"
  >
    <div class="agreement-content">
      <p v-if="type === 'user'">
        用户协议内容...<br><br>
        1. 用户在使用本系统时应遵守相关法律法规。<br>
        2. 用户应对上传的合同文件内容负责。<br>
        3. 系统提供的审查结果仅供参考，不构成法律意见。<br>
        4. 用户应妥善保管账号密码，不得将账号借给他人使用。
      </p>
      <p v-else>
        隐私协议内容...<br><br>
        1. 我们重视用户隐私保护，不会泄露用户上传的合同内容。<br>
        2. 用户数据仅用于提供合同审查服务。<br>
        3. 我们采用加密技术保护用户数据传输安全。<br>
        4. 用户有权要求删除其个人数据。
      </p>
    </div>
    <template #footer>
      <el-button @click="handleClose">关闭</el-button>
      <el-button type="primary" @click="handleAgree">同意</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  type: {
    type: String,
    default: 'user'
  }
})

const emit = defineEmits(['update:modelValue', 'agree'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const title = computed(() => {
  return props.type === 'user' ? '用户协议' : '隐私协议'
})

function handleClose() {
  visible.value = false
}

function handleAgree() {
  emit('agree')
  handleClose()
}
</script>

<style scoped lang="scss">
.agreement-dialog {
  .agreement-content {
    max-height: 400px;
    overflow-y: auto;
    line-height: 1.8;
    color: $text-primary;
    
    p {
      margin: 0;
    }
  }
}
</style>
