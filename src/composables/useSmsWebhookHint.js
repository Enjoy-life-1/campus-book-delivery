// 全局单例：Webhook 短信提示弹窗状态
import { ref } from 'vue'

const visible = ref(false)
const detail = ref('')

export function useSmsWebhookHint() {
  function open(message = '') {
    detail.value = message
    visible.value = true
  }
  function close() {
    visible.value = false
  }
  return { visible, detail, open, close }
}
