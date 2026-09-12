<template>
  <a
    ref="rootEl"
    :href="serviceUrl"
    target="_blank"
    rel="noopener noreferrer"
    class="service-card"
    @click.prevent="handleClick"
    @contextmenu.prevent="handleContextMenu"
  >
    <div class="card-icon" :style="iconBgStyle">
      <img
        v-if="iconProxyUrl"
        :src="iconProxyUrl"
        :alt="service.name"
        class="icon-img"
        :class="{ 'icon-loaded': iconLoaded }"
        @load="iconLoaded = true"
        @error="iconFailed = true"
      />
      <span class="icon-initials" :class="{ 'icon-hidden': iconLoaded }">{{ initials }}</span>
    </div>

    <div class="card-info">
      <h3 class="card-name">{{ service.name }}</h3>
      <p v-if="service.description" class="card-desc">{{ service.description }}</p>
    </div>

    <div class="card-footer">
      <StatusBadge :status="service.status" />
      <span v-if="networkTag" class="network-tag" :class="networkTagClass">{{ networkTag }}</span>
    </div>

    <!-- 右键菜单 -->
    <div v-if="showMenu" class="context-menu" @click.stop>
      <a :href="service.lan_url" target="_blank" class="menu-item" v-if="service.lan_url">
        🏠 内网访问
      </a>
      <a :href="service.wan_url" target="_blank" class="menu-item" v-if="service.wan_url">
        🌐 外网访问
      </a>
      <button class="menu-item" @click="copyLink">📋 复制链接</button>
    </div>
  </a>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue'
import type { Service } from '@/types/service'
import StatusBadge from './StatusBadge.vue'
import { getSmartRedirectUrl } from '@/api'

const props = defineProps<{
  service: Service
  networkType?: 'lan' | 'wan' | 'unknown'
}>()

const showMenu = ref(false)
const iconFailed = ref(false)
const iconLoaded = ref(false)
const rootEl = ref<HTMLAnchorElement | null>(null)

// 取前两个字符作为图标
const initials = computed(() => {
  const name = props.service.name || '?'
  return name.slice(0, 2).toUpperCase()
})

// 根据名称生成一致的颜色
const iconBgStyle = computed(() => {
  const name = props.service.name || ''
  let hash = 0
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash)
  }
  const hue = Math.abs(hash) % 360
  return {
    background: `linear-gradient(135deg, hsl(${hue}, 65%, 50%), hsl(${(hue + 40) % 360}, 70%, 40%))`,
  }
})

// 图标代理URL：CDN图标走后端代理，本地/相对路径直接用
const iconProxyUrl = computed(() => {
  if (iconFailed.value) return null
  const url = props.service.icon_url
  if (!url) return null
  // 本地上传的或已经是/api/开头的，直接用
  if (url.startsWith('/') || url.startsWith('/api/')) return url
  // CDN图标走后端代理
  return `/api/icons/proxy?url=${encodeURIComponent(url)}`
})

const serviceUrl = computed(() => getSmartRedirectUrl(props.service.id))

const networkTag = computed(() => {
  const s = props.service
  if (s.lan_url && s.wan_url) return '双栈'
  if (s.lan_url) return '内网'
  if (s.wan_url) return '公网'
  return null
})

const networkTagClass = computed(() => {
  const tag = networkTag.value
  if (tag === '双栈') return 'tag-dual'
  if (tag === '内网') return 'tag-lan'
  if (tag === '公网') return 'tag-wan'
  return ''
})

function handleClick(e: MouseEvent) {
  if (e.metaKey || e.ctrlKey) {
    // 允许带 Cmd/Ctrl 中键在新标签打开原始链接
    return
  }
  window.open(serviceUrl.value, '_blank')
}

function handleContextMenu() {
  showMenu.value = !showMenu.value
}

function copyLink() {
  const url = props.networkType === 'lan' && props.service.lan_url
    ? props.service.lan_url
    : props.service.wan_url || props.service.lan_url || ''
  navigator.clipboard.writeText(url)
  showMenu.value = false
}

// 全局点击关闭菜单（精确判断是否点在当前卡片外部），随组件挂载/卸载增减监听器
function closeOnOutsideClick(e: MouseEvent) {
  if (showMenu.value && !rootEl.value?.contains(e.target as Node)) {
    showMenu.value = false
  }
}

onMounted(() => document.addEventListener('click', closeOnOutsideClick))
onUnmounted(() => document.removeEventListener('click', closeOnOutsideClick))
</script>

<style scoped>
.service-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px 12px 16px;
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: var(--card-radius);
  cursor: pointer;
  transition: all 0.25s ease;
  text-decoration: none;
  color: inherit;
  position: relative;
  min-width: 140px;
  max-width: 180px;
}

.service-card:hover {
  transform: translateY(-4px);
  border-color: var(--accent);
  box-shadow: 0 8px 25px var(--shadow-card);
}

.card-icon {
  width: 52px;
  height: 52px;
  border-radius: 12px;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: 800;
  color: white;
  letter-spacing: 1px;
  text-shadow: 0 1px 3px var(--shadow-card);
  flex-shrink: 0;
  overflow: hidden;
  position: relative;
}

.icon-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  padding: 6px;
  position: absolute;
  inset: 0;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.icon-img.icon-loaded {
  opacity: 1;
}

.icon-initials {
  text-shadow: 0 1px 3px var(--shadow-card);
  transition: opacity 0.3s ease;
}

.icon-initials.icon-hidden {
  opacity: 0;
}

.card-info {
  text-align: center;
  margin-bottom: 8px;
  width: 100%;
  overflow: hidden;
}

.card-name {
  font-size: 14px;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-desc {
  font-size: 11px;
  color: var(--text-secondary);
  margin-top: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-footer {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  justify-content: center;
}

.network-tag {
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 4px;
  font-weight: 500;
}

.tag-lan {
  color: var(--accent);
  background: var(--accent-soft);
}

.tag-wan {
  color: #8b5cf6;
  background: rgba(139, 92, 246, 0.1);
}

.tag-dual {
  background: linear-gradient(135deg, var(--accent-soft), rgba(139, 92, 246, 0.1));
  color: #a78bfa;
}

.context-menu {
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 4px;
  z-index: 100;
  min-width: 140px;
  box-shadow: 0 8px 25px var(--shadow-dropdown);
}

.menu-item {
  display: block;
  width: 100%;
  padding: 8px 12px;
  font-size: 13px;
  color: var(--text-primary);
  background: none;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  text-align: left;
  text-decoration: none;
}

.menu-item:hover {
  background: var(--bg-hover);
}
</style>
