// ISBN 查询：campusAPI.lookupIsbn → 回填书名作者
import { ref } from 'vue'
import { campusAPI } from '@/utils/api'

export function useIsbnLookup() {
  const loading = ref(false)

  async function lookup(isbn, onResult) {
    const code = (isbn || '').replace(/[^0-9Xx]/g, '')
    if (code.length < 10) return { ok: false, message: 'ISBN至少10位' }
    loading.value = true
    try {
      const res = await campusAPI.lookupIsbn(code)
      if (res.status === 'success' && res.book) {
        onResult?.(res.book)
        return { ok: true, book: res.book }
      }
      return { ok: false, message: res.message || '未找到' }
    } catch (e) {
      return { ok: false, message: e.message || '查询失败' }
    } finally {
      loading.value = false
    }
  }

  return { loading, lookup }
}
