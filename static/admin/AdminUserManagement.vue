<template>
  <div class="admin-user-management">
    <div class="card">
      <div class="card-header">
        <h2>用户管理</h2>
      </div>
      
      <!-- 添加用户按钮 -->
      <div class="add-user-section">
        <button class="btn btn-primary" @click="showAddUserDialog = true">
          添加用户
        </button>
      </div>

      <!-- 搜索和筛选 -->
      <div class="search-filter">
        <input
          type="text"
          v-model="searchKeyword"
          placeholder="搜索用户名..."
          class="form-control"
          @input="handleSearch"
        />
        <select v-model="filterIdentity" class="form-control" @change="handleFilter">
          <option value="">全部身份</option>
          <option value="student">学生</option>
          <option value="admin">管理员</option>
        </select>
      </div>

      <!-- 加载状态 -->
      <div v-if="loading" class="loading">
        <p>加载中...</p>
      </div>

      <!-- 错误提示 -->
      <div v-else-if="error" class="error-message">
        {{ error }}
      </div>

      <!-- 用户列表表格 -->
      <div v-else class="table-container">
        <table class="table">
          <thead>
            <tr>
              <th>用户ID</th>
              <th>用户名</th>
              <th>身份</th>
              <th>注册时间</th>
              <th>状态</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="filteredUsers.length === 0">
              <td colspan="6" class="no-data">暂无用户数据</td>
            </tr>
            <tr v-for="user in filteredUsers" :key="user.id">
              <td>{{ user.id }}</td>
              <td>{{ user.username }}</td>
              <td>
                <span class="identity-badge" :class="`identity-${user.identity}`">
                  {{ user.identity === 'admin' ? '管理员' : '学生' }}
                </span>
              </td>
              <td>{{ user.register_time || '未知' }}</td>
              <td>
                <span class="status-badge" :class="`status-${user.status}`">
                  {{ user.status === 'active' ? '正常' : '禁用' }}
                </span>
              </td>
              <td>
                <button
                  class="btn btn-danger btn-sm"
                  @click="deleteUser(user)"
                  :disabled="isCurrentUser(user.username)"
                  title="删除用户"
                >
                  删除
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 添加用户对话框 -->
    <div v-if="showAddUserDialog" class="dialog-overlay" @click="closeAddUserDialog">
      <div class="dialog" @click.stop>
        <div class="dialog-header">
          <h3>添加用户</h3>
          <button class="close-btn" @click="closeAddUserDialog">&times;</button>
        </div>
        <div class="dialog-body">
          <div class="form-group">
            <label class="form-label">用户名</label>
            <input
              type="text"
              v-model="newUser.username"
              class="form-control"
              placeholder="请输入用户名"
            />
          </div>
          <div class="form-group">
            <label class="form-label">密码</label>
            <input
              type="password"
              v-model="newUser.password"
              class="form-control"
              placeholder="请输入密码"
            />
          </div>
          <div class="form-group">
            <label class="form-label">身份</label>
            <select v-model="newUser.identity" class="form-control">
              <option value="student">学生</option>
              <option value="admin">管理员</option>
            </select>
          </div>
          <div v-if="dialogError" class="error-message">
            {{ dialogError }}
          </div>
        </div>
        <div class="dialog-footer">
          <button class="btn btn-outline" @click="closeAddUserDialog">
            取消
          </button>
          <button class="btn btn-primary" @click="submitAddUser" :disabled="dialogLoading">
            {{ dialogLoading ? '添加中...' : '添加' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue';
import { users } from '../utils/api.js';

export default {
  name: 'AdminUserManagement',
  setup() {
    // 响应式数据
    const allUsers = ref([]);
    const loading = ref(false);
    const error = ref('');
    const searchKeyword = ref('');
    const filterIdentity = ref('');
    
    // 添加用户对话框状态
    const showAddUserDialog = ref(false);
    const newUser = ref({
      username: '',
      password: '',
      identity: 'student'
    });
    const dialogLoading = ref(false);
    const dialogError = ref('');

    // 计算过滤后的用户列表
    const filteredUsers = computed(() => {
      return allUsers.value.filter(user => {
        const matchesKeyword = !searchKeyword.value || 
          user.username.toLowerCase().includes(searchKeyword.value.toLowerCase());
        const matchesIdentity = !filterIdentity.value || 
          user.identity === filterIdentity.value;
        return matchesKeyword && matchesIdentity;
      });
    });

    // 获取用户列表
    const fetchUsers = async () => {
      loading.value = true;
      error.value = '';
      try {
        const response = await users.getList();
        allUsers.value = response.data || [];
      } catch (err) {
        error.value = err.message || '获取用户列表失败';
        console.error('获取用户列表失败:', err);
      } finally {
        loading.value = false;
      }
    };

    // 处理搜索
    const handleSearch = () => {
      // 搜索逻辑由computed属性自动处理
    };

    // 处理筛选
    const handleFilter = () => {
      // 筛选逻辑由computed属性自动处理
    };

    // 检查是否为当前登录用户
    const isCurrentUser = (username) => {
      // 从localStorage获取当前用户信息
      const userInfo = localStorage.getItem('userInfo');
      if (userInfo) {
        const currentUser = JSON.parse(userInfo);
        return currentUser.username === username;
      }
      return false;
    };

    // 删除用户
    const deleteUser = async (user) => {
      if (isCurrentUser(user.username)) {
        alert('不能删除当前登录的用户');
        return;
      }

      if (!confirm(`确定要删除用户 ${user.username} 吗？`)) {
        return;
      }

      try {
        await users.delete(user.username);
        // 从列表中移除删除的用户
        allUsers.value = allUsers.value.filter(u => u.username !== user.username);
        alert('用户删除成功');
      } catch (err) {
        alert(err.message || '删除用户失败');
      }
    };

    // 关闭添加用户对话框
    const closeAddUserDialog = () => {
      showAddUserDialog.value = false;
      resetNewUserForm();
    };

    // 重置添加用户表单
    const resetNewUserForm = () => {
      newUser.value = {
        username: '',
        password: '',
        identity: 'student'
      };
      dialogError.value = '';
    };

    // 提交添加用户表单
    const submitAddUser = async () => {
      // 简单验证
      if (!newUser.value.username.trim()) {
        dialogError.value = '请输入用户名';
        return;
      }
      if (!newUser.value.password.trim()) {
        dialogError.value = '请输入密码';
        return;
      }

      dialogLoading.value = true;
      dialogError.value = '';

      try {
        await users.add(newUser.value);
        // 重新获取用户列表
        await fetchUsers();
        closeAddUserDialog();
        alert('用户添加成功');
      } catch (err) {
        dialogError.value = err.message || '添加用户失败';
      } finally {
        dialogLoading.value = false;
      }
    };

    // 组件挂载时获取用户列表
    onMounted(() => {
      fetchUsers();
    });

    return {
      allUsers,
      filteredUsers,
      loading,
      error,
      searchKeyword,
      filterIdentity,
      showAddUserDialog,
      newUser,
      dialogLoading,
      dialogError,
      handleSearch,
      handleFilter,
      isCurrentUser,
      deleteUser,
      closeAddUserDialog,
      submitAddUser
    };
  }
};
</script>

<style scoped>
.admin-user-management {
  width: 100%;
}

.add-user-section {
  margin-bottom: 16px;
  text-align: right;
}

.search-filter {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
}

.search-filter .form-control:first-child {
  flex: 1;
}

.search-filter .form-control:last-child {
  width: 150px;
}

.table-container {
  overflow-x: auto;
}

.table {
  width: 100%;
}

.table th,
.table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #ebeef5;
}

.table th {
  background-color: #f5f7fa;
  font-weight: 500;
}

.table tbody tr:hover {
  background-color: #f5f7fa;
}

.no-data {
  text-align: center;
  color: #909399;
  padding: 40px;
}

.identity-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.identity-admin {
  background-color: #e6f7ff;
  color: #1890ff;
}

.identity-student {
  background-color: #f6ffed;
  color: #52c41a;
}

.status-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.status-active {
  background-color: #f6ffed;
  color: #52c41a;
}

.status-disabled {
  background-color: #fff2e8;
  color: #fa8c16;
}

.btn-sm {
  padding: 4px 12px;
  font-size: 12px;
}

/* 对话框样式 */
.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.dialog {
  background-color: #fff;
  border-radius: 8px;
  width: 90%;
  max-width: 500px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #ebeef5;
}

.dialog-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 500;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  color: #909399;
  cursor: pointer;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  color: #606266;
}

.dialog-body {
  padding: 20px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px;
  border-top: 1px solid #ebeef5;
}

@media (max-width: 768px) {
  .search-filter {
    flex-direction: column;
  }
  
  .search-filter .form-control:last-child {
    width: 100%;
  }
  
  .dialog {
    width: 95%;
    margin: 20px;
  }
  
  .dialog-footer {
    flex-direction: column-reverse;
  }
  
  .dialog-footer .btn {
    width: 100%;
  }
}
</style>