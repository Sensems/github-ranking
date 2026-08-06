<script setup lang="ts">
const tabs = [
  { to: '/', label: '总榜' },
  { to: '/daily', label: '日增速' },
  { to: '/weekly', label: '周增速' },
  { to: '/monthly', label: '月增速' },
  { to: '/yearly', label: '年增速' },
] as const

const route = useRoute()
const current = computed(() => route.path)

async function onTabChange(value: string | number) {
  const path = String(value)
  if (path !== route.path) await navigateTo(path)
}
</script>

<template>
  <Tabs :model-value="current" class="mb-6" @update:model-value="onTabChange">
    <TabsList class="flex h-auto w-full flex-wrap justify-start gap-1">
      <TabsTrigger
        v-for="tab in tabs"
        :key="tab.to"
        :value="tab.to"
      >
        {{ tab.label }}
      </TabsTrigger>
    </TabsList>
  </Tabs>
</template>
