<template>
  <nav class="navbar navbar-expand-lg sticky-top bg-success text-white">
    <div class="container">
      <router-link class="navbar-brand text-white" to="/">
        <i class="fa fa-book"></i> 校园书递
      </router-link>
      <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
        <span class="navbar-toggler-icon"></span>
      </button>
      <div class="collapse navbar-collapse" id="navbarNav">
        <ul class="navbar-nav me-auto">
          <li class="nav-item">
            <router-link class="nav-link text-white" :class="{ active: $route.name === 'Home' }" to="/">
              首页
            </router-link>
          </li>
          <li class="nav-item">
            <router-link class="nav-link text-white" :class="{ active: $route.name === 'BooksList' }" to="/booksList">
              全部书籍
            </router-link>
          </li>
          <li class="nav-item dropdown">
            <a class="nav-link dropdown-toggle text-white" href="#" role="button" data-bs-toggle="dropdown">
              书籍分类
            </a>
            <ul class="dropdown-menu">
              <li><router-link class="dropdown-item" to="/booksList?category=textbook">教材教辅</router-link></li>
              <li><router-link class="dropdown-item" to="/booksList?category=postgraduate">考研资料</router-link></li>
              <li><router-link class="dropdown-item" to="/booksList?category=literature">文学小说</router-link></li>
              <li><router-link class="dropdown-item" to="/booksList?category=professional">专业书籍</router-link></li>
              <li><router-link class="dropdown-item" to="/booksList?category=other">其他书籍</router-link></li>
            </ul>
          </li>
          <li class="nav-item">
            <router-link class="nav-link text-white" to="/guide">交易指南</router-link>
          </li>
        </ul>
        <div class="navbar-nav">
          <router-link v-if="user" class="nav-link me-3 text-white" to="/publishBook">
            <i class="fa fa-plus-circle"></i> 发布书籍
          </router-link>
          <div class="nav-item dropdown">
            <a class="nav-link dropdown-toggle text-white" href="#" role="button" data-bs-toggle="dropdown">
              <i class="fa fa-user"></i> {{ user ? user.username : '登录/注册' }}
            </a>
            <ul class="dropdown-menu dropdown-menu-end">
              <template v-if="user">
                <li><router-link class="dropdown-item" to="/personalCenter">个人中心</router-link></li>
                <li><router-link class="dropdown-item" to="/myBooks">我的书籍</router-link></li>
                <li><router-link class="dropdown-item" to="/myCollections">我的收藏</router-link></li>
                <li><router-link class="dropdown-item" to="/cart">购物车</router-link></li>
                <li v-if="user.is_admin"><router-link class="dropdown-item" to="/admin">管理员后台</router-link></li>
                <li><hr class="dropdown-divider"></li>
                <li><a class="dropdown-item" href="#" @click.prevent="handleLogout">退出登录</a></li>
              </template>
              <template v-else>
                <li><router-link class="dropdown-item" to="/login">登录</router-link></li>
                <li><router-link class="dropdown-item" to="/register">注册</router-link></li>
                <li><hr class="dropdown-divider"></li>
                <li><router-link class="dropdown-item" to="/login?role=admin"><i class="fa fa-lock"></i> 管理员登录</router-link></li>
              </template>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { getCurrentUser, removeUser } from '@/utils/auth'
import { authAPI } from '@/utils/api'

const user = ref(null)

function updateUser() {
  user.value = getCurrentUser()
}

function handleLogout() {
  authAPI.logout().finally(() => {
    removeUser()
    window.location.href = '/login'
  })
}

onMounted(() => {
  updateUser()
  window.addEventListener('storage', updateUser)
})

onUnmounted(() => {
  window.removeEventListener('storage', updateUser)
})
</script>

