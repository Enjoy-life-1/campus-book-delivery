<template>
  <div
    v-if="notice && !isAdminRoute"
    class="ban-notice-bar"
    :class="notice.alertClass"
    role="alert"
  >
    <div class="container d-flex flex-wrap align-items-center gap-2 py-2">
      <i class="fa fa-exclamation-circle"></i>
      <strong>{{ notice.title }}</strong>
      <span class="ban-notice-detail">{{ notice.detail }}</span>
      <router-link
        v-if="notice.appealable"
        to="/accountSettings"
        class="btn btn-sm ms-auto"
        :class="notice.level === 'ban' ? 'btn-outline-danger' : 'btn-outline-primary'"
      >
        提交申诉
      </router-link>
    </div>
  </div>
</template>

<script setup>
// 顶栏封禁/禁言提示，管理端路由不显示
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useUserStore } from '@/stores/user'
import { getBanNotice } from '@/utils/banStatus'

const route = useRoute()
const { profile } = storeToRefs(useUserStore())

const isAdminRoute = computed(() => (route.path || '').startsWith('/admin'))
const notice = computed(() => getBanNotice(profile.value))
</script>

<style scoped>
.ban-notice-bar {
  font-size: 0.875rem;
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
}
.ban-notice-bar.alert-warning { background: #fff8e6; color: #856404; }
.ban-notice-bar.alert-info { background: #e8f4fd; color: #0c5460; }
.ban-notice-bar.alert-danger { background: #fdecea; color: #842029; }
.ban-notice-detail { opacity: 0.9; }
</style>
