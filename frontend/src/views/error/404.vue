<template>
  <div class="error-page">
    <div class="error-content">
      <div class="error-code">404</div>
      <h1 class="error-title">页面不存在</h1>
      <p class="error-desc">抱歉，您访问的页面不存在或已被移除</p>
      <div class="error-actions">
        <el-button type="primary" size="large" @click="$router.push('/dashboard')">
          <el-icon><HomeFilled /></el-icon>
          <span>返回首页</span>
        </el-button>
        <el-button size="large" @click="$router.back()">
          <el-icon><ArrowLeft /></el-icon>
          <span>返回上一页</span>
        </el-button>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
.error-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: $bg-secondary;
}

.error-content {
  text-align: center;
  padding: 40px;
}

.error-code {
  font-size: 120px;
  font-weight: 700;
  color: $primary-color;
  line-height: 1;
  margin-bottom: 16px;
  opacity: 0.8;
}

.error-title {
  font-size: $font-size-2xl;
  font-weight: 600;
  color: $text-primary;
  margin: 0 0 12px 0;
}

.error-desc {
  font-size: $font-size-base;
  color: $text-secondary;
  margin: 0 0 32px 0;
}

.error-actions {
  display: flex;
  gap: 16px;
  justify-content: center;
}
</style>
