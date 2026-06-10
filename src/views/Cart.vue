<template>
  <div class="page-container">
    <Navbar />
    <div class="container mt-4">
      <h2 class="mb-4"><i class="fa fa-shopping-cart text-success"></i> 购物车</h2>
      <LoadError v-if="error" :message="error" @retry="load" />
      <PageLoader v-else-if="loading" />
      <EmptyState v-else-if="!items.length" icon="fa-shopping-cart" title="购物车是空的">
        <router-link to="/booksList" class="btn btn-success">去逛逛</router-link>
      </EmptyState>
      <template v-else-if="!error">
        <div v-for="group in sellerGroups" :key="group.sellerId" class="card mb-4">
          <div class="card-header bg-light d-flex justify-content-between align-items-center">
            <span><i class="fa fa-user text-success"></i> 卖家：{{ group.sellerName }}</span>
            <span class="text-success">小计 ¥{{ formatPrice(group.total) }}</span>
          </div>
          <div class="card-body p-0">
            <div v-for="item in group.items" :key="item.id" class="cart-item p-3 border-bottom">
              <div class="d-flex align-items-center gap-3">
                <input type="checkbox" class="form-check-input" :checked="checkedIds.has(item.id)" @change="toggleItem(item.id)">
                <router-link :to="`/book/${item.book_id}`">
                  <img :src="item.book?.cover_url || 'https://picsum.photos/id/24/80/100'" class="cart-thumb" alt="">
                </router-link>
                <div class="flex-grow-1">
                  <h6 class="mb-1">{{ item.book?.title }}</h6>
                  <p class="text-success mb-0">¥{{ formatPrice(item.book?.price) }}</p>
                  <p v-if="item.book?.status !== 'available'" class="small text-danger mb-0">不可购买</p>
                </div>
                <div class="qty-control d-flex align-items-center gap-2">
                  <button class="btn btn-sm btn-outline-secondary" @click="changeQty(item, -1)" :disabled="item.quantity <= 1">-</button>
                  <span>{{ item.quantity }}</span>
                  <button class="btn btn-sm btn-outline-secondary" @click="changeQty(item, 1)">+</button>
                </div>
                <button class="btn btn-sm btn-outline-danger" @click="remove(item.id)"><i class="fa fa-trash"></i></button>
              </div>
            </div>
          </div>
          <div class="card-footer d-flex flex-wrap gap-2 justify-content-end">
            <button class="btn btn-outline-success btn-sm" :disabled="!selectedInGroup(group).length || checkingOut" @click="checkoutGroup(group)">
              仅下单（{{ selectedInGroup(group).length }}件）
            </button>
            <button class="btn btn-success btn-sm" :disabled="!selectedInGroup(group).length || checkingOut" @click="openBatchAppt(group)">
              合单下单并预约面交
            </button>
          </div>
        </div>
        <div class="card p-4 checkout-bar">
          <div class="d-flex justify-content-between align-items-center flex-wrap gap-3">
            <div>
              <span class="text-muted">共 {{ items.length }} 件</span>
              <h4 class="text-success mb-0 mt-1">合计：¥{{ formatPrice(total) }}</h4>
            </div>
            <div class="d-flex gap-2">
              <button class="btn btn-outline-secondary" @click="clearAll">清空</button>
              <button class="btn btn-success btn-lg" :disabled="checkingOut" @click="checkoutAll">
                {{ checkingOut ? '处理中...' : '全部结算' }}
              </button>
            </div>
          </div>
        </div>
      </template>
    </div>

    <div v-if="apptModal" class="modal d-block" tabindex="-1" style="background:rgba(0,0,0,.5)">
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
            <h5>合单面交预约 · {{ apptModal.sellerName }}</h5>
            <button type="button" class="btn-close" @click="apptModal = null"></button>
          </div>
          <div class="modal-body">
            <p class="small text-muted">将创建 {{ selectedInGroup(apptModal).length }} 笔订单并发送统一面交预约</p>
            <label class="form-label">面交地点</label>
            <select v-model="apptForm.place" class="form-select mb-2">
              <option value="">选择或自定义</option>
              <option v-for="s in spots" :key="s.id" :value="s.name">{{ s.name }}（{{ s.zone }}）</option>
            </select>
            <input v-model="apptForm.place" class="form-control mb-2" placeholder="或输入地点">
            <label class="form-label">面交时间</label>
            <input v-model="apptForm.meeting_time" type="datetime-local" class="form-control mb-2">
            <input v-model="apptForm.note" class="form-control" placeholder="备注（选填）">
          </div>
          <div class="modal-footer">
            <button class="btn btn-success" :disabled="checkingOut" @click="submitBatchAppt">确认</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
// 购物车：按卖家分组、合单结算、批量面交预约
import { ref, computed, onMounted, reactive } from 'vue'
import { useRouter } from 'vue-router'
import Navbar from '@/components/Navbar.vue'
import PageLoader from '@/components/PageLoader.vue'
import EmptyState from '@/components/EmptyState.vue'
import LoadError from '@/components/LoadError.vue'
import { cartAPI, campusAPI } from '@/utils/api'
import { formatPrice } from '@/utils/helpers'
import { useToast } from '@/composables/useToast'
import { useAsync } from '@/composables/useAsync'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const { show } = useToast()
const userStore = useUserStore()
const items = ref([])
const { loading, error, run } = useAsync()
const checkingOut = ref(false)
const spots = ref([])
const apptModal = ref(null)
const apptForm = reactive({ place: '', meeting_time: '', note: '' })
const checkedIds = ref(new Set())

function syncChecked() {
  const s = new Set()
  for (const item of items.value) {
    if (item.book?.status === 'available') s.add(item.id)
  }
  checkedIds.value = s
}

function toggleItem(id) {
  const s = new Set(checkedIds.value)
  if (s.has(id)) s.delete(id)
  else s.add(id)
  checkedIds.value = s
}

function selectedInGroup(group) {
  return group.items.filter(i => checkedIds.value.has(i.id)).map(i => i.id)
}

const total = computed(() =>
  items.value.reduce((s, i) => s + (i.book?.price || 0) * (i.quantity || 1), 0)
)

const sellerGroups = computed(() => {
  // 同一卖家合并 checkout
  const map = {}
  for (const item of items.value) {
    const b = item.book
    if (!b || b.status !== 'available') continue
    const sid = b.owner_id || 'unknown'
    if (!map[sid]) {
      map[sid] = {
        sellerId: sid,
        sellerName: b.owner_name || '卖家',
        items: [],
        total: 0,
      }
    }
    map[sid].items.push(item)
    map[sid].total += (b.price || 0) * (item.quantity || 1)
  }
  return Object.values(map)
})

async function load() {
  await run(async () => {
    const res = await cartAPI.getCart()
    if (res?.status === 'success') {
      items.value = res.cart || []
      syncChecked()
      userStore.cartCount = items.value.length
      return
    }
    throw new Error(res?.message || '加载购物车失败')
  })
}

async function changeQty(item, delta) {
  const q = Math.max(1, (item.quantity || 1) + delta)
  await cartAPI.updateCartItem(item.id, { quantity: q })
  load()
}

async function remove(id) {
  await cartAPI.deleteCartItem(id)
  show('已移除', 'info')
  load()
  window.dispatchEvent(new Event('user-updated'))
}

async function clearAll() {
  if (!confirm('清空购物车？')) return
  await cartAPI.clearCart()
  load()
  window.dispatchEvent(new Event('user-updated'))
}

function openBatchAppt(group) {
  apptModal.value = group
  apptForm.place = ''
  apptForm.meeting_time = ''
  apptForm.note = ''
}

async function checkoutGroup(group) {
  const ids = selectedInGroup(group)
  if (!ids.length) return show('请勾选商品', 'warning')
  if (!confirm(`向 ${group.sellerName} 下单 ${ids.length} 件？`)) return
  checkingOut.value = true
  try {
    const res = await cartAPI.checkoutSeller({
      seller_id: group.sellerId,
      cart_item_ids: ids
    })
      if (res.status === 'success') {
        show(res.message, 'success')
        window.dispatchEvent(new Event('user-updated'))
        router.push('/transactionHistory')
      }
  } catch (e) {
    show(e.message || '失败', 'error')
  } finally {
    checkingOut.value = false
  }
}

async function submitBatchAppt() {
  // checkoutSeller + place/meeting_time → 跳转私信
  const g = apptModal.value
  if (!g) return
  const mt = apptForm.meeting_time.replace('T', ' ')
  if (!apptForm.place.trim() || !mt) return show('请填写地点和时间', 'warning')
  checkingOut.value = true
  try {
    const res = await cartAPI.checkoutSeller({
      seller_id: g.sellerId,
      cart_item_ids: selectedInGroup(g),
      place: apptForm.place.trim(),
      meeting_time: mt.length === 16 ? mt + ':00' : mt,
      note: apptForm.note
    })
    if (res.status === 'success') {
      show(res.message, 'success')
      apptModal.value = null
      window.dispatchEvent(new Event('user-updated'))
      if (res.conversation_id) {
        router.push({ name: 'Messages', query: { conv: res.conversation_id } })
      } else {
        router.push('/transactionHistory')
      }
    }
  } catch (e) {
    show(e.message || '失败', 'error')
  } finally {
    checkingOut.value = false
  }
}

async function checkoutAll() {
  const groups = sellerGroups.value
  if (!groups.length) return show('没有可结算的商品', 'warning')
  if (!confirm(`按卖家分 ${groups.length} 组全部下单？`)) return
  checkingOut.value = true
  let ok = 0
  try {
    for (const g of groups) {
      if (!selectedInGroup(g).length) continue
      try {
        const res = await cartAPI.checkoutSeller({
          seller_id: g.sellerId,
          cart_item_ids: selectedInGroup(g)
        })
        if (res.status === 'success') ok += res.orders?.length || selectedInGroup(g).length
      } catch (_) {}
    }
    show(ok ? `成功 ${ok} 笔订单` : '结算失败', ok ? 'success' : 'error')
    window.dispatchEvent(new Event('user-updated'))
    if (ok) router.push('/transactionHistory')
    else load()
  } finally {
    checkingOut.value = false
  }
}

onMounted(async () => {
  const sr = await campusAPI.getSpots().catch(() => null)
  if (sr?.status === 'success') spots.value = sr.spots || []
  load()
})
</script>

<style scoped>
.cart-thumb { width: 72px; height: 90px; object-fit: cover; border-radius: 6px; }
.checkout-bar { position: sticky; bottom: 16px; background: #fff; }
</style>
