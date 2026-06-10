// 统一异步 loading/error 包装，BooksList 等页复用
import { ref } from 'vue'

/** 统一异步加载 / 错误状态 */
export function useAsync() {
  const loading = ref(false)
  const error = ref('')

  async function run(fn) {
    loading.value = true
    error.value = ''
    try {
      return await fn()
    } catch (e) {
      error.value = e?.message || '加载失败，请稍后重试'
      return null
    } finally {
      loading.value = false
    }
  }

  function clearError() {
    error.value = ''
  }

  return { loading, error, run, clearError }
}
