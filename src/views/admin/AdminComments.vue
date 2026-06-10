<template>
  <AdminLayout title="评论审核" :show-refresh="true" @refresh="load">
    <div class="admin-panel">
      <div v-if="!list.length" class="text-muted">暂无待审评论</div>
      <table v-else class="table table-sm">
        <thead><tr><th>书籍</th><th>用户</th><th>内容</th><th>时间</th><th></th></tr></thead>
        <tbody>
          <tr v-for="c in list" :key="c.id">
            <td>{{ c.book_title }}</td>
            <td>{{ c.username }}</td>
            <td class="text-truncate" style="max-width:240px">{{ c.content }}</td>
            <td>{{ c.created_at }}</td>
            <td>
              <button class="btn btn-sm btn-success me-1" @click="audit(c.id, 'approved')">通过</button>
              <button class="btn btn-sm btn-outline-danger" @click="audit(c.id, 'rejected')">驳回</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div class="admin-panel mt-3">
      <h6 class="admin-panel-title">举报处理</h6>
      <table v-if="reports.length" class="table table-sm">
        <thead><tr><th>类型</th><th>对象</th><th>原因</th><th>举报人</th><th></th></tr></thead>
        <tbody>
          <tr v-for="r in reports" :key="r.id">
            <td>{{ r.target_type }}</td>
            <td>{{ r.target_id }}</td>
            <td class="text-truncate" style="max-width:200px">{{ r.reason }}</td>
            <td>{{ r.reporter_name }}</td>
            <td><button class="btn btn-sm btn-secondary" @click="handleReport(r.id)">标记已处理</button></td>
          </tr>
        </tbody>
      </table>
      <div v-else class="text-muted">暂无待处理举报</div>
    </div>
  </AdminLayout>
</template>

<script setup>
// 评论审核：待审列表 + 通过/驳回
import { ref, onMounted } from 'vue'
import AdminLayout from '@/components/admin/AdminLayout.vue'
import { adminAPI } from '@/utils/api'
import { useToast } from '@/composables/useToast'

const { show } = useToast()
const list = ref([])
const reports = ref([])

async function load() {
  const [c, r] = await Promise.all([
    adminAPI.getPendingComments(),
    adminAPI.getReports({ status: 'pending' })
  ])
  if (c.status === 'success') list.value = c.comments || []
  if (r.status === 'success') reports.value = r.reports || []
}

async function audit(id, status) {
  const res = await adminAPI.auditComment(id, { status })
  if (res.status === 'success') { show('已处理', 'success'); load() }
}

async function handleReport(id) {
  const res = await adminAPI.handleReport(id, { status: 'handled' })
  if (res.status === 'success') { show('已处理', 'success'); load() }
}

onMounted(load)
</script>
