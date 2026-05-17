import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  uploadContract,
  batchUploadContracts,
  getContractList,
  getContractDetail,
  deleteContract,
  batchDeleteContracts
} from '@/api/contract'
import { ElMessage } from 'element-plus'

export const useContractStore = defineStore('contract', () => {
  // State
  const contractList = ref([])
  const currentContract = ref(null)
  const uploadQueue = ref([])
  const loading = ref(false)
  const pagination = ref({
    page: 1,
    pageSize: 10,
    total: 0
  })

  // Getters
  const uploadedContracts = computed(() => {
    return uploadQueue.value.filter(item => item.status === 'success')
  })

  const hasUploadingFiles = computed(() => {
    return uploadQueue.value.some(item => item.status === 'uploading')
  })

  // Actions
  // 添加文件到上传队列
  function addToUploadQueue(files) {
    const newItems = files.map(file => ({
      id: Date.now() + Math.random(),
      file,
      name: file.name,
      size: file.size,
      progress: 0,
      status: 'pending', // pending, uploading, success, error
      errorMsg: ''
    }))
    uploadQueue.value.push(...newItems)
    return newItems
  }

  // 从队列中移除
  function removeFromQueue(id) {
    const index = uploadQueue.value.findIndex(item => item.id === id)
    if (index > -1) {
      uploadQueue.value.splice(index, 1)
    }
  }

  // 清空队列
  function clearQueue() {
    uploadQueue.value = []
  }

  // 更新文件状态
  function updateFileStatus(id, status) {
    const item = uploadQueue.value.find(i => i.id === id)
    if (item) {
      item.status = status
      item.progress = 0
      item.errorMsg = ''
    }
  }

  // 上传单个文件
  async function uploadSingleFile(id) {
    const item = uploadQueue.value.find(i => i.id === id)
    if (!item) return

    item.status = 'uploading'
    
    try {
      const result = await uploadContract(
        item.file,
        (progress) => {
          item.progress = progress
        }
      )
      
      item.status = 'success'
      item.contractId = result.contractId
      ElMessage.success(`${item.name} 上传成功`)
      return result
    } catch (error) {
      item.status = 'error'
      item.errorMsg = error.message || '上传失败'
      ElMessage.error(`${item.name} 上传失败`)
      throw error
    }
  }

  // 上传所有待上传文件
  async function uploadAllFiles() {
    const pendingItems = uploadQueue.value.filter(item => item.status === 'pending')
    
    for (const item of pendingItems) {
      try {
        await uploadSingleFile(item.id)
      } catch (error) {
        console.error('上传失败:', error)
      }
    }
  }

  // 获取合同列表
  async function fetchContractList(params = {}) {
    loading.value = true
    try {
      const result = await getContractList({
        page: pagination.value.page,
        pageSize: pagination.value.pageSize,
        ...params
      })
      
      contractList.value = result.data || []
      pagination.value.total = result.total || 0
      return result
    } catch (error) {
      console.error('获取合同列表失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  // 获取合同详情
  async function fetchContractDetail(id) {
    loading.value = true
    try {
      const result = await getContractDetail(id)
      currentContract.value = result
      return result
    } catch (error) {
      console.error('获取合同详情失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  // 删除合同
  async function removeContract(id) {
    try {
      await deleteContract(id)
      ElMessage.success('删除成功')
      // 从列表中移除
      const index = contractList.value.findIndex(item => item.id === id)
      if (index > -1) {
        contractList.value.splice(index, 1)
        pagination.value.total--
      }
    } catch (error) {
      console.error('删除合同失败:', error)
      throw error
    }
  }

  // 批量删除
  async function removeBatch(ids) {
    try {
      await batchDeleteContracts(ids)
      ElMessage.success(`成功删除 ${ids.length} 个合同`)
      await fetchContractList()
    } catch (error) {
      console.error('批量删除失败:', error)
      throw error
    }
  }

  // 设置当前合同
  function setCurrentContract(contract) {
    currentContract.value = contract
  }

  // 更新分页
  function updatePagination(page, pageSize) {
    pagination.value.page = page
    pagination.value.pageSize = pageSize
  }

  return {
    // State
    contractList,
    currentContract,
    uploadQueue,
    loading,
    pagination,
    // Getters
    uploadedContracts,
    hasUploadingFiles,
    // Actions
    addToUploadQueue,
    removeFromQueue,
    clearQueue,
    updateFileStatus,
    uploadSingleFile,
    uploadAllFiles,
    fetchContractList,
    fetchContractDetail,
    removeContract,
    removeBatch,
    setCurrentContract,
    updatePagination
  }
})
