<template>
  <AdminLayout title="订单管理" :show-refresh="true" @refresh="load">
    <div class="page-header d-flex justify-content-between align-items-center flex-wrap gap-2">
      <h2>订单管理</h2>
      <a href="/api/admin/export/orders" class="btn btn-outline-success btn-sm" download><i class="fa fa-download me-1"></i>导出 CSV</a>
    </div>
    <div class="admin-panel mb-3">
      <ul class="nav nav-pills gap-1 flex-wrap">
        <li v-for="t in statusTabs" :key="t.k" class="nav-item">
          <button
            type="button"
            class="nav-link"
            :class="{ active: statusFilter === t.k }"
            @click="setStatus(t.k)"
          >
            {{ t.l }}<span v-if="t.count != null" class="ms-1 badge rounded-pill" :class="statusFilter === t.k ? 'bg-light text-dark' : 'bg-secondary'">{{ t.count }}</span>
          </button>
        </li>
      </ul>
    </div>
    <div class="admin-panel">
      <div class="data-table">
        <table>
          <thead>
            <tr><th>订单号</th><th>类型</th><th>书籍</th><th>买家</th><th>卖家</th><th>金额</th><th>状态</th><th>时间</th></tr>
          </thead>
          <tbody>
            <tr v-for="o in shown" :key="o.id">
              <td><router-link :to="`/order/${o.id}`">{{ o.id.slice(-8) }}</router-link></td>
              <td>{{ o.order_type === 'exchange' ? '换书' : '购买' }}</td>
              <td>{{ o.book_title }}</td>
              <td>{{ o.buyer_name }}</td>
              <td>{{ o.seller_name }}</td>
              <td>{{ o.order_type === 'exchange' ? '—' : '¥' + formatPrice(o.price) }}</td>
              <td><span class="badge" :class="statusBadge(o.status)">{{ getOrderStatusText(o.status) }}</span></td>
              <td>{{ o.created_at }}</td>
            </tr>
          </tbody>
        </table>
        <div v-if="!shown.length" class="p-4 text-center text-muted">
          {{ statusFilter === 'all' ? '暂无订单' : `暂无「${currentTabLabel}」订单` }}
        </div>
      </div>
    </div>
  </AdminLayout>
</template>

<script setup>
// 全站订单列表 + 状态筛选 + CSV 导出链接
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AdminLayout from '@/components/admin/AdminLayout.vue'
import { adminAPI } from '@/utils/api'
import { formatPrice, getOrderStatusText } from '@/utils/helpers'

const route = useRoute()
const router = useRouter()
const orders = ref([])
const statusFilter = ref('all')

const statusDefs = [
  { k: 'all', l: '全部' },
  { k: 'pending', l: '待确认' },
  { k: 'pickup', l: '已约面交' },
  { k: 'completed', l: '已完成' },
  { k: 'cancelled', l: '已取消' }
]

const statusTabs = computed(() =>
  statusDefs.map(t => ({
    ...t,
    count: t.k === 'all' ? orders.value.length : orders.value.filter(o => o.status === t.k).length
  }))
)

const shown = computed(() => {
  if (statusFilter.value === 'all') return orders.value
  return orders.value.filter(o => o.status === statusFilter.value)
})

const currentTabLabel = computed(() => statusDefs.find(t => t.k === statusFilter.value)?.l || '')

function statusBadge(s) {
  return { pending: 'bg-warning text-dark', pickup: 'bg-info', completed: 'bg-success', cancelled: 'bg-secondary' }[s] || 'bg-secondary'
}

function setStatus(k) {
  statusFilter.value = k
  router.replace({ query: k === 'all' ? {} : { status: k } })
}

function syncFromRoute() {
  const s = route.query.status
  statusFilter.value = statusDefs.some(t => t.k === s) ? s : 'all'
}

async function load() {
  const res = await adminAPI.getOrders()
  if (res.status === 'success') orders.value = (res.orders || []).slice().reverse()
}

watch(() => route.query.status, syncFromRoute)

onMounted(async () => {
  syncFromRoute()
  await load()
})
</script>
