<template>
  <div v-if="toast.show" :class="['vue-toast', `vue-toast-${toast.type}`]" role="alert">
    <i :class="toast.type === 'success' ? 'fa fa-check-circle' : 'fa fa-exclamation-circle'"></i>
    {{ toast.message }}
  </div>
</template>

<script setup>
// 订阅 useToast 单例，全局右上角提示
import { useToast } from '@/composables/useToast'
const { toast } = useToast()
</script>

<style scoped>
.vue-toast {
  position: fixed;
  top: 80px;
  right: 20px;
  z-index: 9999;
  padding: 12px 20px;
  border-radius: 8px;
  color: #fff;
  box-shadow: 0 4px 12px rgba(0,0,0,.15);
  display: flex;
  align-items: center;
  gap: 8px;
  max-width: 360px;
}
.vue-toast-success { background: #28a745; }
.vue-toast-error, .vue-toast-danger { background: #dc3545; }
.vue-toast-info { background: #17a2b8; }
</style>
