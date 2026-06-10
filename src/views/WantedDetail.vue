<template>
  <div class="page-container">
    <Navbar />
    <div class="container mt-4">
      <router-link to="/wanted" class="btn btn-link mb-2">&larr; 返回求购广场</router-link>
      <div v-if="loading" class="text-center py-5"><div class="spinner-border text-success"></div></div>
      <template v-else-if="wanted">
        <div class="card p-4 mb-4">
          <div class="d-flex justify-content-between align-items-start">
            <h3>{{ wanted.title }}</h3>
            <button type="button" class="btn btn-sm btn-outline-success" @click="copyShare"><i class="fa fa-share-alt"></i> 分享</button>
          </div>
          <p class="text-muted">求购人：{{ wanted.username }} · {{ wanted.created_at }}</p>
          <p v-if="wanted.max_price">最高预算：¥{{ wanted.max_price }}</p>
          <p v-if="wanted.isbn">ISBN：{{ wanted.isbn }}</p>
          <p>{{ wanted.desc }}</p>
        </div>
        <h5 class="mb-3">匹配在售书籍（{{ matches.length }}）</h5>
        <div v-if="!matches.length" class="alert alert-info">暂无匹配，稍后再来看看</div>
        <div v-else class="row g-3">
          <div v-for="b in matches" :key="b.id" class="col-md-6">
            <div class="card p-3">
              <div class="d-flex gap-3">
                <img :src="cover(b)" class="rounded" style="width:80px;height:100px;object-fit:cover">
                <div class="flex-grow-1">
                  <h6>{{ b.title }}</h6>
                  <p class="text-success mb-1">¥{{ formatPrice(b.price) }}</p>
                  <p class="small text-muted">卖家：{{ b.owner_name || b.seller }}</p>
                  <div class="d-flex flex-wrap gap-2">
                    <router-link :to="`/book/${b.id}`" class="btn btn-sm btn-outline-success">详情</router-link>
                    <button v-if="user && String(b.owner_id) !== String(user.id)" type="button" class="btn btn-sm btn-success" @click="buyNow(b)">立即购买</button>
                    <button v-if="user && String(b.owner_id) !== String(user.id)" type="button" class="btn btn-sm btn-outline-primary" @click="contactSeller(b)">联系卖家</button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
// 求购详情 + find_wanted_matches 匹配书、购买/私信
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Navbar from '@/components/Navbar.vue'
import { wantedAPI, messageAPI, orderAPI } from '@/utils/api'
import { getCurrentUser, checkAuth } from '@/utils/auth'
import { formatPrice } from '@/utils/helpers'
import { useToast } from '@/composables/useToast'

const route = useRoute()
const router = useRouter()
const { show } = useToast()
const user = getCurrentUser()
const wanted = ref(null)
const matches = ref([])
const loading = ref(true)

function cover(b) {
  if (b.imgs?.length) return b.imgs[0]
  return b.cover_url || b.image || 'https://picsum.photos/id/24/300/400'
}

function copyShare() {
  navigator.clipboard?.writeText(`${location.origin}/share/wanted/${route.params.id}`)
  show('分享链接已复制', 'success')
}

async function load() {
  loading.value = true
  try {
    const res = await wantedAPI.get(route.params.id)
    if (res.status === 'success') {
      wanted.value = res.wanted
      matches.value = res.wanted.matches || []
    }
  } finally { loading.value = false }
}

async function buyNow(book) {
  if (!checkAuth()) {
    router.push({ name: 'Login', query: { redirect: route.fullPath } })
    return
  }
  const res = await orderAPI.createOrder({ book_id: book.id })
  if (res.status === 'success') {
    show('订单已创建', 'success')
    router.push('/transactionHistory')
  } else show(res.message, 'error')
}

async function contactSeller(book) {
  if (!checkAuth()) {
    router.push({ name: 'Login', query: { redirect: route.fullPath } })
    return
  }
  try {
    const res = await messageAPI.startConversation({
      peer_id: book.owner_id || book.sellerId,
      book_id: book.id
    })
    if (res.status === 'success') {
      router.push({ name: 'Messages', query: { conv: res.conversation.id } })
    }
  } catch (e) { show(e.message || '无法发起会话', 'danger') }
}

onMounted(load)
</script>
