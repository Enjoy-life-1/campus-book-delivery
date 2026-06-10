<template>
  <div class="page-container">
    <Navbar />
    <div class="container mt-4">
      <h2 class="mb-4"><i class="fa fa-star text-warning"></i> 我的收藏</h2>
      <div v-if="loading" class="text-center py-5"><div class="spinner-border text-success"></div></div>
      <div v-else-if="!books.length" class="text-center py-5 text-muted">
        <i class="fa fa-star-o fa-4x mb-3"></i>
        <p>还没有收藏任何书籍</p>
        <router-link to="/booksList" class="btn btn-success">去发现好书</router-link>
      </div>
      <div v-else class="row g-4">
        <div v-for="book in books" :key="book.id" class="col-md-4 col-lg-3">
          <div class="card h-100 shadow-sm">
            <router-link :to="`/book/${book.id}`">
              <img :src="cover(book)" class="card-img-top" style="height:180px;object-fit:cover">
            </router-link>
            <div class="card-body">
              <h6 class="text-truncate">{{ book.title }}</h6>
              <p class="text-success mb-1">¥{{ formatPrice(book.price) }}</p>
              <p v-if="book.price_dropped_since_collect" class="small text-danger mb-1">
                <i class="fa fa-arrow-down"></i> 较收藏时 ¥{{ formatPrice(book.collected_price) }} 已降价
              </p>
              <div class="form-check form-switch mb-2">
                <input :id="'pa'+book.id" class="form-check-input" type="checkbox" :checked="book.price_alert !== false" @change="e => toggleAlert(book, e)">
                <label class="form-check-label small" :for="'pa'+book.id">降价提醒</label>
              </div>
              <div class="d-flex gap-2">
                <router-link :to="`/book/${book.id}`" class="btn btn-sm btn-success flex-grow-1">查看</router-link>
                <button class="btn btn-sm btn-outline-danger" @click="uncollect(book.id)">取消</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
// 收藏列表：降价对比、price_alert 开关
import { ref, onMounted } from 'vue'
import Navbar from '@/components/Navbar.vue'
import { collectionAPI } from '@/utils/api'
import { formatPrice } from '@/utils/helpers'
import { useToast } from '@/composables/useToast'

const { show } = useToast()
const books = ref([])
const loading = ref(false)

function cover(book) {
  if (book.imgs?.length) return book.imgs[0]
  return book.cover_url || 'https://picsum.photos/id/24/300/400'
}

async function load() {
  loading.value = true
  try {
    const res = await collectionAPI.getCollections()
    if (res.status === 'success') books.value = res.collections || res.books || []
  } finally {
    loading.value = false
  }
}

async function toggleAlert(book, e) {
  // PATCH 单本书降价提醒开关
  const enabled = e.target.checked
  await collectionAPI.setPriceAlert(book.id, { enabled })
  book.price_alert = enabled
}

async function uncollect(id) {
  await collectionAPI.toggleCollection(id)
  show('已取消收藏', 'info')
  load()
}

onMounted(load)
</script>
