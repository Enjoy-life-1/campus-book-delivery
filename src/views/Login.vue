<template>
  <div class="login-page">
    <router-link to="/" class="back-home" aria-label="返回首页">
      <i class="fa fa-arrow-left"></i> 返回首页
    </router-link>

    <div class="login-card">
      <aside class="brand-panel">
        <div class="brand-inner">
          <img class="brand-logo" src="/static/img/logo.png" alt="校园书递">
          <h1>校园书递</h1>
          <p class="brand-desc">安全便捷的校园二手教材交易平台</p>
          <ul class="brand-features">
            <li><i class="fa fa-shield"></i> 校内面交，交易更放心</li>
            <li><i class="fa fa-leaf"></i> 教材循环，环保又省钱</li>
            <li><i class="fa fa-search"></i> 课程检索，快速找书</li>
          </ul>
        </div>
        <img class="brand-art" src="/static/img/520.jpg" alt="" loading="lazy">
      </aside>

      <section class="form-panel">
        <div class="form-panel-inner">
          <header class="form-header">
            <h2>账号登录</h2>
            <p>欢迎回来，登录后即可发布与购买书籍</p>
          </header>

          <form class="login-form" @submit.prevent="handleLogin">
            <div class="field">
              <label for="username">账号</label>
              <div class="input-wrap">
                <i class="fa fa-user input-icon"></i>
                <input
                  id="username"
                  v-model="form.username"
                  type="text"
                  class="form-control"
                  placeholder="用户名"
                  autocomplete="username"
                  required
                >
              </div>
            </div>

            <div class="field">
              <label for="password">密码</label>
              <div class="input-wrap">
                <i class="fa fa-lock input-icon"></i>
                <input
                  id="password"
                  v-model="form.password"
                  type="password"
                  class="form-control"
                  placeholder="密码"
                  autocomplete="current-password"
                  required
                >
              </div>
            </div>

            <div class="form-meta">
              <label class="remember-me">
                <input v-model="rememberMe" type="checkbox" id="rememberMe">
                <span>记住我（7天）</span>
              </label>
              <a href="#" class="link-muted" @click.prevent="showForgot = true">忘记密码？</a>
            </div>

            <div v-if="errorMessage" class="login-error" role="alert">
              <i class="fa fa-exclamation-circle"></i> {{ errorMessage }}
            </div>

            <button type="submit" class="login-btn" :disabled="loading">
              <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
              <i v-else class="fa fa-sign-in me-2"></i>
              {{ loading ? '登录中...' : '立即登录' }}
            </button>

            <p class="form-footer">
              还没有账号？
              <router-link to="/register">立即注册</router-link>
            </p>
          </form>
        </div>
      </section>
    </div>

    <div v-if="showForgot" class="modal-overlay" @click.self="showForgot = false">
      <div class="modal-box" role="dialog" aria-labelledby="forgotTitle">
        <div class="modal-head">
          <h5 id="forgotTitle">找回密码</h5>
          <button type="button" class="modal-close" aria-label="关闭" @click="showForgot = false">
            <i class="fa fa-times"></i>
          </button>
        </div>
        <input v-model="forgot.phone" class="form-control mb-2" placeholder="注册手机号">
        <div class="input-group mb-2">
          <input v-model="forgot.code" class="form-control" placeholder="验证码">
          <button type="button" class="btn btn-outline-success" :disabled="forgotSending" @click="sendForgotCode">
            {{ forgotSending ? '发送中' : '获取验证码' }}
          </button>
        </div>
        <input v-model="forgot.new1" type="password" class="form-control mb-2" placeholder="新密码（至少6位）">
        <input v-model="forgot.new2" type="password" class="form-control mb-3" placeholder="确认新密码">
        <div class="modal-actions">
          <button type="button" class="btn btn-secondary" @click="showForgot = false">取消</button>
          <button type="button" class="btn btn-success" :disabled="forgotLoading" @click="resetPwd">
            {{ forgotLoading ? '提交中...' : '重置密码' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
// 用户登录页：表单登录 + 找回密码弹窗
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { loginAndSync } from '@/composables/useAuth'  // POST /api/login + refreshSession
import { useToast } from '@/composables/useToast'
import { useSmsWebhookHint } from '@/composables/useSmsWebhookHint'  // 开发短信 Webhook 提示
import { authAPI } from '@/utils/api'

const router = useRouter()
const route = useRoute()

const form = ref({ username: '', password: '' })
const rememberMe = ref(false)
const loading = ref(false)
const errorMessage = ref('')
const showForgot = ref(false)  // 找回密码弹窗
const forgotSending = ref(false)
const forgotLoading = ref(false)
const forgot = ref({ phone: '', code: '', new1: '', new2: '' })
const { show } = useToast()
const { open: openSmsWebhookHint } = useSmsWebhookHint()

async function sendForgotCode() {
  // 发送手机验证码
  if (!/^1[3-9]\d{9}$/.test(forgot.value.phone)) return show('请输入有效手机号', 'warning')
  forgotSending.value = true
  try {
    const r = await authAPI.sendCode({ phone: forgot.value.phone })
    if (r.webhook_mode) openSmsWebhookHint(r.message)
    else show(r.message || '验证码已发送', 'success')
  } catch (e) { show(e.message || '发送失败', 'danger') }
  finally { forgotSending.value = false }
}

async function resetPwd() {
  // 验证码 + 新密码重置
  if (forgot.value.new1 !== forgot.value.new2) return show('两次密码不一致', 'warning')
  forgotLoading.value = true
  try {
    const r = await authAPI.forgotReset({
      phone: forgot.value.phone,
      code: forgot.value.code,
      new_password: forgot.value.new1
    })
    if (r.status === 'success') {
      show('密码已重置，请登录', 'success')
      showForgot.value = false
    } else show(r.message || '重置失败', 'danger')
  } catch (e) { show(e.message || '重置失败', 'danger') }
  finally { forgotLoading.value = false }
}

async function handleLogin() {
  // 提交登录，成功后跳 redirect 或首页
  if (!form.value.username || !form.value.password) {
    errorMessage.value = '请填写用户名和密码'
    return
  }
  loading.value = true
  errorMessage.value = ''
  try {
    const response = await loginAndSync({
      username: form.value.username,
      password: form.value.password
    })
    if (response.status === 'success') {
      show('登录成功', 'success')
      const redirect = route.query.redirect || '/'
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
  // 已登录非 admin 则直接进首页
  const raw = localStorage.getItem('currentUser')
  if (raw) {
    try {
      const u = JSON.parse(raw)
      if (u.is_admin) return
      router.push('/')
    } catch {
      router.push('/')
    }
  }
})
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.5rem;
  background: linear-gradient(160deg, #e8f5e9 0%, #f5f7fa 45%, #fff 100%);
  position: relative;
}

.back-home {
  position: absolute;
  top: 1.25rem;
  left: 1.5rem;
  color: #2e7d32;
  text-decoration: none;
  font-size: 0.9rem;
  font-weight: 500;
  z-index: 2;
}
.back-home:hover { color: #1b5e20; }

.login-card {
  display: flex;
  width: 100%;
  max-width: 920px;
  min-height: 520px;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 12px 40px rgba(40, 167, 69, 0.12), 0 4px 16px rgba(0, 0, 0, 0.06);
  overflow: hidden;
}

.brand-panel {
  flex: 0 0 42%;
  position: relative;
  background: linear-gradient(145deg, #1e7e34 0%, #28a745 55%, #34ce57 100%);
  color: #fff;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  overflow: hidden;
}

.brand-inner {
  padding: 2.5rem 2rem 1rem;
  position: relative;
  z-index: 1;
}

.brand-logo {
  width: 72px;
  height: 72px;
  object-fit: contain;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.15);
  padding: 6px;
}

.brand-panel h1 {
  font-size: 1.65rem;
  font-weight: 700;
  margin: 1rem 0 0.5rem;
}

.brand-desc {
  font-size: 0.9rem;
  opacity: 0.92;
  line-height: 1.5;
  margin-bottom: 1.25rem;
}

.brand-features {
  list-style: none;
  padding: 0;
  margin: 0;
}
.brand-features li {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  font-size: 0.85rem;
  margin-bottom: 0.65rem;
  opacity: 0.95;
}
.brand-features i { width: 1.1rem; text-align: center; }

.brand-art {
  width: 100%;
  max-height: 200px;
  object-fit: cover;
  object-position: center top;
  opacity: 0.35;
  mask-image: linear-gradient(to top, transparent, #000 40%);
  -webkit-mask-image: linear-gradient(to top, transparent, #000 40%);
}

.form-panel {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem 2.5rem;
}

.form-panel-inner {
  width: 100%;
  max-width: 360px;
}

.form-header h2 {
  color: #212529;
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 0.35rem;
}
.form-header p {
  color: #6c757d;
  font-size: 0.9rem;
  margin-bottom: 1.75rem;
}

.field { margin-bottom: 1.1rem; }
.field label {
  display: block;
  font-size: 0.85rem;
  font-weight: 600;
  color: #495057;
  margin-bottom: 0.4rem;
}

.input-wrap { position: relative; }
.input-icon {
  position: absolute;
  left: 0.85rem;
  top: 50%;
  transform: translateY(-50%);
  color: #adb5bd;
  font-size: 0.9rem;
  pointer-events: none;
}
.input-wrap .form-control {
  padding-left: 2.35rem;
  height: 46px;
  border-radius: 10px;
  border: 1px solid #dee2e6;
  font-size: 0.95rem;
}
.input-wrap .form-control:focus {
  border-color: #28a745;
  box-shadow: 0 0 0 0.2rem rgba(40, 167, 69, 0.15);
}

.form-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1.25rem;
  font-size: 0.85rem;
}
.remember-me {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  margin: 0;
  cursor: pointer;
  color: #495057;
}
.remember-me input { accent-color: #28a745; }
.link-muted {
  color: #6c757d;
  text-decoration: none;
}
.link-muted:hover { color: #28a745; }

.login-error {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.6rem 0.75rem;
  margin-bottom: 1rem;
  font-size: 0.85rem;
  color: #842029;
  background: #f8d7da;
  border-radius: 8px;
}

.login-btn {
  width: 100%;
  height: 46px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #28a745;
  color: #fff;
  border: none;
  border-radius: 10px;
  font-size: 1rem;
  font-weight: 600;
  transition: background 0.2s, transform 0.15s;
}
.login-btn:hover:not(:disabled) {
  background: #218838;
  transform: translateY(-1px);
}
.login-btn:disabled { opacity: 0.75; cursor: not-allowed; }

.form-footer {
  text-align: center;
  margin-top: 1.25rem;
  margin-bottom: 0;
  font-size: 0.9rem;
  color: #6c757d;
}
.form-footer a {
  color: #28a745;
  font-weight: 600;
  text-decoration: none;
}
.form-footer a:hover { text-decoration: underline; }

.modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 1050;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  background: rgba(0, 0, 0, 0.45);
}
.modal-box {
  width: 100%;
  max-width: 400px;
  background: #fff;
  border-radius: 12px;
  padding: 1.25rem 1.5rem 1.5rem;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
}
.modal-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
}
.modal-head h5 { margin: 0; font-weight: 700; }
.modal-close {
  border: none;
  background: none;
  color: #6c757d;
  font-size: 1.1rem;
  padding: 0.25rem;
  line-height: 1;
}
.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
}

@media (max-width: 768px) {
  .login-page { padding: 1rem; align-items: flex-start; padding-top: 3.5rem; }
  .back-home { top: 1rem; left: 1rem; }
  .login-card {
    flex-direction: column;
    min-height: auto;
    max-width: 420px;
  }
  .brand-panel { flex: none; }
  .brand-inner { padding: 1.5rem 1.25rem 0.75rem; text-align: center; }
  .brand-logo { margin: 0 auto; }
  .brand-features { display: none; }
  .brand-art { display: none; }
  .form-panel { padding: 1.5rem 1.25rem 2rem; }
}
</style>
