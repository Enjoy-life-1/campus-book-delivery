<template>
  <div class="page-container">
    <Navbar />
    <div class="container mt-4">
      <h2 class="mb-3"><i class="fa fa-handshake-o text-success"></i> 议价管理</h2>
      <ul class="nav nav-tabs mb-3">
        <li class="nav-item"><a class="nav-link" :class="{ active: tab==='seller' }" href="#" @click.prevent="tab='seller';load()">收到的报价</a></li>
        <li class="nav-item"><a class="nav-link" :class="{ active: tab==='buyer' }" href="#" @click.prevent="tab='buyer';load()">我的报价</a></li>
      </ul>
      <div v-if="loading" class="text-center py-5"><div class="spinner-border text-success"></div></div>
      <div v-else-if="!offers.length" class="text-muted text-center py-4">暂无记录</div>
      <div v-else class="list-group">
        <div v-for="o in offers" :key="o.id" class="list-group-item">
          <div class="d-flex justify-content-between flex-wrap">
            <div>
              <router-link :to="`/book/${o.book_id}`" class="fw-bold">{{ o.book_title }}</router-link>
              <p class="mb-0 small">标价 ¥{{ o.list_price }} → 报价 <span class="text-success">¥{{ o.offer_price }}</span></p>
              <p v-if="o.message" class="small text-muted">{{ o.message }}</p>
              <p class="small">{{ tab==='seller' ? '买家' : '卖家' }}：{{ tab==='seller' ? o.buyer_name : '' }} · {{ o.created_at }}</p>
            </div>
            <div class="text-end">
              <span class="badge" :class="statusClass(o.status)">{{ statusText(o.status) }}</span>
              <div v-if="tab==='seller' && o.status==='pending'" class="mt-2">
                <button type="button" class="btn btn-sm btn-success me-1" @click="respond(o.id,'accept')">接受</button>
                <button type="button" class="btn btn-sm btn-outline-secondary me-1" @click="respond(o.id,'reject')">拒绝</button>
              </div>
              <router-link v-if="o.status==='accepted'" to="/transactionHistory" class="btn btn-sm btn-outline-primary mt-2">交易记录</router-link>
              <button v-if="tab==='buyer' && o.status==='pending'" type="button" class="btn btn-sm btn-outline-success mt-2" @click="contact(o)">联系卖家</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
// 议价：卖家 accept/reject 生成订单；买家联系卖家
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import Navbar from '@/components/Navbar.vue'
import { offerAPI, messageAPI } from '@/utils/api'
import { useToast } from '@/composables/useToast'

const router = useRouter()
const { show } = useToast()
const tab = ref('seller')
const offers = ref([])
const loading = ref(false)

function statusText(s) {
  return { pending: '待处理', accepted: '已接受', rejected: '已拒绝', cancelled: '已失效' }[s] || s
}
function statusClass(s) {
  return { pending: 'bg-warning text-dark', accepted: 'bg-success', rejected: 'bg-secondary', cancelled: 'bg-light text-dark' }[s] || 'bg-secondary'
}

async function load() {
  loading.value = true
  try {
    const res = await offerAPI.list({ role: tab.value })
    if (res.status === 'success') offers.value = res.offers || []
  } finally { loading.value = false }
}

async function respond(id, action) {
  // accept → 创建订单并跳转 OrderDetail
  const res = await offerAPI.respond(id, { action })
  if (res.status === 'success') {
    show(action === 'accept' ? '已接受并生成订单' : '已拒绝', 'success')
    if (action === 'accept' && res.order?.id) {
      router.push(`/order/${res.order.id}`)
      return
    }
    load()
  } else show(res.message, 'danger')
}

async function contact(o) {
  try {
    const res = await messageAPI.startConversation({ peer_id: o.seller_id, book_id: o.book_id })
    if (res.status === 'success') router.push({ name: 'Messages', query: { conv: res.conversation.id } })
  } catch (e) { show(e.message, 'danger') }
}

onMounted(load)
</script>
