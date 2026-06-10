<template>
  <AdminLayout title="私信审计" :show-refresh="true" @refresh="loadConvs">
    <div class="page-header"><h2>私信与会话审计</h2></div>
    <div class="row g-3">
      <div class="col-md-5">
        <div class="admin-panel" style="max-height:520px;overflow-y:auto">
          <div v-for="c in convs" :key="c.id" class="border-bottom py-2 cursor-pointer" :class="{ 'bg-light': activeId===c.id }" @click="select(c.id)">
            <strong>{{ c.user_a_name }}</strong> ↔ {{ c.user_b_name }}
            <p class="small text-muted mb-0">{{ c.book_title || '无关联书籍' }} · {{ c.message_count }} 条</p>
            <p class="small mb-0 text-truncate">{{ c.last_preview }}</p>
          </div>
          <p v-if="!convs.length" class="text-muted p-3">暂无会话</p>
        </div>
      </div>
      <div class="col-md-7">
        <div class="admin-panel" style="min-height:400px">
          <div v-if="!activeId" class="text-muted text-center py-5">选择左侧会话查看记录</div>
          <div v-else>
            <p class="small text-muted mb-2">会话 {{ activeId }}</p>
            <div v-for="m in messages" :key="m.id" class="mb-2 p-2 rounded" :class="m.msg_type==='appointment'?'bg-warning-subtle':'bg-light'">
              <div class="small text-muted">{{ m.sender_name }} · {{ m.created_at }} · {{ m.msg_type }}</div>
              <div v-if="m.msg_type==='appointment' && m.appointment">
                [面交] {{ m.appointment.place }} {{ m.appointment.meeting_time }} ({{ m.appointment.status }})
              </div>
              <div v-else>{{ m.content }}</div>
              <span v-if="m.msg_type !== 'system'" class="badge mt-1" :class="m.is_read ? 'bg-light text-muted border' : 'bg-warning text-dark'">{{ m.is_read ? '已读' : '未读' }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </AdminLayout>
</template>

<script setup>
// 私信审计：会话列表 + 消息详情只读
import { ref, onMounted } from 'vue'
import AdminLayout from '@/components/admin/AdminLayout.vue'
import { adminAPI } from '@/utils/api'

const convs = ref([])
const messages = ref([])
const activeId = ref('')

async function loadConvs() {
  const res = await adminAPI.getConversations()
  if (res.status === 'success') convs.value = res.conversations || []
}

async function select(id) {
  activeId.value = id
  const res = await adminAPI.getConversationMessages(id)
  if (res.status === 'success') messages.value = res.messages || []
}

onMounted(loadConvs)
</script>

<style scoped>
.cursor-pointer { cursor: pointer; }
</style>
