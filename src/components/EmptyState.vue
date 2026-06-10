<template>
  <div class="empty-state text-center py-5">
    <i :class="['fa', icon, 'fa-3x', 'text-muted', 'mb-3']"></i>
    <p class="mb-1">{{ title }}</p>
    <p v-if="description" class="text-muted small mb-3">{{ description }}</p>
    <slot />
  </div>
</template>

<script setup>
// 列表空态占位（BooksList/Cart 等）
defineProps({  icon: { type: String, default: 'fa-inbox' },
  title: { type: String, default: '暂无数据' },
  description: { type: String, default: '' }
})
</script>
