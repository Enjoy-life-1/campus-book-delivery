// Pinia 用户状态：profile、购物车/消息/通知角标
import { defineStore } from 'pinia'
import { getCurrentUser, saveUser, removeUser } from '@/utils/auth'
import { cartAPI, messageAPI, notificationAPI } from '@/utils/api'

/** 用户全局状态：profile、购物车/消息/通知角标 */
export const useUserStore = defineStore('user', {
  state: () => ({
    profile: getCurrentUser(),  // 启动时从 localStorage 恢复
    cartCount: 0,
    msgCount: 0,
    notifyCount: 0
  }),
  getters: {
    isLoggedIn: (s) => !!s.profile,
    isAdmin: (s) => !!(s.profile?.is_admin || s.profile?.role === 'admin')
  },
  actions: {
    setUser(user) {
      this.profile = user || null
      if (user) {
        saveUser(user)  // 持久化
        this.refreshBadges()
      } else {
        removeUser()
        this.cartCount = 0
        this.msgCount = 0
        this.notifyCount = 0
      }
    },
    syncFromStorage() {
      this.profile = getCurrentUser()
      if (this.profile) this.refreshBadges()
      else {
        this.cartCount = 0
        this.msgCount = 0
        this.notifyCount = 0
      }
    },
    async refreshBadges() {
      if (!this.profile) return
      try {
        const [cartRes, msgRes, notifyRes] = await Promise.all([
          cartAPI.getCart().catch(() => null),
          messageAPI.unreadCount().catch(() => null),
          notificationAPI.unreadCount().catch(() => null)
        ])
        if (cartRes?.status === 'success') this.cartCount = (cartRes.cart || []).length
        if (msgRes?.status === 'success') this.msgCount = msgRes.unread_total || 0
        if (notifyRes?.status === 'success') this.notifyCount = notifyRes.unread_count || 0
      } catch (_) {}
    }
  }
})
