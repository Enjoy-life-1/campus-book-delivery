// 工具函数

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
    'pending': '待处理',
    'processing': '处理中',
    'completed': '已完成',
    'cancelled': '已取消'
  }
  return statusMap[status] || status
}

// 格式化日期
export function formatDate(dateString) {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN')
}

// 格式化价格
export function formatPrice(price) {
  return parseFloat(price || 0).toFixed(2)
}

