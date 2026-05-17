<template>
  <el-container class="layout-container">
    <!-- 顶部导航 -->
    <el-header class="layout-header" height="64px">
      <div class="header-left">
        <div class="logo">
          <el-icon class="logo-icon"><DocumentChecked /></el-icon>
          <span class="logo-text">智能合同审查助手</span>
        </div>
        
        <nav class="header-nav">
          <router-link
            v-for="item in visibleMenuItems"
            :key="item.path"
            :to="item.path"
            :class="['nav-item', { active: isActive(item.path) }]"
          >
            <el-icon v-if="item.icon"><component :is="item.icon" /></el-icon>
            <span>{{ item.title }}</span>
          </router-link>
        </nav>
      </div>
      
      <div class="header-right">
        <el-button
          type="primary"
          class="upload-btn"
          @click="$router.push('/contract/upload')"
        >
          <el-icon><Upload /></el-icon>
          <span>上传合同</span>
        </el-button>
        
        <el-dropdown trigger="click" @command="handleCommand">
          <div class="user-info">
            <el-avatar :size="32" :src="userStore.avatar">
              <el-icon><User /></el-icon>
            </el-avatar>
            <span class="username">{{ userStore.displayName }}</span>
            <el-icon><ArrowDown /></el-icon>
          </div>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="settings">
                <el-icon><Setting /></el-icon>
                <span>系统设置</span>
              </el-dropdown-item>
              <el-dropdown-item divided command="logout">
                <el-icon><SwitchButton /></el-icon>
                <span>退出登录</span>
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </el-header>
    
    <!-- 主内容区 -->
    <el-main class="layout-main">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </el-main>
  </el-container>

  <!-- 智能客服 -->
  <ChatBot />
</template>

<script setup>
import { computed } from 'vue'
import ChatBot from '@/components/ChatBot/ChatBot.vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { logout } from '@/api/user'
import { ElMessage, ElMessageBox } from 'element-plus'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

// 菜单项
const menuItems = [
  { path: '/dashboard', title: '仪表盘', icon: 'DataLine' },
  { path: '/contract/list', title: '合同管理', icon: 'Document' },
  { path: '/history', title: '审查历史', icon: 'Clock' },
  { path: '/knowledge', title: '法律知识库', icon: 'Collection' },
  { path: '/admin', title: '系统管理', icon: 'Setting', adminOnly: true }
]

// 可见菜单项
const visibleMenuItems = computed(() => {
  return menuItems.filter(item => {
    if (item.hidden) return false
    if (item.adminOnly && userStore.role?.toLowerCase() !== 'admin') return false
    return true
  })
})

// 判断是否激活
function isActive(path) {
  if (path === '/contract/list') {
    return route.path.startsWith('/contract')
  }
  return route.path === path || route.path.startsWith(path + '/')
}

// 处理下拉菜单命令
function handleCommand(command) {
  switch (command) {
    case 'settings':
      router.push('/settings')
      break
    case 'logout':
      handleLogout()
      break
  }
}

// 退出登录
async function handleLogout() {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    // 调用后端退出登录接口
    await logout()

    userStore.logout()
    ElMessage.success('已退出登录')
    router.push('/login')
  } catch {
    // 取消退出
  }
}
</script>

<style scoped lang="scss">
.layout-container {
  min-height: 100vh;
  background-color: $bg-secondary;
}

.layout-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: linear-gradient(135deg, $primary-color 0%, $primary-light 100%);
  color: white;
  padding: 0 24px;
  box-shadow: $shadow-md;
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 48px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  
  .logo-icon {
    font-size: 28px;
    color: $secondary-color;
  }
  
  .logo-text {
    font-size: $font-size-lg;
    font-weight: 600;
    letter-spacing: 1px;
  }
}

.header-nav {
  display: flex;
  align-items: center;
  gap: 8px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  color: rgba(255, 255, 255, 0.85);
  text-decoration: none;
  border-radius: $radius-md;
  transition: all $transition-fast;
  font-size: $font-size-base;
  
  &:hover {
    color: white;
    background-color: rgba(255, 255, 255, 0.1);
  }
  
  &.active {
    color: white;
    background-color: rgba(255, 255, 255, 0.15);
    font-weight: 500;
  }
  
  .el-icon {
    font-size: 16px;
  }
}

.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.upload-btn {
  background-color: $secondary-color;
  border-color: $secondary-color;
  font-weight: 500;
  
  &:hover {
    background-color: $secondary-light;
    border-color: $secondary-light;
  }
  
  .el-icon {
    margin-right: 4px;
  }
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: $radius-md;
  transition: background-color $transition-fast;
  
  &:hover {
    background-color: rgba(255, 255, 255, 0.1);
  }
  
  .username {
    font-size: $font-size-sm;
    font-weight: 500;
    color: rgba(255, 255, 255, 0.95);
    max-width: 100px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  
  .el-icon {
    color: rgba(255, 255, 255, 0.7);
    font-size: 12px;
    transition: transform $transition-fast, color $transition-fast;
  }
  
  &:hover .el-icon {
    color: rgba(255, 255, 255, 0.95);
    transform: translateY(2px);
  }
}

.layout-main {
  padding: 0;
  min-height: calc(100vh - 64px);
}

// 页面过渡动画
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
