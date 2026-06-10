<template>
  <div class="page-container">
    <Navbar />
    <div class="container mt-4">
      <div class="d-flex justify-content-between align-items-center mb-4">
        <h2><i class="fa fa-book text-success"></i> 我的书籍</h2>
        <router-link to="/publishBook" class="btn btn-success"><i class="fa fa-plus"></i> 发布新书籍</router-link>
      </div>
      <div class="btn-group mb-3">
        <button v-for="f in filters" :key="f.k" type="button" class="btn btn-sm" :class="statusFilter === f.k ? 'btn-success' : 'btn-outline-success'" @click="statusFilter = f.k">{{ f.l }}</button>
      </div>
      <LoadError v-if="error" :message="error" @retry="load" />
      <PageLoader v-else-if="loading" />
      <EmptyState v-else-if="!filtered.length" icon="fa-book" title="暂无书籍">
        <router-link to="/publishBook" class="btn btn-success">去发布</router-link>
      </EmptyState>
      <div v-else-if="!error" class="row g-4">
        <div v-for="book in filtered" :key="book.id" class="col-md-6 col-lg-4">
          <div class="card h-100 shadow-sm">
            <img :src="cover(book)" class="card-img-top" style="height:180px;object-fit:cover" alt="">
            <div class="card-body">
              <h6 class="text-truncate">{{ book.title }}</h6>
              <p class="text-success mb-1">¥{{ formatPrice(book.price) }}
                <small v-if="book.is_price_dropping" class="text-danger">降价中</small>
              </p>
              <div class="mb-2">
                <span class="badge" :class="statusClass(book.status)">{{ getStatusText(book.status) }}</span>
                <span v-if="book.campaign_tag" class="badge bg-warning text-dark ms-1">专场</span>
                <span v-if="book.dorm_building" class="badge bg-light text-dark ms-1">{{ book.dorm_building }}</span>
              </div>
              <div class="d-flex flex-wrap gap-1">
                <button v-if="book.status === 'available'" type="button" class="btn btn-sm btn-outline-secondary" @click="toggleStatus(book, 'sold')">标为已售</button>
                <button v-if="book.status === 'sold'" type="button" class="btn btn-sm btn-outline-success" @click="toggleStatus(book, 'available')">重新上架</button>
                <button v-if="book.status === 'sold'" type="button" class="btn btn-sm btn-outline-info" @click="cloneBook(book.id)">复制再发</button>
                <button type="button" class="btn btn-sm btn-outline-secondary" @click="saveTpl(book.id)">存模板</button>
                <button v-if="book.status === 'available' && !book.is_price_dropping" type="button" class="btn btn-sm btn-outline-warning" @click="openDrop(book)">降价</button>
                <router-link :to="`/publishBook?edit=${book.id}`" class="btn btn-sm btn-outline-primary">编辑</router-link>
                <button type="button" class="btn btn-sm btn-outline-danger" @click="removeBook(book.id)">删除</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div v-if="dropBook" class="modal d-block" style="background:rgba(0,0,0,.5)">
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header"><h5>倒计时降价</h5><button type="button" class="btn-close" @click="dropBook=null"></button></div>
          <div class="modal-body">
            <p>当前价 ¥{{ formatPrice(dropBook.price) }}</p>
            <input v-model.number="dropPrice" type="number" step="0.01" class="form-control" placeholder="目标价（须低于现价）">
          </div>
          <div class="mb-2">
            <label class="form-label small">模式</label>
            <select v-model="dropMode" class="form-select form-select-sm">
              <option value="countdown">倒计时一口价</option>
              <option value="ladder">阶梯自动降价</option>
            </select>
          </div>
          <div v-if="dropMode === 'ladder'" class="small text-muted mb-2">
            24h→90% · 48h→80% · 72h→70%（相对目标价比例示例，见下方目标价）
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-success" @click="submitDrop">{{ dropMode === 'ladder' ? '开启阶梯降价' : '开启72小时降价' }}</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
// 卖家书籍管理：上下架、降价、模板、删除
import { ref, computed, onMounted } from 'vue'
import Navbar from '@/components/Navbar.vue'
import PageLoader from '@/components/PageLoader.vue'
import EmptyState from '@/components/EmptyState.vue'
import LoadError from '@/components/LoadError.vue'
import { useAsync } from '@/composables/useAsync'
import { bookAPI, campusAPI, sellerAPI } from '@/utils/api'
import { getCurrentUser } from '@/utils/auth'
import { getStatusText, formatPrice } from '@/utils/helpers'
import { useToast } from '@/composables/useToast'

const { show } = useToast()
const books = ref([])
const { loading, error, run } = useAsync()
const statusFilter = ref('all')
const dropBook = ref(null)
const dropPrice = ref(null)
const dropMode = ref('countdown')
const filters = [
  { k: 'all', l: '全部' },
  { k: 'available', l: '在售' },
  { k: 'pending', l: '待审核' },
  { k: 'sold', l: '已售' }
]

const filtered = computed(() =>
  statusFilter.value === 'all' ? books.value : books.value.filter(b => b.status === statusFilter.value)
)

function cover(book) {
  if (book.imgs?.length) return book.imgs[0]
  return book.cover_url || 'https://picsum.photos/id/24/300/400'
}

function statusClass(s) {
  return { available: 'bg-success', sold: 'bg-secondary', pending: 'bg-warning text-dark' }[s] || 'bg-light'
}

async function cloneBook(id) {
  const res = await bookAPI.cloneBook(id)
  if (res.status === 'success') {
    show(res.message || '已复制', 'success')
    load()
  } else show(res.message || '失败', 'danger')
}

async function load() {
  const user = getCurrentUser()
  await run(async () => {
    const res = await bookAPI.getBooks({ page_size: 1000, include_sold: true, owner_id: user?.id })
    if (res?.status === 'success') {
      books.value = res.books || []
      return
    }
    throw new Error(res?.message || '加载失败')
  })
}

function openDrop(book) {
  dropBook.value = book
  dropPrice.value = Math.max(0.01, (book.price || 0) * 0.9)
}

async function saveTpl(id) {
  await sellerAPI.templateFromBook(id, {})
  show('已存为发布模板', 'success')
}

async function submitDrop() {
  // countdown 或 ladder → /api/books/:id/price-drop
  if (!dropBook.value || !dropPrice.value || dropPrice.value >= dropBook.value.price) {
    return show('目标价须低于现价', 'warning')
  }
  const p = dropPrice.value
  const cur = dropBook.value.price
  const payload = dropMode.value === 'ladder'
    ? {
        mode: 'ladder',
        steps: [
          { hours: 24, price: Math.round(p * 1.1 * 100) / 100 },
          { hours: 48, price: p },
          { hours: 72, price: Math.round(p * 0.9 * 100) / 100 }
        ].filter(s => s.price < cur)
      }
    : { hours: 72, target_price: p, mode: 'countdown' }
  const res = await campusAPI.setPriceDrop(dropBook.value.id, payload)
  if (res.status === 'success') {
    show('降价已开启', 'success')
    dropBook.value = null
    load()
  } else show(res.message, 'error')
}

async function toggleStatus(book, status) {
  const res = await bookAPI.updateBook(book.id, { status })
  if (res.status === 'success') { show('状态已更新', 'success'); load() }
}

async function removeBook(id) {
  if (!confirm('确定删除？')) return
  const res = await bookAPI.deleteBook(id)
  if (res.status === 'success') { show('已删除', 'success'); load() }
}

onMounted(load)
</script>
