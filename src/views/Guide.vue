<template>
  <div class="page-container">
    <Navbar />
    <div class="container mt-4 guide-wrap">
      <h2 class="text-center mb-4 text-success">使用指南</h2>
      <div class="row g-4 mb-5">
        <div v-for="step in steps" :key="step.t" class="col-md-4 col-lg-2">
          <div class="card h-100 text-center p-3 step-card">
            <i :class="['fa', step.icon, 'fa-2x text-success mb-2']"></i>
            <h6>{{ step.t }}</h6>
            <p class="small text-muted mb-0">{{ step.d }}</p>
          </div>
        </div>
      </div>
      <h4 class="mb-3">校园特色功能</h4>
      <div class="row g-3 mb-5">
        <div v-for="f in campusFeatures" :key="f.to" class="col-md-6">
          <router-link :to="f.to" class="card p-3 text-decoration-none text-dark h-100 border-success">
            <h6 class="text-success"><i :class="['fa', f.icon]"></i> {{ f.title }}</h6>
            <p class="small text-muted mb-0">{{ f.desc }}</p>
          </router-link>
        </div>
      </div>
      <h4 class="mb-3">平台公告</h4>
      <div v-if="loading" class="text-center py-4"><div class="spinner-border text-success"></div></div>
      <div v-else-if="announcements.length">
        <div v-for="a in announcements" :key="a.id" class="card mb-3 ann-card">
          <div class="card-body">
            <span class="badge bg-success mb-2">{{ typeLabel(a.type) }}</span>
            <h5>{{ a.title }}</h5>
            <p class="mb-1" style="white-space:pre-wrap">{{ a.content }}</p>
            <small class="text-muted">{{ a.created_at }}</small>
          </div>
        </div>
      </div>
      <div v-else class="card p-4">
        <h5>交易规则</h5>
        <ul>
          <li>发布需审核；ISBN 国内书源填书，支持扫码与复制再发</li>
          <li>书籍列表支持价格/时间排序；可筛认证卖家、同校同楼</li>
          <li>收藏书降价会在「我的收藏」标红提示</li>
          <li>支持购买与换书订单；交易记录可导出 CSV</li>
          <li>私信约面交；遇违规可举报、拉黑</li>
          <li>请勿发布盗版、违禁内容</li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup>
// 使用指南：步骤卡片 + 公告 API + 功能入口
import { ref, onMounted } from 'vue'
import Navbar from '@/components/Navbar.vue'
import { announcementAPI } from '@/utils/api'

const steps = [
  { t: '注册', d: '选校+学籍邮箱认证', icon: 'fa-user-plus' },
  { t: '发布', d: 'ISBN扫码/复制再发', icon: 'fa-upload' },
  { t: '找书', d: '排序/同校/认证卖家', icon: 'fa-search' },
  { t: '议价', d: '报价、换书或购物车', icon: 'fa-handshake-o' },
  { t: '面交', d: '私信轮询+面交点', icon: 'fa-map-marker' },
  { t: '评价', d: '完成后互评', icon: 'fa-star' }
]
const campusFeatures = [
  { to: '/courses', title: '按课找书', desc: '学院-专业-课程教材推荐', icon: 'fa-graduation-cap' },
  { to: '/wanted', title: '求购广场', desc: '发布求购自动匹配在售', icon: 'fa-bullhorn' },
  { to: '/semester', title: '学期专场', desc: '开学季/期末清仓倒计时', icon: 'fa-calendar' },
  { to: '/feature/campus-trade', title: '校园交易', desc: '同校认证、举报拉黑', icon: 'fa-map-marker' },
  { to: '/accountSettings', title: '账号设置', desc: '学籍认证、改密、拉黑管理', icon: 'fa-cog' },
  { to: '/myCollections', title: '我的收藏', desc: '收藏降价提醒', icon: 'fa-star' }
]
const announcements = ref([])
const loading = ref(false)

function typeLabel(t) {
  return { rule: '平台规则', guide: '使用指南', safety: '安全提示' }[t] || '公告'
}

onMounted(async () => {
  loading.value = true
  try {
    const res = await announcementAPI.getAnnouncements()
    if (res.status === 'success') announcements.value = res.announcements || []
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.step-card { border-top: 3px solid #28a745; }
.ann-card { border-left: 4px solid #28a745; }
</style>
