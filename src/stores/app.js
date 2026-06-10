// Pinia 全局 UI：Navbar 分类下拉等
import { defineStore } from 'pinia'
import { categoryAPI } from '@/utils/api'

/** 全局 UI 数据：Navbar 分类下拉等 */
export const useAppStore = defineStore('app', {
  state: () => ({
    categories: [],
    categoriesLoaded: false
  }),
  actions: {
    async loadCategories(force = false) {
      // GET /api/categories，后端 SimpleCache 120s
      if (this.categoriesLoaded && !force) return
      try {
        const res = await categoryAPI.getCategories()
        if (res.status === 'success') {
          this.categories = res.categories || []
          this.categoriesLoaded = true
        }
      } catch (_) {}
    }
  }
})
