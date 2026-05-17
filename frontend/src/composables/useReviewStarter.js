import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getContractFileBlob } from '@/api/contract'
import { startReview as startReviewApi } from '@/api/review'

export function useReviewStarter() {
  const router = useRouter()

  const reviewOptionsVisible = ref(false)
  const startingReview = ref(false)
  const pendingContract = ref(null)

  function startReview(contract) {
    pendingContract.value = contract
    reviewOptionsVisible.value = true
  }

  async function handleReviewConfirm(reviewOptions) {
    if (!pendingContract.value) {
      ElMessage.error('未找到合同信息')
      return
    }

    startingReview.value = true

    try {
      const contractId = Number(
        pendingContract.value?.id ||
        pendingContract.value?.contractId
      )

      if (!contractId) {
        throw new Error('合同 ID 不存在')
      }

      const fileBlob = await getContractFileBlob(contractId)

      const res = await startReviewApi(
        contractId,
        fileBlob,
        pendingContract.value.fileName,
        reviewOptions
      )

      if (res.code === 200) {
        ElMessage.success('审查已启动')
        sessionStorage.setItem('reviewOptions', JSON.stringify(reviewOptions))
        if (res.data?.reviewId) {
          sessionStorage.setItem('currentReviewId', res.data.reviewId)
        }
        reviewOptionsVisible.value = false
        router.push(`/review/${contractId}`)
      } else {
        ElMessage.error(res.message || '启动审查失败')
      }
    } catch (error) {
      console.error('启动审查失败:', error)
      ElMessage.error('启动审查失败: ' + (error.message || '未知错误'))
    } finally {
      startingReview.value = false
    }
  }

  return {
    reviewOptionsVisible,
    startingReview,
    pendingContract,
    startReview,
    handleReviewConfirm
  }
}
