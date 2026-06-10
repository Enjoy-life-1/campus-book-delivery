<template>
  <div class="page-container">
    <Navbar />
    <div class="container mt-4" style="max-width:720px">
      <h2 class="mb-3"><i class="fa fa-calendar text-success"></i> 我的课表</h2>
      <div class="card p-3 mb-3">
        <label class="form-label small text-muted">粘贴课表，每行：课程代码,课程名（可省略名）</label>
        <textarea v-model="text" class="form-control mb-2" rows="6" placeholder="CS201,C语言程序设计&#10;MATH101,高等数学"></textarea>
        <button class="btn btn-success btn-sm" :disabled="importing" @click="doImport">导入课表</button>
      </div>
      <div v-if="schedule.length" class="card p-3 mb-3">
        <h6>已导入 {{ schedule.length }} 门课</h6>
        <ul class="list-group list-group-flush small mb-3">
          <li v-for="c in schedule" :key="c.course_code" class="list-group-item d-flex justify-content-between">
            <span>{{ c.course_code }} · {{ c.course_name }}</span>
            <span class="text-muted">{{ c.textbook_title || '未匹配教材' }}</span>
          </li>
        </ul>
        <div class="row g-2">
          <div class="col-md-4"><input v-model.number="batch.price" type="number" class="form-control" placeholder="默认单价"></div>
          <div class="col-md-4"><input v-model="batch.condition" class="form-control" placeholder="成色"></div>
          <div class="col-md-4"><input v-model="batch.contact" class="form-control" placeholder="联系方式"></div>
        </div>
        <button class="btn btn-warning btn-sm mt-2" :disabled="publishing" @click="batchPublish">一键批量挂书</button>
        <p class="small text-muted mt-2 mb-0">将按课表教材创建在售书籍（已挂同课程码的会跳过）</p>
      </div>
      <router-link to="/courses" class="btn btn-outline-success btn-sm">按课找书</router-link>
      <router-link to="/campus/map" class="btn btn-outline-secondary btn-sm ms-2">宿舍地图</router-link>
    </div>
  </div>
</template>

<script setup>
// 课表导入 → schedule_json → 批量挂书
import { ref, onMounted } from 'vue'
import Navbar from '@/components/Navbar.vue'
import { campusAPI } from '@/utils/api'
import { useToast } from '@/composables/useToast'
import { getCurrentUser } from '@/utils/auth'

const { show } = useToast()
const text = ref('')
const schedule = ref([])
const importing = ref(false)
const publishing = ref(false)
const batch = ref({ price: 15, condition: '九成新', contact: '' })

onMounted(async () => {
  const u = getCurrentUser()
  batch.value.contact = u?.phone || u?.email || ''
  const res = await campusAPI.getSchedule().catch(() => null)
  if (res?.status === 'success') schedule.value = res.schedule || []
})

async function doImport() {
  importing.value = true
  try {
    const res = await campusAPI.importSchedule({ text: text.value })
    if (res.status === 'success') {
      schedule.value = res.schedule || []
      show(`已导入 ${res.count} 门课`, 'success')
    }
  } catch (e) {
    show(e.message || '导入失败', 'error')
  } finally {
    importing.value = false
  }
}

async function batchPublish() {
  // POST /api/my/schedule/batch-publish
  publishing.value = true
  try {
    const res = await campusAPI.batchPublishSchedule(batch.value)
    if (res.status === 'success') {
      show(`已发布 ${res.count} 本`, 'success')
    }
  } catch (e) {
    show(e.message || '发布失败', 'error')
  } finally {
    publishing.value = false
  }
}
</script>
