<template>
  <div>
    <Navbar />
    <div class="container mt-4">
      <h2>发布书籍</h2>
      <form @submit.prevent="handleSubmit">
        <div class="form-group mb-3">
          <label>书名 *</label>
          <input v-model="form.title" type="text" class="form-control" required>
        </div>
        <div class="form-group mb-3">
          <label>作者</label>
          <input v-model="form.author" type="text" class="form-control">
        </div>
        <div class="form-group mb-3">
          <label>分类 *</label>
          <select v-model="form.category" class="form-control" required>
            <option value="textbook">教材教辅</option>
            <option value="postgraduate">考研资料</option>
            <option value="literature">文学小说</option>
            <option value="professional">专业书籍</option>
            <option value="other">其他书籍</option>
          </select>
        </div>
        <div class="form-group mb-3">
          <label>价格 *</label>
          <input v-model.number="form.price" type="number" step="0.01" class="form-control" required>
        </div>
        <div class="form-group mb-3">
          <label>描述 *</label>
          <textarea v-model="form.desc" class="form-control" rows="5" required></textarea>
        </div>
        <div class="form-group mb-3">
          <label>联系方式 *</label>
          <input v-model="form.contact" type="text" class="form-control" required>
        </div>
        <div class="form-group mb-3">
          <label>图片URL（多个用逗号分隔）</label>
          <input v-model="form.imgs" type="text" class="form-control" placeholder="https://example.com/image1.jpg,https://example.com/image2.jpg">
        </div>
        <button type="submit" class="btn btn-success" :disabled="loading">
          {{ loading ? '发布中...' : '发布' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import Navbar from '@/components/Navbar.vue'
import { bookAPI } from '@/utils/api'

const router = useRouter()
const form = ref({
  title: '',
  author: '',
  category: 'textbook',
  price: 0,
  desc: '',
  contact: '',
  imgs: ''
})
const loading = ref(false)

async function handleSubmit() {
  loading.value = true
  try {
    const data = {
      ...form.value,
      imgs: form.value.imgs ? form.value.imgs.split(',').map(url => url.trim()) : []
    }
    const response = await bookAPI.addBook(data)
    if (response.status === 'success') {
      alert('发布成功')
      router.push('/myBooks')
    }
  } catch (error) {
    alert(error.message || '发布失败')
  } finally {
    loading.value = false
  }
}
</script>

