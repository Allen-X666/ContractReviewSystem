<template>
  <div class="login-page">
    <div class="login-container">
      <!-- 左侧品牌区域 - 使用 v-once 优化静态内容 -->
      <div v-once class="login-left">
        <div class="brand-section">
          <div class="logo">
            <el-icon class="logo-icon"><DocumentChecked /></el-icon>
          </div>
          <h1 class="brand-name">智能合同审查助手</h1>
          <p class="brand-slogan">AI 驱动的企业法务合规解决方案</p>
        </div>
        
        <div class="features-section">
          <div class="feature-item">
            <div class="feature-icon">
              <el-icon><CircleCheck /></el-icon>
            </div>
            <div class="feature-text">
              <h4>智能风险识别</h4>
              <p>自动识别合同中的风险条款和缺失条款</p>
            </div>
          </div>
          <div class="feature-item">
            <div class="feature-icon">
              <el-icon><Collection /></el-icon>
            </div>
            <div class="feature-text">
              <h4>法条智能关联</h4>
              <p>自动关联相关法律法规和司法解释</p>
            </div>
          </div>
          <div class="feature-item">
            <div class="feature-icon">
              <el-icon><Document /></el-icon>
            </div>
            <div class="feature-text">
              <h4>专业报告生成</h4>
              <p>一键生成专业审查报告，支持 Word/PDF 导出</p>
            </div>
          </div>
        </div>
      </div>
      
      <div class="login-right">
        <div class="login-form-wrapper">
          <h2 class="form-title">欢迎登录</h2>
          <p class="form-subtitle">请使用您的方式登录系统</p>
          
          <!-- 登录方式切换 -->
          <div class="login-tabs">
            <div
              v-for="tab in loginTabs"
              :key="tab.type"
              :class="['tab-item', { active: currentTab === tab.type }]"
              @click="currentTab = tab.type"
            >
              <el-icon><component :is="tab.icon" /></el-icon>
              <span>{{ tab.label }}</span>
            </div>
          </div>
          
          <el-form
            ref="loginFormRef"
            :model="loginForm"
            :rules="currentRules"
            class="login-form"
            @keyup.enter="handleLogin"
          >
            <!-- 账号登录 -->
            <AccountLoginForm
              v-if="currentTab === 'account'"
              :form="loginForm"
              :captcha-image="captchaImage"
              @refresh-captcha="refreshCaptcha"
            />
            
            <!-- 邮箱登录 -->
            <EmailLoginForm
              v-if="currentTab === 'email'"
              :form="loginForm"
              :code-sending="codeSending"
              :code-countdown="codeCountdown"
              @send-code="sendCode"
            />
            
            <div class="form-options">
              <el-checkbox v-model="rememberMe">记住我</el-checkbox>
              <el-button link type="primary" @click="showForgotPasswordDialog">忘记密码？</el-button>
            </div>
            
            <!-- 用户协议 -->
            <div class="agreement-section">
              <el-checkbox v-model="agreedToTerms">
                <span class="agreement-text">
                  已阅读并同意
                  <el-button link type="primary" @click="showAgreement('user')">用户协议</el-button>
                  和
                  <el-button link type="primary" @click="showAgreement('privacy')">隐私协议</el-button>
                </span>
              </el-checkbox>
            </div>
            
            <el-form-item>
              <el-button
                type="primary"
                size="large"
                class="login-btn"
                :loading="loading"
                @click="handleLogin"
              >
                登录
              </el-button>
            </el-form-item>
          </el-form>
          
          <!-- 注册入口 -->
          <div class="register-section">
            <span class="register-text">还没有账号？</span>
            <el-button link type="primary" class="register-btn" @click="goToRegister">
              去注册
            </el-button>
          </div>
        </div>
      </div>
    </div>
    
    <div v-once class="login-footer">
      <p>© 2026 智能合同审查助手 - 企业法务合规 AI 系统</p>
    </div>
    
    <!-- 协议弹窗 -->
    <AgreementDialog
      v-model="agreementDialogVisible"
      :type="currentAgreement"
      @agree="agreeAndClose"
    />

    <!-- 忘记密码弹窗 -->
    <ForgotPasswordDialog
      ref="forgotPasswordRef"
      v-model="forgotPasswordVisible"
      @send-code="sendForgotCode"
      @submit="handleResetPassword"
    />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'
import { sendVerificationCode, login, resetPassword } from '@/api/user'
import { md5 } from '@/utils/crypto'
import { useCaptcha } from '@/composables/useCaptcha'

// 导入拆分后的组件
import AccountLoginForm from './components/AccountLoginForm.vue'
import EmailLoginForm from './components/EmailLoginForm.vue'
import AgreementDialog from './dialogs/AgreementDialog.vue'
import ForgotPasswordDialog from './dialogs/ForgotPasswordDialog.vue'

const router = useRouter()
const userStore = useUserStore()
const loginFormRef = ref(null)
const forgotPasswordRef = ref(null)
const loading = ref(false)
const rememberMe = ref(false)
const agreedToTerms = ref(false)
const currentTab = ref('account')
const codeSending = ref(false)
const codeCountdown = ref(0)
const agreementDialogVisible = ref(false)
const currentAgreement = ref('')
const forgotPasswordVisible = ref(false)

// 登录方式配置
const loginTabs = [
  { type: 'account', label: '账号登录', icon: 'User' },
  { type: 'email', label: '邮箱登录', icon: 'Message' }
]

// 登录表单
const loginForm = reactive({
  username: 'admin',
  password: '123456',
  phone: '',
  email: '',
  code: '',
  captcha: '',
  captchaId: ''
})

// 使用验证码组合式函数
const {
  captchaImage,
  refreshCaptcha
} = useCaptcha('login', (captchaId) => {
  loginForm.captchaId = captchaId
  loginForm.captcha = ''
})

// 页面加载时获取验证码并清空表单
onMounted(() => {
  resetForm()
  refreshCaptcha()
})

// 重置表单
function resetForm() {
  loginForm.username = ''
  loginForm.password = ''
  loginForm.phone = ''
  loginForm.email = ''
  loginForm.code = ''
  loginForm.captcha = ''
  loginForm.captchaId = ''
  rememberMe.value = false
  agreedToTerms.value = false
}

// 账号登录规则
const accountRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ],
  captcha: [
    { required: true, message: '请输入验证码', trigger: 'blur' },
    { len: 4, message: '验证码为4位字符', trigger: 'blur' }
  ]
}

// 邮箱登录规则
const emailRules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ],
  code: [
    { required: true, message: '请输入验证码', trigger: 'blur' },
    { len: 4, message: '验证码为4位数字', trigger: 'blur' }
  ]
}

// 当前规则
const currentRules = computed(() => {
  switch (currentTab.value) {
    case 'email':
      return emailRules
    default:
      return accountRules
  }
})

// 发送验证码
let countdownTimer = null

async function sendCode() {
  if (currentTab.value === 'email' && !loginForm.email) {
    ElMessage.warning('请先输入邮箱')
    return
  }

  const target = loginForm.email
  const targetType = 'email'

  codeSending.value = true

  try {
    const res = await sendVerificationCode(target, targetType, 'login')

    if (res.code === 200) {
      const expireSeconds = res.data?.expireSeconds || 60
      codeCountdown.value = expireSeconds

      if (countdownTimer) {
        clearInterval(countdownTimer)
      }

      countdownTimer = setInterval(() => {
        codeCountdown.value--
        if (codeCountdown.value <= 0) {
          clearInterval(countdownTimer)
          countdownTimer = null
          codeSending.value = false
        }
      }, 1000)

      ElMessage.success(res.message || '验证码已发送')
    }
  } catch (error) {
    console.error('发送验证码失败:', error)
    codeSending.value = false
    codeCountdown.value = 0
  }
}

// 组件卸载时清除定时器
onUnmounted(() => {
  if (countdownTimer) {
    clearInterval(countdownTimer)
  }
})

// 显示忘记密码弹窗
function showForgotPasswordDialog() {
  forgotPasswordVisible.value = true
}

// 发送忘记密码验证码
async function sendForgotCode(email) {
  if (!email) {
    ElMessage.warning('请先输入邮箱')
    return
  }

  forgotPasswordRef.value?.setCodeSending(true)

  try {
    const res = await sendVerificationCode(email, 'email', 'resetPassword')

    if (res.code === 200) {
      const expireSeconds = res.data?.expireSeconds || 60
      forgotPasswordRef.value?.startCountdown(expireSeconds)
      ElMessage.success(res.message || '验证码已发送')
    }
  } catch (error) {
    console.error('发送验证码失败:', error)
    forgotPasswordRef.value?.setCodeSending(false)
  }
}

// 重置密码
async function handleResetPassword(formData) {
  try {
    const res = await resetPassword({
      email: formData.email,
      code: formData.code,
      newPassword: md5(formData.newPassword),
      confirmPassword: md5(formData.confirmPassword)
    })

    if (res.code === 200) {
      ElMessage.success(res.message || '密码重置成功，请使用新密码登录')
      forgotPasswordVisible.value = false
    } else {
      ElMessage.error(res.message || '重置密码失败')
    }
  } catch (error) {
    console.error('重置密码失败:', error)
    ElMessage.error('重置密码失败，请稍后重试')
  }
}

// 显示协议
function showAgreement(type) {
  currentAgreement.value = type
  agreementDialogVisible.value = true
}

// 同意并关闭
function agreeAndClose() {
  agreedToTerms.value = true
}

// 跳转到注册
function goToRegister() {
  router.push('/register')
}

// 登录处理
async function handleLogin() {
  if (!agreedToTerms.value) {
    ElMessage.warning('请先阅读并同意用户协议和隐私协议')
    return
  }

  const valid = await loginFormRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true

  try {
    const params = {
      username: loginForm.username,
      password: md5(loginForm.password),
      code: loginForm.captcha,
      captchaId: loginForm.captchaId,
      loginType: currentTab.value
    }

    if (currentTab.value === 'phone') {
      params.username = loginForm.phone
      params.code = loginForm.code
    } else if (currentTab.value === 'email') {
      params.username = loginForm.email
      params.code = loginForm.code
    }

    const res = await login(params)

    if (res.code === 2007) {
      ElMessage.error(res.message || '该账号已在其他设备登录，请先退出后再登录')
      loading.value = false
      return
    }

    ElMessage.success('登录成功')
    userStore.setToken(res.data.token)
    userStore.setUserInfo(res.data.userInfo)
    // 登录成功后建立SSE连接
    import('@/utils/sse').then(({ sseClient }) => {
      sseClient.connect()
    })
    router.push('/dashboard')
  } catch (error) {
    console.error('登录失败:', error)
    refreshCaptcha()
  } finally {
    loading.value = false
  }
}
</script>

<style scoped lang="scss">
.login-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: linear-gradient(135deg, $primary-color 0%, $primary-light 100%);
}

.login-container {
  flex: 1;
  display: flex;
  max-width: 1200px;
  width: 100%;
  margin: 0 auto;
  padding: 40px 20px;
}

.login-left {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 40px;
  color: white;
  
  .brand-section {
    margin-bottom: 60px;
    
    .logo {
      width: 80px;
      height: 80px;
      background: rgba(255, 255, 255, 0.15);
      border-radius: 20px;
      display: flex;
      align-items: center;
      justify-content: center;
      margin-bottom: 24px;
      backdrop-filter: blur(10px);
      
      .logo-icon {
        font-size: 40px;
        color: $secondary-color;
      }
    }
    
    .brand-name {
      font-size: 36px;
      font-weight: 700;
      margin: 0 0 12px 0;
      letter-spacing: 2px;
    }
    
    .brand-slogan {
      font-size: $font-size-lg;
      opacity: 0.9;
      margin: 0;
    }
  }
  
  .features-section {
    display: flex;
    flex-direction: column;
    gap: 24px;
    
    .feature-item {
      display: flex;
      align-items: flex-start;
      gap: 16px;
      
      .feature-icon {
        width: 48px;
        height: 48px;
        background: rgba(255, 255, 255, 0.1);
        border-radius: $radius-md;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        flex-shrink: 0;
      }
      
      .feature-text {
        h4 {
          font-size: $font-size-md;
          font-weight: 600;
          margin: 0 0 4px 0;
        }
        
        p {
          font-size: $font-size-sm;
          opacity: 0.8;
          margin: 0;
        }
      }
    }
  }
}

.login-right {
  width: 420px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.login-form-wrapper {
  width: 100%;
  background: white;
  border-radius: $radius-xl;
  padding: 40px;
  box-shadow: $shadow-xl;
  
  .form-title {
    font-size: $font-size-xl;
    font-weight: 600;
    color: $text-primary;
    margin: 0 0 8px 0;
    text-align: center;
  }
  
  .form-subtitle {
    font-size: $font-size-sm;
    color: $text-secondary;
    margin: 0 0 24px 0;
    text-align: center;
  }
}

// 登录方式切换
.login-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 24px;
  padding: 4px;
  background: $bg-secondary;
  border-radius: $radius-lg;
  
  .tab-item {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    padding: 10px 8px;
    border-radius: $radius-md;
    cursor: pointer;
    transition: all $transition-fast;
    font-size: $font-size-sm;
    color: $text-secondary;
    white-space: nowrap;
    
    .el-icon {
      font-size: 16px;
      flex-shrink: 0;
    }
    
    span {
      white-space: nowrap;
    }
    
    &:hover {
      color: $primary-color;
      background: rgba($primary-color, 0.05);
    }
    
    &.active {
      color: $primary-color;
      background: white;
      font-weight: 500;
      box-shadow: $shadow-sm;
    }
  }
}

.login-form {
  .el-input {
    :deep(.el-input__wrapper) {
      padding: 4px 12px;
    }
  }
  
  .form-options {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
  }
  
  .agreement-section {
    margin-bottom: 16px;
    
    .agreement-text {
      font-size: $font-size-sm;
      color: $text-secondary;
      
      .el-button {
        font-size: $font-size-sm;
        padding: 0 4px;
        height: auto;
      }
    }
  }
  
  .login-btn {
    width: 100%;
  }
}

.register-section {
  text-align: center;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid $border-color;
  
  .register-text {
    font-size: $font-size-sm;
    color: $text-secondary;
  }
}

.login-footer {
  text-align: center;
  padding: 20px;
  color: rgba(255, 255, 255, 0.6);
  font-size: $font-size-sm;
  
  p {
    margin: 0;
  }
}

// 响应式
@media (max-width: 768px) {
  .login-container {
    flex-direction: column;
    padding: 20px;
  }
  
  .login-left {
    display: none;
  }
  
  .login-right {
    width: 100%;
  }
  
  .login-form-wrapper {
    padding: 24px;
  }
}
</style>
