<template>
  <div id="app">
    <OfflineBanner /> <!-- 断网提示 -->
    <BanNotice /> <!-- 封禁状态条 -->
    <GlobalToast /> <!-- 全局消息 Toast -->
    <SmsWebhookModal /> <!-- 开发模式短信 Webhook 提示 -->
    <router-view /> <!-- 当前路由页面 -->
  </div>
</template>

<script setup>
import { watch } from 'vue'
import { useRoute } from 'vue-router'
import GlobalToast from '@/components/GlobalToast.vue'
import SmsWebhookModal from '@/components/SmsWebhookModal.vue'
import OfflineBanner from '@/components/OfflineBanner.vue'
import BanNotice from '@/components/BanNotice.vue'

const route = useRoute()
// 路由切换时触发 user-updated，刷新 Pinia 用户状态与角标
watch(() => route.fullPath, () => {
  window.dispatchEvent(new Event('user-updated'))
})
</script>

<style>
#app { min-height: 100vh; }
.page-container { padding-bottom: 48px; }
</style>
