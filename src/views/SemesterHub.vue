<template>
  <div class="page-container">
    <Navbar />
    <div class="container mt-4">
      <div v-for="c in campaigns" :key="c.id" class="semester-banner mb-4" :class="c.campaign_type">
        <h2>{{ c.title }}</h2>
        <p>{{ c.description }}</p>
        <span class="badge bg-light text-dark">{{ c.start_date }} ~ {{ c.end_date }}</span>
        <router-link class="btn btn-light btn-sm ms-2" :to="`/booksList?campaign=${c.tag}`">进入专场</router-link>
      </div>
      <h4 class="mb-3">专场书籍</h4>
      <div v-if="loading" class="text-center py-5"><div class="spinner-border text-success"></div></div>
      <div v-else-if="!books.length" class="text-muted text-center py-4">
        暂无专场书籍，发布时可选择「参与学期专场」
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
// 学期专场：活动 banner + campaign_tag 书籍
import { ref, onMounted } from 'vue'
import Navbar from '@/components/Navbar.vue'
import BookCard from '@/components/BookCard.vue'
import { campusAPI } from '@/utils/api'

const campaigns = ref([])
const books = ref([])
const loading = ref(true)

onMounted(async () => {
  // GET /api/semester/active
  const res = await campusAPI.getSemester()
  if (res.status === 'success') {
    campaigns.value = res.campaigns || []
    books.value = res.books || []
  }
  loading.value = false
})
</script>

<style scoped>
.semester-banner { border-radius: 12px; padding: 1.5rem; color: #fff; }
.semester-banner.back_to_school { background: linear-gradient(135deg, #007f73, #34a853); }
.semester-banner.clearance { background: linear-gradient(135deg, #fa8c16, #f5222d); }
</style>
