<template>
  <AdminLayout title="用户管理" :show-refresh="true" @refresh="load">
    <div class="page-header d-flex justify-content-between align-items-center flex-wrap gap-2">
      <h2>用户管理</h2>
      <button type="button" class="btn btn-success btn-sm" @click="showAdd = true"><i class="fa fa-plus me-1"></i>添加用户</button>
    </div>
    <div class="admin-panel">
      <div class="data-table">
        <table>
          <thead>
            <tr>
              <th>用户名</th><th>手机</th><th>邮箱</th><th>认证</th><th>角色</th><th>封禁</th><th>注册时间</th><th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="u in users" :key="u.id">
              <td>{{ u.username }}</td>
              <td>{{ u.phone || '-' }}</td>
              <td>{{ u.email || '-' }}</td>
              <td>
                <span v-if="u.campus_verified" class="badge bg-primary">已认证</span>
                <span v-else class="badge bg-secondary">未认证</span>
              </td>
              <td><span class="badge" :class="roleBadge(u.role)">{{ roleLabel(u.role) }}</span></td>
              <td>
                <span v-if="u.ban_level && u.ban_level !== 'none'" class="badge bg-danger">{{ u.ban_level }}</span>
                <span v-else class="text-muted">-</span>
              </td>
              <td>{{ u.created_at || '-' }}</td>
              <td>
                <button type="button" class="btn btn-sm btn-outline-primary me-1" @click="openEdit(u)">编辑</button>
                <button type="button" class="btn btn-sm btn-outline-warning me-1" :disabled="u.id === currentId" @click="openBan(u)">封禁</button>
                <button type="button" class="btn btn-sm btn-outline-danger" :disabled="u.id === currentId" @click="removeUser(u)">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div v-if="showAdd || editing" class="modal d-block" style="background:rgba(0,0,0,.5)">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5>{{ editing ? '编辑用户' : '添加用户' }}</h5>
            <button type="button" class="btn-close" @click="closeModal"></button>
          </div>
          <form @submit.prevent="saveUser">
            <div class="modal-body">
              <div class="mb-3"><label>用户名</label><input v-model="form.username" class="form-control" required :disabled="!!editing"></div>
              <div class="mb-3"><label>密码{{ editing ? '（留空不改）' : '' }}</label><input v-model="form.password" type="password" class="form-control" :required="!editing"></div>
              <div class="mb-3"><label>手机</label><input v-model="form.phone" class="form-control"></div>
              <div class="mb-3"><label>邮箱</label><input v-model="form.email" type="email" class="form-control"></div>
              <div class="mb-3">
                <label>角色</label>
                <select v-model="form.role" class="form-select">
                  <option value="student">学生</option>
                  <option value="moderator">审核员</option>
                  <option value="admin">超级管理员</option>
                </select>
              </div>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" @click="closeModal">取消</button>
              <button type="submit" class="btn btn-success">保存</button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <div v-if="banUser" class="modal d-block" style="background:rgba(0,0,0,.5)">
      <div class="modal-dialog modal-sm">
        <div class="modal-content">
          <div class="modal-header"><h5>封禁 {{ banUser.username }}</h5><button type="button" class="btn-close" @click="banUser = null"></button></div>
          <div class="modal-body">
            <select v-model="banForm.level" class="form-select form-select-sm mb-2">
              <option value="warning">警告</option>
              <option value="mute">禁言</option>
              <option value="ban">封禁</option>
            </select>
            <input v-model.number="banForm.days" type="number" min="0" class="form-control form-control-sm mb-2" placeholder="天数（0=永久）">
            <input v-model="banForm.reason" class="form-control form-control-sm" placeholder="原因">
          </div>
          <div class="modal-footer">
            <button v-if="banUser.ban_level && banUser.ban_level !== 'none'" type="button" class="btn btn-sm btn-outline-success" @click="doUnban">解除</button>
            <button type="button" class="btn btn-sm btn-danger" @click="doBan">确认</button>
          </div>
        </div>
      </div>
    </div>
  </AdminLayout>
</template>

<script setup>
// 用户 CRUD + 封禁/解封（adminAPI）
import { ref, onMounted } from 'vue'
import AdminLayout from '@/components/admin/AdminLayout.vue'
import { adminAPI } from '@/utils/api'
import { getCurrentUser } from '@/utils/auth'
import { useToast } from '@/composables/useToast'

const { show } = useToast()
const currentId = getCurrentUser()?.id
const users = ref([])
const showAdd = ref(false)
const editing = ref(null)
const form = ref({ username: '', password: '', phone: '', email: '', role: 'student' })
const banUser = ref(null)
const banForm = ref({ level: 'mute', days: 7, reason: '违反平台规则' })

function roleLabel(r) {
  return { admin: '超级管理员', moderator: '审核员', student: '学生' }[r] || r
}
function roleBadge(r) {
  return { admin: 'bg-danger', moderator: 'bg-warning text-dark', student: 'bg-success' }[r] || 'bg-secondary'
}

async function load() {
  const res = await adminAPI.getUsers()
  if (res.status === 'success') users.value = res.users || []
}

function openEdit(u) {
  editing.value = u
  form.value = { username: u.username, password: '', phone: u.phone || '', email: u.email || '', role: u.role || 'student' }
}

function openBan(u) {
  banUser.value = u
  banForm.value = { level: 'mute', days: 7, reason: u.ban_reason || '违反平台规则' }
}

async function doBan() {
  await adminAPI.banUser(banUser.value.id, banForm.value)
  show('已处理', 'success')
  banUser.value = null
  load()
}

async function doUnban() {
  await adminAPI.unbanUser(banUser.value.id)
  show('已解除', 'success')
  banUser.value = null
  load()
}

function closeModal() {
  showAdd.value = false
  editing.value = null
  form.value = { username: '', password: '', phone: '', email: '', role: 'student' }
}

async function saveUser() {
  try {
    let res
    if (editing.value) {
      const data = { username: form.value.username, phone: form.value.phone, email: form.value.email, role: form.value.role }
      if (form.value.password) data.password = form.value.password
      res = await adminAPI.updateUser(editing.value.id, data)
    } else {
      res = await adminAPI.createUser({ ...form.value, is_admin: form.value.role === 'admin' })
    }
    if (res.status === 'success') {
      show('保存成功', 'success')
      closeModal()
      load()
    } else show(res.message, 'error')
  } catch (e) {
    show(e.message, 'error')
  }
}

async function removeUser(u) {
  if (!confirm(`删除用户 ${u.username}？`)) return
  try {
    const res = await adminAPI.deleteUser(u.id)
    if (res.status === 'success') { show('已删除', 'success'); load() }
    else show(res.message, 'error')
  } catch (e) {
    show(e.message, 'error')
  }
}

onMounted(load)
</script>
