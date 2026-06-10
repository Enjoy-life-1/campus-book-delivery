<template>
  <div class="page-container">
    <Navbar />
    <div class="container mt-4">
      <h2 class="mb-3"><i class="fa fa-map-marker text-success"></i> 校园地图</h2>
      <div class="card p-3">
        <svg viewBox="0 0 100 100" class="campus-map w-100" style="max-height:420px;background:#f0f7f0;border-radius:8px">
          <rect x="5" y="12" width="52" height="88" fill="#e8f5e9" stroke="#81c784" rx="2"/>
          <text x="31" y="18" text-anchor="middle" font-size="3.2" fill="#2e7d32">西校区（江高）</text>
          <rect x="58" y="12" width="37" height="88" fill="#fff8e1" stroke="#ffb74d" rx="2"/>
          <text x="76" y="18" text-anchor="middle" font-size="3.2" fill="#e65100">北校区（钟落潭）</text>
          <circle v-for="s in spotsWithPos" :key="'s'+s.id" :cx="s.map_x" :cy="s.map_y" r="2.2" fill="#1976d2" />
          <text v-for="s in spotsWithPos" :key="'st'+s.id" :x="s.map_x" :y="s.map_y - 3" text-anchor="middle" font-size="2.2" fill="#1565c0">{{ s.name }}</text>
          <circle v-for="d in dorms" :key="d.name" :cx="d.x" :cy="d.y" r="2.8" fill="#43a047" class="dorm-dot" @click="pickDorm(d)" style="cursor:pointer"/>
          <text v-for="d in dorms" :key="'t'+d.name" :x="d.x" :y="d.y + 5" text-anchor="middle" font-size="2.4" fill="#1b5e20">{{ d.name }}</text>
        </svg>
        <div v-if="selected" class="mt-3 alert alert-success py-2 mb-0">
          <strong>{{ selected.name }}</strong>（{{ selected.zone }}）
          <span v-if="selected.near_spot"> · 推荐面交：{{ selected.near_spot }}</span>
          <span v-if="selected.note" class="d-block small mt-1">{{ selected.note }}</span>
        </div>
      </div>
      <p class="small text-muted mt-2">点击宿舍楼查看推荐面交点；发布书籍时可选择对应楼栋。</p>
    </div>
  </div>
</template>

<script setup>
// SVG 校园地图：宿舍楼 + 面交点，点击看推荐面交
import { ref, computed, onMounted } from 'vue'
import Navbar from '@/components/Navbar.vue'
import { campusAPI } from '@/utils/api'

const dorms = ref([])
const spots = ref([])
const selected = ref(null)

const spotDefaults = {}

const spotsWithPos = computed(() =>
  // 无 map_x/y 时用默认坐标排布
  spots.value.map((s, i) => ({
    ...s,
    map_x: s.map_x ?? spotDefaults[s.name]?.[0] ?? (20 + (i % 5) * 15),
    map_y: s.map_y ?? spotDefaults[s.name]?.[1] ?? (30 + Math.floor(i / 5) * 12)
  }))
)

function pickDorm(d) {
  selected.value = d
}

onMounted(async () => {
  const res = await campusAPI.getDormMap()
  if (res.status === 'success') {
    dorms.value = res.dorms || []
    spots.value = res.spots || []
  }
})
</script>

<style scoped>
.dorm-dot:hover { fill: #2e7d32; }
</style>
