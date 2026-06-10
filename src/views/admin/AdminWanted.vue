<template>
  <AdminLayout title="求购审计" :show-refresh="true" @refresh="load">
    <div class="page-header"><h2>求购信息审计</h2></div>
    <div class="admin-panel">
      <div class="data-table">
        <table>
          <thead><tr><th>书名</th><th>用户</th><th>预算</th><th>状态</th><th>匹配</th><th>时间</th><th>操作</th></tr></thead>
          <tbody>
            <tr v-for="w in list" :key="w.id">
              <td>{{ w.title }}</td>
              <td>{{ w.username }}</td>
              <td>{{ w.max_price ? '¥'+w.max_price : '-' }}</td>
              <td><span class="badge" :class="w.status==='open'?'bg-success':'bg-secondary'">{{ w.status }}</span></td>
              <td>{{ w.match_count }}</td>
              <td>{{ w.created_at }}</td>
              <td>
                <router-link :to="`/wanted/${w.id}`" class="btn btn-sm btn-outline-success me-1">查看</router-link>
                <button v-if="w.status==='open'" type="button" class="btn btn-sm btn-outline-secondary me-1" @click="close(w.id)">关闭</button>
                <button type="button" class="btn btn-sm btn-outline-danger" @click="del(w.id)">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
        <p v-if="!list.length" class="text-muted p-3 mb-0">暂无求购</p>
      </div>
    </div>
  </AdminLayout>
</template>

<script setup>
// 求购帖审计：关闭/删除
import { ref, onMounted } from 'vue'
import AdminLayout from '@/components/admin/AdminLayout.vue'
import { adminAPI } from '@/utils/api'
import { useToast } from '@/composables/useToast'

const { show } = useToast()
const list = ref([])

async function load() {
  const res = await adminAPI.getWanted()
  if (res.status === 'success') list.value = res.wanted || []
}

async function close(id) {
  await adminAPI.closeWanted(id)
  show('已关闭', 'info')
  load()
}

async function del(id) {
  if (!confirm('删除该求购？')) return
  await adminAPI.deleteWanted(id)
  show('已删除', 'info')
  load()
}

onMounted(load)
</script>
