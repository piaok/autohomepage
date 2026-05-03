<template>
  <span class="status-badge" :class="statusClass">
    <span class="status-dot"></span>
    {{ statusText }}
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  status: 'online' | 'offline' | 'checking' | 'unknown'
}>()

const statusClass = computed(() => `status-${props.status}`)

const statusText = computed(() => {
  const map: Record<string, string> = {
    online: '在线',
    offline: '离线',
    checking: '检测中',
    unknown: '未知',
  }
  return map[props.status] || '未知'
})
</script>

<style scoped>
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 9999px;
  font-weight: 500;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.status-online {
  color: var(--success);
  background: color-mix(in srgb, var(--success) 10%, transparent);
}
.status-online .status-dot {
  background: var(--success);
}

.status-offline {
  color: var(--muted);
  background: color-mix(in srgb, var(--muted) 10%, transparent);
}
.status-offline .status-dot {
  background: var(--muted);
}

.status-checking {
  color: var(--warning);
  background: color-mix(in srgb, var(--warning) 10%, transparent);
}
.status-checking .status-dot {
  background: var(--warning);
  animation: pulse 1s ease-in-out infinite;
}

.status-unknown {
  color: var(--muted);
  background: color-mix(in srgb, var(--muted) 10%, transparent);
}
.status-unknown .status-dot {
  background: var(--muted);
  opacity: 0.5;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}
</style>
