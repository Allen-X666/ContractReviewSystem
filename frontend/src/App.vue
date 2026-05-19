<template>
  <router-view />
  <ToastNotification ref="toastRef" />
</template>

<script setup>
import { onMounted, ref, watch, nextTick } from 'vue'
import { useUserStore } from '@/stores/user'
import { useTokenRefresh } from '@/composables/useTokenRefresh'
import ToastNotification from '@/components/Notification/ToastNotification.vue'
import { setToastInstance, sseClient } from '@/utils/sse'

const userStore = useUserStore()
const toastRef = ref(null)

watch(toastRef, (instance) => {
  console.log('App: toastRef变化', instance)
  if (instance) {
    setToastInstance(instance)
  }
})

useTokenRefresh()

onMounted(() => {
  userStore.loadUserFromStorage()
  // 确保ToastNotification组件已渲染并设置实例
  nextTick(() => {
    if (toastRef.value) {
      setToastInstance(toastRef.value)
      console.log('App: toastInstance已设置')
    }
    // 延迟建立SSE连接
    setTimeout(() => {
      if (userStore.isLoggedIn) {
        sseClient.connect()
      }
    }, 100)
  })
})
</script>

<style>
</style>
