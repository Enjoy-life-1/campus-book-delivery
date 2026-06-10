<template>
  <div class="page-container">
    <Navbar />
    <div class="container mt-4">
      <div v-if="loading" class="text-center py-5"><div class="spinner-border text-success"></div></div>
      <template v-else-if="seller">
        <div class="card p-4 mb-4">
          <div class="d-flex flex-wrap align-items-center gap-3">
            <img :src="seller.avatar || 'https://picsum.photos/id/64/100/100'" class="rounded-circle" width="80" height="80" alt="">
            <div class="flex-grow-1">
              <h3>{{ seller.username }}</h3>
              <p class="text-muted mb-1">{{ seller.school || '未填写学校' }}</p>
              <span v-if="seller.campus_verified" class="badge bg-success me-1">学籍认证</span>
              <span class="badge bg-secondary">{{ stats.credit_tag }}</span>
              <span v-if="stats.credit_score != null" class="badge bg-info text-dark">信用 {{ stats.credit_score }}</span>
            </div>
            <button v-if="user && user.id !== seller.id" class="btn" :class="following ? 'btn-secondary' : 'btn-success'" @click="toggleFollow">
              {{ following ? '已关注' : '+ 关注卖家' }}
            </button>
          </div>
          <div class="row g-2 mt-3 text-center">
            <div class="col"><div class="fw-bold text-success">{{ stats.on_sale_count }}</div><small>在售</small></div>
            <div class="col"><div class="fw-bold">{{ stats.completed_count }}</div><small>成交</small></div>
            <div class="col"><div class="fw-bold">{{ stats.month_sales || 0 }}</div><small>近30天</small></div>
            <div class="col"><div class="fw-bold">{{ stats.pending_offers || 0 }}</div><small>待议价</small></div>
            <div class="col"><div class="fw-bold">{{ stats.avg_rating }}</div><small>评分</small></div>
            <div class="col"><div class="fw-bold">{{ stats.good_rate }}%</div><small>好评</small></div>
            <div class="col"><div class="fw-bold">{{ stats.total_views || 0 }}</div><small>浏览</small></div>
            <div class="col"><div class="fw-bold">{{ stats.conversion_rate || 0 }}%</div><small>转化</small></div>
          </div>
          <button v-if="user" type="button" class="btn btn-sm btn-outline-success mt-2" @click="copyShare"><i class="fa fa-share-alt"></i> 分享书单</button>
        </div>
        <h5 class="mb-3">在售书籍</h5>
        <div v-if="!books.length" class="text-muted">暂无在售</div>
        <div v-else class="row g-3">
          <div v-for="b in books" :key="b.id" class="col-md-4">
            <router-link :to="`/book/${b.id}`" class="card h-100 text-decoration-none text-dark p-3">
              <h6 class="text-truncate">{{ b.title }}</h6>
              <p class="text-success mb-0">¥{{ formatPrice(b.price) }}</p>
            </router-link>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
// 卖家主页：信用/成交统计、关注、分享书单
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import Navbar from '@/components/Navbar.vue'
import { sellerAPI, followAPI } from '@/utils/api'
import { getCurrentUser } from '@/utils/auth'
import { formatPrice } from '@/utils/helpers'
import { useToast } from '@/composables/useToast'

const { show } = useToast()
const route = useRoute()
const user = getCurrentUser()
const seller = ref(null)
const stats = ref({})
const books = ref([])
const following = ref(false)
const loading = ref(true)

async function load() {
  loading.value = true
  try {
    const res = await sellerAPI.getProfile(route.params.id)
    if (res.status === 'success') {
      seller.value = res.seller
      stats.value = res.stats || {}
      books.value = res.books || []
      following.value = res.is_following
    }
  } finally { loading.value = false }
}

function copyShare() {
  const url = `${location.origin}/share/seller/${route.params.id}`
  navigator.clipboard?.writeText(url)
  show('分享链接已复制', 'success')
}

async function toggleFollow() {
  const id = route.params.id
  if (following.value) {
    await followAPI.unfollow(id)
    following.value = false
  } else {
    await followAPI.follow(id)
    following.value = true
  }
}

onMounted(load)
</script>
