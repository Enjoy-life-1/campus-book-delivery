<template>
  <div class="page-container">
    <Navbar />
    <div class="container mt-4">
      <div class="d-flex justify-content-between align-items-center mb-3 flex-wrap gap-2">
        <h2><i class="fa fa-bell text-success"></i> 消息通知</h2>
        <button type="button" class="btn btn-sm btn-outline-success" @click="readAll">全部已读</button>
      </div>
      <div class="btn-group mb-3">
        <button v-for="t in types" :key="t.k" type="button" class="btn btn-sm" :class="typeFilter===t.k?'btn-success':'btn-outline-success'" @click="typeFilter=t.k">{{ t.l }}</button>
      </div>
      <div v-if="loading" class="text-center py-5"><div class="spinner-border text-success"></div></div>
      <div v-else-if="!filtered.length" class="text-center text-muted py-5">暂无通知</div>
      <div v-else class="list-group">
        <a
          v-for="n in filtered"
          :key="n.id"
          href="#"
          class="list-group-item list-group-item-action"
          :class="{ 'list-group-item-light': !n.is_read }"
          @click.prevent="open(n)"
        >
          <div class="d-flex justify-content-between align-items-start">
            <div>
              <span class="badge bg-secondary me-2">{{ typeName(n.ntype) }}</span>
              <span class="badge me-2" :class="n.is_read ? 'bg-light text-muted border' : 'bg-danger'">{{ n.is_read ? '已读' : '未读' }}</span>
              <strong :class="{ 'text-dark': !n.is_read }">{{ n.title }}</strong>
            </div>
            <small class="text-muted">{{ n.created_at }}</small>
          </div>
          <p class="mb-0 small text-secondary">{{ n.content }}</p>
        </a>
      </div>
    </div>
  </div>
</template>

<script setup>
// 站内通知：按 ntype 筛选、已读、跳转 link
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import Navbar from '@/components/Navbar.vue'
import { notificationAPI } from '@/utils/api'

const router = useRouter()
const list = ref([])
const loading = ref(true)
const typeFilter = ref('all')
const types = [
  { k: 'all', l: '全部' },
  { k: 'order', l: '订单' },
  { k: 'offer', l: '议价' },
  { k: 'new_book', l: '匹配' },
  { k: 'appointment', l: '面交' },
  { k: 'audit', l: '审核' }
]

const filtered = computed(() =>
  typeFilter.value === 'all' ? list.value : list.value.filter(n => n.ntype === typeFilter.value)
)

function typeName(t) {
  return { order: '订单', offer: '议价', new_book: '书籍', appointment: '面交', audit: '审核', price_drop: '降价', review: '评价' }[t] || t
}

async function load() {
  loading.value = true
  try {
    const res = await notificationAPI.list()
    if (res.status === 'success') list.value = res.notifications || []
  } finally { loading.value = false }
}

async function open(n) {
  // 点击标记已读并 router.push(link)
  if (!n.is_read) await notificationAPI.read(n.id)
  n.is_read = true
  window.dispatchEvent(new Event('user-updated'))
  if (n.link) {
    const path = n.link.startsWith('/') ? n.link : `/${n.link}`
    router.push(path)
  }
}

async function readAll() {
  await notificationAPI.readAll()
  list.value.forEach(n => { n.is_read = true })
  window.dispatchEvent(new Event('user-updated'))
}

onMounted(load)
</script>
