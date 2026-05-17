<template>
  <el-dialog
    v-model="visible"
    title="忘记密码"
    width="450px"
    class="forgot-password-dialog"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-position="top"
    >
      <el-form-item label="邮箱" prop="email">
        <el-input
          v-model="form.email"
          placeholder="请输入注册邮箱"
          :prefix-icon="Message"
        />
      </el-form-item>

      <el-form-item label="新密码" prop="newPassword">
        <el-input
          v-model="form.newPassword"
          type="password"
          placeholder="请输入新密码"
          :prefix-icon="Lock"
          show-password
        />
      </el-form-item>

      <el-form-item label="确认新密码" prop="confirmPassword">
        <el-input
          v-model="form.confirmPassword"
          type="password"
          placeholder="请再次输入新密码"
          :prefix-icon="Lock"
          show-password
        />
      </el-form-item>

      <el-form-item label="验证码" prop="code" class="code-form-item">
        <el-input
          v-model="form.code"
          placeholder="请输入邮箱验证码"
          :prefix-icon="Key"
          maxlength="4"
        />
        <el-button
          type="primary"
          :disabled="codeSending || codeCountdown > 0"
          class="send-code-btn"
          @click="handleSendCode"
        >
          {{ codeCountdown > 0 ? `${codeCountdown}s后重发` : '获取验证码' }}
        </el-button>
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" :loading="loading" @click="handleSubmit">
        重置密码
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { Message, Key, Lock } from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'send-code', 'submit'])

const formRef = ref(null)
const loading = ref(false)
const codeSending = ref(false)
const codeCountdown = ref(0)

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const form = reactive({
  email: '',
  code: '',
  newPassword: '',
  confirmPassword: ''
})

const rules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ],
  code: [
    { required: true, message: '请输入验证码', trigger: 'blur' },
    { len: 4, message: '验证码为4位数字', trigger: 'blur' }
  ],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== form.newPassword) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

function handleSendCode() {
  emit('send-code', form.email)
}

async function handleSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  
  loading.value = true
  try {
    await emit('submit', { ...form })
  } finally {
    loading.value = false
  }
}

function handleClose() {
  visible.value = false
  // 重置表单
  form.email = ''
  form.code = ''
  form.newPassword = ''
  form.confirmPassword = ''
  codeCountdown.value = 0
  codeSending.value = false
}

// 暴露方法给父组件
defineExpose({
  startCountdown(seconds) {
    codeCountdown.value = seconds
    const timer = setInterval(() => {
      codeCountdown.value--
      if (codeCountdown.value <= 0) {
        clearInterval(timer)
        codeSending.value = false
      }
    }, 1000)
  },
  setCodeSending(value) {
    codeSending.value = value
  }
})
</script>

<style scoped lang="scss">
.forgot-password-dialog {
  .code-form-item {
    :deep(.el-form-item__content) {
      display: flex;
      gap: 12px;
    }
    
    .el-input {
      flex: 1;
    }
    
    .send-code-btn {
      width: 120px;
      white-space: nowrap;
    }
  }
}
</style>
