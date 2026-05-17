import { ref } from 'vue'
import { getCaptcha } from '@/api/user'
import { ElMessage } from 'element-plus'

/**
 * 验证码管理组合式函数
 * @param {string} type - 验证码类型（'login' | 'register'）
 * @param {Function} onCaptchaIdChange - 验证码ID变更回调函数
 * @returns {Object} 验证码相关的状态和方法
 */
export function useCaptcha(type, onCaptchaIdChange) {
  const captchaImage = ref('')
  const captchaLoading = ref(false)

  /**
   * 获取图形验证码
   */
  async function fetchCaptcha() {
    captchaLoading.value = true
    try {
      const res = await getCaptcha(type)
      captchaImage.value = res.data.imageBase64
      
      // 通过回调函数更新表单中的 captchaId
      if (onCaptchaIdChange) {
        onCaptchaIdChange(res.data.captchaId)
      }
      
      return res.data.captchaId
    } catch (error) {
      console.error('获取验证码失败:', error)
      ElMessage.error('获取验证码失败')
      throw error
    } finally {
      captchaLoading.value = false
    }
  }

  /**
   * 刷新验证码
   */
  function refreshCaptcha() {
    return fetchCaptcha()
  }

  /**
   * 重置验证码
   */
  function resetCaptcha() {
    captchaImage.value = ''
  }

  return {
    captchaImage,
    captchaLoading,
    fetchCaptcha,
    refreshCaptcha,
    resetCaptcha
  }
}
