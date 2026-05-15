import axios from 'axios'

// 创建axios实例
const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
  withCredentials: true, // 允许携带cookie
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    // 可以在这里添加token等
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    if (error.response) {
      const { status, data } = error.response
      if (status === 401) {
        // 未授权，清除用户信息并跳转登录
        localStorage.removeItem('currentUser')
        window.location.href = '/login'
      }
      return Promise.reject(data || error)
    }
    return Promise.reject(error)
  }
)

// API方法
export const authAPI = {
  login: (data) => api.post('/login', data),
  register: (data) => api.post('/register', data),
  sendCode: (data) => api.post('/send_code', data),
  logout: () => api.post('/logout'),
  getUserInfo: () => api.get('/user/info'),
  updateUserInfo: (data) => api.put('/user/info', data),
  changePassword: (data) => api.put('/user/password', data)
}

export const bookAPI = {
  getBooks: (params) => api.get('/books', { params }),
  getBookDetail: (id) => api.get(`/books/${id}`),
  addBook: (data) => api.post('/books', data),
  updateBook: (id, data) => api.put(`/books/${id}`, data),
  deleteBook: (id) => api.delete(`/books/${id}`)
}

export const orderAPI = {
  createOrder: (data) => api.post('/orders', data),
  getOrders: () => api.get('/orders')
}

export const collectionAPI = {
  checkCollection: (bookId) => api.get(`/collections/check/${bookId}`),
  toggleCollection: (bookId) => api.post(`/collections/${bookId}`),
  getCollections: () => api.get('/collections')
}

export const commentAPI = {
  getComments: (bookId) => api.get(`/comments/${bookId}`),
  addComment: (data) => api.post('/comments', data),
  deleteComment: (commentId) => api.delete(`/comments/${commentId}`)
}

export const cartAPI = {
  getCart: () => api.get('/cart'),
  addToCart: (data) => api.post('/cart', data),
  updateCartItem: (itemId, data) => api.put(`/cart/${itemId}`, data),
  deleteCartItem: (itemId) => api.delete(`/cart/${itemId}`),
  clearCart: () => api.delete('/cart')
}

export const adminAPI = {
  getUsers: () => api.get('/admin/users'),
  createUser: (data) => api.post('/admin/users', data),
  getOrders: () => api.get('/admin/orders'),
  getStats: () => api.get('/admin/stats'),
  getSettings: () => api.get('/admin/settings'),
  saveSettings: (data) => api.post('/admin/settings', data)
}

export default api

