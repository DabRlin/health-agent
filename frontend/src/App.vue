<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AppLayout from './components/layout/AppLayout.vue'

const route = useRoute()

// 判断是否为独立页面（不需要布局）
const isStandalonePage = computed(() => {
  return route.meta.public === true
})
</script>

<template>
  <!-- 独立页面直接渲染 -->
  <router-view v-if="isStandalonePage" />
  <!-- 其他页面使用布局 -->
  <AppLayout v-else />
</template>

<style scoped>
</style>
