<template>
  <AdminLayout title="合规管理" :show-refresh="true" @refresh="loadAll">
    <ul class="nav nav-tabs mb-3">
      <li v-for="t in tabs" :key="t.k" class="nav-item">
        <button type="button" class="nav-link" :class="{ active: tab === t.k }" @click="tab = t.k">{{ t.l }}</button>
      </li>
    </ul>

    <div v-if="tab === 'words'" class="admin-panel">
      <form class="row g-2 mb-3" @submit.prevent="addWord">
        <div class="col-md-4"><input v-model="newWord.word" class="form-control form-control-sm" placeholder="敏感词" required></div>
        <div class="col-md-3">
          <select v-model="newWord.scope" class="form-select form-select-sm">
            <option value="all">全部</option>
            <option value="comment">评论</option>
            <option value="message">私信</option>
          </select>
        </div>
        <div class="col-md-2"><button class="btn btn-sm btn-success w-100">添加</button></div>
      </form>
      <table class="table table-sm"><thead><tr><th>词</th><th>范围</th><th></th></tr></thead>
        <tbody><tr v-for="w in words" :key="w.id"><td>{{ w.word }}</td><td>{{ w.scope }}</td>
          <td><button class="btn btn-sm btn-outline-danger" @click="delWord(w.id)">删</button></td></tr></tbody>
      </table>
    </div>

    <div v-if="tab === 'isbn'" class="admin-panel">
      <form class="row g-2 mb-3" @submit.prevent="addIsbn">
        <div class="col-md-4"><input v-model="newIsbn.isbn" class="form-control form-control-sm" placeholder="ISBN" required></div>
        <div class="col-md-5"><input v-model="newIsbn.reason" class="form-control form-control-sm" placeholder="原因"></div>
        <div class="col-md-2"><button class="btn btn-sm btn-success w-100">加入黑名单</button></div>
      </form>
      <table class="table table-sm"><thead><tr><th>ISBN</th><th>原因</th><th></th></tr></thead>
        <tbody><tr v-for="i in isbns" :key="i.id"><td>{{ i.isbn }}</td><td>{{ i.reason }}</td>
          <td><button class="btn btn-sm btn-outline-danger" @click="delIsbn(i.id)">移除</button></td></tr></tbody>
      </table>
    </div>

    <div v-if="tab === 'ban'" class="admin-panel">
      <p class="small text-muted">在用户管理中可对用户执行 warning / mute / ban；此处处理申诉。</p>
      <table class="table table-sm">
        <thead><tr><th>用户</th><th>封禁级别</th><th>申诉</th><th>状态</th><th>操作</th></tr></thead>
        <tbody>
          <tr v-for="a in appeals" :key="a.id">
            <td>{{ a.username }}</td>
            <td>{{ a.ban_level }}</td>
            <td class="small" style="max-width:200px">{{ a.content }}</td>
            <td><span class="badge" :class="a.status === 'pending' ? 'bg-warning text-dark' : 'bg-secondary'">{{ a.status }}</span></td>
            <td>
              <template v-if="a.status === 'pending'">
                <button class="btn btn-sm btn-success me-1" @click="handleAppeal(a.id, 'approved')">通过</button>
                <button class="btn btn-sm btn-outline-danger" @click="handleAppeal(a.id, 'rejected')">驳回</button>
              </template>
              <small v-else class="text-muted">{{ a.admin_reply }}</small>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-if="!appeals.length" class="text-muted mb-0">暂无申诉</p>
    </div>

    <div v-if="tab === 'logs'" class="admin-panel">
      <div class="data-table" style="max-height:420px;overflow-y:auto">
        <table><thead><tr><th>时间</th><th>管理员</th><th>操作</th><th>目标</th><th>详情</th></tr></thead>
          <tbody><tr v-for="l in logs" :key="l.id"><td>{{ l.created_at }}</td><td>{{ l.admin_name }}</td><td>{{ l.action }}</td>
            <td>{{ l.target_type }} {{ l.target_id }}</td><td class="small text-truncate" style="max-width:180px">{{ l.detail }}</td></tr></tbody>
        </table>
      </div>
    </div>

    <div v-if="tab === 'report'" class="admin-panel">
      <p class="mb-2">导出近 7 天 / 30 天运营汇总 CSV（含订单明细）。</p>
      <a href="/api/admin/reports/periodic?period=week" class="btn btn-outline-success btn-sm me-2" download>周报 CSV</a>
      <a href="/api/admin/reports/periodic?period=month" class="btn btn-outline-success btn-sm" download>月报 CSV</a>
    </div>
  </AdminLayout>
</template>

<script setup>
// 合规：敏感词/ISBN 黑名单/举报/申诉/审计日志
import { ref, onMounted } from 'vue'
import AdminLayout from '@/components/admin/AdminLayout.vue'
import { adminAPI } from '@/utils/api'
import { useToast } from '@/composables/useToast'

const { show } = useToast()
const tab = ref('words')
const tabs = [
  { k: 'words', l: '敏感词' },
  { k: 'isbn', l: 'ISBN 黑名单' },
  { k: 'ban', l: '封禁申诉' },
  { k: 'logs', l: '操作日志' },
  { k: 'report', l: '周期报表' }
]
const words = ref([])
const isbns = ref([])
const appeals = ref([])
const logs = ref([])
const newWord = ref({ word: '', scope: 'all' })
const newIsbn = ref({ isbn: '', reason: '' })

async function loadAll() {
  const [w, i, a, l] = await Promise.all([
    adminAPI.getSensitiveWords(),
    adminAPI.getIsbnBlacklist(),
    adminAPI.getBanAppeals(),
    adminAPI.getAuditLogs()
  ])
  if (w.status === 'success') words.value = w.words || []
  if (i.status === 'success') isbns.value = i.items || []
  if (a.status === 'success') appeals.value = a.appeals || []
  if (l.status === 'success') logs.value = l.logs || []
}

async function addWord() {
  await adminAPI.addSensitiveWord(newWord.value)
  newWord.value = { word: '', scope: 'all' }
  show('已添加', 'success')
  loadAll()
}

async function delWord(id) {
  await adminAPI.deleteSensitiveWord(id)
  loadAll()
}

async function addIsbn() {
  await adminAPI.addIsbnBlacklist(newIsbn.value)
  newIsbn.value = { isbn: '', reason: '' }
  show('已加入黑名单', 'success')
  loadAll()
}

async function delIsbn(id) {
  await adminAPI.deleteIsbnBlacklist(id)
  loadAll()
}

async function handleAppeal(id, status) {
  const reply = status === 'approved' ? '申诉通过，已解除限制' : '申诉未通过'
  await adminAPI.handleBanAppeal(id, { status, admin_reply: reply })
  show('已处理', 'success')
  loadAll()
}

onMounted(loadAll)
</script>
