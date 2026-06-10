// 前端通用：展示格式化、分类/状态/成色映射
export function normalizeAvatar(url) {
  // 过滤无效或过短的 data URL
  const u = (url || '').trim()
  if (!u) return ''
  if (u.startsWith('data:image')) return u.length >= 1000 ? u : ''
  if (u.startsWith('/static/') || u.startsWith('http://') || u.startsWith('https://')) return u
  return ''
}

// HTML转义
export function escapeHtml(unsafe) {
  if (unsafe === undefined || unsafe === null) {
    return ''
  }
  return String(unsafe)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
}

// 获取分类名称
export function getCategoryName(category) {
  const categories = {
    'textbook': '教材教辅',
    'postgraduate': '考研资料',
    'literature': '文学小说',
    'professional': '专业书籍',
    'other': '其他书籍'
  }
  return categories[category] || category
}

// 获取状态文本
export function getStatusText(status) {
  const statusMap = {
    'available': '在售',
    'sold': '已售出',
    'pending': '待审核',
    'pickup': '待面交',
    'processing': '处理中',
    'completed': '已完成',
    'cancelled': '已取消'
  }
  return statusMap[status] || status
}

export function getOrderStatusText(status) {
  // 订单流转：pending → pickup → completed
  const map = {
    pending: '待确认',
    pickup: '已约面交',
    completed: '已完成',
    cancelled: '已取消'
  }
  return map[status] || status
}

export const conditionOptions = [
  { value: 'new', label: '全新' },
  { value: 'like_new', label: '九成新' },
  { value: 'good', label: '八成新' },
  { value: 'fair', label: '七成新及以下' }
]

export function getConditionLabel(v) {
  return conditionOptions.find(o => o.value === v)?.label || v || '未标注'
}

// 格式化日期
export function formatDate(dateString) {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN')
}

// 格式化价格（保留两位小数）
export function formatPrice(price) {
  return parseFloat(price || 0).toFixed(2)
}
