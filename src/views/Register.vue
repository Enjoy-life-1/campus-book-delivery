<template>
  <div class="register-container">
    <div class="register-form">
      <h2>注册账号</h2>
      <form @submit.prevent="handleRegister">
        <div class="form-group">
          <label>用户名 <span class="text-danger">*</span></label>
          <input 
            v-model="form.username" 
            type="text" 
            class="form-control" 
            :class="{ 'is-invalid': errors.username }"
            placeholder="请输入用户名"
            required
            @blur="validateUsername"
          >
          <div v-if="errors.username" class="invalid-feedback">{{ errors.username }}</div>
        </div>
        <div class="form-group">
          <label>手机号 <span class="text-danger">*</span></label>
          <input 
            v-model="form.phone" 
            type="tel" 
            class="form-control" 
            :class="{ 'is-invalid': errors.phone }"
            placeholder="请输入11位手机号"
            required
            @blur="validatePhone"
          >
          <div v-if="errors.phone" class="invalid-feedback">{{ errors.phone }}</div>
        </div>
        <div class="form-group">
          <label>验证码 <span class="text-danger">*</span></label>
          <div class="verify-code-group">
            <input 
              v-model="form.verifyCode" 
              type="text" 
              class="form-control" 
              :class="{ 'is-invalid': errors.verifyCode }"
              placeholder="请输入6位验证码"
              required
              maxlength="6"
              @blur="validateVerifyCode"
            >
            <button 
              type="button" 
              class="btn btn-outline-primary send-code-btn"
              :disabled="codeCountdown > 0 || sendingCode"
              @click="sendVerificationCode"
            >
              {{ codeCountdown > 0 ? `${codeCountdown}秒后重试` : (sendingCode ? '发送中...' : '获取验证码') }}
            </button>
          </div>
          <div v-if="errors.verifyCode" class="invalid-feedback">{{ errors.verifyCode }}</div>
        </div>
        <div class="form-group">
          <label>密码 <span class="text-danger">*</span></label>
          <input 
            v-model="form.password" 
            type="password" 
            class="form-control" 
            :class="{ 'is-invalid': errors.password }"
            placeholder="请输入密码（至少6位）"
            required
            @blur="validatePassword"
          >
          <div v-if="errors.password" class="invalid-feedback">{{ errors.password }}</div>
        </div>
        <div class="form-group">
          <label>确认密码 <span class="text-danger">*</span></label>
          <input 
            v-model="form.confirmPassword" 
            type="password" 
            class="form-control" 
            :class="{ 'is-invalid': errors.confirmPassword }"
            placeholder="请再次输入密码"
            required
            @blur="validateConfirmPassword"
          >
          <div v-if="errors.confirmPassword" class="invalid-feedback">{{ errors.confirmPassword }}</div>
        </div>
        <div class="form-group">
          <label>邮箱（可选）</label>
          <input 
            v-model="form.email" 
            type="email" 
            class="form-control" 
            :class="{ 'is-invalid': errors.email }"
            placeholder="请输入邮箱地址"
            @blur="validateEmail"
          >
          <div v-if="errors.email" class="invalid-feedback">{{ errors.email }}</div>
        </div>
        <div v-if="errorMessage" class="alert alert-danger">{{ errorMessage }}</div>
        <div v-if="successMessage" class="alert alert-success">{{ successMessage }}</div>
        <button type="submit" class="btn btn-success w-100" :disabled="loading">
          {{ loading ? '注册中...' : '注册' }}
        </button>
        <p class="text-center mt-3">
          <router-link to="/login">已有账号？去登录</router-link>
        </p>
      </form>
    </div>
    
    <!-- Toast提示框 -->
    <div v-if="toast.show" :class="['toast-message', `toast-${toast.type}`]">
      <div class="toast-content">
        <span class="toast-icon">{{ toast.type === 'success' ? '✓' : '✗' }}</span>
        <span class="toast-text">{{ toast.message }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { authAPI } from '@/utils/api'

const router = useRouter()
const form = ref({
  username: '',
  password: '',
  confirmPassword: '',
  email: '',
  phone: '',
  verifyCode: ''
})
const loading = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const errors = ref({})
const sendingCode = ref(false)
const codeCountdown = ref(0)

// Toast提示框
const toast = ref({
  show: false,
  message: '',
  type: 'success' // success, error, info
})

// 显示Toast提示
function showToast(message, type = 'success') {
  toast.value = {
    show: true,
    message,
    type
  }
  setTimeout(() => {
    toast.value.show = false
  }, 3000)
}

// 验证用户名
function validateUsername() {
  const username = form.value.username.trim()
  if (!username) {
    errors.value.username = '请输入用户名'
    return false
  }
  delete errors.value.username
  return true
}

// 验证手机号
function validatePhone() {
  const phone = form.value.phone.trim()
  if (!phone) {
    errors.value.phone = '请输入手机号'
    return false
  }
  if (!/^1[3-9]\d{9}$/.test(phone)) {
    errors.value.phone = '请输入有效的11位手机号码'
    return false
  }
  delete errors.value.phone
  return true
}

// 验证验证码
function validateVerifyCode() {
  const verifyCode = form.value.verifyCode.trim()
  if (!verifyCode) {
    errors.value.verifyCode = '请输入验证码'
    return false
  }
  if (!/^\d{6}$/.test(verifyCode)) {
    errors.value.verifyCode = '请输入6位数字验证码'
    return false
  }
  delete errors.value.verifyCode
  return true
}

// 验证密码
function validatePassword() {
  const password = form.value.password
  if (!password) {
    errors.value.password = '请输入密码'
    return false
  }
  if (password.length < 6) {
    errors.value.password = '密码长度不能少于6位'
    return false
  }
  delete errors.value.password
  return true
}

// 验证确认密码
function validateConfirmPassword() {
  const confirmPassword = form.value.confirmPassword
  if (!confirmPassword) {
    errors.value.confirmPassword = '请确认密码'
    return false
  }
  if (confirmPassword !== form.value.password) {
    errors.value.confirmPassword = '两次输入的密码不一致'
    return false
  }
  delete errors.value.confirmPassword
  return true
}

// 验证邮箱
function validateEmail() {
  const email = form.value.email.trim()
  if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    errors.value.email = '请输入有效的邮箱地址'
    return false
  }
  delete errors.value.email
  return true
}

// 发送验证码
async function sendVerificationCode() {
  // 先验证手机号
  if (!validatePhone()) {
    showToast('请先输入有效的手机号', 'error')
    return
  }

  sendingCode.value = true
  try {
    const response = await authAPI.sendCode({
      phone: form.value.phone.trim()
    })

    if (response.success) {
      showToast(response.message || '验证码已发送', 'success')
      // 开始倒计时
      codeCountdown.value = 60
      const timer = setInterval(() => {
        codeCountdown.value--
        if (codeCountdown.value <= 0) {
          clearInterval(timer)
        }
      }, 1000)
    } else {
      showToast(response.message || '发送验证码失败', 'error')
    }
  } catch (error) {
    showToast(error.message || '发送验证码失败，请稍后重试', 'error')
  } finally {
    sendingCode.value = false
  }
}

// 表单提交
async function handleRegister() {
  // 清除之前的错误和成功消息
  errorMessage.value = ''
  successMessage.value = ''
  errors.value = {}

  // 验证所有字段
  const isValid = 
    validateUsername() &&
    validatePhone() &&
    validateVerifyCode() &&
    validatePassword() &&
    validateConfirmPassword() &&
    validateEmail()

  if (!isValid) {
    showToast('请检查并修正表单错误', 'error')
    return
  }

  // 再次确认密码一致性
  if (form.value.password !== form.value.confirmPassword) {
    errors.value.confirmPassword = '两次输入的密码不一致'
    showToast('两次输入的密码不一致', 'error')
    return
  }

  loading.value = true

  try {
    const response = await authAPI.register({
      username: form.value.username.trim(),
      password: form.value.password,
      phone: form.value.phone.trim(),
      verifyCode: form.value.verifyCode.trim(),
      email: form.value.email.trim() || ''
    })

    if (response.status === 'success') {
      showToast('注册成功！即将跳转到登录页', 'success')
      successMessage.value = '注册成功！'
      setTimeout(() => {
        router.push('/login')
      }, 1500)
    } else {
      errorMessage.value = response.message || '注册失败'
      showToast(response.message || '注册失败', 'error')
    }
  } catch (error) {
    const errorMsg = error.message || error.response?.data?.message || '注册失败，请稍后重试'
    errorMessage.value = errorMsg
    showToast(errorMsg, 'error')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.register-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f5f5;
  padding: 20px;
  position: relative;
}

.register-form {
  background: white;
  padding: 40px;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  width: 100%;
  max-width: 500px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #333;
}

.form-control {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  transition: border-color 0.3s;
}

.form-control:focus {
  outline: none;
  border-color: #4CAF50;
  box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.1);
}

.form-control.is-invalid {
  border-color: #dc3545;
}

.invalid-feedback {
  display: block;
  width: 100%;
  margin-top: 5px;
  font-size: 12px;
  color: #dc3545;
}

.verify-code-group {
  display: flex;
  gap: 10px;
}

.verify-code-group .form-control {
  flex: 1;
}

.send-code-btn {
  white-space: nowrap;
  min-width: 120px;
}

.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-success {
  background-color: #4CAF50;
  color: white;
}

.btn-success:hover:not(:disabled) {
  background-color: #45a049;
}

.btn-success:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

.btn-outline-primary {
  background-color: transparent;
  border: 1px solid #007bff;
  color: #007bff;
}

.btn-outline-primary:hover:not(:disabled) {
  background-color: #007bff;
  color: white;
}

.btn-outline-primary:disabled {
  border-color: #cccccc;
  color: #cccccc;
  cursor: not-allowed;
}

.w-100 {
  width: 100%;
}

.text-center {
  text-align: center;
}

.mt-3 {
  margin-top: 1rem;
}

.text-danger {
  color: #dc3545;
}

.alert {
  padding: 12px 16px;
  border-radius: 4px;
  margin-bottom: 20px;
}

.alert-danger {
  background-color: #f8d7da;
  border: 1px solid #f5c6cb;
  color: #721c24;
}

.alert-success {
  background-color: #d4edda;
  border: 1px solid #c3e6cb;
  color: #155724;
}

/* Toast提示框样式 */
.toast-message {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 9999;
  min-width: 300px;
  max-width: 400px;
  padding: 16px 20px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

.toast-content {
  display: flex;
  align-items: center;
  gap: 12px;
}

.toast-icon {
  font-size: 20px;
  font-weight: bold;
}

.toast-text {
  flex: 1;
  font-size: 14px;
  line-height: 1.5;
}

.toast-success {
  background-color: #4CAF50;
  color: white;
}

.toast-error {
  background-color: #f44336;
  color: white;
}

.toast-info {
  background-color: #2196F3;
  color: white;
}

@media (max-width: 768px) {
  .register-form {
    padding: 30px 20px;
  }
  
  .verify-code-group {
    flex-direction: column;
  }
  
  .send-code-btn {
    width: 100%;
  }
  
  .toast-message {
    left: 20px;
    right: 20px;
    min-width: auto;
  }
}
</style>

