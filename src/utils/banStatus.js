// 封禁/禁言展示：与 User.ban_level 对齐
export function banLevelLabel(level) {
  return { warning: '账号警告', mute: '禁言中', ban: '账号封禁' }[level] || level
}

export function banRestrictions(level) {
  if (level === 'warning') return '信用分将受影响，请规范交易行为'
  if (level === 'mute') return '暂无法发送私信、图片、语音及面交预约'
  if (level === 'ban') return '无法发布书籍，重新登录将被拒绝；其他功能可能受限'
  return ''
}

export function getBanNotice(user) {
  // PublishBook / Messages / AccountSettings 顶部提示
  const level = user?.ban_level || 'none'
  if (!level || level === 'none') return null
  const until = user.ban_until ? `，至 ${user.ban_until}` : ''
  const reason = user.ban_reason ? `原因：${user.ban_reason}` : ''
  const detail = [banRestrictions(level), reason].filter(Boolean).join('。')
  return {
    level,
    title: `${banLevelLabel(level)}${until}`,
    detail,
    appealable: level === 'mute' || level === 'ban',
    alertClass: level === 'warning' ? 'alert-warning' : level === 'mute' ? 'alert-info' : 'alert-danger'
  }
}

export function isMuted(user) {
  // Messages 禁发私信
  const level = user?.ban_level || 'none'
  return level === 'mute' || level === 'ban'
}

export function isBanned(user) {
  return (user?.ban_level || 'none') === 'ban'
}
