<template>
  <div class="page-container">
    <Navbar />
    <div class="container mt-4">
      <div class="d-flex justify-content-between align-items-center mb-4">
        <h2><i class="fa fa-bullhorn text-success"></i> 求购广场</h2>
        <button v-if="user" class="btn btn-success" @click="showForm = !showForm">
          <i class="fa fa-plus"></i> 发布求购
        </button>
      </div>
      <ul class="nav nav-tabs mb-3">
        <li class="nav-item"><a class="nav-link" :class="{ active: tab === 'all' }" href="#" @click.prevent="tab='all';load()">全部求购</a></li>
        <li v-if="user" class="nav-item"><a class="nav-link" :class="{ active: tab === 'mine' }" href="#" @click.prevent="tab='mine';load()">我的求购</a></li>
      </ul>
      <div v-if="showForm && user" class="card p-4 mb-4">
        <h5>发布求购</h5>
        <div class="row g-2">
          <div class="col-md-6"><input v-model="form.title" class="form-control" placeholder="书名 *" required></div>
          <div class="col-md-3"><input v-model="form.author" class="form-control" placeholder="作者"></div>
          <div class="col-md-3">
            <div class="input-group">
              <input v-model="form.isbn" class="form-control" placeholder="ISBN">
              <button type="button" class="btn btn-outline-success btn-sm" :disabled="isbnLoading" @click="fillIsbn">查</button>
              <IsbnScanner @scan="(c) => { form.isbn = c; fillIsbn() }" />
            </div>
          </div>
          <div class="col-md-3">
            <select v-model="form.category" class="form-select">
              <option v-for="c in cats" :key="c.code" :value="c.code">{{ c.name }}</option>
            </select>
          </div>
          <div class="col-md-3"><input v-model.number="form.max_price" type="number" class="form-control" placeholder="最高预算(元)"></div>
          <div class="col-md-6"><input v-model="form.desc" class="form-control" placeholder="补充说明"></div>
        </div>
        <button class="btn btn-success mt-3" :disabled="submitting" @click="submit">提交</button>
      </div>
      <div v-if="loading" class="text-center py-5"><div class="spinner-border text-success"></div></div>
      <div v-else-if="!list.length" class="text-center text-muted py-5">暂无求购信息</div>
      <div v-else class="row g-3">
        <div v-for="w in list" :key="w.id" class="col-md-6">
          <div class="card h-100 shadow-sm">
            <div class="card-body">
              <div class="d-flex justify-content-between">
                <h5 class="card-title">{{ w.title }}</h5>
                <span v-if="w.match_count" class="badge bg-success">{{ w.match_count }} 本匹配</span>
              </div>
              <p class="small text-muted mb-1">{{ w.username }} · {{ w.created_at }}</p>
              <p v-if="w.max_price" class="mb-1">预算：¥{{ w.max_price }}</p>
              <p v-if="w.desc" class="small text-secondary">{{ w.desc }}</p>
              <div class="d-flex gap-2 mt-2">
                <router-link :to="`/wanted/${w.id}`" class="btn btn-sm btn-outline-success">查看匹配</router-link>
                <button v-if="tab==='mine' && w.status==='open'" class="btn btn-sm btn-outline-secondary" @click="closeWanted(w.id)">关闭</button>
                <button v-if="tab==='mine'" class="btn btn-sm btn-outline-danger" @click="delWanted(w.id)">删除</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
// 求购广场：发布/匹配数/我的求购管理
import { ref, onMounted } from 'vue'
import Navbar from '@/components/Navbar.vue'
import { wantedAPI, categoryAPI } from '@/utils/api'
import { getCurrentUser } from '@/utils/auth'
import { useToast } from '@/composables/useToast'
import { useIsbnLookup } from '@/composables/useIsbnLookup'
import IsbnScanner from '@/components/IsbnScanner.vue'

const { show } = useToast()
const { loading: isbnLoading, lookup } = useIsbnLookup()
const user = getCurrentUser()
const tab = ref('all')
const list = ref([])
const loading = ref(false)
const showForm = ref(false)
const submitting = ref(false)
const cats = ref([{ code: 'other', name: '其他' }])
const form = ref({ title: '', author: '', isbn: '', category: 'other', max_price: null, desc: '' })

async function load() {
  loading.value = true
  try {
    const res = await wantedAPI.list(tab.value === 'mine' ? { mine: 1 } : {})
    if (res.status === 'success') list.value = res.wanted || []
  } finally { loading.value = false }
}

async function fillIsbn() {
  const r = await lookup(form.value.isbn, (b) => {
    if (b.title) form.value.title = b.title
    if (b.author) form.value.author = b.author
    if (b.isbn) form.value.isbn = b.isbn
  })
  if (r.ok) show('已填充', 'success')
  else show(r.message, 'warning')
}

async function submit() {
  // 创建后自动切到「我的求购」
  if (!form.value.title.trim()) { show('请填写书名', 'warning'); return }
  submitting.value = true
  try {
    const res = await wantedAPI.create(form.value)
    if (res.status === 'success') {
      show('发布成功', 'success')
      showForm.value = false
      form.value = { title: '', author: '', isbn: '', category: 'other', max_price: null, desc: '' }
      tab.value = 'mine'
      load()
    }
  } catch (e) { show(e.message || '发布失败', 'danger') }
  finally { submitting.value = false }
}

async function closeWanted(id) {
  await wantedAPI.update(id, { status: 'closed' })
  show('已关闭', 'info')
  load()
}

async function delWanted(id) {
  if (!confirm('确定删除？')) return
  await wantedAPI.delete(id)
  show('已删除', 'info')
  load()
}

onMounted(async () => {
  const c = await categoryAPI.getCategories()
  if (c.status === 'success' && c.categories?.length) cats.value = c.categories
  load()
})
</script>
