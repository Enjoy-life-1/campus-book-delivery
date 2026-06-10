// HTTP 客户端：统一 /api 前缀，携带 Cookie 配合 Flask Session
import axios from 'axios'

const api = axios.create({
  baseURL: '/api', // Vite 开发代理到 Flask :5000
  timeout: 15000,
  withCredentials: true, // 跨域携带 Cookie
  headers: { 'Content-Type': 'application/json' }
})

const publicPaths = ['/login', '/register', '/admin/login'] // 401 时不跳转这些页

function loginRedirectPath() {
  const path = window.location.pathname
  if (path.startsWith('/admin')) {
    const redirect = encodeURIComponent(path + window.location.search)
    return `/admin/login?redirect=${redirect}`
  }
  const redirect = encodeURIComponent(path + window.location.search)
  return `/login?redirect=${redirect}`
}

api.interceptors.response.use(
  (response) => response.data, // 成功直接返回 data
  (error) => {
    const data = error.response?.data
    const status = error.response?.status
    if (status === 401 && !publicPaths.includes(window.location.pathname)) {
      localStorage.removeItem('currentUser')
      window.location.href = loginRedirectPath() // 未登录跳转
    }
    return Promise.reject(data || { message: error.message || '网络错误' })
  }
)

export const appealAPI = {
  // 封禁申诉
  submit: (data) => api.post('/ban-appeal', data),
  mine: () => api.get('/ban-appeal/mine')
}

export const authAPI = {
  // 登录注册、资料、信用分
  login: (data) => api.post('/login', data),
  adminLogin: (data) => api.post('/admin/login', data),
  register: (data) => api.post('/register', data),
  sendCode: (data) => api.post('/send_code', data),
  forgotReset: (data) => api.post('/forgot-password', data),
  logout: () => api.post('/logout'),
  getUserInfo: () => api.get('/user/info'),
  updateUserInfo: (data) => api.put('/user/info', data),
  uploadAvatar: (formData) => api.post('/user/avatar', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  subscribePriceDrop: (data) => api.put('/user/subscribe-price-drop', data),
  changePassword: (data) => api.put('/user/password', data),
  getMyCredit: () => api.get('/my/credit'),
  getUserCredit: (id) => api.get(`/users/${id}/credit`)
}

export const bookAPI = {
  // 书籍 CRUD + 图片上传
  getBooks: (params) => api.get('/books', { params }),
  getBookDetail: (id) => api.get(`/books/${id}`),
  addBook: (data) => api.post('/books', data),
  updateBook: (id, data) => api.put(`/books/${id}`, data),
  deleteBook: (id) => api.delete(`/books/${id}`),
  cloneBook: (id) => api.post(`/books/${id}/clone`),
  uploadImage: (formData) => api.post('/books/upload-image', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export const orderAPI = {
  // 下单、换书、状态流转
  createOrder: (data) => api.post('/orders', data),
  createExchange: (data) => api.post('/orders/exchange', data),
  getOrders: () => api.get('/orders'),
  getOrderDetail: (id) => api.get(`/orders/${id}`),
  updateStatus: (id, data) => api.put(`/orders/${id}/status`, data)
}

export const collectionAPI = {
  // 收藏 + 降价提醒
  checkCollection: (bookId) => api.get(`/collections/check/${bookId}`),
  toggleCollection: (bookId) => api.post(`/collections/${bookId}`),
  getCollections: () => api.get('/collections'),
  setPriceAlert: (bookId, data) => api.put(`/collections/${bookId}/price-alert`, data)
}

export const commentAPI = {
  // 书籍评论
  getComments: (bookId) => api.get(`/comments/${bookId}`),
  addComment: (data) => api.post('/comments', data),
  deleteComment: (commentId) => api.delete(`/comments/${commentId}`)
}

export const reviewAPI = {
  // 交易评价
  submit: (data) => api.post('/reviews', data),
  getByOrder: (orderId) => api.get(`/reviews/order/${orderId}`)
}

export const cartAPI = {
  // 购物车 + 按卖家结算
  getCart: () => api.get('/cart'),
  addToCart: (data) => api.post('/cart', data),
  updateCartItem: (itemId, data) => api.put(`/cart/${itemId}`, data),
  deleteCartItem: (itemId) => api.delete(`/cart/${itemId}`),
  clearCart: () => api.delete('/cart'),
  checkoutSeller: (data) => api.post('/cart/checkout-seller', data)
}

export const categoryAPI = {
  // 分类列表
  getCategories: () => api.get('/categories')
}

export const announcementAPI = {
  // 首页公告
  getAnnouncements: () => api.get('/announcements')
}

export const adminAPI = {
  // 管理端全量接口
  getUsers: () => api.get('/admin/users'),
  createUser: (data) => api.post('/admin/users', data),
  updateUser: (id, data) => api.put(`/admin/users/${id}`, data),
  deleteUser: (id) => api.delete(`/admin/users/${id}`),
  getOrders: () => api.get('/admin/orders'),
  getStats: () => api.get('/admin/stats'),
  getSettings: () => api.get('/admin/settings'),
  saveSettings: (data) => api.post('/admin/settings', data),
  getCategories: () => api.get('/categories'),
  addCategory: (data) => api.post('/admin/categories', data),
  updateCategory: (id, data) => api.put(`/admin/categories/${id}`, data),
  deleteCategory: (id) => api.delete(`/admin/categories/${id}`),
  getAnnouncements: () => api.get('/admin/announcements'),
  addAnnouncement: (data) => api.post('/admin/announcements', data),
  updateAnnouncement: (id, data) => api.put(`/admin/announcements/${id}`, data),
  deleteAnnouncement: (id) => api.delete(`/admin/announcements/${id}`),
  getSpots: () => api.get('/admin/campus/spots'),
  createSpot: (data) => api.post('/admin/campus/spots', data),
  updateSpot: (id, data) => api.put(`/admin/campus/spots/${id}`, data),
  deleteSpot: (id) => api.delete(`/admin/campus/spots/${id}`),
  getCourses: () => api.get('/admin/campus/courses'),
  createCourse: (data) => api.post('/admin/campus/courses', data),
  updateCourse: (id, data) => api.put(`/admin/campus/courses/${id}`, data),
  deleteCourse: (id) => api.delete(`/admin/campus/courses/${id}`),
  getCampaigns: () => api.get('/admin/campus/campaigns'),
  createCampaign: (data) => api.post('/admin/campus/campaigns', data),
  updateCampaign: (id, data) => api.put(`/admin/campus/campaigns/${id}`, data),
  deleteCampaign: (id) => api.delete(`/admin/campus/campaigns/${id}`),
  getWanted: () => api.get('/admin/wanted'),
  deleteWanted: (id) => api.delete(`/admin/wanted/${id}`),
  closeWanted: (id) => api.put(`/admin/wanted/${id}/close`),
  getConversations: () => api.get('/admin/conversations'),
  getConversationMessages: (id) => api.get(`/admin/conversations/${id}/messages`),
  getNotifyOutbox: (params) => api.get('/admin/notification-outbox', { params }),
  retryOutbox: (id) => api.post(`/admin/notification-outbox/${id}/retry`),
  testGateway: (data) => api.post('/admin/gateway/test', data),
  getSensitiveWords: () => api.get('/admin/sensitive-words'),
  addSensitiveWord: (data) => api.post('/admin/sensitive-words', data),
  deleteSensitiveWord: (id) => api.delete(`/admin/sensitive-words/${id}`),
  getAuditLogs: () => api.get('/admin/audit-logs'),
  getIsbnBlacklist: () => api.get('/admin/isbn-blacklist'),
  addIsbnBlacklist: (data) => api.post('/admin/isbn-blacklist', data),
  deleteIsbnBlacklist: (id) => api.delete(`/admin/isbn-blacklist/${id}`),
  banUser: (id, data) => api.post(`/admin/users/${id}/ban`, data),
  unbanUser: (id) => api.post(`/admin/users/${id}/unban`),
  getBanAppeals: (params) => api.get('/admin/ban-appeals', { params }),
  handleBanAppeal: (id, data) => api.put(`/admin/ban-appeals/${id}`, data),
  getPendingComments: () => api.get('/admin/comments/pending'),
  auditComment: (id, data) => api.put(`/admin/comments/${id}/audit`, data),
  getReports: (params) => api.get('/admin/reports', { params }),
  handleReport: (id, data) => api.put(`/admin/reports/${id}`, data),
  getSchools: () => api.get('/admin/schools'),
  createSchool: (data) => api.post('/admin/schools', data),
  updateSchool: (id, data) => api.put(`/admin/schools/${id}`, data),
  deleteSchool: (id) => api.delete(`/admin/schools/${id}`),
  getEcoStats: () => api.get('/admin/stats/eco')
}

export const systemAPI = {
  // 健康检查
  health: () => api.get('/health'),
  info: () => api.get('/system/info')
}

export const wantedAPI = {
  // 求购帖
  list: (params) => api.get('/wanted', { params }),
  get: (id) => api.get(`/wanted/${id}`),
  create: (data) => api.post('/wanted', data),
  update: (id, data) => api.put(`/wanted/${id}`, data),
  delete: (id) => api.delete(`/wanted/${id}`),
  matches: (id) => api.get(`/wanted/${id}/matches`)
}

export const messageAPI = {
  // 私信 + 面约 + 媒体
  getConversations: () => api.get('/conversations'),
  startConversation: (data) => api.post('/conversations', data),
  getMessages: (convId, params) => api.get(`/conversations/${convId}/messages`, { params }),
  sendMessage: (convId, data) => api.post(`/conversations/${convId}/messages`, data),
  recallMessage: (convId, msgId) => api.post(`/conversations/${convId}/messages/${msgId}/recall`),
  uploadMedia: (formData) => api.post('/messages/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  createAppointment: (convId, data) => api.post(`/conversations/${convId}/appointments`, data),
  updateAppointment: (apptId, data) => api.put(`/appointments/${apptId}/status`, data),
  unreadCount: () => api.get('/messages/unread')
}

export const safetyAPI = {
  // 举报 + 拉黑
  report: (data) => api.post('/reports', data),
  block: (userId) => api.post(`/block/${userId}`),
  unblock: (userId) => api.delete(`/block/${userId}`),
  blockList: () => api.get('/block/list')
}

export const offerAPI = {
  // 议价
  list: (params) => api.get('/offers', { params }),
  create: (data) => api.post('/offers', data),
  respond: (id, data) => api.put(`/offers/${id}`, data)
}

export const notificationAPI = {
  // 站内通知
  list: () => api.get('/notifications'),
  read: (id) => api.put(`/notifications/${id}/read`),
  readAll: () => api.put('/notifications/read-all'),
  unreadCount: () => api.get('/notifications/unread-count')
}

export const sellerAPI = {
  // 卖家主页 + 发布模板
  getProfile: (id) => api.get(`/sellers/${id}`),
  similarBooks: (bookId) => api.get(`/books/${bookId}/similar`),
  dashboard: () => api.get('/seller/dashboard'),
  getTemplates: () => api.get('/my/publish-templates'),
  saveTemplate: (data) => api.post('/my/publish-templates', data),
  templateFromBook: (bookId, data) => api.post(`/my/publish-templates/from-book/${bookId}`, data),
  deleteTemplate: (id) => api.delete(`/my/publish-templates/${id}`)
}

export const publicAPI = {
  // 免登录分享页
  getWanted: (id) => api.get(`/public/wanted/${id}`),
  getSellerBooks: (id) => api.get(`/public/seller/${id}/books`)
}

export const followAPI = {
  // 关注卖家
  check: (sellerId) => api.get(`/follow/check/${sellerId}`),
  follow: (sellerId) => api.post(`/follow/${sellerId}`),
  unfollow: (sellerId) => api.delete(`/follow/${sellerId}`)
}

export const discoveryAPI = {
  // 搜索联想、推荐、发布提示
  searchSuggest: (q) => api.get('/search/suggest', { params: { q } }),
  priceInsights: (bookId) => api.get(`/books/${bookId}/price-insights`),
  forYou: (params) => api.get('/recommendations/for-you', { params }),
  publishHints: (params) => api.get('/publish/hints', { params })
}

export const aiAPI = {
  // RAG 问答
  status: () => api.get('/ai/status'),
  ask: (data) => api.post('/ai/ask', data)
}

export const campusAPI = {
  // 校园认证、课表、宿舍、ISBN
  lookupIsbn: (isbn) => api.get(`/isbn/${isbn}`),
  getSchools: () => api.get('/schools'),
  verifyCampus: (data) => api.post('/campus/verify', data),
  getSpots: () => api.get('/campus/spots'),
  getDorms: (campusZone) => api.get('/campus/dorms', {
    params: campusZone ? { campus_zone: campusZone } : {}
  }),
  getCourses: (params) => api.get('/courses', { params }),
  getCourseBooks: (code) => api.get(`/courses/${code}/books`),
  getSemester: () => api.get('/semester/active'),
  getSemesterCampaigns: () => api.get('/semester/campaigns'),
  getDormMap: () => api.get('/campus/dorm-map'),
  getSchedule: () => api.get('/my/schedule'),
  importSchedule: (data) => api.post('/my/schedule/import', data),
  batchPublishSchedule: (data) => api.post('/my/schedule/batch-publish', data),
  setPriceDrop: (bookId, data) => api.post(`/books/${bookId}/price-drop`, data)
}

export default api
