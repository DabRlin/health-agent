<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { Bell, Search, Settings } from 'lucide-vue-next'

const route = useRoute()

const pageTitle = computed(() => {
  return route.meta.title || 'HealthAI'
})
</script>

<template>
  <header class="header">
    <div class="header-left">
      <h1 class="page-title">{{ pageTitle }}</h1>
    </div>

    <div class="header-center">
      <div class="search-box">
        <Search :size="18" class="search-icon" />
        <input 
          type="text" 
          class="search-input" 
          placeholder="搜索健康知识、症状、指标..."
        />
      </div>
    </div>

    <div class="header-right">
      <button class="btn btn-icon">
        <Bell :size="20" />
      </button>
      <button class="btn btn-icon">
        <Settings :size="20" />
      </button>
      <div class="user-avatar">
        <img src="https://api.dicebear.com/7.x/avataaars/svg?seed=health" alt="用户头像" />
      </div>
    </div>
  </header>
</template>

<style scoped>
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-md) var(--spacing-lg);
  background-color: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
  position: sticky;
  top: 0;
  z-index: 50;
}

.header-left {
  flex: 1;
}

.page-title {
  font-size: var(--font-size-xl);
  font-weight: 600;
}

.header-center {
  flex: 2;
  max-width: 480px;
  margin: 0 var(--spacing-lg);
}

.search-box {
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 16px;
  color: var(--color-text-tertiary);
}

.search-input {
  width: 100%;
  padding: 10px 16px 10px 44px;
  font-size: var(--font-size-sm);
  background-color: var(--color-bg);
  border: none;
  border-radius: var(--radius-full);
  outline: none;
  transition: all var(--transition-fast);
}

.search-input:focus {
  background-color: var(--color-surface);
  box-shadow: 0 0 0 2px var(--color-primary);
}

.search-input::placeholder {
  color: var(--color-text-tertiary);
}

.header-right {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: var(--spacing-sm);
}

.user-avatar {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-full);
  overflow: hidden;
  margin-left: var(--spacing-sm);
  cursor: pointer;
}

.user-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
</style>
