// Vue Router：懒加载页面 + beforeEach 鉴权（refreshSession 对齐 Flask Session）
import { createRouter, createWebHistory } from 'vue-router'
import { refreshSession } from '@/composables/useAuth'
import Login from '@/views/Login.vue'
import Register from '@/views/Register.vue'

const routes = [
  // 公开页：首页、列表、详情无需登录
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/Home.vue')
    // 移除 requiresAuth，允许未登录用户浏览
  },
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  {
    path: '/register',
    name: 'Register',
    component: Register
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
    path: '/order/:id',
    name: 'OrderDetail',
    component: () => import('@/views/OrderDetail.vue'),
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
    path: '/ai',
    name: 'AiAssistant',
    component: () => import('@/views/AiAssistant.vue')
  },
  {
    path: '/feature/:slug',
    name: 'FeaturePage',
    component: () => import('@/views/feature/FeaturePage.vue')
  },
  {
    path: '/courses',
    name: 'CourseBooks',
    component: () => import('@/views/CourseBooks.vue')
  },
  {
    path: '/mySchedule',
    name: 'MySchedule',
    component: () => import('@/views/MySchedule.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/campus/map',
    name: 'DormMap',
    component: () => import('@/views/DormMap.vue')
  },
  {
    path: '/semester',
    name: 'SemesterHub',
    component: () => import('@/views/SemesterHub.vue')
  },
  {
    path: '/wanted',
    name: 'WantedList',
    component: () => import('@/views/WantedList.vue')
  },
  {
    path: '/wanted/:id',
    name: 'WantedDetail',
    component: () => import('@/views/WantedDetail.vue')
  },
  {
    path: '/messages',
    name: 'Messages',
    component: () => import('@/views/Messages.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/notifications',
    name: 'Notifications',
    component: () => import('@/views/Notifications.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/seller/:id',
    name: 'SellerProfile',
    component: () => import('@/views/SellerProfile.vue')
  },
  {
    path: '/share/wanted/:id',
    name: 'ShareWanted',
    component: () => import('@/views/SharePublic.vue'),
    meta: { shareType: 'wanted' }
  },
  {
    path: '/share/seller/:id',
    name: 'ShareSeller',
    component: () => import('@/views/SharePublic.vue'),
    meta: { shareType: 'seller' }
  },
  {
    path: '/offers',
    name: 'Offers',
    component: () => import('@/views/Offers.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/admin/login',
    name: 'AdminLogin',
    component: () => import('@/views/admin/AdminLogin.vue'),
    meta: { guestOnly: true }
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
  },
  {
    path: '/admin/orders',
    name: 'AdminOrders',
    component: () => import('@/views/admin/AdminOrders.vue'),
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/admin/wanted',
    name: 'AdminWanted',
    component: () => import('@/views/admin/AdminWanted.vue'),
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/admin/messages',
    name: 'AdminMessages',
    component: () => import('@/views/admin/AdminMessages.vue'),
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/admin/campus',
    name: 'AdminCampus',
    component: () => import('@/views/admin/AdminCampus.vue'),
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/admin/comments',
    name: 'AdminComments',
    component: () => import('@/views/admin/AdminComments.vue'),
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/admin/compliance',
    name: 'AdminCompliance',
    component: () => import('@/views/admin/AdminCompliance.vue'),
    meta: { requiresAuth: true, requiresAdmin: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  }
})

// 路由守卫：以服务端 Session 为准，进入受保护页前同步 /api/user/info
router.beforeEach(async (to) => {
  if (to.meta.guestOnly) return true
  if (!to.meta.requiresAuth && !to.meta.requiresAdmin) return true
  const user = await refreshSession()
  if (!user) {
    if (to.meta.requiresAdmin) {
      return { name: 'AdminLogin', query: { redirect: to.fullPath } }
    }
    return { name: 'Login', query: { redirect: to.fullPath } }
  }
  if (to.meta.requiresAdmin && !user.is_admin) {
    return { name: 'AdminLogin', query: { redirect: to.fullPath } }
  }
  return true
})

export default router

