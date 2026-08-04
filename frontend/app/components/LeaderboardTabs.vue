<script setup lang="ts">
const tabs = [
  { to: '/', label: '总榜' },
  { to: '/daily', label: '日增速' },
  { to: '/weekly', label: '周增速' },
  { to: '/monthly', label: '月增速' },
  { to: '/yearly', label: '年增速' },
]
const route = useRoute()
</script>

<template>
  <nav class="mb-6 flex flex-wrap gap-2 border-b border-gray-200">
    <NuxtLink
      v-for="tab in tabs"
      :key="tab.to"
      :to="tab.to"
      class="border-b-2 px-3 py-2 text-sm font-medium"
      :class="route.path === tab.to ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-800'"
    >
      {{ tab.label }}
    </NuxtLink>
  </nav>
</template>
