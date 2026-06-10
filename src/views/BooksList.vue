<template>
  <div class="page-container">
    <Navbar />
    <div class="container mt-4">
      <h2 class="mb-3">全部书籍</h2>
      <div class="card p-3 mb-4 filter-card">
        <div class="row g-2 align-items-end">
          <div class="col-md-3">
            <label class="form-label small">搜索</label>
            <input v-model="search" class="form-control" placeholder="书名 / 作者 / ISBN" list="searchSuggestList" @input="onSearchInput" @keyup.enter="load">
            <datalist id="searchSuggestList">
              <option v-for="s in suggestions" :key="s.text" :value="s.text" />
            </datalist>
          </div>
          <div class="col-md-2">
            <label class="form-label small">分类</label>
            <select v-model="category" class="form-select" @change="load">
              <option value="">全部</option>
              <option v-for="c in cats" :key="c.code" :value="c.code">{{ c.name }}</option>
            </select>
          </div>
          <div class="col-md-2">
            <label class="form-label small">宿舍楼</label>
            <select v-model="dormBuilding" class="form-select" @change="load">
              <option value="">全部楼栋</option>
              <option v-for="d in dorms" :key="d" :value="d">{{ d }}</option>
            </select>
          </div>
          <div class="col-md-2">
            <label class="form-label small">排序</label>
            <select v-model="sortBy" class="form-select" @change="load">
              <option value="newest">最新发布</option>
              <option value="oldest">最早发布</option>
              <option value="price_asc">价格从低到高</option>
              <option value="price_desc">价格从高到低</option>
              <option value="title">书名 A-Z</option>
            </select>
          </div>
          <div class="col-md-2">
            <label class="form-label small">价格</label>
            <select v-model="priceRange" class="form-select" @change="load">
              <option value="all">全部</option>
              <option value="0-50">0-50元</option>
              <option value="50-100">50-100元</option>
              <option value="100+">100元以上</option>
            </select>
          </div>
          <div class="col-md-2">
            <label class="form-label small">课程</label>
            <select v-model="courseCode" class="form-select" @change="load">
              <option value="">全部</option>
              <option v-for="c in courseList" :key="c.course_code" :value="c.course_code">{{ c.course_name }}</option>
            </select>
          </div>
          <div class="col-md-2">
            <div class="form-check mt-2">
              <input v-model="sameSchool" class="form-check-input" type="checkbox" id="sameSchool" @change="load">
              <label class="form-check-label small" for="sameSchool">仅同校</label>
            </div>
            <div class="form-check">
              <input v-model="verifiedOnly" class="form-check-input" type="checkbox" id="verifiedOnly" @change="load">
              <label class="form-check-label small" for="verifiedOnly">认证卖家</label>
            </div>
            <button type="button" class="btn btn-success w-100 mt-1" @click="load"><i class="fa fa-search"></i> 筛选</button>
          </div>
        </div>
      </div>
      <p v-if="offlineMode" class="alert alert-warning py-2 small mb-2">离线模式：显示上次缓存的书籍列表</p>
      <LoadError v-if="error" :message="error" @retry="load" />
      <p v-if="!loading && !error" class="text-muted small">共 {{ books.length }} 本</p>
      <PageLoader v-if="loading" />
      <EmptyState v-else-if="!error && !books.length" icon="fa-search" title="没有找到符合条件的书籍" />
      <div v-else-if="!error && books.length" class="row g-4">
        <div v-for="book in books" :key="book.id" class="col-md-4 col-lg-3">
          <BookCard :book="book" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
// 书籍列表：多条件筛选 + 搜索联想 + 离线缓存
import { ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import Navbar from '@/components/Navbar.vue'
import BookCard from '@/components/BookCard.vue'
import PageLoader from '@/components/PageLoader.vue'
import EmptyState from '@/components/EmptyState.vue'
import LoadError from '@/components/LoadError.vue'
import { useAsync } from '@/composables/useAsync'
import { bookAPI, categoryAPI, campusAPI, discoveryAPI } from '@/utils/api'
import { getCurrentUser } from '@/utils/auth'
import { isOnline, saveBooksList, loadBooksList } from '@/utils/offlineStore'

const route = useRoute()
const user = getCurrentUser()
const books = ref([])
const cats = ref([])
const dorms = ref([])
const { loading, error, run } = useAsync()
const search = ref('')
const category = ref('')
const priceRange = ref('all')
const timeRange = ref('all')
const dormBuilding = ref('')
const sameSchool = ref(false)
const verifiedOnly = ref(false)
const courseCode = ref('')
const courseList = ref([])
const sortBy = ref('newest')
const suggestions = ref([])
const offlineMode = ref(false)
let suggestTimer = null

function listCacheKey() {
  // 离线缓存键：随筛选条件变化
  return [category.value, search.value, sortBy.value, dormBuilding.value, sameSchool.value].join('|')
}

function onSearchInput() {
  // 防抖 280ms 拉搜索建议
  clearTimeout(suggestTimer)
  const q = search.value.trim()
  if (q.length < 1) { suggestions.value = []; return }
  suggestTimer = setTimeout(async () => {
    const res = await discoveryAPI.searchSuggest(q).catch(() => null)
    if (res?.status === 'success') suggestions.value = res.suggestions || []
  }, 280)
}

function syncQuery() {
  // URL query → 筛选表单（首页/专场跳转带参）
  search.value = route.query.keyword || route.query.search || ''
  category.value = route.query.category || ''
  timeRange.value = route.query.time_range || 'all'
  dormBuilding.value = route.query.dorm || ''
  courseCode.value = route.query.course_code || ''
  sameSchool.value = route.query.same_school === '1' || route.query.same_school === 'true'
}

async function loadCats() {
  const res = await categoryAPI.getCategories()
  if (res.status === 'success') cats.value = res.categories || []
}

async function load() {
  // 请求 /api/books；失败且离线则读 IndexedDB 缓存
  offlineMode.value = false
  const key = listCacheKey()
  await run(async () => {
    const res = await bookAPI.getBooks({
      category: category.value || undefined,
      search: search.value || undefined,
      priceRange: priceRange.value !== 'all' ? priceRange.value : undefined,
      time_range: timeRange.value !== 'all' ? timeRange.value : undefined,
      dorm_building: dormBuilding.value || undefined,
      same_school: sameSchool.value && user ? 'true' : undefined,
      verified_only: verifiedOnly.value ? 'true' : undefined,
      campaign: route.query.campaign || undefined,
      course_code: courseCode.value || undefined,
      sort_by: sortBy.value,
      page_size: 1000
    })
    if (res?.status === 'success') {
      books.value = res.books || []
      saveBooksList(books.value, key)
      return
    }
    throw new Error(res?.message || '加载失败')
  })
  if (error.value && !isOnline()) {
    const cached = loadBooksList(key) || loadBooksList('default')
    if (cached) {
      books.value = cached
      offlineMode.value = true
      error.value = ''
    }
  }
}

watch(() => route.query, () => { syncQuery(); load() })

onMounted(async () => {
  syncQuery()
  const [dr, cr] = await Promise.all([campusAPI.getDorms(), campusAPI.getCourses()])
  if (dr.status === 'success') dorms.value = dr.dorms || []
  if (cr.status === 'success') courseList.value = cr.courses || []
  await loadCats()
  load()
})
</script>

<style scoped>
.filter-card { background: #f8fdf8; border: 1px solid #d4edda; }
</style>
