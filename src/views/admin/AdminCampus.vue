<template>
  <AdminLayout title="校园数据" :show-refresh="true" @refresh="load">
    <div class="page-header"><h2>校园数据管理</h2></div>
    <ul class="nav nav-tabs mb-3">
      <li class="nav-item"><a class="nav-link" :class="{active:tab==='spots'}" href="#" @click.prevent="tab='spots'">面交点</a></li>
      <li class="nav-item"><a class="nav-link" :class="{active:tab==='courses'}" href="#" @click.prevent="tab='courses'">课程教材</a></li>
      <li class="nav-item"><a class="nav-link" :class="{active:tab==='campaigns'}" href="#" @click.prevent="tab='campaigns'">学期活动</a></li>
      <li class="nav-item"><a class="nav-link" :class="{active:tab==='schools'}" href="#" @click.prevent="tab='schools'">多校配置</a></li>
    </ul>

    <div v-if="tab==='spots'" class="admin-panel">
      <form class="row g-2 mb-3" @submit.prevent="saveSpot">
        <div class="col-md-3"><input v-model="spotForm.name" class="form-control" placeholder="地点名称*" required></div>
        <div class="col-md-2"><input v-model="spotForm.zone" class="form-control" placeholder="校区"></div>
        <div class="col-md-4"><input v-model="spotForm.description" class="form-control" placeholder="说明"></div>
        <div class="col-md-1"><input v-model.number="spotForm.sort_order" type="number" class="form-control" placeholder="序"></div>
        <div class="col-md-2"><button type="submit" class="btn btn-success w-100">{{ spotEdit ? '保存' : '添加' }}</button></div>
      </form>
      <div class="data-table"><table><thead><tr><th>名称</th><th>校区</th><th>说明</th><th>序</th><th>操作</th></tr></thead>
        <tbody><tr v-for="s in spots" :key="s.id"><td>{{ s.name }}</td><td>{{ s.zone }}</td><td>{{ s.description }}</td><td>{{ s.sort_order }}</td>
          <td><button type="button" class="btn btn-sm btn-outline-primary me-1" @click="editSpot(s)">编辑</button><button type="button" class="btn btn-sm btn-outline-danger" @click="delSpot(s.id)">删</button></td></tr></tbody></table></div>
    </div>

    <div v-if="tab==='courses'" class="admin-panel">
      <form class="row g-2 mb-3" @submit.prevent="saveCourse">
        <div class="col-md-2"><input v-model="courseForm.college" class="form-control" placeholder="学院"></div>
        <div class="col-md-2"><input v-model="courseForm.major" class="form-control" placeholder="专业"></div>
        <div class="col-md-2"><input v-model="courseForm.course_code" class="form-control" placeholder="课程代码*" required></div>
        <div class="col-md-2"><input v-model="courseForm.course_name" class="form-control" placeholder="课程名"></div>
        <div class="col-md-2"><input v-model="courseForm.textbook_title" class="form-control" placeholder="教材名"></div>
        <div class="col-md-2"><button type="submit" class="btn btn-success w-100">{{ courseEdit ? '保存' : '添加' }}</button></div>
        <div class="col-md-3"><input v-model="courseForm.textbook_author" class="form-control" placeholder="作者"></div>
        <div class="col-md-3"><input v-model="courseForm.textbook_isbn" class="form-control" placeholder="ISBN"></div>
      </form>
      <div class="data-table"><table><thead><tr><th>学院</th><th>专业</th><th>代码</th><th>课程</th><th>教材</th><th>操作</th></tr></thead>
        <tbody><tr v-for="c in courses" :key="c.id"><td>{{ c.college }}</td><td>{{ c.major }}</td><td>{{ c.course_code }}</td><td>{{ c.course_name }}</td><td>{{ c.textbook_title }}</td>
          <td><button type="button" class="btn btn-sm btn-outline-primary me-1" @click="editCourse(c)">编辑</button><button type="button" class="btn btn-sm btn-outline-danger" @click="delCourse(c.id)">删</button></td></tr></tbody></table></div>
    </div>

    <div v-if="tab==='campaigns'" class="admin-panel">
      <form class="row g-2 mb-3" @submit.prevent="saveCampaign">
        <div class="col-md-3"><input v-model="campForm.title" class="form-control" placeholder="活动标题*" required></div>
        <div class="col-md-2"><input v-model="campForm.tag" class="form-control" placeholder="标签"></div>
        <div class="col-md-2"><select v-model="campForm.campaign_type" class="form-select"><option value="back_to_school">开学季</option><option value="clearance">期末清仓</option></select></div>
        <div class="col-md-2"><input v-model="campForm.start_date" class="form-control" placeholder="开始 MM-DD"></div>
        <div class="col-md-2"><input v-model="campForm.end_date" class="form-control" placeholder="结束 MM-DD"></div>
        <div class="col-md-12"><input v-model="campForm.description" class="form-control" placeholder="说明"></div>
        <div class="col-md-2 form-check mt-2"><input v-model="campForm.is_active" class="form-check-input" type="checkbox" id="act"><label class="form-check-label" for="act">设为当前活动</label></div>
        <div class="col-md-2"><button type="submit" class="btn btn-success w-100">{{ campEdit ? '保存' : '添加' }}</button></div>
      </form>
      <div class="data-table"><table><thead><tr><th>标题</th><th>类型</th><th>标签</th><th>期</th><th>进度</th><th>启用</th><th>操作</th></tr></thead>
        <tbody><tr v-for="c in campaigns" :key="c.id"><td>{{ c.title }}</td><td>{{ c.campaign_type }}</td><td>{{ c.tag }}</td><td>{{ c.start_date }}~{{ c.end_date }}</td>
          <td style="min-width:120px"><div class="progress" style="height:8px"><div class="progress-bar bg-success" :style="{width:(c.progress_pct||0)+'%'}"></div></div><small class="text-muted">{{ c.phase }} {{ c.progress_pct }}%</small></td>
          <td>{{ c.is_active ? '是' : '' }}</td>
          <td><button type="button" class="btn btn-sm btn-outline-primary me-1" @click="editCamp(c)">编辑</button><button type="button" class="btn btn-sm btn-outline-danger" @click="delCamp(c.id)">删</button></td></tr></tbody></table></div>
    </div>

    <div v-if="tab==='schools'" class="admin-panel">
      <form class="row g-2 mb-3" @submit.prevent="saveSchool">
        <div class="col-md-3"><input v-model="schoolForm.name" class="form-control" placeholder="学校名称*" required></div>
        <div class="col-md-5"><input v-model="schoolForm.domains" class="form-control" placeholder="邮箱后缀，逗号分隔 如 edu.cn,stu.xxx.edu.cn"></div>
        <div class="col-md-2"><button type="submit" class="btn btn-success w-100">{{ schoolEdit ? '保存' : '添加' }}</button></div>
      </form>
      <div class="data-table"><table><thead><tr><th>学校</th><th>邮箱域</th><th>启用</th><th>操作</th></tr></thead>
        <tbody><tr v-for="s in schoolList" :key="s.id"><td>{{ s.name }}</td><td>{{ (s.email_domains||[]).join(', ') }}</td><td>{{ s.is_active ? '是' : '否' }}</td>
          <td><button type="button" class="btn btn-sm btn-outline-primary me-1" @click="editSchool(s)">编辑</button><button type="button" class="btn btn-sm btn-outline-danger" @click="delSchool(s.id)">删</button></td></tr></tbody></table></div>
    </div>
  </AdminLayout>
</template>

<script setup>
// 校园数据：面交点/课表教材/学期活动/多校配置
import { ref, onMounted } from 'vue'
import AdminLayout from '@/components/admin/AdminLayout.vue'
import { adminAPI } from '@/utils/api'
import { useToast } from '@/composables/useToast'

const { show } = useToast()
const tab = ref('spots')
const spots = ref([])
const courses = ref([])
const campaigns = ref([])
const spotForm = ref({ name: '', zone: '西校区', description: '', sort_order: 0 })
const courseForm = ref({ college: '', major: '', course_code: '', course_name: '', textbook_title: '', textbook_author: '', textbook_isbn: '' })
const campForm = ref({ title: '', tag: '', campaign_type: 'back_to_school', start_date: '', end_date: '', description: '', is_active: false })
const spotEdit = ref(null)
const courseEdit = ref(null)
const campEdit = ref(null)
const schoolList = ref([])
const schoolForm = ref({ name: '', domains: '' })
const schoolEdit = ref(null)

async function load() {
  const [sp, co, ca, sc] = await Promise.all([adminAPI.getSpots(), adminAPI.getCourses(), adminAPI.getCampaigns(), adminAPI.getSchools()])
  if (sp.status === 'success') spots.value = sp.spots || []
  if (co.status === 'success') courses.value = co.courses || []
  if (ca.status === 'success') campaigns.value = ca.campaigns || []
  if (sc.status === 'success') schoolList.value = sc.schools || []
}

function editSchool(s) {
  schoolEdit.value = s
  schoolForm.value = { name: s.name, domains: (s.email_domains || []).join(', ') }
}
async function saveSchool() {
  const payload = { name: schoolForm.value.name, email_domains: schoolForm.value.domains }
  const res = schoolEdit.value ? await adminAPI.updateSchool(schoolEdit.value.id, payload) : await adminAPI.createSchool(payload)
  if (res.status === 'success') { show('已保存', 'success'); schoolEdit.value = null; schoolForm.value = { name: '', domains: '' }; load() }
}
async function delSchool(id) { if (!confirm('删除？')) return; await adminAPI.deleteSchool(id); load() }

function editSpot(s) { spotEdit.value = s; spotForm.value = { ...s } }
async function saveSpot() {
  const res = spotEdit.value ? await adminAPI.updateSpot(spotEdit.value.id, spotForm.value) : await adminAPI.createSpot(spotForm.value)
  if (res.status === 'success') { show('已保存', 'success'); spotEdit.value = null; spotForm.value = { name: '', zone: '西校区', description: '', sort_order: 0 }; load() }
  else show(res.message, 'error')
}
async function delSpot(id) { if (!confirm('删除？')) return; await adminAPI.deleteSpot(id); load() }

function editCourse(c) { courseEdit.value = c; courseForm.value = { ...c } }
async function saveCourse() {
  const res = courseEdit.value ? await adminAPI.updateCourse(courseEdit.value.id, courseForm.value) : await adminAPI.createCourse(courseForm.value)
  if (res.status === 'success') { show('已保存', 'success'); courseEdit.value = null; courseForm.value = { college: '', major: '', course_code: '', course_name: '', textbook_title: '', textbook_author: '', textbook_isbn: '' }; load() }
}
async function delCourse(id) { if (!confirm('删除？')) return; await adminAPI.deleteCourse(id); load() }

function editCamp(c) { campEdit.value = c; campForm.value = { ...c, is_active: !!c.is_active } }
async function saveCampaign() {
  const res = campEdit.value ? await adminAPI.updateCampaign(campEdit.value.id, campForm.value) : await adminAPI.createCampaign(campForm.value)
  if (res.status === 'success') { show('已保存', 'success'); campEdit.value = null; campForm.value = { title: '', tag: '', campaign_type: 'back_to_school', start_date: '', end_date: '', description: '', is_active: false }; load() }
}
async function delCamp(id) { if (!confirm('删除？')) return; await adminAPI.deleteCampaign(id); load() }

onMounted(load)
</script>
