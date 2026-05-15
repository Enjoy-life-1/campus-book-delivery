<template>
  <div>
    <Navbar />
    
    <!-- 轮播图 -->
    <div id="carouselExampleIndicators" class="carousel slide" data-bs-ride="true">
      <div class="carousel-indicators">
        <button type="button" data-bs-target="#carouselExampleIndicators" data-bs-slide-to="0" class="active"></button>
        <button type="button" data-bs-target="#carouselExampleIndicators" data-bs-slide-to="1"></button>
        <button type="button" data-bs-target="#carouselExampleIndicators" data-bs-slide-to="2"></button>
      </div>
      <div class="carousel-inner">
        <div class="carousel-item active">
          <img src="https://picsum.photos/id/24/1600/800" class="d-block w-100" alt="二手书籍合集" loading="lazy">
          <div class="carousel-caption d-none d-md-block">
            <h5>以书会友，知识传递</h5>
            <p>闲置教材、考研资料、文学书籍，低价转让，让知识流动起来</p>
          </div>
        </div>
        <div class="carousel-item">
          <img src="https://picsum.photos/id/48/1600/800" class="d-block w-100" alt="校园图书馆" loading="lazy">
          <div class="carousel-caption d-none d-md-block">
            <h5>校园二手书，性价比之选</h5>
            <p>9成新教材低至3折，正版保障，省钱又环保</p>
          </div>
        </div>
        <div class="carousel-item">
          <img src="https://picsum.photos/id/20/1600/800" class="d-block w-100" alt="阅读学习" loading="lazy">
          <div class="carousel-caption d-none d-md-block">
            <h5>当面交易，放心选购</h5>
            <p>校园内指定地点交易，可验货后付款，买得安心</p>
          </div>
        </div>
      </div>
      <button class="carousel-control-prev" type="button" data-bs-target="#carouselExampleIndicators" data-bs-slide="prev">
        <span class="carousel-control-prev-icon"></span>
      </button>
      <button class="carousel-control-next" type="button" data-bs-target="#carouselExampleIndicators" data-bs-slide="next">
        <span class="carousel-control-next-icon"></span>
      </button>
    </div>

    <!-- 搜索栏 -->
    <div class="container mt-5">
      <div class="input-group search-input-group">
        <input 
          v-model="searchKeyword" 
          type="text" 
          class="form-control form-control-lg" 
          placeholder="搜索书名、作者、ISBN、专业方向..."
          @keypress.enter="handleSearch"
        >
        <button class="btn btn-success" type="button" @click="handleSearch">
          <i class="fa fa-search me-2"></i> 搜索书籍
        </button>
      </div>
    </div>

    <!-- 书籍特色标签区 -->
    <div class="container mt-4">
      <div class="feature-tags d-flex justify-content-center flex-wrap gap-3">
        <div class="feature-tag"><i class="fa fa-check-circle"></i> 正版保障</div>
        <div class="feature-tag"><i class="fa fa-money"></i> 低价转让</div>
        <div class="feature-tag"><i class="fa fa-map-marker"></i> 校园交易</div>
        <div class="feature-tag"><i class="fa fa-star"></i> 9成新以上</div>
        <div class="feature-tag"><i class="fa fa-exchange"></i> 支持互换</div>
      </div>
    </div>

    <!-- 书籍分类导航 -->
    <div class="category-section mt-4">
      <div class="container">
        <h3 class="section-title text-center mb-5" style="color: #28a745;">书籍分类</h3>
        <div class="row g-4">
          <div class="col-md-3" v-for="category in categories" :key="category.key">
            <router-link :to="`/booksList?category=${category.key}`" class="text-decoration-none">
              <div class="category-card h-100">
                <div class="category-icon">
                  <i :class="category.icon"></i>
                </div>
                <h5>{{ category.name }}</h5>
                <p>{{ category.desc }}</p>
              </div>
            </router-link>
          </div>
        </div>
      </div>
    </div>

    <!-- 热门书籍 -->
    <div class="books-section mt-4">
      <div class="container">
        <div class="section-header">
          <h3 class="section-title text-center" style="color: #28a745;">热门书籍</h3>
          <router-link to="/booksList" class="section-more text-success">
            查看全部 <i class="fa fa-angle-right"></i>
          </router-link>
        </div>
        <div v-if="loading" class="text-center py-5">
          <div class="spinner-border text-success" role="status">
            <span class="visually-hidden">加载中...</span>
          </div>
        </div>
        <div v-else class="row g-4">
          <div class="col-md-4 col-sm-6" v-for="book in hotBooks" :key="book.id">
            <router-link :to="`/book/${book.id}`" class="text-decoration-none">
              <div class="card">
                <img :src="getBookImage(book)" class="card-img-top" :alt="book.title" loading="lazy">
                <div class="card-body">
                  <h5 class="card-title">{{ book.title }}</h5>
                  <div class="card-author">
                    <i class="fa fa-pencil"></i> 作者：{{ book.author || '未知作者' }}
                  </div>
                  <div class="card-meta">
                    <span class="price">¥{{ formatPrice(book.price) }}</span>
                    <span class="book-tag">{{ getCategoryName(book.category) }}</span>
                  </div>
                  <div class="book-additional">
                    <span v-if="book.stock > 0" class="book-stock">库存：{{ book.stock }}</span>
                  </div>
                  <div class="create-time">
                    <i class="fa fa-clock-o"></i> {{ formatDate(book.created_at) }} · {{ book.owner_name || book.seller }}
                  </div>
                </div>
              </div>
            </router-link>
          </div>
        </div>
      </div>
    </div>

    <!-- 页脚 -->
    <footer class="footer mt-8 bg-success text-white">
      <div class="container py-5">
        <div class="row">
          <div class="col-md-4">
            <div class="footer-logo">
              <i class="fa fa-book"></i> 校园书递
            </div>
            <p>专注于校园二手书籍交易，让闲置教材焕发新价值，为大学生提供安全、便捷、高效的书籍交易平台，促进知识共享，传递校园温情。</p>
          </div>
          <div class="col-md-4">
            <h5>快速链接</h5>
            <ul class="footer-links">
              <li><router-link to="/guide" class="text-white"><i class="fa fa-angle-right"></i> 关于我们</router-link></li>
              <li><router-link to="/guide" class="text-white"><i class="fa fa-angle-right"></i> 交易规则</router-link></li>
              <li><router-link to="/guide" class="text-white"><i class="fa fa-angle-right"></i> 常见问题</router-link></li>
            </ul>
          </div>
          <div class="col-md-4">
            <h5>联系我们</h5>
            <div class="contact-item">
              <i class="fa fa-wechat"></i>
              <span>微信公众号：校园书递</span>
            </div>
            <div class="contact-item">
              <i class="fa fa-envelope"></i>
              <span>邮箱：support@xiaoyuanshudi.com</span>
            </div>
          </div>
        </div>
        <div class="copyright">
          © 2025 校园书递 版权所有 | 大学生校园二手书籍交易平台
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import Navbar from '@/components/Navbar.vue'
import { bookAPI } from '@/utils/api'
import { getCategoryName, formatPrice, formatDate } from '@/utils/helpers'

const router = useRouter()
const searchKeyword = ref('')
const hotBooks = ref([])
const loading = ref(false)

const categories = [
  { key: 'textbook', name: '教材教辅', desc: '大学教材、习题集、课件、辅导资料', icon: 'fa fa-graduation-cap' },
  { key: 'postgraduate', name: '考研资料', desc: '考研真题、复习笔记、网课讲义、背诵手册', icon: 'fa fa-bookmark' },
  { key: 'literature', name: '文学小说', desc: '经典文学、当代小说、散文随笔、外国名著', icon: 'fa fa-book' },
  { key: 'professional', name: '专业书籍', desc: '计算机、经管、法律、医学、工程等专业书籍', icon: 'fa fa-flask' }
]

function getBookImage(book) {
  if (book.cover_url) return book.cover_url
  if (book.imgs && book.imgs.length > 0) {
    return Array.isArray(book.imgs) ? book.imgs[0] : JSON.parse(book.imgs)[0]
  }
  if (book.image) return book.image
  return 'https://picsum.photos/id/48/400/300'
}

function handleSearch() {
  if (searchKeyword.value.trim()) {
    router.push({ path: '/booksList', query: { keyword: searchKeyword.value.trim() } })
  } else {
    router.push('/booksList')
  }
}

async function loadHotBooks() {
  loading.value = true
  try {
    const response = await bookAPI.getBooks({ page_size: 1000 })
    if (response.status === 'success') {
      const books = response.books || []
      // 只显示在售的书籍，取前6本
      hotBooks.value = books
        .filter(book => book.status === 'available')
        .slice(0, 6)
    }
  } catch (error) {
    console.error('加载热门书籍失败:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadHotBooks()
})
</script>

