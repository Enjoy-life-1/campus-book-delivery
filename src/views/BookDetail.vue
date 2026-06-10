<template>
  <div class="page-container">
    <Navbar />
    <div class="container mt-4">
      <div v-if="loading" class="text-center py-5"><div class="spinner-border text-success"></div></div>
      <div v-else-if="book" class="row g-4">
        <div class="col-lg-5">
          <div id="bookCarousel" class="carousel slide" data-bs-ride="false">
            <div class="carousel-inner rounded shadow-sm">
              <div v-for="(img, i) in images" :key="i" :class="['carousel-item', { active: i === 0 }]">
                <img :src="img" class="d-block w-100 detail-img" :alt="book.title">
              </div>
            </div>
            <button v-if="images.length > 1" class="carousel-control-prev" type="button" data-bs-target="#bookCarousel" data-bs-slide="prev">
              <span class="carousel-control-prev-icon"></span>
            </button>
            <button v-if="images.length > 1" class="carousel-control-next" type="button" data-bs-target="#bookCarousel" data-bs-slide="next">
              <span class="carousel-control-next-icon"></span>
            </button>
          </div>
        </div>
        <div class="col-lg-7">
          <h2>{{ book.title }}</h2>
          <p class="text-muted mb-2"><i class="fa fa-pencil"></i> {{ book.author || '未知作者' }}</p>
          <p v-if="book.isbn" class="small text-muted">ISBN：{{ book.isbn }} <span v-if="book.edition">· {{ book.edition }}</span></p>
          <div class="d-flex flex-wrap gap-2 mb-2">
            <span v-if="book.condition" class="badge bg-success-subtle text-success">{{ getConditionLabel(book.condition) }}</span>
            <span v-if="book.campaign_tag" class="badge bg-warning text-dark">学期专场</span>
            <span v-if="book.dorm_building" class="badge bg-light text-dark"><i class="fa fa-building-o"></i> {{ book.dorm_building }}</span>
            <span v-if="book.campus_zone" class="badge bg-light text-dark">{{ book.campus_zone }}</span>
            <span v-if="book.course_code" class="badge bg-info text-dark">课程 {{ book.course_code }}</span>
          </div>
          <p class="display-6 text-success mb-1">
            ¥{{ formatPrice(book.price) }}
            <small v-if="book.original_price && book.is_price_dropping" class="text-muted text-decoration-line-through fs-6">¥{{ formatPrice(book.original_price) }}</small>
          </p>
          <div v-if="priceInsights" class="alert alert-light border small py-2 mb-2">
            <strong>比价参考：</strong>同类均价 ¥{{ priceInsights.avg_price }}
            <span v-if="priceInsights.min_price != null">（在售 {{ priceInsights.on_sale_count }} 本，¥{{ priceInsights.min_price }}~{{ priceInsights.max_price }}）</span>
            <span v-if="priceInsights.history_avg_price"> · 历史成交均价 ¥{{ priceInsights.history_avg_price }}</span>
            <div v-if="priceInsights.hint" class="text-success mt-1">{{ priceInsights.hint }}</div>
          </div>
          <div v-if="courseHints?.warnings?.length" class="alert alert-warning small py-2 mb-2">
            <div v-for="(w,i) in courseHints.warnings" :key="'w'+i">{{ w }}</div>
          </div>
          <div v-if="courseHints?.tips?.length" class="alert alert-info small py-2 mb-2">
            <div v-for="(t,i) in courseHints.tips" :key="'t'+i">{{ t }}</div>
          </div>
          <p v-if="book.is_price_dropping" class="text-danger small mb-2"><i class="fa fa-clock-o"></i> 倒计时降价剩余 {{ dropLabel }}</p>
          <div v-if="book.listing_type === 'bundle' && book.bundle_items?.length" class="alert alert-light border mb-2">
            <strong>套装含 {{ book.bundle_items.length }} 本：</strong>
            <ul class="mb-0 small"><li v-for="(it, i) in book.bundle_items" :key="i">{{ it.title }} <span v-if="it.author">— {{ it.author }}</span></li></ul>
          </div>
          <p class="desc-box">{{ book.description || book.desc }}</p>
          <p class="text-muted">
            <i class="fa fa-user"></i> 卖家：
            <router-link v-if="sellerId" :to="`/seller/${sellerId}`" class="text-success">{{ book.owner_name || book.seller }}</router-link>
            <span v-else>{{ book.owner_name || book.seller || '匿名' }}</span>
            <span v-if="book.seller_verified" class="badge bg-success ms-1">认证</span>
            <button v-if="sellerId && user && user.id !== sellerId" class="btn btn-sm ms-2" :class="following ? 'btn-secondary' : 'btn-outline-success'" @click="toggleFollow">
              {{ following ? '已关注' : '关注' }}
            </button>
          </p>
          <p v-if="book.status !== 'available'" class="alert alert-warning py-2">该书籍当前不可购买（{{ getStatusText(book.status) }}）</p>
          <div v-if="isOwner && pendingOffers.length" class="alert alert-info py-2">
            <strong>{{ pendingOffers.length }} 条待处理报价</strong>
            <router-link to="/offers" class="ms-2">去处理</router-link>
          </div>
          <div class="d-flex flex-wrap gap-2 mt-3">
            <button class="btn btn-success btn-lg" :disabled="book.status !== 'available' || isOwner" @click="handleBuy">
              <i class="fa fa-shopping-bag"></i> 立即购买
            </button>
            <button class="btn btn-outline-primary" :disabled="book.status !== 'available' || isOwner" @click="showOffer = true">
              <i class="fa fa-handshake-o"></i> 我要议价
            </button>
            <button class="btn btn-outline-success" :disabled="isOwner" @click="contactSeller"><i class="fa fa-comments"></i> 站内联系</button>
            <button class="btn" :class="collected ? 'btn-warning' : 'btn-outline-warning'" @click="toggleCollect">
              <i :class="collected ? 'fa fa-star' : 'fa fa-star-o'"></i> {{ collected ? '已收藏' : '收藏' }}
            </button>
            <button class="btn btn-outline-secondary" :disabled="book.status !== 'available' || isOwner" @click="addCart">
              <i class="fa fa-cart-plus"></i> 加购物车
            </button>
            <button class="btn btn-outline-info" :disabled="book.status !== 'available' || isOwner" @click="showExchange = true">
              <i class="fa fa-exchange"></i> 申请换书
            </button>
            <button v-if="sellerId && !isOwner" class="btn btn-outline-danger btn-sm" @click="reportBook">举报</button>
            <button v-if="sellerId && !isOwner" class="btn btn-outline-dark btn-sm" @click="blockSeller">拉黑卖家</button>
          </div>
        </div>
      </div>

      <div v-if="similarBooks.length" class="mt-5">
        <h5 class="mb-3">相似推荐</h5>
        <div class="row g-3">
          <div v-for="b in similarBooks" :key="b.id" class="col-md-4">
            <router-link :to="`/book/${b.id}`" class="card p-3 text-decoration-none text-dark h-100">
              <h6 class="text-truncate">{{ b.title }}</h6>
              <p class="text-success mb-0">¥{{ formatPrice(b.price) }}</p>
            </router-link>
          </div>
        </div>
      </div>

      <div v-if="book" class="mt-5"><CommentSection :book-id="route.params.id" /></div>
    </div>

    <div v-if="showExchange" class="modal d-block" tabindex="-1" style="background:rgba(0,0,0,.5)">
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header"><h5 class="modal-title">以书换书</h5><button type="button" class="btn-close" @click="showExchange = false"></button></div>
          <div class="modal-body">
            <input v-model="exchangeTitle" class="form-control mb-2" placeholder="您用于交换的书名 *">
            <textarea v-model="exchangeNote" class="form-control" rows="2" placeholder="补差价说明等（选填）"></textarea>
          </div>
          <div class="modal-footer"><button class="btn btn-success" @click="submitExchange">提交换书申请</button></div>
        </div>
      </div>
    </div>

    <div v-if="showOffer" class="modal d-block" tabindex="-1" style="background:rgba(0,0,0,.5)">
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">提交报价</h5>
            <button type="button" class="btn-close" @click="showOffer = false"></button>
          </div>
          <div class="modal-body">
            <p>标价：¥{{ formatPrice(book?.price) }}</p>
            <input v-model.number="offerPrice" type="number" step="0.01" class="form-control mb-2" placeholder="您的出价">
            <textarea v-model="offerMsg" class="form-control" rows="2" placeholder="留言（选填）"></textarea>
          </div>
          <div class="modal-footer">
            <button class="btn btn-success" @click="submitOffer">提交</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
// 书籍详情：购买、议价、换书、收藏、加购、私信、举报
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Navbar from '@/components/Navbar.vue'
import CommentSection from '@/components/CommentSection.vue'
import { bookAPI, orderAPI, collectionAPI, cartAPI, messageAPI, offerAPI, followAPI, safetyAPI } from '@/utils/api'
import { formatPrice, getConditionLabel, getStatusText } from '@/utils/helpers'
import { formatCountdown } from '@/utils/formatCountdown'
import { checkAuth, getCurrentUser } from '@/utils/auth'
import { useToast } from '@/composables/useToast'
import { isOnline, saveBookDetail, loadBookDetail } from '@/utils/offlineStore'

const route = useRoute()
const router = useRouter()
const { show } = useToast()
const user = getCurrentUser()
const book = ref(null)
const loading = ref(false)
const collected = ref(false)
const following = ref(false)
const similarBooks = ref([])
const priceInsights = ref(null)  // 同类比价
const courseHints = ref(null)    // 课程教材提示
const pendingOffers = ref([])  // 卖家待处理报价
const showOffer = ref(false)
const showExchange = ref(false)
const exchangeTitle = ref('')
const exchangeNote = ref('')
const offerPrice = ref(null)
const offerMsg = ref('')

const sellerId = computed(() => book.value?.owner_id || book.value?.sellerId || '')
const isOwner = computed(() => user && String(sellerId.value) === String(user.id))

const dropLabel = computed(() => formatCountdown(book.value?.price_drop_seconds_left))

const images = computed(() => {
  // 轮播图：imgs / cover_url / 默认占位
  if (!book.value) return []
  const b = book.value
  if (b.imgs?.length) return Array.isArray(b.imgs) ? b.imgs : [b.imgs]
  if (b.cover_url) return [b.cover_url]
  if (b.image) return [b.image]
  return ['https://picsum.photos/id/48/600/400']
})

async function contactSeller() {
  // 发起与卖家的私信会话
  if (!checkAuth()) return router.push({ name: 'Login', query: { redirect: route.fullPath } })
  try {
    const res = await messageAPI.startConversation({ peer_id: sellerId.value, book_id: book.value.id })
    if (res.status === 'success') router.push({ name: 'Messages', query: { conv: res.conversation.id } })
  } catch (e) { show(e.message || '无法发起会话', 'danger') }
}

async function loadBook() {
  // 拉详情 + 收藏/关注/报价状态；断网读缓存
  loading.value = true
  try {
    const res = await bookAPI.getBookDetail(route.params.id)
    if (res.status === 'success') {
      book.value = res.book
      saveBookDetail(route.params.id, res.book)
      similarBooks.value = res.similar_books || res.book?.similar_books || []
      priceInsights.value = res.price_insights || res.book?.price_insights || null
      courseHints.value = res.book?.course_hints || null
    }
    if (checkAuth()) {
      const c = await collectionAPI.checkCollection(route.params.id)
      if (c.status === 'success') collected.value = c.is_collected
      if (sellerId.value) {
        const f = await followAPI.check(sellerId.value)
        if (f.status === 'success') following.value = f.is_following
      }
      if (isOwner.value) {
        const o = await offerAPI.list({ book_id: route.params.id, role: 'seller' })
        if (o.status === 'success') pendingOffers.value = (o.offers || []).filter(x => x.status === 'pending')
      }
    }
  } catch (_) {
    if (!isOnline()) {
      const cached = loadBookDetail(route.params.id)
      if (cached) book.value = cached
    }
  } finally { loading.value = false }
}

async function submitOffer() {
  if (!checkAuth()) return router.push({ name: 'Login', query: { redirect: route.fullPath } })
  if (!offerPrice.value || offerPrice.value <= 0) return show('请输入有效报价', 'warning')
  try {
    const res = await offerAPI.create({
      book_id: route.params.id,
      offer_price: offerPrice.value,
      message: offerMsg.value
    })
    if (res.status === 'success') {
      show('报价已提交，等待卖家处理', 'success')
      showOffer.value = false
    }
  } catch (e) { show(e.message || '失败', 'danger') }
}

async function toggleFollow() {
  if (!checkAuth()) return router.push('/login')
  if (following.value) {
    await followAPI.unfollow(sellerId.value)
    following.value = false
    show('已取消关注', 'info')
  } else {
    await followAPI.follow(sellerId.value)
    following.value = true
    show('关注成功，上新将通知您', 'success')
  }
}

async function handleBuy() {
  // 立即购买 → 创建订单
  if (!checkAuth()) return router.push({ name: 'Login', query: { redirect: route.fullPath } })
  const res = await orderAPI.createOrder({ book_id: route.params.id })
  if (res.status === 'success') {
    show('订单已创建', 'success')
    router.push('/transactionHistory')
  } else show(res.message || '失败', 'error')
}

async function submitExchange() {
  // 换书申请 order_type=exchange
  if (!checkAuth()) return router.push({ name: 'Login', query: { redirect: route.fullPath } })
  if (!exchangeTitle.value.trim()) return show('请填写交换书名', 'warning')
  try {
    const res = await orderAPI.createExchange({
      book_id: route.params.id,
      exchange_book_title: exchangeTitle.value.trim(),
      exchange_note: exchangeNote.value
    })
    if (res.status === 'success') {
      show('换书申请已提交', 'success')
      showExchange.value = false
      router.push(`/order/${res.order.id}`)
    }
  } catch (e) { show(e.message || '失败', 'danger') }
}

async function reportBook() {
  if (!checkAuth()) return router.push('/login')
  const reason = prompt('举报原因（必填）')
  if (!reason) return
  const res = await safetyAPI.report({ target_type: 'book', target_id: route.params.id, reason })
  show(res.message || '已提交', res.status === 'success' ? 'success' : 'danger')
}

async function blockSeller() {
  if (!checkAuth()) return router.push('/login')
  if (!confirm('确定拉黑该卖家？将无法与其私信')) return
  const res = await safetyAPI.block(sellerId.value)
  show(res.message || '已拉黑', 'success')
}

async function toggleCollect() {
  if (!checkAuth()) return router.push('/login')
  const res = await collectionAPI.toggleCollection(route.params.id)
  if (res.status === 'success') {
    collected.value = res.is_collected
    show(res.is_collected ? '已收藏，降价将提醒您' : '已取消收藏', 'success')
  }
}

async function addCart() {
  if (!checkAuth()) return router.push('/login')
  const res = await cartAPI.addToCart({ book_id: route.params.id, quantity: 1 })
  if (res.status === 'success') {
    show('已加入购物车', 'success')
    window.dispatchEvent(new Event('user-updated'))
  } else show(res.message, 'error')
}

onMounted(loadBook)
</script>

<style scoped>
.detail-img { max-height: 420px; object-fit: contain; background: #f8f9fa; }
.desc-box { background: #f8f9fa; padding: 16px; border-radius: 8px; line-height: 1.8; }
</style>
