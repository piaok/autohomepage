<template>
  <div class="settings-page">
    <header class="settings-header">
      <router-link to="/" class="back-btn">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 19.5 3 12m0 0 7.5-7.5M3 12h18" />
        </svg>
        返回
      </router-link>
      <h1>⚙️ 设置</h1>
    </header>

    <main class="settings-content">
      <!-- Service Management -->
      <section class="settings-section">
        <div class="section-header-row">
          <h2>服务管理</h2>
          <div class="header-actions">
            <label class="check-all">
              <input type="checkbox" :checked="allSelected" @change="toggleSelectAll" />
              全选
            </label>
            <button v-if="selectedIds.length" @click="batchDelete" class="btn-sm btn-danger">
              删除 ({{ selectedIds.length }})
            </button>
            <button v-if="selectedIds.length" @click="batchHide" class="btn-sm">
              隐藏 ({{ selectedIds.length }})
            </button>
          </div>
        </div>
        <div class="section-body">
          <!-- 添加服务表单 (展开在列表顶部) -->
          <div v-if="showAddForm" class="edit-card">
            <div class="edit-card-header">
              <span>+ 添加服务</span>
              <button @click="cancelForm" class="btn-sm">✕</button>
            </div>
            <form @submit.prevent="saveService" class="service-form">
              <div class="form-group">
                <label>名称 *</label>
                <input v-model="form.name" type="text" required placeholder="服务名称" />
              </div>
              <div class="form-group">
                <label>描述</label>
                <input v-model="form.description" type="text" placeholder="服务描述" />
              </div>
              <div class="form-group">
                <label>内网地址</label>
                <input v-model="form.lan_url" type="url" placeholder="http://192.168.1.100:8080" />
              </div>
              <div class="form-group">
                <label>外网地址</label>
                <input v-model="form.wan_url" type="url" placeholder="https://app.example.com" />
              </div>
              <div class="form-group">
                <label>分类</label>
                <input v-model="form.category" type="text" placeholder="如：监控、下载、媒体" />
              </div>
              <div class="form-group">
                <label>图标URL</label>
                <input v-model="form.icon_url" type="url" placeholder="https://..." />
              </div>
              <div class="form-actions">
                <button type="submit" class="btn-primary">保存</button>
                <button type="button" @click="cancelForm" class="btn-secondary">取消</button>
              </div>
            </form>
          </div>

          <div class="service-list">
            <template v-for="service in services" :key="service.id">
              <div class="service-item" :class="{ selected: selectedIds.includes(service.id), editing: editingId === service.id }">
                <div class="service-info">
                  <input type="checkbox" :checked="selectedIds.includes(service.id)" @change="toggleSelect(service.id)" />
                  <span class="service-name">{{ service.name }}</span>
                  <span :class="'service-source badge-' + service.source">{{ service.source }}</span>
                  <StatusBadge :status="service.status" />
                </div>
                <div class="service-actions">
                  <button @click="editService(service)" class="btn-sm">{{ editingId === service.id ? '收起' : '编辑' }}</button>
                  <button @click="deleteService(service.id)" class="btn-sm btn-danger">删除</button>
                </div>
              </div>
              <!-- 编辑卡片：紧跟在当前服务项下方展开 -->
              <div v-if="editingId === service.id" class="edit-card">
                <form @submit.prevent="saveService" class="service-form">
                  <div class="form-group">
                    <label>名称 *</label>
                    <input v-model="form.name" type="text" required placeholder="服务名称" />
                  </div>
                  <div class="form-group">
                    <label>描述</label>
                    <input v-model="form.description" type="text" placeholder="服务描述" />
                  </div>
                  <div class="form-group">
                    <label>内网地址</label>
                    <input v-model="form.lan_url" type="url" placeholder="http://192.168.1.100:8080" />
                  </div>
                  <div class="form-group">
                    <label>外网地址</label>
                    <input v-model="form.wan_url" type="url" placeholder="https://app.example.com" />
                  </div>
                  <div class="form-group">
                    <label>分类</label>
                    <input v-model="form.category" type="text" placeholder="如：监控、下载、媒体" />
                  </div>
                  <div class="form-group">
                    <label>图标URL</label>
                    <input v-model="form.icon_url" type="url" placeholder="https://..." />
                  </div>
                  <div class="form-actions">
                    <button type="submit" class="btn-primary">保存</button>
                    <button type="button" @click="cancelForm" class="btn-secondary">取消</button>
                  </div>
                </form>
              </div>
            </template>
            <div v-if="services.length === 0" class="empty-msg">暂无服务</div>
          </div>
          <div class="bottom-actions">
            <button @click="startAddForm" class="btn-primary">+ 添加服务</button>
          </div>
        </div>
      </section>

      <!-- Backup & Restore -->
      <section class="settings-section">
        <h2>备份与恢复</h2>
        <div class="section-body">
          <div class="backup-actions">
            <button @click="exportBackup" class="btn-primary">📦 导出备份</button>
            <button @click="triggerImport" class="btn-secondary">📥 导入恢复</button>
            <input ref="fileInput" type="file" accept=".json" @change="importBackup" style="display:none" />
          </div>
          <p class="hint">导出包含所有服务和应用设置，可用于迁移或恢复</p>
        </div>
      </section>

      <!-- App Settings -->
      <section class="settings-section">
        <h2>应用设置</h2>
        <div class="section-body">
          <div class="setting-item">
            <label>Lucky集成</label>
            <span>{{ appSettings.lucky_enabled ? '已启用' : '已禁用' }}</span>
          </div>
          <div class="setting-item">
            <label>Lucky地址</label>
            <span>{{ appSettings.lucky_base_url }}</span>
          </div>
          <div class="setting-item">
            <label>Docker发现</label>
            <span>{{ appSettings.docker_enabled ? '已启用' : '已禁用' }}</span>
          </div>
          <div class="setting-item">
            <label>自动发现间隔</label>
            <span>{{ appSettings.auto_discovery_interval }}秒</span>
          </div>
          <div class="setting-item">
            <label>主题</label>
            <span>{{ appSettings.default_theme }}</span>
          </div>
          <div class="setting-item column">
            <div class="setting-label-row">
              <label>网络代理</label>
              <span class="hint">用于访问CDN图标等国外资源，如 http://172.25.0.1:7890</span>
            </div>
            <div class="proxy-input-row">
              <input
                v-model="proxyUrl"
                type="text"
                placeholder="http://host:port（留空则直连）"
                class="proxy-input"
              />
              <button @click="saveProxy" class="btn-sm" :disabled="proxySaving">
                {{ proxySaving ? '保存中...' : '保存' }}
              </button>
              <button @click="testProxy" class="btn-sm" :disabled="proxyTesting">
                {{ proxyTesting ? '测试中...' : '测试' }}
              </button>
            </div>
            <span v-if="proxyTestResult" :class="proxyTestOk ? 'test-ok' : 'test-fail'">{{ proxyTestResult }}</span>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed, nextTick } from 'vue'
import { useServiceStore } from '@/stores/services'
import { createService, updateService, deleteService as apiDeleteService } from '@/api'
import type { Service } from '@/types/service'
import StatusBadge from '@/components/StatusBadge.vue'

const store = useServiceStore()
const services = computed(() => {
  const statusOrder: Record<string, number> = { online: 0, checking: 1, unknown: 2, offline: 3 }
  return [...store.services].sort((a, b) => (statusOrder[a.status] ?? 2) - (statusOrder[b.status] ?? 2))
})

const showAddForm = ref(false)
const editingId = ref<string | null>(null)
const selectedIds = ref<string[]>([])
const fileInput = ref<HTMLInputElement | null>(null)

const form = reactive({
  name: '',
  description: '',
  lan_url: '',
  wan_url: '',
  category: '',
  icon_url: '',
})

const appSettings = reactive({
  lucky_enabled: true,
  lucky_base_url: '',
  docker_enabled: true,
  auto_discovery_interval: 300,
  default_theme: 'dark',
})

const proxyUrl = ref('')
const proxySaving = ref(false)
const proxyTesting = ref(false)
const proxyTestResult = ref('')
const proxyTestOk = ref(false)

const allSelected = computed(() => services.value.length > 0 && selectedIds.value.length === services.value.length)

function toggleSelect(id: string) {
  const idx = selectedIds.value.indexOf(id)
  if (idx >= 0) selectedIds.value.splice(idx, 1)
  else selectedIds.value.push(id)
}

function toggleSelectAll() {
  if (allSelected.value) {
    selectedIds.value = []
  } else {
    selectedIds.value = services.value.map(s => s.id)
  }
}

async function batchDelete() {
  if (!confirm(`确定删除选中的 ${selectedIds.value.length} 个服务？`)) return
  try {
    await fetch('/api/services/batch/delete', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ids: selectedIds.value }),
    })
    selectedIds.value = []
    await store.loadServices()
  } catch (e) {
    console.error('批量删除失败:', e)
  }
}

async function batchHide() {
  try {
    await fetch('/api/services/batch/hide', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ids: selectedIds.value, visible: false }),
    })
    selectedIds.value = []
    await store.loadServices()
  } catch (e) {
    console.error('批量隐藏失败:', e)
  }
}

async function exportBackup() {
  try {
    const res = await fetch('/api/services/backup/export')
    const data = await res.json()
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `nas-homepage-backup-${new Date().toISOString().slice(0,10)}.json`
    a.click()
    URL.revokeObjectURL(url)
  } catch (e) {
    console.error('导出失败:', e)
  }
}

function triggerImport() {
  fileInput.value?.click()
}

async function importBackup(e: Event) {
  const target = e.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return

  if (!confirm('导入将覆盖当前所有服务和设置，确定继续？')) return

  try {
    const text = await file.text()
    const data = JSON.parse(text)
    await fetch('/api/services/backup/import', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    await store.loadServices()
    alert('导入成功！')
  } catch (e) {
    console.error('导入失败:', e)
    alert('导入失败，请检查文件格式')
  }
  target.value = ''
}

function startAddForm() {
  editingId.value = null
  resetForm()
  showAddForm.value = true
  nextTick(() => {
    document.querySelector('.edit-card')?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
  })
}

function editService(service: Service) {
  // 点击同一个服务的编辑按钮 → 收起
  if (editingId.value === service.id) {
    cancelForm()
    return
  }
  showAddForm.value = false
  editingId.value = service.id
  form.name = service.name
  form.description = service.description || ''
  form.lan_url = service.lan_url || ''
  form.wan_url = service.wan_url || ''
  form.category = service.category || ''
  form.icon_url = service.icon_url || ''
  nextTick(() => {
    const card = document.querySelector('.edit-card')
    card?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
  })
}

async function saveService() {
  try {
    if (editingId.value) {
      await updateService(editingId.value, { ...form })
    } else {
      await createService({ ...form })
    }
    await store.loadServices()
    cancelForm()
  } catch (e) {
    console.error('保存失败:', e)
  }
}

async function deleteService(id: string) {
  if (!confirm('确定删除此服务？')) return
  try {
    await apiDeleteService(id)
    if (editingId.value === id) cancelForm()
    await store.loadServices()
  } catch (e) {
    console.error('删除失败:', e)
  }
}

function resetForm() {
  form.name = ''
  form.description = ''
  form.lan_url = ''
  form.wan_url = ''
  form.category = ''
  form.icon_url = ''
}

function cancelForm() {
  showAddForm.value = false
  editingId.value = null
  resetForm()
}

async function saveProxy() {
  proxySaving.value = true
  proxyTestResult.value = ''
  try {
    await fetch('/api/settings', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ http_proxy: proxyUrl.value }),
    })
    proxyTestResult.value = '代理设置已保存'
    proxyTestOk.value = true
  } catch (e) {
    proxyTestResult.value = '保存失败'
    proxyTestOk.value = false
  }
  proxySaving.value = false
}

async function testProxy() {
  proxyTesting.value = true
  proxyTestResult.value = ''
  try {
    // 先保存
    await fetch('/api/settings', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ http_proxy: proxyUrl.value }),
    })
    // 测试：通过图标代理拉一个已知CDN图标
    const testUrl = 'https://cdn.jsdelivr.net/gh/walkxcode/dashboard-icons/png/portainer.png'
    const start = Date.now()
    const resp = await fetch(`/api/icons/proxy?url=${encodeURIComponent(testUrl)}`)
    const elapsed = Date.now() - start
    if (resp.ok) {
      proxyTestResult.value = `✅ 连通，耗时 ${elapsed}ms`
      proxyTestOk.value = true
    } else {
      proxyTestResult.value = `❌ 失败: HTTP ${resp.status}`
      proxyTestOk.value = false
    }
  } catch (e) {
    proxyTestResult.value = '❌ 测试失败'
    proxyTestOk.value = false
  }
  proxyTesting.value = false
}

onMounted(async () => {
  try {
    const res = await fetch('/api/settings')
    const data = await res.json()
    Object.assign(appSettings, data)
    proxyUrl.value = data.http_proxy || ''
  } catch {
    // Use defaults
  }
})
</script>

<style scoped>
.settings-page {
  min-height: 100vh;
  background: var(--bg-primary);
}

.settings-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 24px;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border);
}

.settings-header h1 {
  font-size: 18px;
  font-weight: 700;
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  color: var(--text-secondary);
  font-size: 14px;
  text-decoration: none;
  padding: 6px 12px;
  border-radius: 8px;
  transition: all 0.2s;
}

.back-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.back-btn svg {
  width: 16px;
  height: 16px;
}

.settings-content {
  max-width: 800px;
  margin: 0 auto;
  padding: 24px;
}

.settings-section {
  margin-bottom: 24px;
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: var(--card-radius);
  overflow: hidden;
}

.section-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 20px;
  border-bottom: 1px solid var(--border);
  background: var(--overlay);
}

.section-header-row h2 {
  font-size: 15px;
  font-weight: 600;
  margin: 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.check-all {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--text-secondary);
  cursor: pointer;
}

.settings-section h2 {
  font-size: 15px;
  font-weight: 600;
  padding: 14px 20px;
  border-bottom: 1px solid var(--border);
  background: var(--overlay);
}

.section-body {
  padding: 16px 20px;
}

.service-list {
  margin-bottom: 12px;
}

.service-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 0;
  border-bottom: 1px solid var(--border);
  transition: background 0.15s;
}

.service-item.selected {
  background: var(--accent-soft);
}

.service-item.editing {
  background: color-mix(in srgb, var(--accent) 8%, transparent);
  border-bottom-color: transparent;
}

.service-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.service-info input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.service-name {
  font-weight: 500;
}

.service-actions {
  display: flex;
  gap: 6px;
}

.service-source {
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 4px;
}

.badge-lucky { color: var(--accent); background: var(--accent-soft); }
.badge-docker { color: #8b5cf6; background: rgba(139,92,246,0.15); }
.badge-manual { color: var(--success); background: color-mix(in srgb, var(--success) 10%, transparent); }

.empty-msg {
  text-align: center;
  color: var(--text-secondary);
  padding: 20px;
  font-size: 14px;
}

.bottom-actions {
  margin-top: 8px;
}

/* 编辑卡片 - 内联展开 */
.edit-card {
  background: var(--accent-soft);
  border: 1px solid var(--accent-soft);
  border-radius: 10px;
  padding: 16px;
  margin: 4px 0 12px;
  animation: slideDown 0.2s ease;
}

.edit-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  font-size: 14px;
  font-weight: 600;
  color: var(--accent);
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.service-form {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.form-group label {
  font-size: 12px;
  color: var(--text-secondary);
  font-weight: 500;
}

.form-group input {
  padding: 8px 12px;
  background: var(--bg-primary);
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text-primary);
  font-size: 13px;
  outline: none;
}

.form-group input:focus {
  border-color: var(--accent);
}

.form-actions {
  grid-column: 1 / -1;
  display: flex;
  gap: 8px;
  margin-top: 8px;
}

.btn-primary {
  padding: 8px 20px;
  background: var(--accent);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary:hover {
  opacity: 0.9;
}

.btn-secondary {
  padding: 8px 20px;
  background: var(--bg-hover);
  color: var(--text-primary);
  border: 1px solid var(--border);
  border-radius: 8px;
  font-size: 13px;
  cursor: pointer;
}

.btn-sm {
  padding: 4px 10px;
  background: var(--bg-hover);
  border: 1px solid var(--border);
  border-radius: 6px;
  font-size: 12px;
  color: var(--text-primary);
  cursor: pointer;
}

.btn-danger {
  color: var(--danger);
  border-color: color-mix(in srgb, var(--danger) 30%, transparent);
}

.btn-danger:hover {
  background: color-mix(in srgb, var(--danger) 10%, transparent);
}

.setting-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid var(--border);
  font-size: 14px;
}

.setting-item:last-child {
  border-bottom: none;
}

.setting-item label {
  color: var(--text-secondary);
}

.setting-item.column {
  flex-direction: column;
  align-items: flex-start;
  gap: 8px;
}

.setting-label-row {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}

.setting-label-row label {
  flex-shrink: 0;
}

.setting-label-row .hint {
  font-size: 11px;
}

.proxy-input-row {
  display: flex;
  gap: 8px;
  width: 100%;
}

.proxy-input {
  flex: 1;
  padding: 8px 12px;
  background: var(--bg-primary);
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text-primary);
  font-size: 13px;
  outline: none;
}

.proxy-input:focus {
  border-color: var(--accent);
}

.test-ok {
  font-size: 12px;
  color: var(--success);
}

.test-fail {
  font-size: 12px;
  color: var(--danger);
}

.backup-actions {
  display: flex;
  gap: 12px;
  margin-bottom: 8px;
}

.hint {
  font-size: 12px;
  color: var(--text-secondary);
  margin: 0;
}

@media (max-width: 640px) {
  .service-form {
    grid-template-columns: 1fr;
  }
  .backup-actions {
    flex-direction: column;
  }
}
</style>
