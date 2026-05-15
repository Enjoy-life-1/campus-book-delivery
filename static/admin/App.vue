<template>
  <div class="app-container">
    <!-- 应用标题 -->
    <h1 class="app-title">校园二手书交易平台</h1>
    
    <!-- 主要内容区域 -->
    <main class="main-content">
      <slot></slot>
    </main>
    
    <!-- 页脚 -->
    <footer class="app-footer">
      <p>© 2025 校园二手书交易平台 - 版权所有</p>
    </footer>
  </div>
</template>

<script>
export default {
  name: 'App',
  data() {
    return {
      // 应用状态可以在这里定义
      isLoggedIn: false,
      userIdentity: '',
      username: ''
    };
  },
  mounted() {
    // 组件挂载时检查登录状态
    this.checkLoginStatus();
  },
  methods: {
    // 检查登录状态
    checkLoginStatus() {
      // 这里可以通过API调用或localStorage检查登录状态
      const userInfo = localStorage.getItem('userInfo');
      if (userInfo) {
        const user = JSON.parse(userInfo);
        this.isLoggedIn = true;
        this.userIdentity = user.identity;
        this.username = user.username;
      }
    },
    // 处理登录成功事件
    handleLoginSuccess(userInfo) {
      this.isLoggedIn = true;
      this.userIdentity = userInfo.identity;
      this.username = userInfo.username;
      localStorage.setItem('userInfo', JSON.stringify(userInfo));
    },
    // 处理退出登录
    handleLogout() {
      this.isLoggedIn = false;
      this.userIdentity = '';
      this.username = '';
      localStorage.removeItem('userInfo');
    }
  }
};
</script>

<style scoped>
.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: #f5f5f5;
}

.app-title {
  text-align: center;
  color: #333;
  padding: 20px 0;
  margin: 0;
  background-color: #fff;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.main-content {
  flex: 1;
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
}

.app-footer {
  background-color: #333;
  color: #fff;
  text-align: center;
  padding: 20px;
  margin-top: auto;
}
</style>