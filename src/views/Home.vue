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
          list="homeSearchSuggest"
          @input="onHomeSearchInput"
          @keypress.enter="handleSearch"
        >
        <datalist id="homeSearchSuggest">
          <option v-for="s in searchSuggestions" :key="s.text" :value="s.text" />
        </datalist>
        <button class="btn btn-success" type="button" @click="handleSearch">
          <i class="fa fa-search me-2"></i> 搜索书籍
        </button>
      </div>
    </div>

    <div v-if="forYouBooks.length" class="container mt-4">
      <h3 class="section-title text-center mb-3" style="color: #28a745;">猜你喜欢</h3>
      <div class="row g-4">
        <div class="col-md-3 col-sm-6" v-for="book in forYouBooks" :key="'fy'+book.id">
          <BookCard :book="book" />
        </div>
      </div>
    </div>

    <!-- 快捷功能 -->
    <div class="container mt-4">
      <div class="row g-3">
        <div class="col-md-3 col-6">
          <router-link to="/courses" class="quick-feature card p-3 text-decoration-none text-dark h-100 border-success">
            <h6 class="text-success mb-1"><i class="fa fa-graduation-cap"></i> 按课找书</h6>
            <p class="mb-0 text-muted small">学院·专业·课程教材推荐</p>
          </router-link>
        </div>
        <div class="col-md-3 col-6">
          <router-link to="/wanted" class="quick-feature card p-3 text-decoration-none text-dark h-100 border-success">
            <h6 class="text-success mb-1"><i class="fa fa-bullhorn"></i> 求购广场</h6>
            <p class="mb-0 text-muted small">发布求购，自动匹配上架</p>
          </router-link>
        </div>
        <div class="col-md-3 col-6">
          <router-link to="/semester" class="quick-feature card p-3 text-decoration-none text-dark h-100 border-warning">
            <h6 class="text-warning mb-1"><i class="fa fa-calendar"></i> 学期专场</h6>
            <p class="mb-0 text-muted small">开学季/期末清仓主题活动</p>
          </router-link>
        </div>
        <div class="col-md-3 col-6">
          <router-link to="/messages" class="quick-feature card p-3 text-decoration-none text-dark h-100 border-primary">
            <h6 class="text-primary mb-1"><i class="fa fa-envelope"></i> 站内消息</h6>
            <p class="mb-0 text-muted small">校内面交点预约交易</p>
          </router-link>
        </div>
      </div>
    </div>

    <!-- 书籍特色标签区 -->
    <div class="container mt-4">
      <div class="feature-tags d-flex justify-content-center flex-wrap gap-3">
        <router-link v-for="f in featureLinks" :key="f.to" :to="f.to" class="feature-tag text-decoration-none text-dark">
          <i :class="['fa', f.icon]"></i> {{ f.label }}
        </router-link>
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

    <!-- 系统公告 -->
    <div v-if="announcements.length" class="container mt-4">
      <div class="alert alert-success" v-for="a in announcements.slice(0, 2)" :key="a.id">
        <strong>{{ a.title }}</strong> — {{ a.content.slice(0, 80) }}{{ a.content.length > 80 ? '...' : '' }}
      </div>
    </div>

    <!-- 最新上架 -->
    <div class="books-section mt-4">
      <div class="container">
        <div class="section-header">
          <h3 class="section-title text-center" style="color: #28a745;">最新上架</h3>
          <router-link to="/booksList?time_range=week" class="section-more text-success">更多 <i class="fa fa-angle-right"></i></router-link>
        </div>
        <div class="row g-4">
          <div class="col-md-4 col-sm-6" v-for="book in latestBooks" :key="'n'+book.id">
            <BookCard :book="book" />
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
            <BookCard :book="book" />
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
          © 2026 校园书递 版权所有 | 大学生校园二手书籍交易平台
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup>
// 首页：轮播、搜索、推荐、分类、公告、最新/热门书籍
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import Navbar from '@/components/Navbar.vue'
import BookCard from '@/components/BookCard.vue'
import { bookAPI, announcementAPI, discoveryAPI } from '@/utils/api'
import { checkAuth } from '@/utils/auth'
import { isOnline, saveHomeBooks, loadHomeBooks } from '@/utils/offlineStore'

const router = useRouter()
const featureLinks = [  // 特色标签入口
  { to: '/feature/genuine', icon: 'fa-check-circle', label: '正版保障' },
  { to: '/feature/low-price', icon: 'fa-money', label: '低价转让' },
  { to: '/feature/campus-trade', icon: 'fa-map-marker', label: '校园交易' },
  { to: '/feature/new-condition', icon: 'fa-star', label: '9成新以上' },
  { to: '/feature/exchange', icon: 'fa-exchange', label: '支持互换' }
]
const searchKeyword = ref('')
const hotBooks = ref([])
const latestBooks = ref([])
const announcements = ref([])
const loading = ref(false)
const forYouBooks = ref([])
const searchSuggestions = ref([])
let homeSuggestTimer = null

function onHomeSearchInput() {
  // 搜索框输入防抖，拉取联想词
  clearTimeout(homeSuggestTimer)
  const q = searchKeyword.value.trim()
  if (q.length < 1) { searchSuggestions.value = []; return }
  homeSuggestTimer = setTimeout(async () => {
    const res = await discoveryAPI.searchSuggest(q).catch(() => null)
    if (res?.status === 'success') searchSuggestions.value = res.suggestions || []
  }, 280)
}

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
  // 跳转书籍列表并带关键词
  if (searchKeyword.value.trim()) {
    router.push({ path: '/booksList', query: { keyword: searchKeyword.value.trim() } })
  } else {
    router.push('/booksList')
  }
}

async function loadAnnouncements() {
  try {
    const res = await announcementAPI.getAnnouncements()
    if (res.status === 'success') announcements.value = res.announcements || []
  } catch (_) {}
}

async function loadHotBooks() {
  loading.value = true
  try {
    const response = await bookAPI.getBooks({ page_size: 1000 })
    if (response.status === 'success') {
      const books = response.books || []
      latestBooks.value = books.filter(b => b.status === 'available').slice(0, 3)  // 最新 3 本
      hotBooks.value = books
        .filter(book => book.status === 'available')
        .slice(0, 6)  // 热门 6 本
      saveHomeBooks(books)  // 离线缓存
    }
  } catch (error) {
    if (!isOnline()) {  // 断网读本地缓存
      const cached = loadHomeBooks()
      if (cached) {
        latestBooks.value = cached.filter(b => b.status === 'available').slice(0, 3)
        hotBooks.value = cached.filter(b => b.status === 'available').slice(0, 6)
      }
    } else {
      console.error('加载热门书籍失败:', error)
    }
  } finally {
    loading.value = false
  }
}

async function loadForYou() {
  if (!checkAuth()) return  // 登录后才展示「猜你喜欢」
  const res = await discoveryAPI.forYou({ limit: 4 }).catch(() => null)
  if (res?.status === 'success') forYouBooks.value = res.books || []
}

onMounted(() => {
  loadAnnouncements()
  loadHotBooks()
  loadForYou()
})
</script>

