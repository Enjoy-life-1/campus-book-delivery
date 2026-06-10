<template>
  <div class="page-container">
    <Navbar />
    <div class="container mt-4">
      <div v-if="loading" class="text-center py-5"><div class="spinner-border text-success"></div></div>
      <div v-else-if="order" class="row g-4">
        <div class="col-lg-8">
          <div class="card p-4">
            <h4>订单详情 <small class="text-muted">#{{ order.id }}</small></h4>
            <hr>
            <p><strong>书籍：</strong>{{ order.book_title }}</p>
            <p v-if="order.order_type === 'exchange'"><strong>类型：</strong><span class="badge bg-info">换书</span></p>
            <p v-if="order.order_type === 'exchange'"><strong>交换书目：</strong>{{ order.exchange_book_title }}</p>
            <p v-if="order.exchange_note"><strong>换书说明：</strong>{{ order.exchange_note }}</p>
            <p v-if="order.order_type !== 'exchange'"><strong>金额：</strong><span class="text-success">¥{{ formatPrice(order.price) }}</span></p>
            <p><strong>买家：</strong>{{ order.buyer_name }}</p>
            <p><strong>卖家：</strong>{{ order.seller_name }}</p>
            <p><strong>下单时间：</strong>{{ order.created_at }}</p>
            <p>
              <strong>状态：</strong>
              <span class="badge" :class="statusBadge(order.status)">{{ getOrderStatusText(order.status) }}</span>
            </p>
            <p v-if="order.cancel_reason" class="small text-danger"><strong>取消原因：</strong>{{ order.cancel_reason }}</p>
            <div class="d-flex flex-wrap gap-2 mt-3">
              <button v-if="canPickup" class="btn btn-warning btn-sm" @click="setStatus('pickup')">确认已约面交</button>
              <button v-if="canComplete" class="btn btn-success btn-sm" @click="setStatus('completed')">确认面交完成</button>
              <button v-if="canCancel" class="btn btn-outline-danger btn-sm" @click="showCancel = true">取消订单</button>
              <button class="btn btn-outline-success btn-sm" @click="openChat"><i class="fa fa-envelope"></i> 私信对方</button>
              <button v-if="order.status !== 'cancelled' && order.status !== 'completed'" class="btn btn-outline-warning btn-sm" @click="openChatAppt"><i class="fa fa-calendar"></i> 预约面交</button>
              <p class="small text-muted mt-2 mb-0">面交可在私信中选择图书馆、食堂等校内预设地点</p>
              <button v-if="order.status === 'completed'" type="button" class="btn btn-outline-secondary btn-sm" @click="openVoucher">交易凭证</button>
              <router-link v-if="book" :to="`/book/${book.id}`" class="btn btn-outline-primary btn-sm">查看书籍</router-link>
            </div>
          </div>
          <div v-if="order.status === 'completed' && !hasReview" class="card p-4 mt-4">
            <h5>交易评价</h5>
            <p class="small text-muted">四维评分：描述相符、态度、品相/履约、效率</p>
            <div class="mb-2">
              <label class="form-label small">{{ reviewLabels.desc }}</label>
              <select v-model.number="review.description_rating" class="form-select form-select-sm">
                <option v-for="n in 5" :key="'d'+n" :value="n">{{ n }} 星</option>
              </select>
            </div>
            <div class="mb-2">
              <label class="form-label small">{{ reviewLabels.attitude }}</label>
              <select v-model.number="review.service_rating" class="form-select form-select-sm">
                <option v-for="n in 5" :key="'s'+n" :value="n">{{ n }} 星</option>
              </select>
            </div>
            <div class="mb-2">
              <label class="form-label small">{{ reviewLabels.condition }}</label>
              <select v-model.number="review.condition_rating" class="form-select form-select-sm">
                <option v-for="n in 5" :key="'c'+n" :value="n">{{ n }} 星</option>
              </select>
            </div>
            <div class="mb-2">
              <label class="form-label small">{{ reviewLabels.efficiency }}</label>
              <select v-model.number="review.efficiency_rating" class="form-select form-select-sm">
                <option v-for="n in 5" :key="'e'+n" :value="n">{{ n }} 星</option>
              </select>
            </div>
            <textarea v-model="review.review_content" class="form-control mb-2" rows="3" placeholder="评价内容（选填）"></textarea>
            <button class="btn btn-success btn-sm" :disabled="submittingReview" @click="submitReview">提交评价</button>
          </div>
          <div v-if="reviews.length" class="card p-4 mt-4">
            <h5>评价记录</h5>
            <div v-for="r in reviews" :key="r.id" class="border-bottom py-2">
              <p class="mb-1">{{ r.reviewer_name }}（{{ r.reviewer_role === 'buyer' ? '买家' : '卖家' }}）</p>
              <p class="small text-muted mb-0">
                描述{{ r.description_rating ?? r.service_rating }} / 态度{{ r.service_rating }} /
                品相{{ r.condition_rating }} / 效率{{ r.efficiency_rating }}
              </p>
              <p v-if="r.review_content">{{ r.review_content }}</p>
            </div>
          </div>
        </div>
        <div v-if="book" class="col-lg-4">
          <div class="card p-3">
            <img :src="bookCover" class="img-fluid rounded mb-2" alt="">
            <h6>{{ book.title }}</h6>
            <p class="text-success mb-0">¥{{ formatPrice(book.price) }}</p>
          </div>
        </div>
      </div>
      <div v-else class="alert alert-warning">订单不存在或无权查看</div>
    </div>

    <div v-if="showCancel" class="modal d-block" tabindex="-1" style="background:rgba(0,0,0,.5)">
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header"><h5>取消订单</h5><button class="btn-close" @click="showCancel=false"></button></div>
          <div class="modal-body">
            <select v-model="cancelReason" class="form-select mb-2">
              <option value="">选择原因</option>
              <option value="不想买了">不想买了</option>
              <option value="已与卖家协商取消">已与卖家协商取消</option>
              <option value="书籍信息不符">书籍信息不符</option>
              <option value="无法按时面交">无法按时面交</option>
              <option value="其他">其他</option>
            </select>
            <input v-if="cancelReason==='其他'" v-model="cancelCustom" class="form-control" placeholder="请说明原因">
          </div>
          <div class="modal-footer">
            <button class="btn btn-danger" @click="confirmCancel">确认取消</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
// 订单详情：状态流转 pending→pickup→completed、评价、私信
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Navbar from '@/components/Navbar.vue'
import { orderAPI, bookAPI, reviewAPI, messageAPI } from '@/utils/api'
import { getCurrentUser } from '@/utils/auth'
import { formatPrice, getOrderStatusText } from '@/utils/helpers'
import { useToast } from '@/composables/useToast'

const route = useRoute()
const router = useRouter()
const { show } = useToast()
const user = getCurrentUser()
const order = ref(null)
const book = ref(null)
const reviews = ref([])
const loading = ref(true)
const submittingReview = ref(false)
const showCancel = ref(false)
const cancelReason = ref('')
const cancelCustom = ref('')
const review = ref({
  description_rating: 5,
  service_rating: 5,
  condition_rating: 5,
  efficiency_rating: 5,
  review_content: ''
})

const reviewLabels = computed(() => {
  const isBuyer = order.value && String(order.value.buyer_id) === String(user?.id)
  if (isBuyer) {
    return { desc: '描述相符', attitude: '卖家态度', condition: '书籍品相', efficiency: '交易效率' }
  }
  return { desc: '沟通/说明相符', attitude: '买家态度', condition: '履约诚信', efficiency: '交易效率' }
})

const hasReview = computed(() =>
  reviews.value.some(r => String(r.reviewer_id) === String(user?.id))
)

const bookCover = computed(() => {
  const b = book.value
  if (!b) return ''
  if (b.imgs?.length) return b.imgs[0]
  return b.cover_url || b.image || ''
})

function statusBadge(s) {
  return { pending: 'bg-warning text-dark', pickup: 'bg-info', completed: 'bg-success', cancelled: 'bg-secondary' }[s] || 'bg-secondary'
}

const canPickup = computed(() =>
  // 卖家确认已约面交
  order.value?.status === 'pending' && String(order.value.seller_id) === String(user?.id)
)
const canComplete = computed(() =>
  // 买家确认面交完成
  order.value?.status === 'pickup' && String(order.value.buyer_id) === String(user?.id)
)
const canCancel = computed(() =>
  order.value?.status === 'pending' &&
  (String(order.value.buyer_id) === String(user?.id) || String(order.value.seller_id) === String(user?.id))
)

async function load() {
  loading.value = true
  try {
    const res = await orderAPI.getOrderDetail(route.params.id)
    if (res.status === 'success') {
      order.value = res.order
      if (order.value.book_id) {
        const br = await bookAPI.getBookDetail(order.value.book_id)
        if (br.status === 'success') book.value = br.book
      }
      const rr = await reviewAPI.getByOrder(route.params.id)
      if (rr.status === 'success') reviews.value = rr.reviews || []
    }
  } catch (e) {
    show(e.message || '加载失败', 'error')
  } finally {
    loading.value = false
  }
}

function openVoucher() {
  window.open(`/api/orders/${order.value.id}/voucher`, '_blank')
}

async function setStatus(status, extra = {}) {
  // PATCH 订单状态
  const res = await orderAPI.updateStatus(order.value.id, { status, ...extra })
  if (res.status === 'success') {
    show('状态已更新', 'success')
    load()
  } else show(res.message, 'error')
}

async function confirmCancel() {
  const reason = cancelReason.value === '其他' ? cancelCustom.value.trim() : cancelReason.value
  if (!reason) return show('请选择或填写取消原因', 'warning')
  showCancel.value = false
  await setStatus('cancelled', { cancel_reason: reason })
}

async function submitReview() {
  const o = order.value
  const isBuyer = String(o.buyer_id) === String(user?.id)
  submittingReview.value = true
  try {
    const res = await reviewAPI.submit({
      order_id: o.id,
      reviewed_user_id: isBuyer ? o.seller_id : o.buyer_id,
      reviewer_role: isBuyer ? 'buyer' : 'seller',
      ...review.value
    })
    if (res.status === 'success') {
      show('评价已提交', 'success')
      load()
    } else show(res.message, 'error')
  } catch (e) {
    show(e.message, 'error')
  } finally {
    submittingReview.value = false
  }
}

function peerId() {
  const o = order.value
  if (!o) return ''
  return String(o.buyer_id) === String(user?.id) ? o.seller_id : o.buyer_id
}

async function openChat() {
  const pid = peerId()
  if (!pid) return
  try {
    const res = await messageAPI.startConversation({
      peer_id: pid,
      order_id: order.value.id,
      book_id: order.value.book_id
    })
    if (res.status === 'success') {
      router.push({ name: 'Messages', query: { conv: res.conversation.id } })
    }
  } catch (e) { show(e.message || '无法发起会话', 'error') }
}

async function openChatAppt() {
  await openChat()
}

onMounted(load)
</script>
