<template>
  <div class="page-container">
    <Navbar />
    <div class="container mt-4">
      <h2 class="mb-3"><i class="fa fa-graduation-cap text-success"></i> 按课程找书
        <router-link to="/mySchedule" class="btn btn-sm btn-outline-success ms-2">导入课表批量挂书</router-link>
      </h2>
      <div class="card p-3 mb-4">
        <div class="row g-2">
          <div class="col-md-4">
            <select v-model="college" class="form-select" @change="major='';courseCode='';loadCourses()">
              <option value="">全部学院</option>
              <option v-for="c in colleges" :key="c" :value="c">{{ c }}</option>
            </select>
          </div>
          <div class="col-md-4">
            <select v-model="major" class="form-select" @change="courseCode='';loadCourses()">
              <option value="">全部专业</option>
              <option v-for="m in filteredMajors" :key="m" :value="m">{{ m }}</option>
            </select>
          </div>
          <div class="col-md-4">
            <select v-model="courseCode" class="form-select" @change="loadBooks">
              <option value="">选择课程</option>
              <option v-for="c in filteredCourses" :key="c.course_code" :value="c.course_code">
                {{ c.course_name }}（{{ c.course_code }}）
              </option>
            </select>
          </div>
        </div>
      </div>
      <div v-if="selectedCourse" class="alert alert-success">
        推荐教材：<strong>{{ selectedCourse.textbook_title }}</strong>
        <span v-if="selectedCourse.textbook_isbn" class="ms-2 small">ISBN {{ selectedCourse.textbook_isbn }}</span>
        <router-link class="btn btn-sm btn-outline-success ms-2" :to="`/publishBook?isbn=${selectedCourse.textbook_isbn}&title=${encodeURIComponent(selectedCourse.textbook_title)}`">我有这本书去发布</router-link>
      </div>
      <p v-if="courseCode" class="text-muted small">共 {{ books.length }} 本在售匹配</p>
      <div v-if="loading" class="text-center py-5"><div class="spinner-border text-success"></div></div>
      <div v-else-if="courseCode && !books.length" class="text-center text-muted py-5">
        暂无该课程在售书籍，可到 <router-link to="/wanted">求购广场</router-link> 发布求购
      </div>
      <div v-else class="row g-4">
        <div v-for="book in books" :key="book.id" class="col-md-4 col-lg-3">
          <BookCard :book="book" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
// 按学院/专业/课程筛选在售教材
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import Navbar from '@/components/Navbar.vue'
import BookCard from '@/components/BookCard.vue'
import { campusAPI } from '@/utils/api'

const route = useRoute()
const colleges = ref([])
const majors = ref([])
const courses = ref([])
const college = ref('')
const major = ref('')
const courseCode = ref(route.query.code || '')
const books = ref([])
const selectedCourse = ref(null)
const loading = ref(false)

const filteredMajors = computed(() => {
  if (!college.value) return majors.value
  return [...new Set(courses.value.filter(c => c.college === college.value).map(c => c.major))]
})
const filteredCourses = computed(() => {
  let list = courses.value
  if (college.value) list = list.filter(c => c.college === college.value)
  if (major.value) list = list.filter(c => c.major === major.value)
  return list
})

async function loadCourses() {
  const res = await campusAPI.getCourses({
    college: college.value || undefined,
    major: major.value || undefined
  })
  if (res.status === 'success') {
    courses.value = res.courses || []
    colleges.value = res.colleges || []
    majors.value = res.majors || []
  }
}

async function loadBooks() {
  // GET /api/courses/:code/books
  if (!courseCode.value) { books.value = []; selectedCourse.value = null; return }
  loading.value = true
  try {
    const res = await campusAPI.getCourseBooks(courseCode.value)
    if (res.status === 'success') {
      books.value = res.books || []
      selectedCourse.value = res.course
    }
  } finally { loading.value = false }
}

watch(courseCode, loadBooks)

onMounted(async () => {
  await loadCourses()
  if (courseCode.value) await loadBooks()
})
</script>
