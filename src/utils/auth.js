// 认证工具：登录态以服务端 Session 为准，localStorage 仅作展示缓存（由 refreshSession 同步）

export function getCurrentUser() {
  try {
    const user = localStorage.getItem('currentUser')
    return user ? JSON.parse(user) : null
  } catch (e) {
    console.error('获取用户信息失败:', e)
    return null
  }
}

export function saveUser(userInfo) {
  try {
    localStorage.setItem('currentUser', JSON.stringify(userInfo))
    window.dispatchEvent(new Event('storage'))
    window.dispatchEvent(new Event('user-updated'))
  } catch (e) {
    console.error('保存用户信息失败:', e)
  }
}

export function removeUser() {
  localStorage.removeItem('currentUser')
  window.dispatchEvent(new Event('storage'))
}

export function isStaff(user) {
  if (!user) return false
  return user.is_admin || user.role === 'admin' || user.role === 'moderator'
}

export function checkAuth(requireAdmin = false) {
  // 本地缓存快速判断；路由守卫以 refreshSession 为准
  const user = getCurrentUser()
  if (!user) return false
  if (requireAdmin && !isStaff(user)) return false
  return true
}

export function logout() {
  removeUser()
  window.location.href = '/login'
}

