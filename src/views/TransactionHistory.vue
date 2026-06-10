<template>
  <div class="page-container">
    <Navbar />
    <div class="container mt-4">
      <div class="d-flex justify-content-between align-items-center flex-wrap gap-2 mb-3">
        <h2 class="mb-0"><i class="fa fa-list-alt text-success"></i> 交易记录</h2>
        <a href="/api/orders/export" class="btn btn-outline-success btn-sm" download><i class="fa fa-download"></i> 导出 CSV</a>
      </div>
      <div class="d-flex flex-wrap gap-2 mb-4">
        <div class="btn-group">
          <button v-for="f in filters" :key="f.k" type="button" class="btn btn-sm" :class="filter === f.k ? 'btn-success' : 'btn-outline-success'" @click="filter = f.k">{{ f.l }}</button>
        </div>
        <div class="btn-group me-2">
          <button v-for="t in typeFilters" :key="t.k" type="button" class="btn btn-sm" :class="typeFilter === t.k ? 'btn-info' : 'btn-outline-info'" @click="typeFilter = t.k">{{ t.l }}</button>
        </div>
        <div class="btn-group">
          <button v-for="s in statusFilters" :key="s.k" type="button" class="btn btn-sm" :class="statusFilter === s.k ? 'btn-secondary' : 'btn-outline-secondary'" @click="statusFilter = s.k">{{ s.l }}</button>
        </div>
      </div>
      <div v-if="loading" class="text-center py-5"><div class="spinner-border text-success"></div></div>
      <div v-else-if="!shown.length" class="alert alert-info">暂无交易记录</div>
      <div v-else>
        <div v-for="o in shown" :key="o.id" class="card order-card mb-3 p-3">
          <div class="d-flex justify-content-between flex-wrap gap-2">
            <div>
              <h5 class="mb-1">{{ o.book_title }}
                <span v-if="o.order_type === 'exchange'" class="badge bg-info ms-1">换书</span>
              </h5>
              <p v-if="o.order_type === 'exchange'" class="text-muted mb-1 small">交换：{{ o.exchange_book_title }}</p>
              <p v-else class="text-success mb-1">¥{{ formatPrice(o.price) }}</p>
              <small class="text-muted">{{ o.created_at }}</small>
              <span class="badge ms-2" :class="statusBadge(o.status)">{{ getOrderStatusText(o.status) }}</span>
              <p v-if="o.cancel_reason" class="small text-danger mb-0 mt-1">取消：{{ o.cancel_reason }}</p>
            </div>
            <div class="d-flex flex-column gap-1 align-items-end">
              <span class="small text-muted">{{ roleLabel(o) }}</span>
              <router-link :to="`/order/${o.id}`" class="btn btn-sm btn-outline-primary">订单详情</router-link>
              <button v-if="canPickup(o)" class="btn btn-sm btn-warning" @click="setStatus(o.id, 'pickup')">确认约定面交</button>
              <button v-if="canComplete(o)" class="btn btn-sm btn-success" @click="setStatus(o.id, 'completed')">确认面交完成</button>
              <button v-if="canCancel(o)" class="btn btn-sm btn-outline-danger" @click="setStatus(o.id, 'cancelled')">取消订单</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
// 交易记录：买/卖/类型/状态筛选 + 快捷改状态
import { ref, computed, onMounted } from 'vue'
import Navbar from '@/components/Navbar.vue'
import { orderAPI } from '@/utils/api'
import { getCurrentUser } from '@/utils/auth'
import { formatPrice, getOrderStatusText } from '@/utils/helpers'
import { useToast } from '@/composables/useToast'

const { show } = useToast()
const user = getCurrentUser()
const filters = [{ k: 'all', l: '全部' }, { k: 'buy', l: '我买到的' }, { k: 'sell', l: '我卖出的' }]
const filter = ref('all')
const statusFilter = ref('all')
const orders = ref([])
const loading = ref(false)
const typeFilter = ref('all')
const typeFilters = [{ k: 'all', l: '全部类型' }, { k: 'sale', l: '购买' }, { k: 'exchange', l: '换书' }]
const statusFilters = [
  { k: 'all', l: '全部状态' },
  { k: 'pending', l: '待面交' },
  { k: 'pickup', l: '已约面交' },
  { k: 'completed', l: '已完成' },
  { k: 'cancelled', l: '已取消' }
]

const shown = computed(() => {
  // 前端多维过滤（数据来自 /api/orders）
  const uid = String(user?.id || '')
  let list = orders.value
  if (filter.value === 'buy') list = list.filter(o => String(o.buyer_id) === uid)
  if (filter.value === 'sell') list = list.filter(o => String(o.seller_id) === uid)
  if (statusFilter.value !== 'all') list = list.filter(o => o.status === statusFilter.value)
  if (typeFilter.value !== 'all') list = list.filter(o => (o.order_type || 'sale') === typeFilter.value)
  return list
})

function statusBadge(s) {
  return { pending: 'bg-warning text-dark', pickup: 'bg-info', completed: 'bg-success', cancelled: 'bg-secondary' }[s] || 'bg-secondary'
}

function roleLabel(o) {
  const uid = String(user?.id || '')
  if (String(o.buyer_id) === uid) return '买入'
  if (String(o.seller_id) === uid) return '卖出'
  return ''
}

function canPickup(o) {
  return o.status === 'pending' && String(o.seller_id) === String(user?.id)
}
function canComplete(o) {
  return o.status === 'pickup' && String(o.buyer_id) === String(user?.id)
}
function canCancel(o) {
  return o.status === 'pending' && (String(o.buyer_id) === String(user?.id) || String(o.seller_id) === String(user?.id))
}

async function load() {
  loading.value = true
  try {
    const res = await orderAPI.getOrders()
    if (res.status === 'success') orders.value = res.orders || []
  } finally {
    loading.value = false
  }
}

async function setStatus(id, status) {
  const res = await orderAPI.updateStatus(id, { status })
  if (res.status === 'success') { show('状态已更新', 'success'); load() }
  else show(res.message || '操作失败', 'error')
}

onMounted(load)
</script>

<style scoped>
.order-card { border-left: 4px solid #28a745; }
</style>
