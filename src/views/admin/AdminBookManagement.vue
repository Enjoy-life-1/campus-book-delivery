<template>
  <AdminLayout title="书籍管理" :show-refresh="true" @refresh="load">
    <div class="page-header">
      <h2>书籍审核与管理</h2>
    </div>
    <div class="admin-panel">
      <div class="btn-group mb-3">
        <button v-for="t in tabs" :key="t.k" type="button" class="btn btn-sm" :class="tab===t.k?'btn-success':'btn-outline-success'" @click="tab=t.k;load()">
          {{ t.l }} <span v-if="t.k==='pending'" class="badge bg-danger">{{ pendingCount }}</span>
        </button>
      </div>
      <div class="data-table">
        <table>
          <thead>
            <tr><th>书名</th><th>作者</th><th>价格</th><th>状态</th><th>发布者</th><th>操作</th></tr>
          </thead>
          <tbody>
            <tr v-for="b in list" :key="b.id">
              <td>{{ b.title }}</td>
              <td>{{ b.author }}</td>
              <td>¥{{ formatPrice(b.price) }}</td>
              <td><span class="badge" :class="b.status==='available'?'bg-success':b.status==='pending'?'bg-warning text-dark':'bg-secondary'">{{ getStatusText(b.status) }}</span></td>
              <td>{{ b.owner_name || b.seller }}</td>
              <td>
                <button v-if="b.status==='pending'" type="button" class="btn btn-sm btn-success me-1" @click="approve(b.id)">通过</button>
                <button v-if="b.status==='pending'" type="button" class="btn btn-sm btn-danger me-1" @click="reject(b.id)">驳回</button>
                <button type="button" class="btn btn-sm btn-outline-danger" @click="del(b.id)">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-if="!list.length && !loading" class="p-4 text-center text-muted">暂无数据</div>
      </div>
    </div>
  </AdminLayout>
</template>

<script setup>
// 书籍审核：pending → available，驳回即删除
import { ref, onMounted } from 'vue'
import AdminLayout from '@/components/admin/AdminLayout.vue'
import { bookAPI } from '@/utils/api'
import { formatPrice, getStatusText } from '@/utils/helpers'
import { useToast } from '@/composables/useToast'

const { show } = useToast()
const tab = ref('pending')
const list = ref([])
const loading = ref(false)
const pendingCount = ref(0)
const tabs = [{ k: 'pending', l: '待审核' }, { k: 'all', l: '全部' }, { k: 'available', l: '在售' }]

async function load() {
  loading.value = true
  try {
    const res = await bookAPI.getBooks({ page_size: 2000, include_sold: true })
    let books = res.books || []
    pendingCount.value = books.filter(b => b.status === 'pending').length
    if (tab.value === 'pending') list.value = books.filter(b => b.status === 'pending')
    else if (tab.value === 'available') list.value = books.filter(b => b.status === 'available')
    else list.value = books
  } finally {
    loading.value = false
  }
}

async function approve(id) {
  const res = await bookAPI.updateBook(id, { status: 'available' })
  if (res.status === 'success') { show('已通过审核', 'success'); load() }
}

async function reject(id) {
  if (!confirm('驳回并删除该书籍？')) return
  await bookAPI.deleteBook(id)
  show('已驳回', 'info')
  load()
}

async function del(id) {
  if (!confirm('确定删除？')) return
  await bookAPI.deleteBook(id)
  load()
}

onMounted(load)
</script>
