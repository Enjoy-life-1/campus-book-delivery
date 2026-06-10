<template>
  <div class="admin-body admin-spa">
    <aside class="sidebar" :class="{ collapsed: sidebarCollapsed }">
      <div class="sidebar-header">
        <img src="/static/img/logo.png" alt="logo" class="sidebar-logo">
        <span class="sidebar-title">校园书递</span>
      </div>
      <nav class="sidebar-nav">
        <ul class="nav-list">
          <li v-for="item in navItems" :key="item.to" class="nav-item" :class="{ active: isActive(item) }">
            <router-link :to="item.to" class="nav-link">
              <i :class="['fa', item.icon]"></i>
              <span>{{ item.label }}</span>
            </router-link>
          </li>
        </ul>
      </nav>
      <div class="sidebar-footer px-3 pb-3">
        <router-link to="/" class="nav-link">
          <i class="fa fa-home"></i><span>返回前台</span>
        </router-link>
      </div>
    </aside>

    <header class="top-navbar">
      <div class="header-left">
        <button type="button" class="sidebar-toggle" @click="sidebarCollapsed = !sidebarCollapsed">
          <i class="fa fa-bars"></i>
        </button>
        <div class="brand-container">
          <img src="/static/img/logo.png" alt="" class="logo-btn">
          <span class="page-title">{{ title }}</span>
        </div>
      </div>
      <div class="header-right">
        <button
          v-if="showRefresh"
          type="button"
          class="refresh-data-btn primary-btn"
          :disabled="refreshing"
          @click="onRefresh"
        >
          <i :class="['fa', refreshing ? 'fa-spinner fa-spin' : 'fa-refresh']"></i>
          <span>刷新数据</span>
        </button>
        <div class="user-profile" @click="router.push('/accountSettings')">
          <img :src="user?.avatar || '/static/img/logo.png'" alt="" class="avatar">
          <span class="username">{{ user?.username || '管理员' }}</span>
        </div>
        <button type="button" class="action-btn secondary-btn" @click="handleLogout">
          <i class="fa fa-sign-out"></i>
        </button>
      </div>
    </header>

    <main class="main-content">
      <div class="container-fluid">
        <slot />
      </div>
    </main>
  </div>
</template>

<script setup>
// 管理端壳：侧栏导航 + 顶栏刷新/登出
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getCurrentUser, removeUser } from '@/utils/auth'
import { authAPI } from '@/utils/api'

const props = defineProps({
  title: { type: String, default: '管理后台' },
  showRefresh: { type: Boolean, default: false }
})
const emit = defineEmits(['refresh'])

const route = useRoute()
const router = useRouter()
const user = ref(getCurrentUser())
const sidebarCollapsed = ref(false)
const refreshing = ref(false)

const navItems = [
  { to: '/admin', name: 'Admin', icon: 'fa-dashboard', label: '控制台' },
  { to: '/admin/bookManagement', name: 'AdminBookManagement', icon: 'fa-book', label: '书籍管理' },
  { to: '/admin/userManagement', name: 'AdminUserManagement', icon: 'fa-users', label: '用户管理' },
  { to: '/admin/orders', name: 'AdminOrders', icon: 'fa-list-alt', label: '订单管理' },
  { to: '/admin/wanted', name: 'AdminWanted', icon: 'fa-bullhorn', label: '求购审计' },
  { to: '/admin/messages', name: 'AdminMessages', icon: 'fa-envelope', label: '私信审计' },
  { to: '/admin/campus', name: 'AdminCampus', icon: 'fa-map-marker', label: '校园数据' },
  { to: '/admin/comments', name: 'AdminComments', icon: 'fa-check-square-o', label: '评论审核' },
  { to: '/admin/compliance', name: 'AdminCompliance', icon: 'fa-shield', label: '合规管理' },
  { to: '/admin/analytics', name: 'AdminAnalytics', icon: 'fa-bar-chart', label: '数据分析' },
  { to: '/admin/settings', name: 'AdminSettings', icon: 'fa-cog', label: '系统设置' }
]

function isActive(item) {
  if (item.name === 'Admin') return route.name === 'Admin'
  return route.name === item.name
}

async function onRefresh() {
  refreshing.value = true
  emit('refresh')
  setTimeout(() => { refreshing.value = false }, 600)
}

function handleLogout() {
  authAPI.logout().finally(() => {
    removeUser()
    router.push('/admin/login')
  })
}

onMounted(() => {
  if (!document.getElementById('fa4-admin')) {
    const link = document.createElement('link')
    link.id = 'fa4-admin'
    link.rel = 'stylesheet'
    link.href = 'https://cdn.jsdelivr.net/npm/font-awesome@4.7.0/css/font-awesome.min.css'
    document.head.appendChild(link)
  }
})
</script>

<style>
@import url('/static/css/admin.css');

.admin-spa .sidebar.collapsed {
  transform: translateX(-100%);
}
.admin-spa .sidebar.collapsed ~ .top-navbar {
  left: 0;
}
.admin-spa .sidebar.collapsed ~ .main-content {
  margin-left: 0;
}
.admin-spa .sidebar-footer {
  margin-top: 1rem;
  border-top: 1px solid var(--border-color);
  padding-top: 0.75rem;
}
.admin-spa .nav-link.router-link-active {
  background-color: rgba(0, 127, 115, 0.1);
  color: var(--primary-color);
  border-left: 3px solid var(--primary-color);
}
.admin-spa .page-header {
  margin-bottom: 1.5rem;
}
.admin-spa .page-header h2 {
  font-size: 1.35rem;
  font-weight: 600;
  color: var(--text-color);
  margin: 0;
}
.admin-spa .admin-panel {
  background: #fff;
  border-radius: 12px;
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow);
  padding: 1.25rem;
  margin-bottom: 1.5rem;
}
.admin-spa .admin-panel-title {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 1rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid var(--border-color);
}
</style>
