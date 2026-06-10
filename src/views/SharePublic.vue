<template>
  <div class="page-container">
    <Navbar />
    <div class="container mt-4 py-3">
      <div v-if="loading" class="text-center py-5"><div class="spinner-border text-success"></div></div>
      <template v-else-if="type === 'wanted' && wanted">
        <p class="text-muted small">校园书递 · 求购分享</p>
        <div class="card p-4">
          <h3>{{ wanted.title }}</h3>
          <p>求购人：{{ wanted.username }}</p>
          <p v-if="wanted.max_price">预算：¥{{ wanted.max_price }}</p>
          <p>{{ wanted.desc }}</p>
          <router-link v-if="user" :to="`/wanted/${wanted.id}`" class="btn btn-success">去平台查看</router-link>
          <router-link v-else to="/login" class="btn btn-success">登录后联系</router-link>
        </div>
        <div v-if="wanted.matches?.length" class="mt-3">
          <h5>匹配在售</h5>
          <div v-for="b in wanted.matches" :key="b.id" class="card p-2 mb-2">
            <router-link :to="`/book/${b.id}`">{{ b.title }} — ¥{{ b.price }}</router-link>
          </div>
        </div>
      </template>
      <template v-else-if="type === 'seller' && seller">
        <p class="text-muted small">校园书递 · 卖家书单</p>
        <div class="card p-4 mb-3">
          <h3>{{ seller.username }}</h3>
          <p class="text-muted">{{ seller.school }}</p>
          <span v-if="seller.campus_verified" class="badge bg-success">已认证</span>
        </div>
        <div class="row g-3">
          <div v-for="b in books" :key="b.id" class="col-md-4">
            <router-link :to="`/book/${b.id}`" class="card p-3 text-decoration-none text-dark">
              <h6>{{ b.title }}</h6>
              <p class="text-success mb-0">¥{{ b.price }}</p>
            </router-link>
          </div>
        </div>
      </template>
      <div v-else class="alert alert-warning">内容不存在</div>
    </div>
  </div>
</template>

<script setup>
// 公开分享页：/share/wanted/:id、/share/seller/:id（无需登录可看）
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import Navbar from '@/components/Navbar.vue'
import { publicAPI } from '@/utils/api'
import { getCurrentUser } from '@/utils/auth'

const route = useRoute()
const user = getCurrentUser()
const loading = ref(true)
const wanted = ref(null)
const seller = ref(null)
const books = ref([])

const type = computed(() => route.meta.shareType)

onMounted(async () => {
  // route.meta.shareType 决定拉求购还是卖家书单
  try {
    if (type.value === 'wanted') {
      const r = await publicAPI.getWanted(route.params.id)
      if (r.status === 'success') wanted.value = r.wanted
    } else {
      const r = await publicAPI.getSellerBooks(route.params.id)
      if (r.status === 'success') {
        seller.value = r.seller
        books.value = r.books || []
      }
    }
  } finally { loading.value = false }
})
</script>
