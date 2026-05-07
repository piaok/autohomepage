<template>
  <div class="service-grid">
    <!-- 分类区块 -->
    <div v-for="group in groupedServices" :key="group.category || '__none__'" class="category-group">
      <h2 v-if="group.category" class="category-title">{{ group.category }}</h2>
      <div class="grid">
        <ServiceCard
          v-for="service in group.services"
          :key="service.id"
          :service="service"
          :network-type="networkType"
        />
      </div>
    </div>

    <!-- 空状态 -->
    <div v-if="services.length === 0 && !isLoading" class="empty-state">
      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1" stroke="currentColor" class="empty-icon">
        <path stroke-linecap="round" stroke-linejoin="round" d="M20.25 7.5l-.625 10.632a2.25 2.25 0 01-2.247 2.118H6.622a2.25 2.25 0 01-2.247-2.118L3.75 7.5m6 4.125l2.25 2.25m0 0l2.25 2.25M12 13.875l2.25-2.25M12 13.875l-2.25 2.25M3.375 7.5h17.25c.621 0 1.125-.504 1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125z" />
      </svg>
      <p>暂无服务</p>
      <p class="empty-hint">点击右上角刷新按钮发现服务</p>
    </div>

    <!-- 排序提示 -->
    <div v-if="services.length > 1" class="drag-hint">
      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="drag-hint-icon">
        <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 6h9.75M10.5 6a1.5 1.5 0 1 1-3 0m3 0a1.5 1.5 0 1 0-3 0M3.75 6H7.5m3 12h9.75m-9.75 0a1.5 1.5 0 0 1-3 0m3 0a1.5 1.5 0 1 0-3 0m-3.75 0H7.5m9-6h3.75m-3.75 0a1.5 1.5 0 0 1-3 0m3 0a1.5 1.5 0 1 0-3 0m-9.75 0h9.75" />
      </svg>
      前往设置页拖拽调整排序
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Service } from '@/types/service'
import ServiceCard from './ServiceCard.vue'

const props = defineProps<{
  services: Service[]
  isLoading: boolean
  networkType?: 'lan' | 'wan' | 'unknown'
}>()

interface ServiceGroup {
  category: string | null
  services: Service[]
}

const groupedServices = computed<ServiceGroup[]>(() => {
  const groups = new Map<string, Service[]>()

  for (const service of props.services) {
    const cat = service.category || ''
    if (!groups.has(cat)) groups.set(cat, [])
    groups.get(cat)!.push(service)
  }

  // Sort: uncategorized first, then alphabetical
  const result: ServiceGroup[] = []
  if (groups.has('')) {
    result.push({ category: null, services: groups.get('')! })
    groups.delete('')
  }

  for (const [category, services] of [...groups.entries()].sort(([a], [b]) => a.localeCompare(b))) {
    result.push({ category, services })
  }

  return result
})
</script>

<style scoped>
.service-grid {
  width: 100%;
}

.category-group {
  margin-bottom: 32px;
}

.category-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 12px;
  padding-left: 4px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 16px;
}

@media (min-width: 768px) {
  .grid {
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  }
}

@media (min-width: 1280px) {
  .grid {
    grid-template-columns: repeat(auto-fill, minmax(170px, 1fr));
  }
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  color: var(--text-secondary);
  text-align: center;
}

.empty-icon {
  width: 64px;
  height: 64px;
  margin-bottom: 16px;
  opacity: 0.4;
}

.empty-state p {
  font-size: 16px;
  margin-bottom: 4px;
}

.empty-hint {
  font-size: 13px !important;
  opacity: 0.6;
}

.drag-hint {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 12px;
  font-size: 12px;
  color: var(--text-secondary);
  opacity: 0.5;
  transition: opacity 0.3s;
}

.drag-hint:hover {
  opacity: 0.8;
}

.drag-hint-icon {
  width: 14px;
  height: 14px;
}
</style>
