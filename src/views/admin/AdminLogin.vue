<template>
  <div class="admin-login-page">
    <div class="admin-login-card">
      <div class="login-brand">
        <img src="/static/img/logo.png" alt="校园书递" class="brand-logo">
        <h1>校园书递</h1>
        <p>管理后台</p>
      </div>

      <form class="login-form" @submit.prevent="handleLogin">
        <h2>管理员登录</h2>
        <p class="login-sub">请使用管理员账号登录后台系统</p>

        <div class="field">
          <label for="username">管理员账号</label>
          <div class="input-wrap">
            <i class="fa fa-user"></i>
            <input
              id="username"
              v-model="form.username"
              type="text"
              placeholder="请输入账号"
              autocomplete="username"
              required
            >
          </div>
        </div>

        <div class="field">
          <label for="password">密码</label>
          <div class="input-wrap">
            <i class="fa fa-lock"></i>
            <input
              id="password"
              v-model="form.password"
              :type="showPwd ? 'text' : 'password'"
              placeholder="请输入密码"
              autocomplete="current-password"
              required
            >
            <button type="button" class="pwd-toggle" @click="showPwd = !showPwd">
              <i :class="['fa', showPwd ? 'fa-eye-slash' : 'fa-eye']"></i>
            </button>
          </div>
        </div>

        <div v-if="errorMessage" class="login-error" role="alert">
          <i class="fa fa-exclamation-circle"></i> {{ errorMessage }}
        </div>

        <button type="submit" class="login-btn" :disabled="loading">
          <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
          {{ loading ? '登录中...' : '登录后台' }}
        </button>

        <p class="login-footer">
          <router-link to="/">← 返回用户端首页</router-link>
        </p>
      </form>
    </div>
  </div>
</template>

<script setup>
// 管理员登录：adminLoginAndSync + isStaff 校验
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { adminLoginAndSync } from '@/composables/useAuth'
import { useToast } from '@/composables/useToast'
import { isStaff } from '@/utils/auth'

const router = useRouter()
const route = useRoute()
const { show } = useToast()

const form = ref({ username: '', password: '' })
const showPwd = ref(false)
const loading = ref(false)
const errorMessage = ref('')

async function handleLogin() {
  if (!form.value.username || !form.value.password) {
    errorMessage.value = '请填写账号和密码'
    return
  }
  loading.value = true
  errorMessage.value = ''
  try {
    const res = await adminLoginAndSync(form.value)
    if (res.status === 'success') {
      show('登录成功', 'success')
      router.push(route.query.redirect || '/admin')
    } else {
      errorMessage.value = res.message || '登录失败'
    }
  } catch (e) {
    errorMessage.value = e.message || '登录失败，请检查账号密码'
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  const { refreshSession } = await import('@/composables/useAuth')
  const user = await refreshSession()
  if (user && isStaff(user)) {
    router.replace(route.query.redirect || '/admin')
  }
})
</script>

<style scoped>
.admin-login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.5rem;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
}

.admin-login-card {
  display: flex;
  width: 100%;
  max-width: 860px;
  min-height: 480px;
  background: #fff;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.35);
}

.login-brand {
  flex: 0 0 38%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  background: linear-gradient(160deg, #007f73 0%, #005a52 100%);
  color: #fff;
  text-align: center;
}

.brand-logo {
  width: 80px;
  height: 80px;
  object-fit: contain;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.15);
  padding: 8px;
  margin-bottom: 1rem;
}

.login-brand h1 {
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0 0 0.35rem;
}

.login-brand p {
  font-size: 0.95rem;
  opacity: 0.85;
  margin: 0;
  letter-spacing: 0.15em;
}

.login-form {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 2.5rem 2.75rem;
}

.login-form h2 {
  font-size: 1.4rem;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 0.35rem;
}

.login-sub {
  color: #64748b;
  font-size: 0.875rem;
  margin: 0 0 1.75rem;
}

.field {
  margin-bottom: 1.1rem;
}

.field label {
  display: block;
  font-size: 0.85rem;
  font-weight: 600;
  color: #475569;
  margin-bottom: 0.4rem;
}

.input-wrap {
  position: relative;
}

.input-wrap > i.fa-user,
.input-wrap > i.fa-lock {
  position: absolute;
  left: 0.85rem;
  top: 50%;
  transform: translateY(-50%);
  color: #94a3b8;
  font-size: 0.9rem;
  pointer-events: none;
}

.input-wrap input {
  width: 100%;
  height: 46px;
  padding: 0 2.5rem 0 2.35rem;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  font-size: 0.95rem;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.input-wrap input:focus {
  outline: none;
  border-color: #007f73;
  box-shadow: 0 0 0 3px rgba(0, 127, 115, 0.15);
}

.pwd-toggle {
  position: absolute;
  right: 0.5rem;
  top: 50%;
  transform: translateY(-50%);
  border: none;
  background: none;
  color: #94a3b8;
  padding: 0.35rem 0.5rem;
  cursor: pointer;
}

.login-error {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.6rem 0.75rem;
  margin-bottom: 1rem;
  font-size: 0.85rem;
  color: #991b1b;
  background: #fef2f2;
  border-radius: 8px;
}

.login-btn {
  width: 100%;
  height: 46px;
  margin-top: 0.25rem;
  background: #007f73;
  color: #fff;
  border: none;
  border-radius: 10px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.login-btn:hover:not(:disabled) {
  background: #00665c;
}

.login-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.login-footer {
  text-align: center;
  margin: 1.25rem 0 0;
  font-size: 0.875rem;
}

.login-footer a {
  color: #64748b;
  text-decoration: none;
}

.login-footer a:hover {
  color: #007f73;
}

@media (max-width: 640px) {
  .admin-login-card {
    flex-direction: column;
    min-height: auto;
  }
  .login-brand {
    flex: none;
    padding: 1.5rem;
  }
  .login-form {
    padding: 1.5rem 1.25rem 2rem;
  }
}
</style>
