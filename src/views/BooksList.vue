<template>
  <div>
    <Navbar />
    <div class="container mt-4">
      <h2>全部书籍</h2>
      <div v-if="loading" class="text-center py-5">
        <div class="spinner-border text-success" role="status"></div>
      </div>
      <div v-else class="row g-4">
        <div class="col-md-3" v-for="book in books" :key="book.id">
          <router-link :to="`/book/${book.id}`" class="text-decoration-none">
            <div class="card">
              <img :src="getBookImage(book)" class="card-img-top" :alt="book.title">
              <div class="card-body">
                <h5 class="card-title">{{ book.title }}</h5>
                <p class="text-muted">¥{{ formatPrice(book.price) }}</p>
              </div>
            </div>
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import Navbar from '@/components/Navbar.vue'
import { bookAPI } from '@/utils/api'
import { formatPrice } from '@/utils/helpers'

const route = useRoute()
const books = ref([])
const loading = ref(false)

function getBookImage(book) {
  if (book.cover_url) return book.cover_url
  if (book.imgs && book.imgs.length > 0) {
    return Array.isArray(book.imgs) ? book.imgs[0] : JSON.parse(book.imgs)[0]
  }
  return 'https://picsum.photos/id/48/400/300'
}

async function loadBooks() {
  loading.value = true
  try {
    const params = {
      category: route.query.category,
      search: route.query.keyword || route.query.search,
      page_size: 1000
    }
    const response = await bookAPI.getBooks(params)
    if (response.status === 'success') {
      books.value = response.books || []
    }
  } catch (error) {
    console.error('加载书籍失败:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadBooks()
})
</script>

