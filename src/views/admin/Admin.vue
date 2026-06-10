<template>
  <AdminLayout title="管理员控制台" :show-refresh="true" @refresh="load">
    <div class="stats-cards">
      <router-link v-for="s in statCards" :key="s.label" :to="s.to" class="stat-card stat-card-link d-flex align-items-center text-decoration-none text-body">
        <div class="stat-icon" :class="s.iconClass">
          <i :class="['fa', s.icon]"></i>
        </div>
        <div class="stat-info">
          <h3>{{ s.value }}</h3>
          <p>{{ s.label }}</p>
        </div>
      </router-link>
    </div>

    <div class="row g-4">
      <div class="col-lg-8">
        <div class="admin-panel">
          <div class="admin-panel-title"><i class="fa fa-th-large me-2"></i>快捷管理</div>
          <div class="row g-3">
            <div v-for="item in menus" :key="item.to" class="col-md-6">
              <router-link :to="item.to" class="admin-quick-card">
                <i :class="['fa', item.icon]"></i>
                <div>
                  <strong>{{ item.title }}</strong>
                  <p>{{ item.desc }}</p>
                </div>
              </router-link>
            </div>
          </div>
        </div>
      </div>
      <div class="col-lg-4">
        <div class="admin-panel">
          <div class="admin-panel-title"><i class="fa fa-bell me-2"></i>待办提醒</div>
          <ul class="admin-todo-list">
            <li>
              <span>待审核书籍</span>
              <router-link to="/admin/bookManagement" class="badge bg-warning text-dark">{{ pendingBooks }}</router-link>
            </li>
            <li>
              <span>待处理订单</span>
              <router-link to="/admin/orders?status=pending" class="badge bg-danger">{{ stats?.pendingTasks ?? 0 }}</router-link>
            </li>
            <li>
              <span>待审评论</span>
              <router-link to="/admin/comments" class="badge bg-info">{{ pendingComments }}</router-link>
            </li>
            <li>
              <span>待处理举报</span>
              <router-link to="/admin/comments" class="badge bg-secondary">{{ pendingReports }}</router-link>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </AdminLayout>
</template>

<script setup>
// 管理后台首页：/api/admin/stats + 待办计数
import { ref, computed, onMounted } from 'vue'
import AdminLayout from '@/components/admin/AdminLayout.vue'
import { adminAPI, bookAPI } from '@/utils/api'

const stats = ref(null)
const pendingBooks = ref(0)
const pendingComments = ref(0)
const pendingReports = ref(0)

const menus = [
  { to: '/admin/bookManagement', title: '书籍审核', desc: '待审书籍通过/驳回', icon: 'fa-book' },
  { to: '/admin/userManagement', title: '用户管理', desc: '增删改用户与角色', icon: 'fa-users' },
  { to: '/admin/orders', title: '订单管理', desc: '全站交易订单', icon: 'fa-list-alt' },
  { to: '/admin/analytics', title: '数据分析', desc: '分类与运营统计', icon: 'fa-bar-chart' },
  { to: '/admin/comments', title: '评论审核', desc: '评论与举报处理', icon: 'fa-check-square-o' },
  { to: '/admin/campus', title: '校园数据', desc: '面交点/课程/多校', icon: 'fa-map-marker' },
  { to: '/admin/settings', title: '系统设置', desc: '公告、推送与 ISBN Key', icon: 'fa-cog' }
]

const statCards = computed(() => [
  { label: '书籍数量', value: stats.value?.totalBooks ?? '-', icon: 'fa-book', iconClass: 'primary', to: '/admin/bookManagement' },
  { label: '注册用户', value: stats.value?.registeredUsers ?? '-', icon: 'fa-user-check', iconClass: 'success', to: '/admin/userManagement' },
  { label: '认证用户', value: stats.value?.verifiedUsers ?? '-', icon: 'fa-id-card', iconClass: 'success', to: '/admin/userManagement' },
  { label: '换书订单', value: stats.value?.exchangeOrders ?? '-', icon: 'fa-exchange', iconClass: 'warning', to: '/admin/orders' },
  { label: '本月销量', value: stats.value?.monthlySales ?? '-', icon: 'fa-line-chart', iconClass: 'warning', to: '/admin/orders' },
  { label: '待处理订单', value: stats.value?.pendingTasks ?? '-', icon: 'fa-clock-o', iconClass: 'danger', to: '/admin/orders?status=pending' }
])

async function load() {
  // 并行拉统计、待审书、待审评论、待处理举报
  const [st, booksRes, pc, pr] = await Promise.all([
    adminAPI.getStats(),
    bookAPI.getBooks({ page_size: 500, include_sold: true }),
    adminAPI.getPendingComments(),
    adminAPI.getReports({ status: 'pending' })
  ])
  if (st.status === 'success') stats.value = st.stats
  pendingBooks.value = (booksRes.books || []).filter(b => b.status === 'pending').length
  if (pc.status === 'success') pendingComments.value = (pc.comments || []).length
  if (pr.status === 'success') pendingReports.value = (pr.reports || []).length
}

onMounted(load)
</script>

<style scoped>
.admin-quick-card {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px;
  border: 1px solid #e8e8e8;
  border-radius: 10px;
  text-decoration: none;
  color: inherit;
  transition: all 0.2s;
}
.admin-quick-card:hover {
  border-color: #007f73;
  box-shadow: 0 4px 12px rgba(0, 127, 115, 0.12);
  transform: translateY(-2px);
}
.admin-quick-card i {
  font-size: 1.5rem;
  color: #007f73;
  margin-top: 2px;
}
.admin-quick-card p {
  margin: 4px 0 0;
  font-size: 0.85rem;
  color: #6c757d;
}
.admin-todo-list {
  list-style: none;
  padding: 0;
  margin: 0;
}
.admin-todo-list li {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px dashed #eee;
}
</style>
