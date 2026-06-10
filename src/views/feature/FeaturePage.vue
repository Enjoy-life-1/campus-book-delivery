<template>
  <div class="page-container">
    <Navbar />
    <div v-if="page" :class="['feature-header', `bg-${page.theme}`]">
      <div class="container text-center text-white py-5">
        <i :class="['fa', page.icon, 'fa-4x mb-3']"></i>
        <h1>{{ page.title }}</h1>
        <p class="lead mb-0">{{ page.subtitle }}</p>
      </div>
    </div>
    <div v-else class="container py-5 text-center text-muted">页面不存在</div>
    <div v-if="page" class="container py-5">
      <div class="row g-4 mb-5">
        <div v-for="b in page.benefits" :key="b.title" class="col-md-4">
          <div class="card h-100 text-center p-4 shadow-sm">
            <i :class="['fa', b.icon, 'fa-3x text-success mb-3']"></i>
            <h5>{{ b.title }}</h5>
            <p class="text-muted small mb-0">{{ b.desc }}</p>
          </div>
        </div>
      </div>
      <div class="text-center">
        <router-link :to="page.cta.to" class="btn btn-success btn-lg">{{ page.cta.label }}</router-link>
        <router-link to="/" class="btn btn-outline-secondary btn-lg ms-2">返回首页</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
// 根据 slug 渲染 FEATURE_PAGES 营销页
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import Navbar from '@/components/Navbar.vue'
import { FEATURE_PAGES } from '@/data/featurePages'

const route = useRoute()
const page = computed(() => FEATURE_PAGES[route.params.slug] || null)
</script>

<style scoped>
.feature-header { margin-top: -1px; }
</style>
