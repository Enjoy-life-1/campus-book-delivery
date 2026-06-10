<template>
  <div class="page-container">
    <Navbar />
    <div class="container mt-4">
      <div class="card profile-card p-4 mb-4" v-if="user">
        <div class="row align-items-center">
          <div class="col-auto">
            <div class="profile-avatar-wrap">
              <img v-if="userAvatar" :src="userAvatar" class="profile-avatar" alt="" @error="avatarBroken = true">
              <i v-else class="fa fa-user-circle profile-avatar-placeholder"></i>
            </div>
          </div>
          <div class="col">
            <h3>{{ user.username }}
              <span v-if="user.campus_verified" class="badge bg-success ms-1">已认证</span>
              <span v-if="banBadge" class="badge ms-1" :class="banBadge.cls">{{ banBadge.text }}</span>
            </h3>
            <p class="text-muted mb-1">
              <i class="fa fa-university"></i> {{ user.school || '未填写学校' }}
              <span v-if="displayZone" class="badge ms-1" :class="zoneBadgeClass">{{ displayZone }}</span>
              <span v-if="user.dorm_building" class="ms-1">· {{ user.dorm_building }}</span>
            </p>
            <p v-if="campusAddress" class="small text-muted mb-1"><i class="fa fa-map-marker"></i> {{ campusAddress }}</p>
            <p class="mb-0">{{ user.introduction || '这个人很懒，什么都没写' }}</p>
          </div>
          <div class="col-auto">
            <router-link to="/accountSettings" class="btn btn-outline-success">编辑资料</router-link>
          </div>
        </div>
      </div>
      <div class="card p-3 mb-4" v-if="user">
        <h6 class="mb-3"><i class="fa fa-building-o text-success"></i> 校园信息</h6>
        <div class="row g-2 align-items-end">
          <div class="col-md-4">
            <label class="form-label small mb-1">校区</label>
            <select v-model="campusForm.campus_zone" class="form-select form-select-sm">
              <option v-for="z in campusZones" :key="z" :value="z">{{ z }}</option>
            </select>
          </div>
          <div class="col-md-4">
            <label class="form-label small mb-1">宿舍楼栋</label>
            <select v-model="campusForm.dorm_building" class="form-select form-select-sm">
              <option value="">未设置</option>
              <option v-for="d in filteredDorms" :key="d" :value="d">{{ d }}</option>
            </select>
          </div>
          <div class="col-md-4">
            <button type="button" class="btn btn-success btn-sm w-100" :disabled="campusSaving" @click="saveCampus">
              保存校区信息
            </button>
          </div>
        </div>
      </div>
      <div class="row g-3 mb-4">
        <div v-for="s in stats" :key="s.label" class="col-6 col-md-3">
          <div class="card text-center p-3 stat-card">
            <h3 class="text-success mb-0">{{ s.value }}</h3>
            <small class="text-muted">{{ s.label }}</small>
          </div>
        </div>
      </div>
      <div v-if="sellerStats" class="row g-3 mb-4">
        <div class="col-12"><small class="text-muted">卖家数据 · {{ sellerStats.credit_tag }}</small></div>
        <div v-for="s in sellerCards" :key="s.label" class="col-6 col-md-3">
          <div class="card text-center p-3 stat-card border-success border-opacity-25">
            <h3 class="text-success mb-0">{{ s.value }}</h3>
            <small class="text-muted">{{ s.label }}</small>
          </div>
        </div>
      </div>
      <h5 class="mb-3">快捷入口</h5>
      <div class="row g-3">
        <div v-for="link in links" :key="link.to" class="col-6 col-md-4">
          <router-link :to="link.to" class="quick-link card p-3 text-decoration-none text-dark text-center">
            <i :class="['fa', link.icon, 'fa-2x text-success mb-2']"></i>
            <div>{{ link.label }}</div>
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
// 个人中心：资料展示、校区编辑、买卖统计、快捷入口
import { ref, computed, onMounted, watch } from 'vue'
import Navbar from '@/components/Navbar.vue'
import { authAPI, bookAPI, collectionAPI, orderAPI, sellerAPI, campusAPI } from '@/utils/api'
import { getCurrentUser, saveUser } from '@/utils/auth'
import { CAMPUS_ZONES, CAMPUS_ADDRESSES, normalizeCampusZone, dormsForZone, syncDormToZone } from '@/utils/campus'
import { banLevelLabel } from '@/utils/banStatus'
import { useToast } from '@/composables/useToast'
import { normalizeAvatar } from '@/utils/helpers'

const { show } = useToast()
const user = ref(getCurrentUser())
const avatarBroken = ref(false)
const userAvatar = computed(() => {
  if (avatarBroken.value) return ''
  return normalizeAvatar(user.value?.avatar)
})
const campusZones = CAMPUS_ZONES
const dormCatalog = ref(null)
const campusForm = ref({ campus_zone: '西校区', dorm_building: '' })
const campusSaving = ref(false)

const displayZone = computed(() => normalizeCampusZone(user.value?.campus_zone))
const campusAddress = computed(() => CAMPUS_ADDRESSES[displayZone.value] || '')
const zoneBadgeClass = computed(() => {
  const z = displayZone.value
  if (z === '北校区') return 'bg-warning text-dark'
  if (z === '校外') return 'bg-secondary'
  return 'bg-success'
})
const banBadge = computed(() => {
  const level = user.value?.ban_level
  if (!level || level === 'none') return null
  return {
    text: banLevelLabel(level),
    cls: level === 'warning' ? 'bg-warning text-dark' : level === 'mute' ? 'bg-info' : 'bg-danger'
  }
})
const filteredDorms = computed(() => dormsForZone(dormCatalog.value, campusForm.value.campus_zone))

watch(() => campusForm.value.campus_zone, () => {
  syncDormToZone(campusForm.value, dormCatalog.value)
})

function syncCampusForm(u) {
  campusForm.value = {
    campus_zone: normalizeCampusZone(u?.campus_zone),
    dorm_building: u?.dorm_building || ''
  }
  syncDormToZone(campusForm.value, dormCatalog.value)
}

async function saveCampus() {
  // 同步 campus_zone / dorm_building 到服务端
  campusSaving.value = true
  try {
    const payload = { campus_zone: campusForm.value.campus_zone, dorm_building: campusForm.value.dorm_building }
    const res = await authAPI.updateUserInfo(payload)
    if (res.status === 'success') {
      user.value = { ...user.value, ...payload }
      saveUser(user.value)
      show('校区信息已保存', 'success')
    } else show(res.message || '保存失败', 'danger')
  } finally {
    campusSaving.value = false
  }
}
const stats = ref([
  { label: '在售书籍', value: 0 },
  { label: '我的收藏', value: 0 },
  { label: '交易订单', value: 0 },
  { label: '待面交', value: 0 }
])
const sellerStats = ref(null)
const sellerCards = computed(() => {
  const s = sellerStats.value
  if (!s) return []
  return [
    { label: '累计浏览', value: s.total_views ?? 0 },
    { label: '转化率(%)', value: s.conversion_rate ?? 0 },
    { label: '成交笔数', value: s.completed_count ?? 0 },
    { label: '本月成交', value: s.month_sales ?? 0 }
  ]
})
const links = [
  { to: '/publishBook', label: '发布书籍', icon: 'fa-plus-circle' },
  { to: '/courses', label: '按课找书', icon: 'fa-graduation-cap' },
  { to: '/mySchedule', label: '课表挂书', icon: 'fa-calendar' },
  { to: '/campus/map', label: '宿舍地图', icon: 'fa-map-marker' },
  { to: '/semester', label: '学期专场', icon: 'fa-calendar' },
  { to: '/wanted', label: '求购广场', icon: 'fa-bullhorn' },
  { to: '/messages', label: '站内消息', icon: 'fa-envelope' },
  { to: '/notifications', label: '消息通知', icon: 'fa-bell' },
  { to: '/offers', label: '议价管理', icon: 'fa-handshake-o' },
  { to: '/myBooks', label: '我的书籍', icon: 'fa-book' },
  { to: '/myCollections', label: '我的收藏', icon: 'fa-star' },
  { to: '/cart', label: '购物车', icon: 'fa-shopping-cart' },
  { to: '/transactionHistory', label: '交易记录', icon: 'fa-list' },
  { to: '/guide', label: '交易指南', icon: 'fa-info-circle' }
]

onMounted(async () => {
  // refreshSession 已在路由守卫；此处拉最新资料与统计
  const dr = await campusAPI.getDorms()
  if (dr.status === 'success') dormCatalog.value = dr
  const res = await authAPI.getUserInfo()
  if (res.status === 'success' && res.user) {
    const u = { ...getCurrentUser(), ...res.user, campus_zone: normalizeCampusZone(res.user.campus_zone) }
    user.value = u
    saveUser(u)
    syncCampusForm(u)
  } else {
    syncCampusForm(user.value)
  }
  const uid = user.value?.id
  const [booksRes, colRes, ordRes] = await Promise.all([
    bookAPI.getBooks({ owner_id: uid, include_sold: true, page_size: 500 }),
    collectionAPI.getCollections().catch(() => ({ collections: [] })),
    orderAPI.getOrders().catch(() => ({ orders: [] }))
  ])
  const myBooks = booksRes.books || []
  const orders = ordRes.orders || []
  stats.value[0].value = myBooks.filter(b => b.status === 'available').length
  stats.value[1].value = (colRes.collections || colRes.books || []).length
  stats.value[2].value = orders.length
  stats.value[3].value = orders.filter(o => o.status === 'pending' || o.status === 'pickup').length
  const dash = await sellerAPI.dashboard().catch(() => null)
  if (dash?.status === 'success') sellerStats.value = dash.stats
})
</script>

<style scoped>
.profile-card { background: linear-gradient(135deg, #f8fff8, #fff); }
.profile-avatar-wrap { width: 96px; height: 96px; border-radius: 50%; border: 3px solid #28a745; overflow: hidden; display: flex; align-items: center; justify-content: center; }
.profile-avatar { width: 100%; height: 100%; object-fit: cover; }
.profile-avatar-placeholder { font-size: 84px; color: #ccc; line-height: 1; }
.stat-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,.08); }
.quick-link:hover { border-color: #28a745; transform: translateY(-2px); transition: .2s; }
</style>
