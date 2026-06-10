// 全局 Toast 单例；App.vue 挂载 GlobalToast 展示
import { ref } from 'vue'

const toast = ref({ show: false, message: '', type: 'success' })
let timer = null

export function useToast() {
  /** type: success | error | danger | info | warning */
  function show(message, type = 'success', duration = 2800) {
    toast.value = { show: true, message, type }
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => {
      toast.value.show = false
    }, duration)
  }
  return { toast, show }
}
