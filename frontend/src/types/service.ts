export interface Service {
  id: string
  name: string
  description?: string
  icon_url?: string
  icon_source: string
  lan_url?: string
  wan_url?: string
  source: 'lucky' | 'docker' | 'manual'
  lucky_id?: string
  container_name?: string
  category?: string
  order: number
  is_visible: boolean
  status: 'online' | 'offline' | 'checking' | 'unknown'
  last_check?: string
  is_deleted?: boolean
  deleted_at?: string
}

export interface NetworkInfo {
  client_ip: string
  network_type: 'lan' | 'wan' | 'unknown'
  is_lan: boolean
}
