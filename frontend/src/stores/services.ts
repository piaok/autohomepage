import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Service } from '../types/service'
import { fetchServices, triggerDiscovery } from '../api'

export const useServiceStore = defineStore('services', () => {
  // State
  const services = ref<Service[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const searchQuery = ref('')
  const selectedCategory = ref<string | null>(null)

  // Getters
  const filteredServices = computed(() => {
    let result = services.value

    // 搜索过滤
    if (searchQuery.value) {
      const query = searchQuery.value.toLowerCase()
      result = result.filter(s =>
        s.name.toLowerCase().includes(query) ||
        (s.description && s.description.toLowerCase().includes(query)) ||
        (s.category && s.category.toLowerCase().includes(query))
      )
    }

    // 分类过滤
    if (selectedCategory.value) {
      result = result.filter(s => s.category === selectedCategory.value)
    }

    // 排序：在线排前，离线排后
    const statusOrder: Record<string, number> = { online: 0, checking: 1, unknown: 2, offline: 3 }
    result = [...result].sort((a, b) => {
      const sa = statusOrder[a.status] ?? 2
      const sb = statusOrder[b.status] ?? 2
      return sa - sb
    })

    return result
  })

  const categories = computed(() => {
    const cats = new Set<string>()
    services.value.forEach(s => {
      if (s.category) cats.add(s.category)
    })
    return Array.from(cats).sort()
  })

  // Actions
  async function loadServices() {
    isLoading.value = true
    error.value = null
    try {
      services.value = await fetchServices()
    } catch (e) {
      error.value = '加载服务失败'
      console.error(e)
    } finally {
      isLoading.value = false
    }
  }

  async function refreshFromDiscovery() {
    isLoading.value = true
    try {
      await triggerDiscovery()
      // 等待一下让扫描完成
      await new Promise(r => setTimeout(r, 2000))
      await loadServices()
    } catch (e) {
      error.value = '刷新失败'
      console.error(e)
    } finally {
      isLoading.value = false
    }
  }

  function setSearchQuery(query: string) {
    searchQuery.value = query
  }

  function setCategory(category: string | null) {
    selectedCategory.value = category
  }

  return {
    services,
    isLoading,
    error,
    searchQuery,
    selectedCategory,
    filteredServices,
    categories,
    loadServices,
    refreshFromDiscovery,
    setSearchQuery,
    setCategory,
  }
})
