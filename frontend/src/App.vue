<template>
  <router-view />
  <ToastNotification ref="toastRef" v-if="userStore.isLoggedIn" />
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'
import { useUserStore } from '@/stores/user'
import { useTokenRefresh } from '@/composables/useTokenRefresh'
import ToastNotification from '@/components/Notification/ToastNotification.vue'
import { setToastInstance } from '@/utils/sse'

const userStore = useUserStore()
const toastRef = ref(null)

watch(toastRef, (instance) => {
  if (instance) {
    setToastInstance(instance)
  }
})

useTokenRefresh()

onMounted(() => {
  userStore.loadUserFromStorage()
})
</script>

<style>
</style>
