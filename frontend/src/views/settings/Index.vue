<template>
  <div class="settings-page">
    <div class="page-header">
      <h1 class="page-title">系统设置</h1>
    </div>
    
    <div class="settings-content">
      <!-- 左侧菜单 -->
      <div class="settings-sidebar">
        <div
          v-for="item in menuItems"
          :key="item.key"
          :class="['menu-item', { active: activeMenu === item.key }]"
          @click="activeMenu = item.key"
        >
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.label }}</span>
        </div>
      </div>
      
      <!-- 右侧内容 -->
      <div class="settings-main">
        <!-- 个人信息 -->
        <div v-if="activeMenu === 'profile'" class="settings-section">
          <h3 class="section-title">个人信息</h3>
          <el-form v-loading="loading" :model="profileForm" label-width="100px">
            <el-form-item label="头像">
              <el-avatar :size="80" :src="profileForm.avatar">
                <el-icon><User /></el-icon>
              </el-avatar>
              <el-button type="primary" link style="margin-left: 16px" @click="avatarDialogVisible = true">
                更换头像
              </el-button>
            </el-form-item>
            <el-form-item label="用户名（账号登录）">
              <el-input v-model="profileForm.username" disabled />
            </el-form-item>
            <el-form-item label="昵称">
              <el-input v-model="profileForm.nickName" disabled />
            </el-form-item>
            <el-form-item label="邮箱">
              <el-input v-model="profileForm.email" disabled />
            </el-form-item>
            <el-form-item label="手机号">
              <el-input v-model="profileForm.phone" disabled />
            </el-form-item>
            <el-form-item label="角色">
              <el-input :value="formatRole(profileForm.role)" disabled />
            </el-form-item>
          </el-form>
          <div class="profile-actions">
            <el-button type="primary" @click="openEditProfileDialog">修改个人信息</el-button>
          </div>
        </div>
        
        <!-- 修改密码 -->
        <div v-if="activeMenu === 'password'" class="settings-section">
          <h3 class="section-title">修改密码</h3>
          <el-form :model="passwordForm" label-width="120px">
            <el-form-item label="当前密码" required>
              <el-input
                v-model="passwordForm.oldPassword"
                type="password"
                placeholder="请输入当前密码"
                show-password
              />
            </el-form-item>
            <el-form-item label="新密码" required>
              <el-input
                v-model="passwordForm.newPassword"
                type="password"
                placeholder="请输入新密码"
                show-password
              />
            </el-form-item>
            <el-form-item label="确认新密码" required>
              <el-input
                v-model="passwordForm.confirmPassword"
                type="password"
                placeholder="请再次输入新密码"
                show-password
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleChangePassword">确认修改</el-button>
            </el-form-item>
          </el-form>
        </div>
        
        <!-- 通知设置 -->
        <div v-if="activeMenu === 'notification'" class="settings-section">
          <h3 class="section-title">通知设置</h3>
          <div class="notification-list">
            <div class="notification-item">
              <div class="notification-info">
                <div class="notification-title">审查完成通知</div>
                <div class="notification-desc">合同审查完成后发送通知</div>
              </div>
              <el-switch v-model="notificationSettings.reviewComplete" @change="saveNotificationSettings" />
            </div>
            <div class="notification-item">
              <div class="notification-info">
                <div class="notification-title">高风险预警</div>
                <div class="notification-desc">检测到高风险合同时发送预警通知</div>
              </div>
              <el-switch v-model="notificationSettings.highRiskAlert" @change="saveNotificationSettings" />
            </div>
            <div class="notification-item">
              <div class="notification-info">
                <div class="notification-title">系统公告</div>
                <div class="notification-desc">接收系统更新和功能公告</div>
              </div>
              <el-switch v-model="notificationSettings.systemNotice" @change="saveNotificationSettings" />
            </div>
            <div class="notification-item">
              <div class="notification-info">
                <div class="notification-title">邮件通知</div>
                <div class="notification-desc">通过邮件接收重要通知</div>
              </div>
              <el-switch v-model="notificationSettings.emailNotification" @change="saveNotificationSettings" />
            </div>
          </div>
        </div>
        
        <!-- 存储设置 -->
        <div v-if="activeMenu === 'storage'" class="settings-section">
          <h3 class="section-title">存储设置</h3>
          <div class="storage-intro">
            <el-alert
              title="配置存储路径"
              description="设置合同文件上传和审查报告生成的存储位置，请确保路径有效且有写入权限"
              type="info"
              :closable="false"
              show-icon
            />
          </div>
          <div class="path-settings">
            <div class="path-card">
              <div class="path-card-header">
                <div class="path-icon upload-icon">
                  <el-icon :size="24"><Upload /></el-icon>
                </div>
                <div class="path-title-section">
                  <div class="path-label">上传文件地址</div>
                  <div class="path-desc">合同文件上传存储路径</div>
                </div>
              </div>
              <div class="path-input-section">
                <el-input
                  v-model="pathSettings.uploadPath"
                  placeholder="请选择或输入上传文件路径"
                  class="path-input"
                  clearable
                >
                  <template #prefix>
                    <el-icon><Folder /></el-icon>
                  </template>
                  <template #append>
                    <el-button type="primary" @click="selectUploadPath">
                      <el-icon><FolderOpened /></el-icon>
                      <span>浏览</span>
                    </el-button>
                  </template>
                </el-input>
                <div v-if="pathSettings.uploadPath" class="path-status success">
                  <el-icon><CircleCheck /></el-icon>
                  <span>已设置</span>
                </div>
                <div v-else class="path-status empty">
                  <el-icon><Warning /></el-icon>
                  <span>未设置</span>
                </div>
              </div>
            </div>
            <div class="path-card">
              <div class="path-card-header">
                <div class="path-icon review-icon">
                  <el-icon :size="24"><DocumentChecked /></el-icon>
                </div>
                <div class="path-title-section">
                  <div class="path-label">生成审查文件地址</div>
                  <div class="path-desc">审查报告生成存储路径</div>
                </div>
              </div>
              <div class="path-input-section">
                <el-input
                  v-model="pathSettings.reviewPath"
                  placeholder="请选择或输入审查文件路径"
                  class="path-input"
                  clearable
                >
                  <template #prefix>
                    <el-icon><Folder /></el-icon>
                  </template>
                  <template #append>
                    <el-button type="primary" @click="selectReviewPath">
                      <el-icon><FolderOpened /></el-icon>
                      <span>浏览</span>
                    </el-button>
                  </template>
                </el-input>
                <div v-if="pathSettings.reviewPath" class="path-status success">
                  <el-icon><CircleCheck /></el-icon>
                  <span>已设置</span>
                </div>
                <div v-else class="path-status empty">
                  <el-icon><Warning /></el-icon>
                  <span>未设置</span>
                </div>
              </div>
            </div>
          </div>
          <div class="path-actions">
            <el-button type="primary" size="large" @click="savePathSettings">
              <el-icon><Check /></el-icon>
              <span>保存路径设置</span>
            </el-button>
          </div>
        </div>
        
        <!-- 系统信息 -->
        <div v-if="activeMenu === 'system'" class="settings-section">
          <h3 class="section-title">系统信息</h3>
          <div class="system-info">
            <div class="info-item">
              <span class="info-label">系统版本</span>
              <span class="info-value">v{{ systemInfo.version }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">前端版本</span>
              <span class="info-value">v{{ systemInfo.frontendVersion }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">后端版本</span>
              <span class="info-value">v{{ systemInfo.backendVersion }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">最后更新</span>
              <span class="info-value">{{ systemInfo.lastUpdate }}</span>
            </div>
            <el-divider />
            <div class="info-item">
              <span class="info-label">知识库版本</span>
              <span class="info-value">v{{ systemInfo.knowledgeVersion }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">AI 模型</span>
              <span class="info-value">{{ systemInfo.aiModel }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 更换头像弹框 -->
    <el-dialog
      v-model="avatarDialogVisible"
      title="更换头像"
      width="400px"
      align-center
    >
      <div class="avatar-upload-content">
        <el-upload
          class="avatar-uploader"
          action="#"
          :auto-upload="false"
          :show-file-list="false"
          :on-change="handleAvatarChange"
          accept="image/*"
        >
          <el-avatar v-if="avatarPreview" :size="120" :src="avatarPreview" />
          <div v-else class="upload-placeholder">
            <el-icon :size="40"><Plus /></el-icon>
            <span>点击上传头像</span>
          </div>
        </el-upload>
        <p class="upload-tip">支持 JPG、PNG 格式，文件大小不超过 2MB</p>
      </div>
      <template #footer>
        <el-button @click="avatarDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveAvatar">确认</el-button>
      </template>
    </el-dialog>

    <!-- 修改个人信息弹框 -->
    <el-dialog
      v-model="editProfileDialogVisible"
      title="修改个人信息"
      width="500px"
      align-center
    >
      <el-form :model="editProfileForm" label-width="100px">
        <el-form-item label="昵称">
          <el-input v-model="editProfileForm.nickName" placeholder="请输入昵称" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="editProfileForm.email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item label="手机号">
          <el-input v-model="editProfileForm.phone" placeholder="请输入手机号" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editProfileDialogVisible = false">取消</el-button>
        <el-button type="primary" :disabled="!hasProfileInput" @click="handleSaveProfile">保存修改</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { get, post } from '@/utils/request'
import { changePassword, updateProfile, uploadAvatar, getNotificationSetting, updateNotificationSetting, getStorageConfig, saveStorageConfig, validatePath } from '@/api/user'
import { getSystemInfo } from '@/api/system'
import { md5 } from '@/utils/crypto'

const userStore = useUserStore()

// 从 localStorage 读取上次选中的菜单项
const savedMenu = localStorage.getItem('settings_active_menu')
const activeMenu = ref(savedMenu || 'profile')
const loading = ref(false)

// 监听菜单变化，保存到 localStorage
watch(activeMenu, (newVal) => {
  localStorage.setItem('settings_active_menu', newVal)
})

// 头像弹框
const avatarDialogVisible = ref(false)
const avatarPreview = ref('')
const avatarFile = ref(null)

// 修改个人信息弹框
const editProfileDialogVisible = ref(false)
const editProfileForm = ref({
  nickName: '',
  email: '',
  phone: ''
})

// 判断是否有至少一个字段有输入
const hasProfileInput = computed(() => {
  return !!editProfileForm.value.nickName ||
         !!editProfileForm.value.email ||
         !!editProfileForm.value.phone
})

// 菜单项
const menuItems = [
  { key: 'profile', label: '个人信息', icon: 'User' },
  { key: 'password', label: '修改密码', icon: 'Lock' },
  { key: 'notification', label: '通知设置', icon: 'Bell' },
  { key: 'storage', label: '存储设置', icon: 'Folder' },
  { key: 'system', label: '系统信息', icon: 'InfoFilled' }
]

// 路径设置
const pathSettings = ref({
  uploadPath: '',
  reviewPath: ''
})

// 选择上传文件路径
function selectUploadPath() {
  const input = document.createElement('input')
  input.type = 'file'
  input.webkitdirectory = true
  input.directory = true
  input.onchange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0]
      const fullPath = file.webkitRelativePath || file.name
      const folderName = fullPath.split('/')[0] || fullPath
      ElMessage.info(`已选择文件夹: ${folderName}，请在输入框中填写完整路径，例如: D:\\BaiduNetdisk\\${folderName}`)
      pathSettings.value.uploadPath = folderName
    }
  }
  input.click()
}

// 选择审查文件路径
function selectReviewPath() {
  const input = document.createElement('input')
  input.type = 'file'
  input.webkitdirectory = true
  input.directory = true
  input.onchange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0]
      const fullPath = file.webkitRelativePath || file.name
      const folderName = fullPath.split('/')[0] || fullPath
      ElMessage.info(`已选择文件夹: ${folderName}，请在输入框中填写完整路径，例如: D:\\BaiduNetdisk\\${folderName}`)
      pathSettings.value.reviewPath = folderName
    }
  }
  input.click()
}

// 获取存储配置
async function fetchStorageConfig() {
  try {
    const res = await getStorageConfig()
    if (res.code === 200) {
      const data = res.data
      pathSettings.value = {
        uploadPath: data.uploadPath || '',
        reviewPath: data.reviewPath || ''
      }
    }
  } catch (error) {
    console.error('获取存储配置失败:', error)
    ElMessage.error('获取存储配置失败')
  }
}

// 保存路径设置
async function savePathSettings() {
  try {
    // 验证路径
    if (!pathSettings.value.uploadPath.trim()) {
      ElMessage.warning('请输入上传文件路径')
      return
    }
    if (!pathSettings.value.reviewPath.trim()) {
      ElMessage.warning('请输入审查文件路径')
      return
    }

    // 验证路径有效性
    const uploadValid = await validatePath(pathSettings.value.uploadPath.trim())
    if (!uploadValid.data) {
      ElMessage.error('上传文件路径无效或没有写入权限')
      return
    }

    const reviewValid = await validatePath(pathSettings.value.reviewPath.trim())
    if (!reviewValid.data) {
      ElMessage.error('审查文件路径无效或没有写入权限')
      return
    }

    // 保存配置
    const data = {
      uploadPath: pathSettings.value.uploadPath.trim(),
      reviewPath: pathSettings.value.reviewPath.trim()
    }
    const res = await saveStorageConfig(data)
    if (res.code === 200) {
      ElMessage.success('路径设置已保存')
    } else {
      ElMessage.error(res.message || '保存失败')
    }
  } catch (error) {
    console.error('保存路径设置失败:', error)
    ElMessage.error('保存失败')
  }
}

// 个人信息表单
const profileForm = ref({
  avatar: '',
  username: '',
  nickName: '',
  email: '',
  phone: '',
  role: ''
})

// 格式化角色显示
function formatRole(role) {
  const roleMap = {
    'admin': '管理员',
    'user': '用户'
  }
  return roleMap[role] || role || '普通用户'
}

// 获取用户信息
async function fetchUserInfo() {
  loading.value = true
  try {
    const res = await get('/auth/user-info')
    if (res.code === 200) {
      const data = res.data
      profileForm.value = {
        avatar: data.avatar || '',
        username: data.username || '',
        nickName: data.nickName || '',
        email: data.email || '',
        phone: data.phone || '',
        role: data.role || 'user'
      }
      // 更新store中的用户信息
      if (data) {
        userStore.setUserInfo(data)
      }
    }
  } catch (error) {
    ElMessage.error('获取用户信息失败')
  } finally {
    loading.value = false
  }
}

// 获取通知设置
async function fetchNotificationSetting() {
  try {
    const res = await getNotificationSetting()
    if (res.code === 200) {
      const data = res.data
      notificationSettings.value = {
        reviewComplete: data.reviewComplete ?? true,
        highRiskAlert: data.riskAlert ?? true,
        systemNotice: data.systemNotice ?? true,
        emailNotification: data.emailNotification ?? false
      }
    }
  } catch (error) {
    console.error('获取通知设置失败:', error)
  }
}

// 页面加载时获取用户信息和通知设置
onMounted(() => {
  fetchUserInfo()
  fetchNotificationSetting()
  fetchStorageConfig()
  loadSystemInfo()
})

// 密码表单
const passwordForm = ref({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

// 通知设置
const notificationSettings = ref({
  reviewComplete: true,
  highRiskAlert: true,
  systemNotice: true,
  emailNotification: false
})

// 系统信息
const systemInfo = ref({
  version: '1.0.0',
  frontendVersion: '1.0.0',
  backendVersion: '1.0.0',
  lastUpdate: '2024-01-15',
  knowledgeVersion: '2024.01',
  aiModel: 'GPT-4'
})

// 加载系统信息
async function loadSystemInfo() {
  try {
    const res = await getSystemInfo()
    if (res.code === 200 && res.data) {
      systemInfo.value = {
        ...systemInfo.value,
        ...res.data
      }
    }
  } catch (error) {
    console.error('加载系统信息失败:', error)
  }
}

// 保存个人信息
function openEditProfileDialog() {
  editProfileForm.value = {
    nickName: profileForm.value.nickName,
    email: profileForm.value.email,
    phone: profileForm.value.phone
  }
  editProfileDialogVisible.value = true
}

async function handleSaveProfile() {
  try {
    await updateProfile({
      nickName: editProfileForm.value.nickName,
      email: editProfileForm.value.email,
      phone: editProfileForm.value.phone
    })
    ElMessage.success('个人信息已保存')
    profileForm.value = {
      ...profileForm.value,
      nickName: editProfileForm.value.nickName,
      email: editProfileForm.value.email,
      phone: editProfileForm.value.phone
    }
    editProfileDialogVisible.value = false
  } catch (error) {
    console.error('保存个人信息失败:', error)
  }
}

// 修改密码
async function handleChangePassword() {
  if (!passwordForm.value.oldPassword || !passwordForm.value.newPassword) {
    ElMessage.warning('请填写完整信息')
    return
  }
  if (passwordForm.value.newPassword !== passwordForm.value.confirmPassword) {
    ElMessage.error('两次输入的密码不一致')
    return
  }

  try {
    await changePassword({
      oldPassword: md5(passwordForm.value.oldPassword),
      newPassword: md5(passwordForm.value.newPassword),
      confirmPassword: md5(passwordForm.value.confirmPassword)
    })
    ElMessage.success('密码修改成功')
    passwordForm.value = { oldPassword: '', newPassword: '', confirmPassword: '' }
  } catch (error) {
    // 错误消息已在请求拦截器中显示
    console.error('修改密码失败:', error)
  }
}

// 保存通知设置
async function saveNotificationSettings() {
  try {
    const data = {
      reviewComplete: notificationSettings.value.reviewComplete,
      riskAlert: notificationSettings.value.highRiskAlert,
      systemNotice: notificationSettings.value.systemNotice,
      emailNotification: notificationSettings.value.emailNotification
    }
    const res = await updateNotificationSetting(data)
    if (res.code === 200) {
      ElMessage.success('通知设置已保存')
    } else {
      ElMessage.error(res.message || '保存失败')
    }
  } catch (error) {
    console.error('保存通知设置失败:', error)
    ElMessage.error('保存失败，请稍后重试')
  }
}

// 处理头像文件选择
function handleAvatarChange(file) {
  const isJPG = file.raw.type === 'image/jpeg'
  const isPNG = file.raw.type === 'image/png'
  const isLt2M = file.raw.size / 1024 / 1024 < 2

  if (!isJPG && !isPNG) {
    ElMessage.error('头像图片只能是 JPG 或 PNG 格式!')
    return false
  }
  if (!isLt2M) {
    ElMessage.error('头像图片大小不能超过 2MB!')
    return false
  }

  avatarFile.value = file.raw
  avatarPreview.value = URL.createObjectURL(file.raw)
}

// 保存头像
async function saveAvatar() {
  if (!avatarFile.value) {
    ElMessage.warning('请先选择头像图片')
    return
  }

  try {
    const formData = new FormData()
    formData.append('file', avatarFile.value)
    const res = await uploadAvatar(formData)

    if (res.code === 200) {
      profileForm.value.avatar = res.data.avatarUrl
      ElMessage.success('头像更换成功')
      avatarDialogVisible.value = false
      avatarPreview.value = ''
      avatarFile.value = null
    } else {
      ElMessage.error(res.message || '头像上传失败')
    }
  } catch (error) {
    console.error('上传头像失败:', error)
    ElMessage.error('头像上传失败，请稍后重试')
  }
}
</script>

<style scoped lang="scss">
.settings-page {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 24px;
  
  .page-title {
    font-size: $font-size-xl;
    font-weight: 600;
    color: $text-primary;
    margin: 0;
  }
}

.settings-content {
  display: flex;
  gap: 24px;
  background: white;
  border-radius: $radius-lg;
  box-shadow: $shadow-sm;
  min-height: 600px;
}

.settings-sidebar {
  width: 200px;
  padding: 16px 0;
  border-right: 1px solid $border-light;
  
  .menu-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 20px;
    cursor: pointer;
    transition: all $transition-fast;
    color: $text-secondary;
    
    &:hover {
      background: $bg-secondary;
      color: $primary-color;
    }
    
    &.active {
      background: rgba($primary-color, 0.08);
      color: $primary-color;
      font-weight: 500;
      border-right: 3px solid $primary-color;
    }
    
    .el-icon {
      font-size: 18px;
    }
  }
}

.settings-main {
  flex: 1;
  padding: 24px;
}

.settings-section {
  max-width: 600px;
  
  .profile-actions {
    margin-top: 24px;
    display: flex;
    justify-content: center;
  }
  
  .section-title {
    font-size: $font-size-lg;
    font-weight: 600;
    color: $text-primary;
    margin: 0 0 24px 0;
    padding-bottom: 12px;
    border-bottom: 1px solid $border-light;
  }
}

.notification-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin-bottom: 24px;
}

.notification-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  background: $bg-secondary;
  border-radius: $radius-md;
  
  .notification-info {
    .notification-title {
      font-weight: 500;
      color: $text-primary;
      margin-bottom: 4px;
    }
    
    .notification-desc {
      font-size: $font-size-sm;
      color: $text-secondary;
    }
  }
}

.system-info {
  .info-item {
    display: flex;
    justify-content: space-between;
    padding: 12px 0;
    border-bottom: 1px solid $border-light;
    
    &:last-child {
      border-bottom: none;
    }
    
    .info-label {
      color: $text-secondary;
    }
    
    .info-value {
      color: $text-primary;
      font-weight: 500;
    }
  }
}

.form-actions {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid $border-light;
}

.avatar-upload-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px;

  .avatar-uploader {
    :deep(.el-upload) {
      border: 2px dashed $border-light;
      border-radius: 50%;
      cursor: pointer;
      position: relative;
      overflow: hidden;
      transition: border-color 0.3s;

      &:hover {
        border-color: $primary-color;
      }
    }
  }

  .upload-placeholder {
    width: 120px;
    height: 120px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    color: $text-secondary;
    background: $bg-secondary;
    border-radius: 50%;

    span {
      margin-top: 8px;
      font-size: $font-size-sm;
    }
  }

  .upload-tip {
    margin-top: 16px;
    color: $text-secondary;
    font-size: $font-size-sm;
  }
}

// 存储设置样式
.storage-intro {
  margin-bottom: $spacing-lg;
}

.path-settings {
  display: flex;
  flex-direction: column;
  gap: $spacing-md;
  margin-bottom: $spacing-lg;
}

.path-card {
  background: $bg-secondary;
  border: 1px solid $border-light;
  border-radius: $radius-md;
  padding: $spacing-md;
  transition: all $transition-base;
  
  &:hover {
    box-shadow: $shadow-md;
    border-color: $border-color;
  }
  
  .path-card-header {
    display: flex;
    align-items: center;
    gap: $spacing-md;
    margin-bottom: $spacing-md;
    
    .path-icon {
      width: 40px;
      height: 40px;
      border-radius: $radius-md;
      display: flex;
      align-items: center;
      justify-content: center;
      
      &.upload-icon {
        background: rgba($info-color, 0.1);
        color: $info-color;
      }
      
      &.review-icon {
        background: rgba($success-color, 0.1);
        color: $success-color;
      }
    }
    
    .path-title-section {
      flex: 1;
      
      .path-label {
        font-size: $font-size-base;
        font-weight: 500;
        color: $text-primary;
        margin-bottom: $spacing-xs;
      }
      
      .path-desc {
        font-size: $font-size-sm;
        color: $text-secondary;
      }
    }
  }
  
  .path-input-section {
    .path-input {
      margin-bottom: $spacing-sm;
      
      :deep(.el-input__inner) {
        font-family: 'Consolas', 'Monaco', monospace;
        font-size: $font-size-sm;
      }
      
      :deep(.el-input-group__append) {
        padding: 0;
        
        .el-button {
          border-radius: 0 $radius-sm $radius-sm 0;
          margin: 0;
          padding: 0 $spacing-md;
          
          span {
            margin-left: $spacing-xs;
          }
        }
      }
    }
    
    .path-status {
      display: flex;
      align-items: center;
      gap: $spacing-xs;
      font-size: $font-size-sm;
      padding: $spacing-xs $spacing-sm;
      border-radius: $radius-sm;
      width: fit-content;
      
      &.success {
        color: $success-color;
        background: rgba($success-color, 0.1);
      }
      
      &.empty {
        color: $warning-color;
        background: rgba($warning-color, 0.1);
      }
      
      .el-icon {
        font-size: $font-size-sm;
      }
    }
  }
}

.path-actions {
  display: flex;
  gap: $spacing-md;
  padding-top: $spacing-lg;
  border-top: 1px solid $border-light;
  
  .el-button {
    min-width: 120px;
    
    .el-icon {
      margin-right: $spacing-xs;
    }
  }
}
</style>
