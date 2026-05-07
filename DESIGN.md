# NAS Homepage Docker Application - Design Document

## Project Overview
一个自动化的NAS主页应用，能够从Lucky Web服务自动发现服务地址，智能区分内外网访问，并提供美观的网格化服务导航界面。

---

## Phase 1: UI设计

### 1.1 设计理念
- **简洁现代**: 采用卡片式布局，清晰的视觉层次
- **响应式**: 适配桌面、平板、手机多端访问
- **暗色优先**: 符合NAS用户的使用场景（多数在暗光环境）
- **高效访问**: 一键直达，减少操作步骤

### 1.2 页面布局

```
┌─────────────────────────────────────────────────────────────┐
│  ┌─────────────────────────────────────────────────────┐   │
│  │  🔍 搜索服务...                    [⚙️设置] [👤用户]  │   │  Header
│  └─────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐          │
│  │  📊     │ │  🎬     │ │  📁     │ │  🔒     │          │
│  │ Grafana │ │  Plex   │ │  File   │ │  VPN    │          │
│  │         │ │         │ │ Manager │ │         │          │
│  │ ● 在线  │ │ ● 在线  │ │ ● 在线  │ │ ○ 离线  │          │
│  │ [内网]  │ │ [公网]  │ │ [内网]  │ │         │          │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘          │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐          │  Grid
│  │  🐳     │ │  ☁️     │ │  📝     │ │  🔧     │          │  Area
│  │ Docker  │ │  Next   │ │  Notes  │ │  Admin  │          │
│  │         │ │  Cloud  │ │         │ │         │          │
│  │ ● 在线  │ │ ● 在线  │ │ ● 在线  │ │ ● 在线  │          │
│  │ [内网]  │ │ [公网]  │ │ [公网]  │ │ [内网]  │          │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘          │
│                                                            │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 组件设计

#### 1.3.1 服务卡片 (Service Card)
```
┌──────────────────────┐
│     ┌──────────┐     │
│     │   Icon   │     │  64x64px SVG图标
│     │   64px   │     │
│     └──────────┘     │
│                      │
│   Service Name       │  16px 粗体
│   Description        │  12px 灰色
│                      │
│   ● Status  [标签]   │  状态指示器 + 访问类型标签
│                      │
└──────────────────────┘
尺寸: 160px x 180px
圆角: 12px
阴影: 0 4px 6px rgba(0,0,0,0.1)
悬停: 上浮效果 + 边框高亮
```

#### 1.3.2 状态指示器
- ● 在线 (绿色 #10b981)
- ○ 离线 (灰色 #6b7280)
- ◐ 检测中 (黄色 #f59e0b)

#### 1.3.3 访问类型标签
- [内网] - 蓝色标签
- [公网] - 紫色标签
- [双栈] - 渐变标签

### 1.4 响应式断点
| 设备 | 宽度 | 列数 | 卡片尺寸 |
|------|------|------|----------|
| 手机 | < 640px | 2-3列 | 自适应 |
| 平板 | 640-1024px | 4列 | 140px |
| 桌面 | > 1024px | 6-8列 | 160px |

### 1.5 主题配色

#### 暗色主题 (默认)
```css
--bg-primary: #0f172a      /* 深蓝灰背景 */
--bg-secondary: #1e293b    /* 卡片背景 */
--bg-hover: #334155        /* 悬停背景 */
--text-primary: #f1f5f9    /* 主文字 */
--text-secondary: #94a3b8  /* 次要文字 */
--accent: #3b82f6          /* 强调色 */
--border: #475569          /* 边框 */
```

#### 浅色主题
```css
--bg-primary: #ffffff
--bg-secondary: #f8fafc
--bg-hover: #f1f5f9
--text-primary: #0f172a
--text-secondary: #64748b
--accent: #2563eb
--border: #e2e8f0
```

### 1.6 动画效果
- **卡片悬停**: transform: translateY(-4px) + box-shadow增强
- **页面加载**: 卡片依次淡入 (stagger: 50ms)
- **状态切换**: 平滑颜色过渡 (300ms ease)
- **搜索过滤**: 卡片缩放消失/出现 (200ms)

### 1.7 交互设计
1. **点击卡片**: 根据访问来源智能跳转
2. **右键卡片**: 显示菜单（复制链接、在新标签打开等）
3. **搜索框**: 实时过滤，支持模糊搜索
4. **拖拽**: 支持自定义排序（可选功能）

---

## Phase 2: 架构设计

### 2.1 技术栈选型

#### 后端
- **语言**: Python 3.11+
- **框架**: FastAPI (异步、高性能、自动API文档)
- **HTTP客户端**: httpx (支持异步)
- **配置管理**: pydantic-settings
- **容器API**: docker-py (获取Docker容器信息)

#### 前端
- **框架**: Vue 3 + TypeScript
- **构建**: Vite
- **UI库**: Tailwind CSS
- **图标**: Heroicons / Phosphor Icons
- **HTTP客户端**: axios

#### 数据存储
- **配置**: JSON文件 (轻量，易于备份)
- **缓存**: 内存缓存 (服务状态、图标)

#### Docker
- **基础镜像**: python:3.11-slim
- **前端构建**: node:18-alpine (多阶段构建)
- **Web服务器**: Caddy/Nginx (静态文件 + API代理)

### 2.2 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Browser                          │
│                    (LAN IP / WAN IP判断)                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        NAS Homepage App                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   Frontend  │  │   Backend   │  │      Auto Discovery     │  │
│  │  (Vue 3)    │◄─┤  (FastAPI)  │◄─┤  ┌───────┐  ┌────────┐ │  │
│  │  - Dashboard│  │  - API      │  │  │ Lucky │  │ Docker │ │  │
│  │  - Settings │  │  - Proxy    │  │  │ API   │  │ API    │ │  │
│  └─────────────┘  └─────────────┘  │  └───────┘  └────────┘ │  │
│                                    └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      External Services                          │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐   │
│  │ Grafana │ │  Plex   │ │  Alist  │ │  NAS    │ │  ...    │   │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 2.3 模块划分

#### Backend Modules
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI入口
│   ├── config.py            # 配置管理
│   ├── api/
│   │   ├── __init__.py
│   │   ├── services.py      # 服务CRUD API
│   │   ├── settings.py      # 设置API
│   │   └── proxy.py         # 代理/跳转逻辑
│   ├── core/
│   │   ├── __init__.py
│   │   ├── lucky_client.py  # Lucky API客户端
│   │   ├── docker_client.py # Docker API客户端
│   │   ├── icon_fetcher.py  # 图标获取服务
│   │   └── network.py       # 网络检测 (内外网判断)
│   ├── models/
│   │   ├── __init__.py
│   │   ├── service.py       # 服务数据模型
│   │   └── settings.py      # 设置数据模型
│   └── services/
│       ├── __init__.py
│       ├── service_manager.py
│       └── auto_discovery.py
├── data/                    # 数据持久化目录
│   └── config.json
└── requirements.txt
```

#### Frontend Modules
```
frontend/
├── src/
│   ├── components/
│   │   ├── ServiceCard.vue
│   │   ├── ServiceGrid.vue
│   │   ├── SearchBar.vue
│   │   ├── SettingsPanel.vue
│   │   └── StatusBadge.vue
│   ├── views/
│   │   ├── Home.vue
│   │   └── Settings.vue
│   ├── stores/
│   │   └── services.ts
│   ├── api/
│   │   └── index.ts
│   └── types/
│       └── service.ts
├── public/
└── package.json
```

### 2.4 Docker集成方案

#### Dockerfile (多阶段构建)
```dockerfile
# 阶段1: 构建前端
FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# 阶段2: Python后端
FROM python:3.11-slim AS backend
WORKDIR /app
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./

# 阶段3: 最终镜像 (Caddy)
FROM caddy:2-alpine
COPY --from=frontend-builder /app/frontend/dist /srv
COPY --from=backend /app /app
COPY Caddyfile /etc/caddy/Caddyfile
EXPOSE 80
```

### 2.5 Lucky集成方案

#### Lucky Web服务API (假设)
```python
# Lucky API 端点 (需要用户配置)
LUCKY_API_BASE = "http://lucky:8080/api"

# 获取Web服务列表
GET /web/services
Response:
{
  "services": [
    {
      "name": "Grafana",
      "lan_url": "http://192.168.1.100:3000",
      "wan_url": "https://grafana.example.com",
      "status": "running"
    }
  ]
}
```

### 2.6 内外网判断机制

#### 方案1: 后端IP判断 (推荐)
```python
def get_client_network_type(client_ip: str) -> str:
    """
    判断客户端来源网络类型
    """
    # 私有地址范围
    private_ranges = [
        ipaddress.ip_network("10.0.0.0/8"),
        ipaddress.ip_network("172.16.0.0/12"),
        ipaddress.ip_network("192.168.0.0/16"),
        ipaddress.ip_network("127.0.0.0/8"),  # 回环
    ]
    
    client = ipaddress.ip_address(client_ip)
    for network in private_ranges:
        if client in network:
            return "lan"
    return "wan"
```

#### 方案2: 前端JS判断 (备用)
```javascript
// 尝试访问内网专用地址，成功即为内网
async function detectNetwork() {
    try {
        await fetch('http://192.168.1.1', { mode: 'no-cors', timeout: 1000 });
        return 'lan';
    } catch {
        return 'wan';
    }
}
```

---

## Phase 3: 前后端设计

### 3.1 数据模型

#### Service Model
```python
class Service(BaseModel):
    id: str                    # 唯一标识 (UUID)
    name: str                  # 显示名称
    description: Optional[str] # 描述
    icon_url: Optional[str]    # 图标URL (自动获取或自定义)
    icon_source: str           # 图标来源: auto_docker / auto_lucky / custom
    
    # 地址配置
    lan_url: Optional[str]     # 局域网地址
    wan_url: Optional[str]     # 外网地址
    
    # 来源信息
    source: str                # 来源: lucky / docker / manual
    lucky_id: Optional[str]    # Lucky中的ID
    container_name: Optional[str]  # Docker容器名
    
    # 显示控制
    category: Optional[str]    # 分类
    order: int                 # 排序
    is_visible: bool = True    # 是否显示
    
    # 状态 (动态)
    status: str = "unknown"    # online / offline / checking
    last_check: Optional[datetime]
```

#### Settings Model
```python
class AppSettings(BaseModel):
    # Lucky配置
    lucky_enabled: bool = True
    lucky_base_url: str = "http://lucky:8080"
    lucky_api_token: Optional[str]
    
    # Docker配置
    docker_enabled: bool = True
    docker_socket: str = "/var/run/docker.sock"
    
    # 图标配置
    auto_fetch_icons: bool = True
    icon_cache_days: int = 7
    
    # 网络配置
    trusted_proxies: List[str] = []
    custom_lan_ranges: List[str] = []
    
    # UI配置
    default_theme: str = "dark"  # dark / light / auto
    show_status_badge: bool = True
    show_url_type: bool = True
```

### 3.2 API设计

#### REST API Endpoints

**服务管理**
```
GET    /api/services              # 获取所有服务列表
POST   /api/services              # 手动添加服务
GET    /api/services/{id}         # 获取单个服务详情
PUT    /api/services/{id}         # 更新服务
DELETE /api/services/{id}         # 删除服务
POST   /api/services/{id}/check   # 手动检测服务状态
```

**自动发现**
```
POST   /api/discovery/scan         # 触发一次扫描
GET    /api/discovery/status      # 获取自动发现状态
GET    /api/discovery/lucky       # 从Lucky同步
GET    /api/discovery/docker      # 从Docker同步
```

**跳转代理**
```
GET    /go/{service_id}           # 智能跳转 (根据来源IP)
GET    /go/{service_id}/lan       # 强制内网跳转
GET    /go/{service_id}/wan       # 强制外网跳转
```

**设置**
```
GET    /api/settings              # 获取设置
PUT    /api/settings              # 更新设置
GET    /api/network/info          # 获取网络信息 (调试用)
```

**图标**
```
GET    /api/icons/search?q={name} # 搜索图标
GET    /api/icons/{service_id}    # 获取服务图标
```

### 3.3 核心功能实现

#### 3.3.1 Lucky客户端
```python
import httpx

class LuckyClient:
    def __init__(self, base_url: str, token: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.client = httpx.AsyncClient(timeout=10.0)
    
    async def get_web_services(self) -> List[Dict]:
        """获取Lucky配置的Web服务列表"""
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        
        # Lucky的API端点 (根据实际API调整)
        response = await self.client.get(
            f"{self.base_url}/api/web/service/list",
            headers=headers
        )
        response.raise_for_status()
        return response.json().get("data", [])
    
    async def get_service_detail(self, service_id: str) -> Dict:
        """获取服务详情，包含内外网地址"""
        response = await self.client.get(
            f"{self.base_url}/api/web/service/{service_id}"
        )
        response.raise_for_status()
        return response.json().get("data", {})
```

#### 3.3.2 Docker图标获取
```python
import docker

class DockerIconFetcher:
    """从Docker Hub或其他 registry 获取图标"""
    
    def __init__(self):
        self.client = docker.from_env()
    
    async def get_icon_for_container(self, container_name: str) -> Optional[str]:
        """
        获取容器对应的应用图标
        策略:
        1. 获取容器镜像名称
        2. 从Docker Hub获取图标
        3. 或使用内置图标库匹配
        """
        try:
            container = self.client.containers.get(container_name)
            image_name = container.image.tags[0] if container.image.tags else container.image.id
            
            # 提取应用名称 (如: linuxserver/plex -> plex)
            app_name = self._extract_app_name(image_name)
            
            # 返回图标URL或base64
            return await self._fetch_icon(app_name)
        except Exception as e:
            logger.warning(f"Failed to get icon for {container_name}: {e}")
            return None
    
    def _extract_app_name(self, image_name: str) -> str:
        """从镜像名提取应用名"""
        # linuxserver/plex:latest -> plex
        # grafana/grafana:9.0 -> grafana
        parts = image_name.split('/')
        name = parts[-1] if len(parts) > 1 else parts[0]
        return name.split(':')[0].split('@')[0]
    
    async def _fetch_icon(self, app_name: str) -> Optional[str]:
        """从外部API获取图标"""
        # 方案1: 使用 WalkxCode 的 dashboard-icons
        icon_url = f"https://cdn.jsdelivr.net/gh/walkxcode/dashboard-icons/png/{app_name}.png"
        
        # 方案2: 使用 selfh.st 图标库
        # icon_url = f"https://cdn.selfh.st/icons/{app_name}.png"
        
        # 验证URL是否可用
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.head(icon_url, timeout=5)
                if resp.status_code == 200:
                    return icon_url
            except:
                pass
        
        return None
```

#### 3.3.3 智能跳转路由
```python
from fastapi import Request, HTTPException, RedirectResponse

@app.get("/go/{service_id}")
async def smart_redirect(
    service_id: str,
    request: Request,
    force: Optional[str] = None  # "lan" | "wan" | None
):
    """
    智能跳转 - 根据客户端IP自动选择最优地址
    """
    # 获取服务
    service = await service_manager.get(service_id)
    if not service:
        raise HTTPException(404, "Service not found")
    
    # 强制模式
    if force == "lan":
        if service.lan_url:
            return RedirectResponse(service.lan_url)
        raise HTTPException(400, "LAN URL not configured")
    
    if force == "wan":
        if service.wan_url:
            return RedirectResponse(service.wan_url)
        raise HTTPException(400, "WAN URL not configured")
    
    # 自动判断
    client_ip = get_client_ip(request)
    network_type = get_client_network_type(client_ip)
    
    if network_type == "lan" and service.lan_url:
        return RedirectResponse(service.lan_url)
    elif service.wan_url:
        return RedirectResponse(service.wan_url)
    elif service.lan_url:
        # 外网访问但只有内网地址，给出提示
        return RedirectResponse(f"/warning?type=no_wan&target={service_id}")
    
    raise HTTPException(400, "No URL available")

def get_client_ip(request: Request) -> str:
    """获取真实客户端IP (考虑反向代理)"""
    # 检查X-Forwarded-For
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    # 检查X-Real-IP
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # 直接连接
    return request.client.host
```

#### 3.3.4 前端智能跳转
```typescript
// Vue组件中的点击处理
async function handleServiceClick(service: Service) {
    // 方式1: 通过后端智能跳转
    window.open(`/go/${service.id}`, '_blank');
    
    // 方式2: 前端判断 (备用方案)
    /*
    const networkType = await detectNetwork();
    const url = networkType === 'lan' ? service.lan_url : service.wan_url;
    if (url) {
        window.open(url, '_blank');
    } else {
        showToast('该服务在当前网络不可用');
    }
    */
}
```

### 3.4 自动发现流程

```
┌─────────────────┐
│   Start Scan    │
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌────────┐
│ Lucky  │ │ Docker │
│  API   │ │  API   │
└───┬────┘ └───┬────┘
    │          │
    ▼          ▼
┌───────────────┐
│ Merge Results │
└───────┬───────┘
        │
        ▼
┌───────────────┐
│ Fetch Icons   │
│ (async)       │
└───────┬───────┘
        │
        ▼
┌───────────────┐
│ Update DB     │
└───────┬───────┘
        │
        ▼
┌───────────────┐
│ Notify Frontend│
│ (WebSocket)   │
└───────────────┘
```

### 3.5 配置示例

#### docker-compose.yml
```yaml
version: '3.8'

services:
  nas-homepage:
    image: nas-homepage:latest
    container_name: nas-homepage
    restart: unless-stopped
    ports:
      - "3000:80"
    volumes:
      - ./data:/app/data
      - /var/run/docker.sock:/var/run/docker.sock:ro
    environment:
      - LUCKY_BASE_URL=http://lucky:8080
      - LUCKY_API_TOKEN=your_token_here
      - AUTO_DISCOVERY_INTERVAL=300  # 5分钟
    networks:
      - default
      - lucky-network  # 连接到lucky的网络

networks:
  lucky-network:
    external: true
```

---

## Phase 4: 开发计划

### 里程碑1: 基础框架 (Day 1-2)
- [ ] Docker环境搭建
- [ ] FastAPI基础项目
- [ ] Vue3 + Tailwind 前端框架
- [ ] 基础API连通

### 里程碑2: 核心功能 (Day 3-4)
- [ ] Lucky API集成
- [ ] Docker API集成
- [ ] 服务CRUD API
- [ ] 网格展示页面

### 里程碑3: 智能功能 (Day 5-6)
- [ ] 内外网判断
- [ ] 智能跳转路由
- [ ] 图标自动获取
- [ ] 状态检测

### 里程碑4: 完善优化 (Day 7)
- [ ] 设置面板
- [ ] 搜索过滤
- [ ] 主题切换
- [ ] Docker打包优化
- [ ] 文档编写

---

## Phase 5: 部署说明

### 环境变量配置
| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| LUCKY_BASE_URL | Lucky服务地址 | http://lucky:8080 |
| LUCKY_API_TOKEN | Lucky API令牌 | - |
| DOCKER_ENABLED | 启用Docker发现 | true |
| AUTO_DISCOVERY_INTERVAL | 自动发现间隔(秒) | 300 |
| THEME_DEFAULT | 默认主题 | dark |

### 快速启动
```bash
# 1. 克隆项目
git clone https://github.com/yourname/nas-homepage.git
cd nas-homepage

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 3. 启动
docker-compose up -d

# 4. 访问 http://your-nas-ip:3000
```
