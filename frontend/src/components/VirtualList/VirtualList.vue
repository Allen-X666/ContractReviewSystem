<template>
  <RecycleScroller
    :items="items"
    :item-size="itemSize"
    :key-field="keyField"
    :buffer="buffer"
    class="virtual-list"
    v-bind="$attrs"
  >
    <template #default="{ item, index, active }">
      <slot :item="item" :index="index" :active="active" />
    </template>
    <template #before>
      <slot name="before" />
    </template>
    <template #after>
      <slot name="after" />
    </template>
    <template #empty>
      <slot name="empty">
        <div class="virtual-list-empty">
          <el-empty description="暂无数据" />
        </div>
      </slot>
    </template>
  </RecycleScroller>
</template>

<script setup>
import { RecycleScroller } from 'vue-virtual-scroller'
import 'vue-virtual-scroller/dist/vue-virtual-scroller.css'

defineProps({
  items: {
    type: Array,
    required: true
  },
  itemSize: {
    type: Number,
    default: 60
  },
  keyField: {
    type: String,
    default: 'id'
  },
  buffer: {
    type: Number,
    default: 200
  }
})
</script>

<style scoped>
.virtual-list {
  height: 100%;
  overflow-y: auto;
}

.virtual-list-empty {
  padding: 40px 0;
}
</style>
