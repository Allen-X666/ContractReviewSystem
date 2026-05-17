<template>
  <div class="register-page">
    <div class="register-container">
      <div class="register-left">
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
      
      <div class="register-right">
        <div class="register-form-wrapper">
          <h2 class="form-title">欢迎注册</h2>
          <p class="form-subtitle">创建您的账号，开启智能合同审查之旅</p>
          
          <!-- 注册方式切换 -->
          <div class="register-tabs">
            <div
              v-for="tab in registerTabs"
              :key="tab.type"
              :class="['tab-item', { active: currentTab === tab.type }]"
              @click="currentTab = tab.type"
            >
              <el-icon><component :is="tab.icon" /></el-icon>
              <span>{{ tab.label }}</span>
            </div>
          </div>
          
          <el-form
            ref="registerFormRef"
            :model="registerForm"
            :rules="currentRules"
            class="register-form"
            @keyup.enter="handleRegister"
          >
            <!-- 账号注册 -->
            <template v-if="currentTab === 'account'">
              <el-form-item prop="username">
                <el-input
                  v-model="registerForm.username"
                  placeholder="请输入用户名"
                  size="large"
                  :prefix-icon="User"
                />
              </el-form-item>
              
              <el-form-item prop="password">
                <el-input
                  v-model="registerForm.password"
                  type="password"
                  placeholder="请输入密码"
                  size="large"
                  :prefix-icon="Lock"
                  show-password
                />
              </el-form-item>
              
              <el-form-item prop="confirmPassword">
                <el-input
                  v-model="registerForm.confirmPassword"
                  type="password"
                  placeholder="请确认密码"
                  size="large"
                  :prefix-icon="Lock"
                  show-password
                />
              </el-form-item>
              
              <!-- 图形验证码 -->
              <el-form-item prop="captcha" class="captcha-form-item">
                <el-input
                  v-model="registerForm.captcha"
                  placeholder="请输入验证码"
                  size="large"
                  :prefix-icon="Key"
                  maxlength="4"
                />
                <div class="captcha-image" @click="refreshCaptcha" title="点击刷新验证码">
                  <img v-if="captchaImage" :src="captchaImage" alt="验证码" class="captcha-img" />
                  <div v-else class="captcha-loading">
                    <el-icon><Loading /></el-icon>
                  </div>
                  <div class="captcha-refresh">
                    <el-icon><Refresh /></el-icon>
                  </div>
                </div>
              </el-form-item>
            </template>
            
            <!-- 邮箱注册 -->
            <template v-if="currentTab === 'email'">
              <el-form-item prop="email">
                <el-input
                  v-model="registerForm.email"
                  placeholder="请输入邮箱"
                  size="large"
                  :prefix-icon="Message"
                />
              </el-form-item>
              
              <el-form-item prop="code" class="code-form-item">
                <el-input
                  v-model="registerForm.code"
                  placeholder="请输入验证码"
                  size="large"
                  :prefix-icon="Key"
                  maxlength="4"
                />
                <el-button
                  type="primary"
                  :disabled="codeSending || codeCountdown > 0"
                  class="send-code-btn"
                  @click="sendCode"
                >
                  {{ codeCountdown > 0 ? `${codeCountdown}s后重发` : '获取验证码' }}
                </el-button>
              </el-form-item>
              
              <el-form-item prop="password">
                <el-input
                  v-model="registerForm.password"
                  type="password"
                  placeholder="请设置密码"
                  size="large"
                  :prefix-icon="Lock"
                  show-password
                />
              </el-form-item>
              
              <el-form-item prop="confirmPassword">
                <el-input
                  v-model="registerForm.confirmPassword"
                  type="password"
                  placeholder="请确认密码"
                  size="large"
                  :prefix-icon="Lock"
                  show-password
                />
              </el-form-item>
            </template>
            
            <!-- 用户协议 -->
            <div class="agreement-section">
              <el-checkbox v-model="agreedToTerms" size="small">
                <span class="agreement-text">
                  已阅读并同意
                  <el-button link type="primary" size="small" @click="showAgreement('user')">用户协议</el-button>
                  和
                  <el-button link type="primary" size="small" @click="showAgreement('privacy')">隐私协议</el-button>
                </span>
              </el-checkbox>
            </div>
            
            <el-form-item>
              <el-button
                type="primary"
                size="large"
                class="register-btn"
                :loading="loading"
                @click="handleRegister"
              >
                注册
              </el-button>
            </el-form-item>
          </el-form>
          
          <!-- 登录入口 -->
          <div class="login-section">
            <span class="login-text">已有账号？</span>
            <el-button link type="primary" class="login-btn-link" @click="goToLogin">
              去登录
            </el-button>
          </div>
        </div>
      </div>
    </div>
    
    <div class="register-footer">
      <p>© 2026 智能合同审查助手 - 企业法务合规 AI 系统</p>
    </div>
    
    <!-- 协议弹窗 -->
    <el-dialog
      v-model="agreementDialogVisible"
      :title="agreementTitle"
      width="600px"
      class="agreement-dialog"
    >
      <div class="agreement-content">
        <p v-if="currentAgreement === 'user'">
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
        <el-button @click="agreementDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="agreeAndClose">同意</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { register, sendVerificationCode } from '@/api/user'
import { md5 } from '@/utils/crypto'
import { useCaptcha } from '@/composables/useCaptcha'

const router = useRouter()
const registerFormRef = ref(null)
const loading = ref(false)
const agreedToTerms = ref(false)
const currentTab = ref('account')
const codeSending = ref(false)
const codeCountdown = ref(0)
const agreementDialogVisible = ref(false)
const currentAgreement = ref('')

// 注册方式配置
const registerTabs = [
  { type: 'account', label: '账号注册', icon: 'User' },
  { type: 'email', label: '邮箱注册', icon: 'Message' }
]

// 注册表单
const registerForm = reactive({
  username: '',
  password: '',
  confirmPassword: '',
  phone: '',
  email: '',
  code: '',
  captcha: '',
  captchaId: ''
})

// 使用验证码组合式函数
const {
  captchaImage,
  captchaLoading,
  fetchCaptcha,
  refreshCaptcha
} = useCaptcha('register', (captchaId) => {
  registerForm.captchaId = captchaId
  registerForm.captcha = ''
})

// 重置表单
function resetForm() {
  registerForm.username = ''
  registerForm.password = ''
  registerForm.confirmPassword = ''
  registerForm.phone = ''
  registerForm.email = ''
  registerForm.code = ''
  registerForm.captcha = ''
  registerForm.captchaId = ''
  agreedToTerms.value = false
}

// 密码确认验证
const validateConfirmPassword = (rule, value, callback) => {
  if (value !== registerForm.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

// 账号注册规则
const accountRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度为3-20个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度为6-20个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ],
  captcha: [
    { required: true, message: '请输入验证码', trigger: 'blur' },
    { len: 4, message: '验证码为4位字符', trigger: 'blur' }
  ]
}

// 邮箱注册规则
const emailRules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ],
  code: [
    { required: true, message: '请输入验证码', trigger: 'blur' },
    { len: 4, message: '验证码为4位数字', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请设置密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度为6-20个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
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

// 协议标题
const agreementTitle = computed(() => {
  return currentAgreement.value === 'user' ? '用户协议' : '隐私协议'
})

// 发送验证码
let countdownTimer = null

async function sendCode() {
  if (currentTab.value === 'email' && !registerForm.email) {
    ElMessage.warning('请先输入邮箱')
    return
  }

  const target = registerForm.email
  const targetType = 'email'

  codeSending.value = true

  try {
    const res = await sendVerificationCode(target, targetType, 'register')

    if (res.code === 200) {
      // 使用后端返回的过期时间设置倒计时
      const expireSeconds = res.data?.expireSeconds || 60
      codeCountdown.value = expireSeconds

      // 清除之前的定时器
      if (countdownTimer) {
        clearInterval(countdownTimer)
      }

      // 开始倒计时
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
    // 限流错误会在拦截器中显示，这里重置状态
    codeSending.value = false
    codeCountdown.value = 0
  }
}

// 页面加载时获取验证码并清空表单
onMounted(() => {
  resetForm()
  fetchCaptcha()
})

// 组件卸载时清除定时器
onUnmounted(() => {
  if (countdownTimer) {
    clearInterval(countdownTimer)
  }
})

// 显示协议
function showAgreement(type) {
  currentAgreement.value = type
  agreementDialogVisible.value = true
}

// 同意并关闭
function agreeAndClose() {
  agreedToTerms.value = true
  agreementDialogVisible.value = false
}

// 跳转到登录
function goToLogin() {
  router.push('/login')
}

// 注册处理
async function handleRegister() {
  if (!agreedToTerms.value) {
    ElMessage.warning('请先阅读并同意用户协议和隐私协议')
    return
  }

  const valid = await registerFormRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true

  try {
    // 构建注册参数，密码使用 MD5 加密
    const params = {
      username: registerForm.username,
      password: md5(registerForm.password),
      confirmPassword: md5(registerForm.confirmPassword),
      code: registerForm.captcha,
      captchaId: registerForm.captchaId,
      registerType: currentTab.value
    }

    // 根据注册类型添加对应字段
    if (currentTab.value === 'email') {
      params.email = registerForm.email
      params.code = registerForm.code
    } else {
      // 账号注册，邮箱可选
      params.email = registerForm.email || ''
    }

    await register(params)

    ElMessage.success('注册成功，请登录')
    router.push('/login')
  } catch (error) {
    console.error('注册失败:', error)
    // 错误消息已在请求拦截器中显示，这里不再重复显示
    // 刷新验证码
    refreshCaptcha()
  } finally {
    loading.value = false
  }
}
</script>

<style scoped lang="scss">
.register-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: linear-gradient(135deg, $primary-color 0%, $primary-light 100%);
}

.register-container {
  flex: 1;
  display: flex;
  max-width: 1200px;
  width: 100%;
  margin: 0 auto;
  padding: 40px 20px;
}

.register-left {
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

.register-right {
  width: 420px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.register-form-wrapper {
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

// 注册方式切换
.register-tabs {
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

.register-form {
  .el-input {
    :deep(.el-input__wrapper) {
      padding: 4px 12px;
    }
  }
  
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
      height: 40px;
      font-size: $font-size-sm;
      border-radius: $radius-md;
      transition: all $transition-fast;
      
      &:not(:disabled) {
        background: linear-gradient(135deg, $primary-color 0%, lighten($primary-color, 15%) 100%);
        border: none;
        
        &:hover {
          transform: translateY(-1px);
          box-shadow: 0 4px 12px rgba($primary-color, 0.3);
        }
      }
      
      &:disabled {
        background: $text-disabled;
        border-color: $text-disabled;
      }
    }
  }
  
  // 图形验证码
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
      background: linear-gradient(135deg, $primary-color 0%, $primary-light 100%);
      border-radius: $radius-md;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      user-select: none;
      position: relative;
      overflow: hidden;
      box-shadow: 0 2px 8px rgba($primary-color, 0.3);
      transition: all $transition-fast;
      
      .captcha-text {
        font-size: 20px;
        font-weight: 700;
        color: white;
        letter-spacing: 6px;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
        z-index: 2;
        font-family: 'Courier New', monospace;
      }
      
      .captcha-noise {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: 
          repeating-linear-gradient(
            45deg,
            transparent,
            transparent 2px,
            rgba(255, 255, 255, 0.1) 2px,
            rgba(255, 255, 255, 0.1) 4px
          );
        z-index: 1;
      }
      
      .captcha-img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        border-radius: $radius-md;
      }
      
      .captcha-loading {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 100%;
        height: 100%;
        
        .el-icon {
          font-size: 20px;
          color: white;
          animation: rotate 1s linear infinite;
        }
      }
      
      .captcha-refresh {
        position: absolute;
        top: 2px;
        right: 2px;
        width: 18px;
        height: 18px;
        background: rgba(255, 255, 255, 0.2);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        opacity: 0;
        transition: opacity $transition-fast;
        z-index: 3;
        
        .el-icon {
          font-size: 12px;
          color: white;
        }
      }
      
      &:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba($primary-color, 0.4);
        
        .captcha-refresh {
          opacity: 1;
        }
      }
      
      &:active {
        transform: translateY(0);
      }
    }
    
    @keyframes rotate {
      from {
        transform: rotate(0deg);
      }
      to {
        transform: rotate(360deg);
      }
    }
  }
  
  .register-btn {
    width: 100%;
    font-size: $font-size-md;
    font-weight: 500;
    background: linear-gradient(135deg, $primary-color 0%, lighten($primary-color, 10%) 100%);
    border: none;
    transition: all $transition-fast;
    
    &:hover {
      transform: translateY(-1px);
      box-shadow: 0 6px 16px rgba($primary-color, 0.35);
    }
    
    &:active {
      transform: translateY(0);
    }
  }
}

// 协议区域
.agreement-section {
  margin-bottom: 16px;
  text-align: left;
  
  .el-checkbox {
    justify-content: flex-start;
  }
  
  .agreement-text {
    font-size: $font-size-sm;
    color: $text-secondary;
    white-space: nowrap;
    
    .el-button {
      font-size: $font-size-xs;
      padding: 0 2px;
    }
  }
}

// 登录入口
.login-section {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid $border-light;
  text-align: center;
  
  .login-text {
    font-size: $font-size-sm;
    color: $text-secondary;
  }
  
  .login-btn-link {
    font-size: $font-size-sm;
    font-weight: 500;
    margin-left: 4px;
  }
}

.register-footer {
  padding: 20px;
  text-align: center;
  color: rgba(255, 255, 255, 0.6);
  font-size: $font-size-sm;
  
  p {
    margin: 0;
  }
}

// 协议弹窗
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

@media (max-width: 900px) {
  .register-container {
    flex-direction: column;
  }
  
  .register-left {
    display: none;
  }
  
  .register-right {
    width: 100%;
    max-width: 420px;
    margin: 0 auto;
  }
}
</style>
