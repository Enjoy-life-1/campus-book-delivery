// Vue 前端入口：创建应用、注册插件、同步登录态
import { createApp } from 'vue'  // 创建 Vue 应用实例
import { createPinia } from 'pinia'  // 全局状态管理
import App from './App.vue'  // 根组件
import router from './router'  // 路由
import { refreshSession } from '@/composables/useAuth'  // 从服务端 Session 同步用户
import { useUserStore } from '@/stores/user'  // 用户 Pinia store
import './assets/css/main.css'  // 全局样式

const app = createApp(App)  // 创建应用
const pinia = createPinia()  // 创建 Pinia
app.use(pinia)  // 注册状态管理
app.use(router)  // 注册路由
app.mount('#app')  // 挂载到 index.html 的 #app

refreshSession().then(() => useUserStore().syncFromStorage())  // 启动后拉 /api/user/info
window.addEventListener('user-updated', () => useUserStore().syncFromStorage())  // 路由切换等刷新 store

if ('serviceWorker' in navigator && import.meta.env.PROD) {
  navigator.serviceWorker.register('/sw.js').catch(() => {})  // 生产环境 PWA
}
