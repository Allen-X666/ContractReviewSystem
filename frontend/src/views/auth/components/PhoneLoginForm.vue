<template>
  <div class="phone-login-form">
    <el-form-item prop="phone">
      <el-input
        v-model="form.phone"
        placeholder="请输入手机号"
        size="large"
        :prefix-icon="Iphone"
        maxlength="11"
      />
    </el-form-item>
    
    <el-form-item prop="code" class="code-form-item">
      <el-input
        v-model="form.code"
        placeholder="请输入验证码"
        size="large"
        :prefix-icon="Message"
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
  </div>
</template>

<script setup>
import { Iphone, Message } from '@element-plus/icons-vue'

defineProps({
  form: {
    type: Object,
    required: true
  },
  codeSending: {
    type: Boolean,
    default: false
  },
  codeCountdown: {
    type: Number,
    default: 0
  }
})

const emit = defineEmits(['send-code'])

function handleSendCode() {
  emit('send-code')
}
</script>

<style scoped lang="scss">
.phone-login-form {
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
