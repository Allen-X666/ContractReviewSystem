<template>
  <div class="page-skeleton" :style="{ height: height }">
    <el-skeleton animated :rows="rows" :throttle="throttle">
      <template #template>
        <slot>
          <div class="skeleton-header" v-if="showHeader">
            <el-skeleton-item variant="h1" style="width: 30%; height: 32px;" />
            <el-skeleton-item variant="button" style="width: 100px; height: 36px; margin-left: auto;" />
          </div>
          <div class="skeleton-content">
            <el-skeleton-item 
              v-for="i in rows" 
              :key="i"
              variant="p" 
              :style="{ width: getRowWidth(i), marginTop: i === 1 && showHeader ? '24px' : '16px' }" 
            />
          </div>
        </slot>
      </template>
    </el-skeleton>
  </div>
</template>

<script setup>
defineProps({
  rows: {
    type: Number,
    default: 8
  },
  height: {
    type: String,
    default: '100%'
  },
  showHeader: {
    type: Boolean,
    default: true
  },
  throttle: {
    type: Number,
    default: 0
  }
})

function getRowWidth(index) {
  const widths = ['100%', '95%', '90%', '85%', '92%', '88%', '95%', '90%']
  return widths[(index - 1) % widths.length]
}
</script>

<style scoped>
.page-skeleton {
  padding: 24px;
}

.skeleton-header {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.skeleton-content {
  display: flex;
  flex-direction: column;
}
</style>
