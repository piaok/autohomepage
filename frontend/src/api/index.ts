import axios from 'axios'
import type { Service, NetworkInfo } from '../types/service'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
})

// 服务API
export async function fetchServices(): Promise<Service[]> {
  const { data } = await api.get('/services', { params: { include_hidden: true, filter_disabled: false } })
  return data
}

export async function fetchService(id: string): Promise<Service> {
  const { data } = await api.get(`/services/${id}`)
  return data
}

export async function createService(service: Partial<Service>): Promise<Service> {
  const { data } = await api.post('/services', service)
  return data
}

export async function updateService(id: string, service: Partial<Service>): Promise<Service> {
  const { data } = await api.put(`/services/${id}`, service)
  return data
}

export async function deleteService(id: string): Promise<void> {
  await api.delete(`/services/${id}`)
}

export async function reorderServices(orders: { id: string; order: number }[]): Promise<void> {
  await api.post('/services/batch/reorder', { orders })
}

// 自动发现API
export async function triggerDiscovery() {
  const { data } = await api.post('/discovery/scan')
  return data
}

export async function getDiscoveryStatus() {
  const { data } = await api.get('/discovery/status')
  return data
}

// 网络信息API
export async function getNetworkInfo(): Promise<NetworkInfo> {
  const { data } = await api.get('/network/info')
  return data
}

// 智能跳转URL
export function getSmartRedirectUrl(serviceId: string): string {
  return `/go/${serviceId}`
}

export function getLanRedirectUrl(serviceId: string): string {
  return `/go/${serviceId}/lan`
}

export function getWanRedirectUrl(serviceId: string): string {
  return `/go/${serviceId}/wan`
}

export default api
