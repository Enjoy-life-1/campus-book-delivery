<template>
  <router-link :to="`/book/${book.id}`" class="text-decoration-none text-dark">
    <div class="card book-card h-100 shadow-sm">
      <img :src="cover" class="card-img-top" :alt="book.title" loading="lazy">
      <div class="card-body">
        <h6 class="card-title text-truncate">{{ book.title }}</h6>
        <p class="text-muted small mb-1">{{ book.author || '未知作者' }}</p>
        <div class="d-flex justify-content-between align-items-center flex-wrap gap-1">
          <span class="text-success fw-bold">
            ¥{{ formatPrice(book.price) }}
            <small v-if="book.original_price && book.is_price_dropping" class="text-muted text-decoration-line-through ms-1">¥{{ formatPrice(book.original_price) }}</small>
          </span>
          <span v-if="book.is_price_dropping" class="badge bg-danger">降价中</span>
          <span v-else-if="book.condition" class="badge bg-light text-dark">{{ getConditionLabel(book.condition) }}</span>
        </div>
        <p class="small mb-0 mt-1">
          <span v-if="book.seller_verified" class="badge bg-success-subtle text-success me-1">认证</span>
          <span v-if="book.dorm_building" class="text-muted"><i class="fa fa-building-o"></i> {{ book.dorm_building }}</span>
        </p>
        <slot />
      </div>
    </div>
  </router-link>
</template>

<script setup>
// 书籍卡片：列表/首页复用，跳转详情
import { computed } from 'vue'
import { formatPrice, getConditionLabel } from '@/utils/helpers'

const props = defineProps({ book: { type: Object, required: true } })

const cover = computed(() => {
  // 封面优先级：cover_url → imgs → image → 占位图
  const b = props.book
  if (b.cover_url) return b.cover_url
  if (b.imgs?.length) return Array.isArray(b.imgs) ? b.imgs[0] : b.imgs
  if (b.image) return b.image
  return 'https://picsum.photos/id/48/400/300'
})
</script>

<style scoped>
.book-card { transition: transform .2s, box-shadow .2s; }
.book-card:hover { transform: translateY(-4px); box-shadow: 0 8px 20px rgba(0,0,0,.1) !important; }
.card-img-top { height: 200px; object-fit: cover; }
</style>
