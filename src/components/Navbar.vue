<template>
  <nav class="navbar navbar-expand-lg sticky-top bg-success text-white navbar-compact">
    <div class="container">
      <router-link class="navbar-brand text-white" to="/">
        <i class="fa fa-book"></i>
        <span class="brand-text">校园书递</span>
      </router-link>
      <button
        class="navbar-toggler border-0"
        type="button"
        data-bs-toggle="collapse"
        data-bs-target="#navbarNav"
        aria-controls="navbarNav"
        aria-expanded="false"
        aria-label="菜单"
      >
        <span class="navbar-toggler-icon"></span>
      </button>
      <div class="collapse navbar-collapse" id="navbarNav">
        <ul class="navbar-nav me-auto gap-lg-1">
          <li class="nav-item">
            <router-link class="nav-link text-white" :class="{ active: $route.name === 'Home' }" to="/">首页</router-link>
          </li>
          <li class="nav-item">
            <router-link class="nav-link text-white" :class="{ active: $route.name === 'BooksList' }" to="/booksList">全部书籍</router-link>
          </li>
          <li class="nav-item dropdown">
            <a
              class="nav-link dropdown-toggle text-white"
              href="#"
              role="button"
              data-bs-toggle="dropdown"
              :class="{ active: discoverActive }"
            >发现</a>
            <ul class="dropdown-menu">
              <li>
                <router-link class="dropdown-item" to="/ai" :class="{ active: $route.name === 'AiAssistant' }">
                  <i class="fa fa-magic text-success me-2"></i>智能找书
                </router-link>
              </li>
              <li>
                <router-link class="dropdown-item" to="/courses" :class="{ active: $route.name === 'CourseBooks' }">
                  <i class="fa fa-graduation-cap text-muted me-2"></i>按课找书
                </router-link>
              </li>
              <li><hr class="dropdown-divider"></li>
              <li>
                <router-link class="dropdown-item" to="/wanted" :class="{ active: isWantedRoute }">
                  <i class="fa fa-bullhorn text-muted me-2"></i>求购广场
                </router-link>
              </li>
              <li>
                <router-link class="dropdown-item" to="/semester" :class="{ active: $route.name === 'SemesterHub' }">
                  <i class="fa fa-calendar text-muted me-2"></i>学期专场
                </router-link>
              </li>
            </ul>
          </li>
          <li class="nav-item dropdown">
            <a class="nav-link dropdown-toggle text-white" href="#" role="button" data-bs-toggle="dropdown">分类</a>
            <ul class="dropdown-menu dropdown-menu-categories">
              <li v-for="c in categories" :key="c.code">
                <router-link class="dropdown-item" :to="`/booksList?category=${c.code}`">{{ c.name }}</router-link>
              </li>
              <li v-if="!categories.length" class="dropdown-item text-muted small">加载中…</li>
            </ul>
          </li>
          <li class="nav-item d-none d-xl-block">
            <router-link class="nav-link text-white" :class="{ active: $route.name === 'Guide' }" to="/guide">指南</router-link>
          </li>
        </ul>

        <div class="navbar-nav align-items-lg-center nav-right">
          <template v-if="profile">
            <router-link class="nav-icon-btn" to="/notifications" title="通知">
              <i class="fa fa-bell"></i>
              <span v-if="notifyCount" class="badge bg-danger">{{ notifyCount > 99 ? '99+' : notifyCount }}</span>
            </router-link>
            <router-link
              class="nav-action-btn nav-action-msg"
              :class="{ 'has-badge': msgCount }"
              to="/messages"
              title="消息"
            >
              <i class="fa fa-envelope"></i>
              <span class="nav-action-label">消息</span>
              <span v-if="msgCount" class="badge bg-danger">{{ msgCount > 99 ? '99+' : msgCount }}</span>
            </router-link>
            <router-link
              class="nav-action-btn nav-action-cart"
              :class="{ 'has-badge': cartCount }"
              to="/cart"
              title="购物车"
            >
              <i class="fa fa-shopping-cart"></i>
              <span class="nav-action-label">购物车</span>
              <span v-if="cartCount" class="badge bg-danger">{{ cartCount > 99 ? '99+' : cartCount }}</span>
            </router-link>
            <router-link class="btn btn-light btn-sm text-success fw-semibold publish-btn" to="/publishBook">
              <i class="fa fa-plus"></i>
              <span class="d-none d-sm-inline">发布</span>
            </router-link>
          </template>

          <div class="nav-item dropdown user-menu">
            <a
              class="nav-link dropdown-toggle text-white user-toggle"
              href="#"
              role="button"
              data-bs-toggle="dropdown"
            >
              <img v-if="showAvatar" :src="normalizeAvatar(profile.avatar)" class="nav-avatar" alt="" @error="avatarBroken = true">
              <i v-else class="fa fa-user"></i>
              <span class="user-name">{{ profile ? profile.username : '登录' }}</span>
              <span v-if="profile?.campus_verified" class="badge bg-light text-success verified-badge">认证</span>
            </a>
            <ul class="dropdown-menu dropdown-menu-end">
              <template v-if="profile">
                <li class="d-xl-none">
                  <router-link class="dropdown-item" to="/guide"><i class="fa fa-info-circle me-2"></i>交易指南</router-link>
                </li>
                <li class="d-xl-none"><hr class="dropdown-divider"></li>
                <li><router-link class="dropdown-item" to="/personalCenter"><i class="fa fa-user me-2"></i>个人中心</router-link></li>
                <li><router-link class="dropdown-item" to="/myBooks"><i class="fa fa-book me-2"></i>我的书籍</router-link></li>
                <li><router-link class="dropdown-item" to="/myCollections"><i class="fa fa-star me-2"></i>我的收藏</router-link></li>
                <li><router-link class="dropdown-item" to="/offers"><i class="fa fa-handshake-o me-2"></i>议价管理</router-link></li>
                <li><router-link class="dropdown-item" to="/transactionHistory"><i class="fa fa-list me-2"></i>交易记录</router-link></li>
                <li><router-link class="dropdown-item" to="/accountSettings"><i class="fa fa-cog me-2"></i>账户设置</router-link></li>
                <li v-if="profile.is_admin"><router-link class="dropdown-item" to="/admin"><i class="fa fa-dashboard me-2"></i>管理后台</router-link></li>
                <li><hr class="dropdown-divider"></li>
                <li><a class="dropdown-item" href="#" @click.prevent="handleLogout"><i class="fa fa-sign-out me-2"></i>退出</a></li>
              </template>
              <template v-else>
                <li class="d-xl-none">
                  <router-link class="dropdown-item" to="/guide"><i class="fa fa-info-circle me-2"></i>交易指南</router-link>
                </li>
                <li class="d-xl-none"><hr class="dropdown-divider"></li>
                <li><router-link class="dropdown-item" to="/login">登录</router-link></li>
                <li><router-link class="dropdown-item" to="/register">注册</router-link></li>
              </template>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </nav>
</template>

<script setup>
// 全局顶栏：导航、角标、用户菜单、登出
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { storeToRefs } from 'pinia'
import { authAPI } from '@/utils/api'
import { useUserStore } from '@/stores/user'
import { useAppStore } from '@/stores/app'
import { normalizeAvatar } from '@/utils/helpers'

const route = useRoute()
const userStore = useUserStore()
const appStore = useAppStore()
const { profile, cartCount, msgCount, notifyCount } = storeToRefs(userStore)  // Pinia 用户态
const { categories } = storeToRefs(appStore)  // 分类下拉
const avatarBroken = ref(false)
const showAvatar = computed(() => !!(normalizeAvatar(profile.value?.avatar) && !avatarBroken.value))
watch(() => profile.value?.avatar, () => { avatarBroken.value = false })  // 换头像后重置加载失败态

const discoverActive = computed(() =>
  ['CourseBooks', 'AiAssistant', 'WantedList', 'WantedDetail', 'SemesterHub', 'ShareWanted'].includes(route.name)
)

const isWantedRoute = computed(() =>
  ['WantedList', 'WantedDetail', 'ShareWanted'].includes(route.name)
)

function handleLogout() {
  // 登出：清 Session + 清 store + 跳登录页
  authAPI.logout().finally(() => {
    userStore.setUser(null)
    window.location.href = '/login'
  })
}

onMounted(() => {
  userStore.syncFromStorage()  // 含 refreshBadges 拉角标
  appStore.loadCategories()  // 加载书籍分类
})
</script>

<style scoped>
.navbar-compact {
  --bs-navbar-padding-y: 0.35rem;
}
.navbar-compact .nav-link {
  padding: 0.4rem 0.55rem;
  font-size: 0.92rem;
}
.brand-text {
  margin-left: 0.25rem;
}
@media (max-width: 991.98px) {
  .brand-text { display: none; }
}
.navbar-toggler-icon {
  filter: invert(1);
}
.nav-right {
  flex-direction: row;
  gap: 0.15rem;
}
.nav-icon-btn {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2.1rem;
  height: 2.1rem;
  color: #fff;
  border-radius: 50%;
  text-decoration: none;
  transition: background 0.15s;
}
.nav-icon-btn:hover {
  background: rgba(255, 255, 255, 0.15);
  color: #fff;
}
.nav-icon-btn .badge,
.nav-action-btn .badge {
  position: absolute;
  top: -4px;
  right: -4px;
  font-size: 0.65rem;
  min-width: 1.1rem;
  padding: 0.2em 0.4em;
  border: 2px solid #198754;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}
.nav-action-btn {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.35rem 0.7rem;
  margin: 0 0.1rem;
  color: #198754;
  background: #fff;
  border-radius: 2rem;
  text-decoration: none;
  font-size: 0.88rem;
  font-weight: 600;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.12);
  transition: transform 0.15s, box-shadow 0.15s, background 0.15s;
}
.nav-action-btn i {
  font-size: 1.05rem;
}
.nav-action-btn:hover {
  color: #157347;
  background: #f8fff9;
  transform: translateY(-1px);
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.15);
}
.nav-action-cart {
  background: #fff8e6;
  color: #b8860b;
  border: 1px solid rgba(255, 193, 7, 0.45);
}
.nav-action-cart:hover {
  color: #996f00;
  background: #fff3cd;
}
.nav-action-msg.has-badge,
.nav-action-cart.has-badge {
  animation: nav-pulse 2s ease-in-out infinite;
}
@keyframes nav-pulse {
  0%, 100% { box-shadow: 0 2px 6px rgba(0, 0, 0, 0.12); }
  50% { box-shadow: 0 2px 12px rgba(220, 53, 69, 0.35); }
}
.nav-action-label {
  line-height: 1;
}
@media (max-width: 575.98px) {
  .nav-action-label { display: none; }
  .nav-action-btn {
    padding: 0.4rem 0.55rem;
  }
  .nav-action-btn i {
    font-size: 1.15rem;
  }
}
.publish-btn {
  margin-left: 0.25rem;
  margin-right: 0.15rem;
  border-radius: 1rem;
  padding: 0.25rem 0.75rem;
}
.user-toggle {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  max-width: 9rem;
  padding-left: 0.35rem !important;
}
.user-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 5.5rem;
}
.verified-badge {
  font-size: 0.6rem;
  flex-shrink: 0;
}
.nav-avatar {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  object-fit: cover;
  flex-shrink: 0;
}
.nav-link.active,
.dropdown-item.active {
  font-weight: 600;
}
.nav-link.active {
  text-decoration: underline;
  text-underline-offset: 3px;
}
.dropdown-menu-categories {
  max-height: 60vh;
  overflow-y: auto;
}
@media (max-width: 991.98px) {
  .nav-right {
    padding-top: 0.5rem;
    padding-bottom: 0.5rem;
    border-top: 1px solid rgba(255, 255, 255, 0.2);
    margin-top: 0.35rem;
  }
  .nav-action-btn {
    flex: 1;
    justify-content: center;
    max-width: 48%;
  }
  .nav-action-label {
    display: inline;
  }
  .publish-btn {
    margin-left: auto;
    width: 100%;
    margin-top: 0.35rem;
  }
  .user-menu {
    width: 100%;
  }
  .user-toggle {
    max-width: none;
  }
}
</style>
