// 认证相关工具函数

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
  } catch (e) {
    console.error('保存用户信息失败:', e)
  }
}

export function removeUser() {
  localStorage.removeItem('currentUser')
  window.dispatchEvent(new Event('storage'))
}

export function checkAuth(requireAdmin = false) {
  const user = getCurrentUser()
  if (!user) return false
  if (requireAdmin && !user.is_admin) return false
  return true
}

export function logout() {
  removeUser()
  window.location.href = '/login'
}

