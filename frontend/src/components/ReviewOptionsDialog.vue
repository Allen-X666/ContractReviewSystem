<template>
  <el-dialog
    :model-value="visible"
    title="审查配置"
    width="480px"
    :close-on-click-modal="false"
    class="review-options-dialog"
    @update:model-value="handleClose"
  >
    <div class="review-options-content">
      <!-- 审查项目列表 -->
      <div class="options-list">
        <div
          v-for="option in reviewOptionList"
          :key="option.value"
          class="option-item"
          :class="{ 'is-selected': selectedOptions.includes(option.value) }"
          @click="toggleOption(option.value)"
        >
          <div class="item-check">
            <el-checkbox 
              :model-value="selectedOptions.includes(option.value)"
              @click.stop
              @change="toggleOption(option.value)"
            />
          </div>
          <div class="item-icon">
            <el-icon><component :is="option.icon" /></el-icon>
          </div>
          <div class="item-info">
            <div class="item-title">
              {{ option.label }}
              <span v-if="option.recommended" class="recommend-tag">推荐</span>
            </div>
            <div class="item-desc">{{ option.description }}</div>
          </div>
        </div>
      </div>
      
      <!-- 快捷操作 -->
      <div class="quick-actions">
        <el-button link size="small" @click="selectAllOptions">全选</el-button>
        <el-divider direction="vertical" />
        <el-button link size="small" @click="clearAllOptions">清空</el-button>
        <el-divider direction="vertical" />
        <el-button link size="small" type="primary" @click="selectRecommendedOptions">推荐配置</el-button>
      </div>
      
      <!-- 合同类型选择 -->
      <div class="contract-type-section">
        <div class="section-label">
          <el-icon><Document /></el-icon>
          <span>合同类型（可选）</span>
        </div>
        <el-select 
          v-model="selectedContractType" 
          placeholder="自动识别" 
          clearable 
          class="contract-type-select"
        >
          <el-option label="采购合同" value="purchase" />
          <el-option label="服务协议" value="service" />
          <el-option label="劳动合同" value="labor" />
          <el-option label="租赁合同" value="lease" />
          <el-option label="保密协议" value="confidentiality" />
          <el-option label="合作协议" value="cooperation" />
        </el-select>
      </div>
    </div>
    
    <template #footer>
      <div class="dialog-footer">
        <span class="selected-count" v-if="selectedOptions.length > 0">
          已选择 {{ selectedOptions.length }} 项
        </span>
        <el-button @click="handleClose">取消</el-button>
        <el-button 
          type="primary" 
          :loading="loading" 
          :disabled="selectedOptions.length === 0"
          @click="handleConfirm"
        >
          开始审查
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'

// Props
const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  loading: {
    type: Boolean,
    default: false
  },
  defaultOptions: {
    type: Array,
    default: () => ['checkInvalidClause', 'checkMissingClause', 'checkUnreasonableClause', 'checkLegalRisk']
  }
})

// Emits
const emit = defineEmits(['update:visible', 'confirm'])

// 审查选项列表
const reviewOptionList = [
  {
    value: 'checkInvalidClause',
    label: '无效条款检查',
    description: '检测合同中违反法律规定的无效条款，确保合同法律效力',
    icon: 'WarningFilled',
    type: 'danger',
    recommended: true
  },
  {
    value: 'checkMissingClause',
    label: '缺失条款检查',
    description: '检测合同是否缺少必要的法定条款，完善合同内容',
    icon: 'CircleCheckFilled',
    type: 'success',
    recommended: true
  },
  {
    value: 'checkUnreasonableClause',
    label: '不合理条款检查',
    description: '检测显失公平或单方面的霸王条款，保护您的权益',
    icon: 'InfoFilled',
    type: 'warning',
    recommended: true
  },
  {
    value: 'checkLegalRisk',
    label: '法律风险检查',
    description: '全面检测潜在的法律风险和合规问题，防范于未然',
    icon: 'Search',
    type: 'primary',
    recommended: true
  }
]

// 选中的选项
const selectedOptions = ref([])
const selectedContractType = ref('')

// 监听对话框显示，重置选项
watch(() => props.visible, (newVal) => {
  if (newVal) {
    selectedOptions.value = [...props.defaultOptions]
    selectedContractType.value = ''
  }
})

// 切换选项
function toggleOption(value) {
  const index = selectedOptions.value.indexOf(value)
  if (index > -1) {
    selectedOptions.value.splice(index, 1)
  } else {
    selectedOptions.value.push(value)
  }
}

// 全选
function selectAllOptions() {
  selectedOptions.value = reviewOptionList.map(opt => opt.value)
}

// 清空
function clearAllOptions() {
  selectedOptions.value = []
}

// 推荐配置
function selectRecommendedOptions() {
  selectedOptions.value = reviewOptionList
    .filter(opt => opt.recommended)
    .map(opt => opt.value)
}

// 关闭对话框
function handleClose() {
  emit('update:visible', false)
}

// 确认开始审查
function handleConfirm() {
  if (selectedOptions.value.length === 0) {
    return
  }
  
  const reviewOptions = {
    checkInvalidClause: selectedOptions.value.includes('checkInvalidClause'),
    checkMissingClause: selectedOptions.value.includes('checkMissingClause'),
    checkUnreasonableClause: selectedOptions.value.includes('checkUnreasonableClause'),
    checkLegalRisk: selectedOptions.value.includes('checkLegalRisk'),
    contractType: selectedContractType.value || undefined
  }
  
  emit('confirm', reviewOptions)
}
</script>

<style scoped lang="scss">
.review-options-dialog {
  :deep(.el-dialog__body) {
    padding: 20px;
  }
  
  :deep(.el-dialog__footer) {
    padding: 12px 20px 20px;
  }
}

.review-options-content {
  .options-list {
    border: 1px solid $border-light;
    border-radius: 8px;
    overflow: hidden;
    margin-bottom: 16px;
    
    .option-item {
      display: flex;
      align-items: center;
      padding: 14px 16px;
      cursor: pointer;
      border-bottom: 1px solid $border-light;
      transition: all 0.2s ease;
      
      &:last-child {
        border-bottom: none;
      }
      
      &:hover {
        background-color: $bg-secondary;
      }
      
      &.is-selected {
        background-color: rgba($primary-color, 0.04);
        
        .item-icon {
          color: $primary-color;
        }
      }
      
      .item-check {
        margin-right: 12px;
      }
      
      .item-icon {
        width: 32px;
        height: 32px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 12px;
        color: $text-tertiary;
        font-size: 18px;
        transition: color 0.2s;
      }
      
      .item-info {
        flex: 1;
        min-width: 0;
        
        .item-title {
          font-size: $font-size-base;
          font-weight: 500;
          color: $text-primary;
          margin-bottom: 2px;
          display: flex;
          align-items: center;
          gap: 8px;
          
          .recommend-tag {
            font-size: 11px;
            color: $primary-color;
            background: rgba($primary-color, 0.1);
            padding: 1px 6px;
            border-radius: 4px;
            font-weight: normal;
          }
        }
        
        .item-desc {
          font-size: $font-size-sm;
          color: $text-secondary;
          line-height: 1.4;
        }
      }
    }
  }
  
  .quick-actions {
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 16px;
    
    .el-divider {
      margin: 0 8px;
    }
  }
  
  .contract-type-section {
    padding-top: 16px;
    border-top: 1px solid $border-light;
    
    .section-label {
      display: flex;
      align-items: center;
      gap: 6px;
      margin-bottom: 8px;
      font-size: $font-size-sm;
      color: $text-secondary;
    }
    
    .contract-type-select {
      width: 100%;
    }
  }
}

.dialog-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  
  .selected-count {
    font-size: $font-size-sm;
    color: $text-secondary;
  }
}
</style>
