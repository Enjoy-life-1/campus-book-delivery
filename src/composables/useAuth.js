// Session 同步与登出：refreshSession 为登录态唯一权威来源
import { authAPI } from '@/utils/api'
import { useUserStore } from '@/stores/user'

/** 从服务端 Session 同步用户信息（唯一权威来源） */
export async function refreshSession() {
  const store = useUserStore()
  try {
    const res = await authAPI.getUserInfo()  // GET /api/user/info + Cookie
    if (res.status === 'success' && res.user) {
      store.setUser(res.user)  // 写入 Pinia + localStorage
      return res.user
    }
  } catch (_) {
    store.setUser(null)  // 401 或未登录
  }
  return null
}

/** 用户登录并同步 Session */
export async function loginAndSync(credentials) {
  const res = await authAPI.login(credentials)  // POST /api/login
  if (res.status === 'success') {
    const user = await refreshSession()
    return { ...res, user: user || res.user }
  }
  return res
}

/** 管理员登录并同步 Session */
export async function adminLoginAndSync(credentials) {
  const res = await authAPI.adminLogin(credentials)  // POST /api/admin/login
  if (res.status === 'success') {
    const user = await refreshSession()
    return { ...res, user: user || res.user }
  }
  return res
}
