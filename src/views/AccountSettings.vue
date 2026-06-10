<template>
  <div class="page-container">
    <Navbar />
    <div class="container mt-4" style="max-width:640px">
      <h2 class="mb-4">账户设置</h2>
      <div v-if="banNotice" class="alert mb-4" :class="banNotice.alertClass">
        <strong><i class="fa fa-exclamation-circle me-1"></i>{{ banNotice.title }}</strong>
        <p class="mb-0 small mt-1">{{ banNotice.detail }}</p>
      </div>
      <div class="card p-4 mb-4 text-center">
        <div class="avatar-lg mb-3 mx-auto">
          <img v-if="avatarPreview" :src="avatarPreview" alt="头像" @error="avatarPreview = ''">
          <i v-else class="fa fa-user-circle avatar-placeholder"></i>
        </div>
        <label class="btn btn-outline-success btn-sm">
          <i class="fa fa-camera"></i> 更换头像
          <input type="file" accept="image/*" hidden @change="onAvatarPick">
        </label>
      </div>
      <div v-if="credit" class="card p-4 mb-4">
        <h5 class="mb-2">我的信用 <span class="badge" :class="creditBadge">{{ credit.level }}</span></h5>
        <div class="progress mb-2" style="height:10px">
          <div class="progress-bar bg-success" :style="{ width: credit.score + '%' }"></div>
        </div>
        <p class="mb-1"><strong>{{ credit.score }}</strong> 分 · {{ credit.credit_tag }}</p>
        <ul v-if="credit.factors?.length" class="small text-muted mb-0 ps-3">
          <li v-for="(f,i) in credit.factors" :key="i">{{ f.label }}（{{ f.delta > 0 ? '+' : '' }}{{ f.delta }}）</li>
        </ul>
        <p v-if="credit.restrict_appointment" class="small text-danger mb-0 mt-2">爽约过多，暂不可发起面交预约</p>
      </div>
      <form @submit.prevent="saveProfile" class="card p-4 mb-4">
        <h5 class="mb-3">基本资料</h5>
        <div class="mb-3"><label class="form-label">用户名</label><input v-model="form.username" class="form-control" required></div>
        <div class="mb-3"><label class="form-label">学校</label><input v-model="form.school" class="form-control" placeholder="用于同校筛选"></div>
        <div class="row">
          <div class="col-md-6 mb-3">
            <label class="form-label">校区</label>
            <select v-model="form.campus_zone" class="form-select">
              <option value="西校区">西校区</option>
              <option value="北校区">北校区</option>
              <option value="校外">校外</option>
            </select>
          </div>
          <div class="col-md-6 mb-3">
            <label class="form-label">宿舍楼栋</label>
            <select v-model="form.dorm_building" class="form-select">
              <option value="">未设置</option>
              <option v-for="d in filteredDorms" :key="d" :value="d">{{ d }}</option>
            </select>
          </div>
        </div>
        <div class="mb-3"><label class="form-label">邮箱</label><input v-model="form.email" type="email" class="form-control"></div>
        <div class="mb-3"><label class="form-label">手机</label><input v-model="form.phone" class="form-control"></div>
        <div class="mb-3"><label class="form-label">个人简介</label><textarea v-model="form.introduction" class="form-control" rows="3"></textarea></div>
        <div class="form-check mb-2"><input v-model="form.notify_email" class="form-check-input" type="checkbox" id="ne"><label class="form-check-label" for="ne">接收邮件通知（需填写邮箱）</label></div>
        <div class="form-check mb-3"><input v-model="form.notify_sms" class="form-check-input" type="checkbox" id="ns"><label class="form-check-label" for="ns">接收短信通知（需填写手机）</label></div>
        <div class="form-check mb-3"><input v-model="form.subscribe_price_drop" class="form-check-input" type="checkbox" id="spd" @change="savePriceSub"><label class="form-check-label" for="spd">收藏书籍降价推送（总开关）</label></div>
        <button type="submit" class="btn btn-success" :disabled="saving">保存资料</button>
      </form>
      <form @submit.prevent="submitVerify" class="card p-4 mb-4">
        <h5 class="mb-3">学籍认证 <span v-if="form.campus_verified" class="badge bg-success">已认证</span></h5>
        <div class="mb-2">
          <label class="form-label">选择学校</label>
          <select v-model="verify.school_id" class="form-select" required>
            <option value="">请选择</option>
            <option v-for="s in schools" :key="s.id" :value="s.id">{{ s.name }}</option>
          </select>
        </div>
        <div class="mb-2"><label class="form-label">学号</label><input v-model="verify.student_id" class="form-control"></div>
        <div class="mb-2"><label class="form-label">校园邮箱</label><input v-model="verify.campus_email" type="email" class="form-control" placeholder="须为本校邮箱后缀"></div>
        <button type="submit" class="btn btn-outline-success" :disabled="form.campus_verified">提交认证</button>
      </form>
      <div class="card p-4 mb-4">
        <h5 class="mb-3">拉黑管理</h5>
        <p v-if="!blocked.length" class="text-muted small mb-0">暂无拉黑用户</p>
        <ul v-else class="list-group list-group-flush">
          <li v-for="u in blocked" :key="u.id" class="list-group-item d-flex justify-content-between px-0">
            <span>{{ u.username }}</span>
            <button type="button" class="btn btn-sm btn-outline-secondary" @click="unblock(u.id)">取消拉黑</button>
          </li>
        </ul>
      </div>
      <form v-if="form.ban_level === 'mute' || form.ban_level === 'ban'" @submit.prevent="submitAppeal" class="card p-4 mb-4 border-danger">
        <h5 class="mb-2 text-danger"><i class="fa fa-gavel me-1"></i>封禁申诉</h5>
        <p class="small text-muted mb-2">如对处理有异议，可提交申诉，管理员将在合规管理中审核。</p>
        <textarea v-model="appealText" class="form-control mb-2" rows="3" placeholder="申诉说明（至少10字）" required></textarea>
        <button type="submit" class="btn btn-outline-danger btn-sm">提交申诉</button>
      </form>
      <form @submit.prevent="changePwd" class="card p-4">
        <h5 class="mb-3">修改密码</h5>
        <div class="mb-3"><input v-model="pwd.old" type="password" class="form-control" placeholder="原密码" required></div>
        <div class="mb-3"><input v-model="pwd.new1" type="password" class="form-control" placeholder="新密码（至少6位）" required></div>
        <div class="mb-3"><input v-model="pwd.new2" type="password" class="form-control" placeholder="确认新密码" required></div>
        <button type="submit" class="btn btn-outline-success">修改密码</button>
      </form>
    </div>
  </div>
</template>

<script setup>
// 账户设置：资料/认证/信用/拉黑/申诉/改密
import { ref, computed, onMounted, watch } from 'vue'
import Navbar from '@/components/Navbar.vue'
import { authAPI, bookAPI, campusAPI, safetyAPI, appealAPI } from '@/utils/api'
import { getCurrentUser } from '@/utils/auth'
import { useUserStore } from '@/stores/user'
import { normalizeCampusZone, dormsForZone, syncDormToZone } from '@/utils/campus'
import { useToast } from '@/composables/useToast'
import { getBanNotice } from '@/utils/banStatus'
import { normalizeAvatar } from '@/utils/helpers'

const { show } = useToast()
const avatarPreview = ref('')
const dormCatalog = ref(null)
const form = ref({ username: '', school: '', campus_zone: '西校区', dorm_building: '', introduction: '', email: '', phone: '', avatar: '', notify_email: true, notify_sms: true, subscribe_price_drop: true, campus_verified: false, ban_level: 'none', ban_until: '', ban_reason: '' })
const filteredDorms = computed(() => dormsForZone(dormCatalog.value, form.value.campus_zone))
watch(() => form.value.campus_zone, () => syncDormToZone(form.value, dormCatalog.value))
const appealText = ref('')
const schools = ref([])
const verify = ref({ school_id: '', student_id: '', campus_email: '' })
const blocked = ref([])
const pwd = ref({ old: '', new1: '', new2: '' })
const saving = ref(false)
const credit = ref(null)
const creditBadge = computed(() => {
  const s = credit.value?.score ?? 0
  if (s >= 90) return 'bg-success'
  if (s >= 75) return 'bg-primary'
  if (s >= 60) return 'bg-warning text-dark'
  return 'bg-danger'
})
const banNotice = computed(() => getBanNotice(form.value))

async function load() {
  // 拉用户资料、学校列表、信用分、拉黑列表
  const [res, sc, cr] = await Promise.all([
    authAPI.getUserInfo(),
    campusAPI.getSchools(),
    authAPI.getMyCredit().catch(() => null)
  ])
  if (cr?.status === 'success') credit.value = cr.credit
  if (res.status === 'success' && res.user) {
    form.value = { ...form.value, ...res.user, campus_zone: normalizeCampusZone(res.user.campus_zone) }
    syncDormToZone(form.value, dormCatalog.value)
    verify.value.student_id = res.user.student_id || ''
    verify.value.campus_email = res.user.campus_email || ''
    verify.value.school_id = res.user.school_id || ''
    avatarPreview.value = normalizeAvatar(res.user.avatar)
  }
  if (sc.status === 'success') schools.value = sc.schools || []
  const bl = await safetyAPI.blockList()
  if (bl.status === 'success') blocked.value = bl.blocked || []
}

async function unblock(uid) {
  const res = await safetyAPI.unblock(uid)
  if (res.status === 'success') { show('已取消拉黑', 'success'); load() }
}

async function submitVerify() {
  // 校园邮箱后缀校验 → campus_verified
  const res = await campusAPI.verifyCampus(verify.value)
  if (res.status === 'success') {
    show('认证成功', 'success')
    form.value = { ...form.value, ...res.user }
    useUserStore().setUser(res.user)
  } else show(res.message || '认证失败', 'danger')
}

async function onAvatarPick(e) {
  const file = e.target.files?.[0]
  if (!file) return
  e.target.value = ''
  if (file.size > 2 * 1024 * 1024) return show('头像不能超过2MB', 'error')
  const fd = new FormData()
  fd.append('file', file)
  try {
    const up = await bookAPI.uploadImage(fd)
    if (up.status !== 'success' || !up.url) return show(up.message || '上传失败', 'error')
    const res = await authAPI.updateUserInfo({ avatar: up.url })
    if (res.status === 'success') {
      const avatar = normalizeAvatar(res.user?.avatar || up.url)
      avatarPreview.value = avatar
      form.value.avatar = avatar
      useUserStore().setUser({ ...getCurrentUser(), avatar })
      show('头像已更新', 'success')
    } else show(res.message || '保存失败', 'error')
  } catch (err) {
    show(err.message || '上传失败', 'error')
  }
}

async function saveProfile() {
  saving.value = true
  try {
    const { avatar, ...profile } = form.value
    const res = await authAPI.updateUserInfo(profile)
    if (res.status === 'success') {
      useUserStore().setUser({ ...getCurrentUser(), ...form.value })
      show('资料已保存', 'success')
    } else show(res.message, 'error')
  } finally {
    saving.value = false
  }
}

async function savePriceSub() {
  await authAPI.subscribePriceDrop({ enabled: form.value.subscribe_price_drop })
}

async function submitAppeal() {
  const res = await appealAPI.submit({ content: appealText.value })
  if (res.status === 'success') {
    show('申诉已提交', 'success')
    appealText.value = ''
  } else show(res.message || '提交失败', 'danger')
}

async function changePwd() {
  if (pwd.value.new1 !== pwd.value.new2) return show('两次密码不一致', 'error')
  const res = await authAPI.changePassword({
    oldPassword: pwd.value.old, newPassword: pwd.value.new1, confirmPassword: pwd.value.new2
  })
  if (res.status === 'success') {
    show('密码已修改', 'success')
    pwd.value = { old: '', new1: '', new2: '' }
  } else show(res.message || '修改失败', 'error')
}

onMounted(async () => {
  const dr = await campusAPI.getDorms()
  if (dr.status === 'success') dormCatalog.value = dr
  await load()
})
</script>

<style scoped>
.avatar-lg { width: 100px; height: 100px; border-radius: 50%; border: 3px solid #28a745; overflow: hidden; display: flex; align-items: center; justify-content: center; }
.avatar-lg img { width: 100%; height: 100%; object-fit: cover; }
.avatar-placeholder { font-size: 88px; color: #ccc; line-height: 1; }
</style>
