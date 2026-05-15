<template>
  <div class="login-container">
    <!-- 左侧品牌区域 -->
    <div class="brand-side">
      <div class="brand-logo">
        <img src="/static/img/logo.png" alt="校园书递Logo">
      </div>
      <h1 class="brand-title">校园书递</h1>
      <div class="brand-slogan">
        专注于校园二手书籍交易，让闲置教材焕发新价值<br>
        为大学生提供安全、便捷、高效的书籍交易平台
      </div>
      <div class="brand-illustration">
        <img src="/static/img/520.jpg" alt="书籍交易插图">
      </div>
    </div>

    <!-- 右侧表单区域 -->
    <div class="form-side">
      <div class="form-header">
        <h2>欢迎使用校园书递</h2>
        <p>请登录您的账号继续使用</p>
      </div>

      <!-- 身份选择 -->
      <div class="identity-select">
        <div 
          class="identity-btn" 
          :class="{ active: role === 'student' }" 
          @click="role = 'student'"
        >
          学生
        </div>
        <div 
          class="identity-btn" 
          :class="{ active: role === 'admin' }" 
          @click="role = 'admin'"
        >
          管理员
        </div>
      </div>

      <!-- 登录表单 -->
      <form class="login-form" @submit.prevent="handleLogin">
        <div class="form-group">
          <label for="username">账号</label>
          <input 
            v-model="form.username" 
            type="text" 
            id="username" 
            class="form-control" 
            placeholder="请输入学号" 
            required
          >
        </div>

        <div class="form-group">
          <label for="password">密码</label>
          <input 
            v-model="form.password" 
            type="password" 
            id="password" 
            class="form-control" 
            placeholder="请输入密码" 
            required
          >
        </div>

        <div class="form-options">
          <div class="remember-me">
            <input type="checkbox" id="rememberMe" v-model="rememberMe"> 
            <label for="rememberMe">记住我（7天）</label>
          </div>
          <div>
            <router-link to="/register" class="register-link">注册账号</router-link>
            <a href="#" class="forgot-password">忘记密码?</a>
          </div>
        </div>

        <div v-if="errorMessage" class="login-error">{{ errorMessage }}</div>
        
        <button type="submit" class="login-btn" :disabled="loading">
          <i class="fa fa-sign-in"></i> {{ loading ? '登录中...' : '立即登录' }}
        </button>

        <div class="sms-login-prompt">
          手机验证码登录
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { authAPI } from '@/utils/api'
import { saveUser } from '@/utils/auth'

const router = useRouter()
const route = useRoute()

const role = ref(route.query.role === 'admin' ? 'admin' : 'student')
const form = ref({
  username: '',
  password: ''
})
const rememberMe = ref(false)
const loading = ref(false)
const errorMessage = ref('')

async function handleLogin() {
  if (!form.value.username || !form.value.password) {
    errorMessage.value = '请填写用户名和密码'
    return
  }

  loading.value = true
  errorMessage.value = ''

  try {
    const response = await authAPI.login({
      username: form.value.username,
      password: form.value.password,
      role: role.value
    })

    if (response.status === 'success') {
      // 保存用户信息
      saveUser(response.user)
      
      // 跳转到目标页面或首页
      const redirect = route.query.redirect || (role.value === 'admin' ? '/admin' : '/')
      router.push(redirect)
    } else {
      errorMessage.value = response.message || '登录失败'
    }
  } catch (error) {
    errorMessage.value = error.message || '登录失败，请检查网络连接'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  // 如果已登录，跳转到首页
  const user = localStorage.getItem('currentUser')
  if (user) {
    router.push('/')
  }
})
</script>

<style scoped>
@import url('/static/css/login.css');
</style>

