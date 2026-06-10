<template>
  <div v-if="!online" class="offline-banner">
    <i class="fa fa-wifi me-2"></i>当前离线，展示的是上次缓存的内容
  </div>
</template>

<script setup>
// App.vue 挂载；监听 online/offline 事件
import { ref, onMounted, onUnmounted } from 'vue'
const online = ref(typeof navigator !== 'undefined' ? navigator.onLine : true)

function sync() {
  online.value = navigator.onLine
}

onMounted(() => {
  window.addEventListener('online', sync)
  window.addEventListener('offline', sync)
})

onUnmounted(() => {
  window.removeEventListener('online', sync)
  window.removeEventListener('offline', sync)
})
</script>

<style scoped>
.offline-banner {
  position: sticky;
  top: 0;
  z-index: 1040;
  padding: 0.45rem 1rem;
  text-align: center;
  font-size: 0.85rem;
  background: #fff3cd;
  color: #664d03;
  border-bottom: 1px solid #ffecb5;
}
</style>
