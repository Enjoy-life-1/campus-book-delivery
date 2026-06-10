<template>
  <div class="alert alert-danger d-flex align-items-center justify-content-between flex-wrap gap-2">
    <span><i class="fa fa-exclamation-circle me-2"></i>{{ message }}</span>
    <button v-if="showRetry" type="button" class="btn btn-sm btn-outline-danger" @click="$emit('retry')">重试</button>
  </div>
</template>

<script setup>
// 加载失败 + 重试按钮
defineProps({  message: { type: String, required: true },
  showRetry: { type: Boolean, default: true }
})
defineEmits(['retry'])
</script>
