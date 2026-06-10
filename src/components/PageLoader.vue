<template>
  <div class="page-loader text-center py-5" :class="{ compact }">
    <div class="spinner-border text-success" role="status">
      <span class="visually-hidden">加载中</span>
    </div>
    <p v-if="text" class="text-muted small mt-2 mb-0">{{ text }}</p>
  </div>
</template>

<script setup>
// 通用加载 spinner
defineProps({
  text: { type: String, default: '加载中...' },
  compact: { type: Boolean, default: false }
})
</script>
