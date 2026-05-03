<template>
  <div class="home">
    <!-- Header -->
    <header class="header">
      <div class="header-left">
        <h1 class="logo">🏠 NAS Homepage</h1>
      </div>
      <div class="header-center">
        <SearchBar v-model="searchQuery" />
      </div>
      <div class="header-right">
        <button @click="handleRefresh" class="icon-btn" :disabled="isLoading" title="刷新发现">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"
            :class="{ 'spinning': isLoading }">
            <path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.992 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182M2.985 19.644l3.181-3.183" />
          </svg>
        </button>

        <!-- 主题切换按钮 -->
        <div class="theme-switcher" ref="switcherRef">
          <button @click="showThemePanel = !showThemePanel" class="icon-btn theme-btn" title="切换主题">
            <span class="theme-emoji">{{ currentThemeOption.emoji }}</span>
          </button>
          <div v-if="showThemePanel" class="theme-panel">
            <div class="theme-panel-title">选择主题</div>
            <button
              v-for="t in THEMES"
              :key="t.name"
              class="theme-option"
              :class="{ active: currentTheme === t.name }"
              @click="handleThemeSelect(t.name)"
            >
              <span class="theme-option-emoji">{{ t.emoji }}</span>
              <span class="theme-option-label">{{ t.label }}</span>
              <span v-if="currentTheme === t.name" class="theme-option-check">✓</span>
            </button>
          </div>
        </div>

        <router-link to="/settings" class="icon-btn" title="设置">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.325.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 0 1 1.37.49l1.296 2.247a1.125 1.125 0 0 1-.26 1.431l-1.003.827c-.293.241-.438.613-.43.992a7.723 7.723 0 0 1 0 .255c-.008.378.137.75.43.991l1.004.827c.424.35.534.955.26 1.43l-1.298 2.247a1.125 1.125 0 0 1-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.47 6.47 0 0 1-.22.128c-.331.183-.581.495-.644.869l-.213 1.281c-.09.543-.56.94-1.11.94h-2.594c-.55 0-1.019-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 0 1-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 0 1-1.369-.49l-1.297-2.247a1.125 1.125 0 0 1 .26-1.431l1.004-.827c.292-.24.437-.613.43-.991a6.932 6.932 0 0 1 0-.255c.007-.38-.138-.751-.43-.992l-1.004-.827a1.125 1.125 0 0 1-.26-1.43l1.297-2.247a1.125 1.125 0 0 1 1.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.086.22-.128.332-.183.582-.495.644-.869l.214-1.28Z" />
            <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
          </svg>
        </router-link>
      </div>
    </header>

    <!-- Category filters -->
    <div v-if="categories.length > 0" class="category-bar">
      <button
        class="cat-btn"
        :class="{ active: !selectedCategory }"
        @click="selectCategory(null)"
      >全部</button>
      <button
        v-for="cat in categories"
        :key="cat"
        class="cat-btn"
        :class="{ active: selectedCategory === cat }"
        @click="selectCategory(cat)"
      >{{ cat }}</button>
    </div>

    <!-- Content -->
    <main class="main-content">
      <ServiceGrid
        :services="filteredServices"
        :is-loading="isLoading"
        :network-type="networkType"
      />
    </main>

    <!-- Last scan info -->
    <footer v-if="lastScanTime" class="footer">
      上次扫描: {{ lastScanTime }}
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, inject } from 'vue'
import { useServiceStore } from '@/stores/services'
import { getNetworkInfo } from '@/api'
import SearchBar from '@/components/SearchBar.vue'
import ServiceGrid from '@/components/ServiceGrid.vue'
import type { NetworkInfo } from '@/types/service'

type ThemeName = 'midnight' | 'daylight' | 'forest' | 'lavender' | 'sunset' | 'ocean'
interface ThemeOption { name: ThemeName; label: string; emoji: string; isDark: boolean }

const store = useServiceStore()

const currentTheme = inject<import('vue').Ref<ThemeName>>('currentTheme', ref('midnight' as ThemeName))
const THEMES = inject<ThemeOption[]>('THEMES', [])
const setTheme = inject<(name: ThemeName) => void>('setTheme', () => {})
const isDark = inject<import('vue').Ref<boolean>>('isDark', ref(true))

const currentThemeOption = computed(() => THEMES.find(t => t.name === currentTheme.value) || THEMES[0])

const showThemePanel = ref(false)
const switcherRef = ref<HTMLElement | null>(null)

function handleThemeSelect(name: ThemeName) {
  setTheme(name)
  showThemePanel.value = false
}

// 点击外部关闭面板
function onClickOutside(e: MouseEvent) {
  if (switcherRef.value && !switcherRef.value.contains(e.target as Node)) {
    showThemePanel.value = false
  }
}

const searchQuery = computed({
  get: () => store.searchQuery,
  set: (v: string) => store.setSearchQuery(v),
})

const selectedCategory = computed(() => store.selectedCategory)
const categories = computed(() => store.categories)
const filteredServices = computed(() => store.filteredServices)
const isLoading = computed(() => store.isLoading)

const networkType = ref<'lan' | 'wan' | 'unknown'>('unknown')
const lastScanTime = ref<string>('')

function selectCategory(cat: string | null) {
  store.setCategory(cat)
}

async function handleRefresh() {
  await store.refreshFromDiscovery()
  updateLastScan()
}

function updateLastScan() {
  lastScanTime.value = new Date().toLocaleString('zh-CN')
}

onMounted(async () => {
  document.addEventListener('click', onClickOutside)
  await store.loadServices()
  updateLastScan()

  try {
    const info: NetworkInfo = await getNetworkInfo()
    networkType.value = info.network_type
  } catch {
    networkType.value = 'unknown'
  }
})
</script>

<style scoped>
.home {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border);
  gap: 16px;
  flex-wrap: wrap;
}

.header-left {
  flex-shrink: 0;
}

.logo {
  font-size: 18px;
  font-weight: 700;
  white-space: nowrap;
  color: var(--logo-color);
}

.header-center {
  flex: 1;
  max-width: 500px;
  min-width: 200px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.icon-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 8px;
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s;
  text-decoration: none;
}

.icon-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
  border-color: var(--accent);
}

.icon-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.icon-btn svg {
  width: 18px;
  height: 18px;
}

.theme-emoji {
  font-size: 18px;
  line-height: 1;
}

/* 主题切换器 */
.theme-switcher {
  position: relative;
}

.theme-panel {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 8px;
  min-width: 180px;
  box-shadow: 0 12px 40px var(--shadow-dropdown);
  z-index: 200;
  animation: panelFadeIn 0.15s ease;
}

@keyframes panelFadeIn {
  from { opacity: 0; transform: translateY(-4px); }
  to { opacity: 1; transform: translateY(0); }
}

.theme-panel-title {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-secondary);
  padding: 4px 12px 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.theme-option {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 8px 12px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: var(--text-primary);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s;
}

.theme-option:hover {
  background: var(--bg-hover);
}

.theme-option.active {
  background: var(--accent-soft);
  color: var(--accent);
  font-weight: 600;
}

.theme-option-emoji {
  font-size: 16px;
  width: 20px;
  text-align: center;
}

.theme-option-label {
  flex: 1;
  text-align: left;
}

.theme-option-check {
  color: var(--accent);
  font-weight: 700;
}

.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.category-bar {
  display: flex;
  gap: 8px;
  padding: 12px 24px;
  overflow-x: auto;
  flex-wrap: wrap;
}

.cat-btn {
  padding: 6px 14px;
  border-radius: 8px;
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  color: var(--text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.cat-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.cat-btn.active {
  background: var(--accent);
  color: white;
  border-color: var(--accent);
}

.main-content {
  flex: 1;
  padding: 24px;
  max-width: 1400px;
  width: 100%;
  margin: 0 auto;
}

.footer {
  text-align: center;
  padding: 16px;
  font-size: 12px;
  color: var(--text-secondary);
  opacity: 0.6;
}

@media (max-width: 640px) {
  .header {
    padding: 12px 16px;
  }
  .main-content {
    padding: 16px;
  }
  .header-center {
    order: 3;
    max-width: 100%;
    min-width: 100%;
  }
}
</style>
