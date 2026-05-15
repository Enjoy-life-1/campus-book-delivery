import { createRouter, createWebHistory } from 'vue-router'
import { getCurrentUser } from '@/utils/auth'

function checkAuth(requireAdmin = false) {
  const user = getCurrentUser()
  if (!user) return false
  if (requireAdmin && !user.is_admin) return false
  return true
}

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/Home.vue')
    // 移除 requiresAuth，允许未登录用户浏览
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue')
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/Register.vue')
  },
  {
    path: '/booksList',
    name: 'BooksList',
    component: () => import('@/views/BooksList.vue')
    // 移除 requiresAuth，允许未登录用户浏览
  },
  {
    path: '/book/:id',
    name: 'BookDetail',
    component: () => import('@/views/BookDetail.vue')
    // 移除 requiresAuth，允许未登录用户浏览书籍详情
  },
  {
    path: '/publishBook',
    name: 'PublishBook',
    component: () => import('@/views/PublishBook.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/personalCenter',
    name: 'PersonalCenter',
    component: () => import('@/views/PersonalCenter.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/myBooks',
    name: 'MyBooks',
    component: () => import('@/views/MyBooks.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/myCollections',
    name: 'MyCollections',
    component: () => import('@/views/MyCollections.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/cart',
    name: 'Cart',
    component: () => import('@/views/Cart.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/transactionHistory',
    name: 'TransactionHistory',
    component: () => import('@/views/TransactionHistory.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/accountSettings',
    name: 'AccountSettings',
    component: () => import('@/views/AccountSettings.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/guide',
    name: 'Guide',
    component: () => import('@/views/Guide.vue')
  },
  {
    path: '/admin',
    name: 'Admin',
    component: () => import('@/views/admin/Admin.vue'),
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/admin/analytics',
    name: 'AdminAnalytics',
    component: () => import('@/views/admin/AdminAnalytics.vue'),
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/admin/settings',
    name: 'AdminSettings',
    component: () => import('@/views/admin/AdminSettings.vue'),
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/admin/userManagement',
    name: 'AdminUserManagement',
    component: () => import('@/views/admin/AdminUserManagement.vue'),
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/admin/bookManagement',
    name: 'AdminBookManagement',
    component: () => import('@/views/admin/AdminBookManagement.vue'),
    meta: { requiresAuth: true, requiresAdmin: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  if (to.meta.requiresAuth && !checkAuth()) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
  } else if (to.meta.requiresAdmin && !checkAuth(true)) {
    next({ name: 'Home' })
  } else {
    next()
  }
})

export default router

