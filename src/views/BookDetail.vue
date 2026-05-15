<template>
  <div>
    <Navbar />
    <div class="container mt-4">
      <div v-if="loading" class="text-center py-5">
        <div class="spinner-border text-success" role="status"></div>
      </div>
      <div v-else-if="book" class="row">
        <div class="col-md-6">
          <img :src="getBookImage(book)" class="img-fluid" :alt="book.title">
        </div>
        <div class="col-md-6">
          <h2>{{ book.title }}</h2>
          <p>作者：{{ book.author || '未知作者' }}</p>
          <p class="text-success h4">¥{{ formatPrice(book.price) }}</p>
          <p>{{ book.description || book.desc }}</p>
          <button class="btn btn-success" @click="handleBuy">立即购买</button>
        </div>
      </div>
      
      <!-- 评论区域 -->
      <div v-if="book" class="mt-4">
        <CommentSection :book-id="route.params.id" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Navbar from '@/components/Navbar.vue'
import CommentSection from '@/components/CommentSection.vue'
import { bookAPI, orderAPI } from '@/utils/api'
import { formatPrice } from '@/utils/helpers'
import { checkAuth } from '@/utils/auth'

const route = useRoute()
const router = useRouter()
const book = ref(null)
const loading = ref(false)

function getBookImage(book) {
  if (book.cover_url) return book.cover_url
  if (book.imgs && book.imgs.length > 0) {
    return Array.isArray(book.imgs) ? book.imgs[0] : JSON.parse(book.imgs)[0]
  }
  return 'https://picsum.photos/id/48/400/300'
}

async function loadBook() {
  loading.value = true
  try {
    const response = await bookAPI.getBookDetail(route.params.id)
    if (response.status === 'success') {
      book.value = response.book
    }
  } catch (error) {
    console.error('加载书籍详情失败:', error)
  } finally {
    loading.value = false
  }
}

async function handleBuy() {
  if (!checkAuth()) {
    if (confirm('购买书籍需要先登录，是否前往登录页面？')) {
      router.push({ name: 'Login', query: { redirect: route.fullPath } })
    }
    return
  }
  
  try {
    const response = await orderAPI.createOrder({ book_id: route.params.id })
    if (response.status === 'success') {
      alert('订单创建成功')
      router.push('/transactionHistory')
    }
  } catch (error) {
    alert(error.message || '购买失败')
  }
}

onMounted(() => {
  loadBook()
})
</script>

