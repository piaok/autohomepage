<template>
  <router-view />
</template>

<script setup lang="ts">
import { ref, computed, provide, onMounted, watch } from 'vue'

type ThemeName = 'midnight' | 'daylight' | 'forest' | 'lavender' | 'sunset' | 'ocean'

interface ThemeOption {
  name: ThemeName
  label: string
  emoji: string
  isDark: boolean
}

const THEMES: ThemeOption[] = [
  { name: 'midnight', label: '深空蓝', emoji: '🌌', isDark: true },
  { name: 'daylight', label: '明亮白', emoji: '☀️', isDark: false },
  { name: 'forest',   label: '森林绿', emoji: '🌲', isDark: true },
  { name: 'lavender', label: '薰衣紫', emoji: '💜', isDark: true },
  { name: 'sunset',   label: '暮光橙', emoji: '🌅', isDark: true },
  { name: 'ocean',    label: '深海青', emoji: '🌊', isDark: true },
]

const currentTheme = ref<ThemeName>('midnight')

const currentThemeOption = computed(() => THEMES.find(t => t.name === currentTheme.value) || THEMES[0])

const isDark = computed(() => currentThemeOption.value.isDark)

function setTheme(name: ThemeName) {
  currentTheme.value = name
  localStorage.setItem('nas-homepage-theme', name)
}

// 把主题 class 挂到 <html> 元素上，这样 body 和所有子元素都能继承 CSS 变量
function applyThemeClass(name: ThemeName) {
  const html = document.documentElement
  // 移除旧主题 class
  THEMES.forEach(t => html.classList.remove(`theme-${t.name}`))
  // 添加新主题 class
  html.classList.add(`theme-${name}`)
}

watch(currentTheme, (name) => {
  applyThemeClass(name)
})

onMounted(() => {
  const saved = localStorage.getItem('nas-homepage-theme')
  if (saved === 'dark') {
    currentTheme.value = 'midnight'
  } else if (saved === 'light') {
    currentTheme.value = 'daylight'
  } else if (saved && THEMES.some(t => t.name === saved)) {
    currentTheme.value = saved as ThemeName
  }
  localStorage.setItem('nas-homepage-theme', currentTheme.value)
  applyThemeClass(currentTheme.value)
})

provide('currentTheme', currentTheme)
provide('THEMES', THEMES)
provide('isDark', isDark)
provide('setTheme', setTheme)
</script>

<style>
/* Theme variables handled by style.css, class applied to <html> */
</style>
