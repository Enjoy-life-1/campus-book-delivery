<template>
  <AdminLayout title="数据分析" :show-refresh="true" @refresh="load">
    <div class="page-header">
      <h2>数据统计</h2>
    </div>
    <div v-if="stats" class="stats-cards">
      <div v-for="s in statCards" :key="s.label" class="stat-card">
        <div class="stat-icon" :class="s.iconClass">
          <i :class="['fa', s.icon]"></i>
        </div>
        <div class="stat-info">
          <h3>{{ s.value }}</h3>
          <p>{{ s.label }}</p>
        </div>
      </div>
    </div>
    <div class="row g-4">
      <div class="col-md-6">
        <div class="admin-panel">
          <div class="admin-panel-title">书籍分类分布</div>
          <div v-for="(cnt, cat) in categoryStats" :key="cat" class="mb-2">
            <div class="d-flex justify-content-between small mb-1">
              <span>{{ getCategoryName(cat) }}</span><span>{{ cnt }}</span>
            </div>
            <div class="progress" style="height:8px">
              <div class="progress-bar bg-success" :style="{ width: barPct(cnt) }"></div>
            </div>
          </div>
          <p v-if="!Object.keys(categoryStats).length" class="text-muted mb-0 mt-2">暂无数据</p>
        </div>
      </div>
      <div class="col-md-6">
        <div class="admin-panel">
          <div class="admin-panel-title">待审核书籍 <span class="badge bg-warning text-dark">{{ pendingBooks }}</span></div>
          <router-link to="/admin/bookManagement" class="btn btn-sm btn-outline-success">去审核</router-link>
        </div>
      </div>
      <div v-if="eco" class="col-12">
        <div class="admin-panel">
          <div class="admin-panel-title">教材流转 / 环保统计</div>
          <div class="row g-3 text-center">
            <div class="col-md-2"><h4 class="text-success mb-0">{{ eco.completed_orders }}</h4><small class="text-muted">完成订单</small></div>
            <div class="col-md-2"><h4 class="text-success mb-0">{{ eco.sold_listings }}</h4><small class="text-muted">已售书籍</small></div>
            <div class="col-md-2"><h4 class="text-success mb-0">{{ eco.distinct_isbn }}</h4><small class="text-muted">流通ISBN</small></div>
            <div class="col-md-3"><h4 class="text-success mb-0">{{ eco.estimated_paper_saved_kg }} kg</h4><small class="text-muted">估算节约纸张</small></div>
            <div class="col-md-3"><h4 class="text-success mb-0">{{ eco.co2_saved_kg }} kg</h4><small class="text-muted">估算减碳</small></div>
          </div>
        </div>
      </div>
    </div>
  </AdminLayout>
</template>

<script setup>
// 数据分析：stats + 生态指标图表
import { ref, computed, onMounted } from 'vue'
import AdminLayout from '@/components/admin/AdminLayout.vue'
import { adminAPI, bookAPI } from '@/utils/api'
import { getCategoryName } from '@/utils/helpers'

const stats = ref(null)
const categoryStats = ref({})
const pendingBooks = ref(0)
const eco = ref(null)

const maxCat = computed(() => Math.max(1, ...Object.values(categoryStats.value)))

function barPct(cnt) {
  return `${Math.round((cnt / maxCat.value) * 100)}%`
}

const statCards = computed(() => {
  if (!stats.value) return []
  return [
    { label: '书籍总数', value: stats.value.totalBooks, icon: 'fa-book', iconClass: 'primary' },
    { label: '注册用户', value: stats.value.registeredUsers, icon: 'fa-user-check', iconClass: 'success' },
    { label: '认证用户', value: stats.value.verifiedUsers ?? 0, icon: 'fa-id-card', iconClass: 'success' },
    { label: '换书订单', value: stats.value.exchangeOrders ?? 0, icon: 'fa-exchange', iconClass: 'warning' },
    { label: '待审评论', value: stats.value.pendingComments ?? 0, icon: 'fa-comment', iconClass: 'info' },
    { label: '待处理举报', value: stats.value.pendingReports ?? 0, icon: 'fa-flag', iconClass: 'danger' },
    { label: '本月订单', value: stats.value.monthlySales, icon: 'fa-line-chart', iconClass: 'warning' },
    { label: '待处理订单', value: stats.value.pendingTasks, icon: 'fa-clock-o', iconClass: 'danger' }
  ]
})

async function load() {
  const [st, booksRes, ecoRes] = await Promise.all([
    adminAPI.getStats(),
    bookAPI.getBooks({ page_size: 5000, include_sold: true }),
    adminAPI.getEcoStats().catch(() => null)
  ])
  if (st.status === 'success') stats.value = st.stats
  if (ecoRes?.status === 'success') eco.value = ecoRes.stats
  const books = booksRes.books || []
  pendingBooks.value = books.filter(b => b.status === 'pending').length
  const map = {}
  books.forEach(b => {
    const c = b.category || 'other'
    map[c] = (map[c] || 0) + 1
  })
  categoryStats.value = map
}

onMounted(load)
</script>
