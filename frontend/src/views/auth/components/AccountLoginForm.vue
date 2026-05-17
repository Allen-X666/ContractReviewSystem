<template>
  <div class="account-login-form">
    <el-form-item prop="username">
      <el-input
        v-model="form.username"
        placeholder="请输入用户名"
        size="large"
        :prefix-icon="User"
      />
    </el-form-item>
    
    <el-form-item prop="password">
      <el-input
        v-model="form.password"
        type="password"
        placeholder="请输入密码"
        size="large"
        :prefix-icon="Lock"
        show-password
      />
    </el-form-item>
    
    <!-- 图形验证码 -->
    <el-form-item prop="captcha" class="captcha-form-item">
      <el-input
        v-model="form.captcha"
        placeholder="请输入验证码"
        size="large"
        :prefix-icon="Key"
        maxlength="4"
      />
      <div class="captcha-image" @click="handleRefreshCaptcha" title="点击刷新验证码">
        <img v-if="captchaImage" :src="captchaImage" alt="验证码" class="captcha-img" />
        <div v-else class="captcha-loading">
          <el-icon><Loading /></el-icon>
        </div>
        <div class="captcha-refresh">
          <el-icon><Refresh /></el-icon>
        </div>
      </div>
    </el-form-item>
  </div>
</template>

<script setup>
import { User, Lock, Key, Loading, Refresh } from '@element-plus/icons-vue'

defineProps({
  form: {
    type: Object,
    required: true
  },
  captchaImage: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['refresh-captcha'])

function handleRefreshCaptcha() {
  emit('refresh-captcha')
}
</script>

<style scoped lang="scss">
.account-login-form {
  .captcha-form-item {
    :deep(.el-form-item__content) {
      display: flex;
      gap: 12px;
    }
    
    .el-input {
      flex: 1;
    }
    
    .captcha-image {
      width: 120px;
      height: 40px;
      border-radius: $radius-md;
      overflow: hidden;
      cursor: pointer;
      position: relative;
      background: $bg-secondary;
      display: flex;
      align-items: center;
      justify-content: center;
      
      .captcha-img {
        width: 100%;
        height: 100%;
        object-fit: cover;
      }
      
      .captcha-loading {
        color: $text-secondary;
      }
      
      .captcha-refresh {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 28px;
        height: 28px;
        background: rgba(0, 0, 0, 0.5);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        opacity: 0;
        transition: opacity $transition-fast;
      }
      
      &:hover .captcha-refresh {
        opacity: 1;
      }
    }
  }
}
</style>
