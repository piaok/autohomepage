# 🏠 NAS Homepage

> 智能 NAS 服务导航页 — 自动发现、健康监测、主题定制

## ✨ 功能特性

- **🔍 自动发现** — 集成 Lucky 反向代理 API，自动发现所有内网/公网服务
- **💚 健康监测** — 定时检测服务在线状态，区分内网/公网可达性
- **🎨 6套主题** — 深空蓝 / 明亮白 / 森林绿 / 薰衣紫 / 暮光橙 / 深海青，一键切换
- **📱 响应式** — 移动端友好，自适应布局
- **⚙️ 灵活配置** — 服务编辑、批量管理、备份导入导出
- **🔗 智能跳转** — 自动识别内网/公网环境，优先直达
- **🛡️ 图标代理** — 后端代理 CDN 图标，国内网络无障碍

## 🛠️ 技术栈

| 层 | 技术 |
|---|---|
| 前端 | Vue 3 + TypeScript + Vite + Tailwind CSS |
| 后端 | FastAPI + Pydantic + httpx |
| 部署 | Docker + Portainer |

## 🚀 快速部署

### Docker Compose

```yaml
version: '3.8'
services:
  nas-homepage:
    image: nas-homepage:latest
    container_name: nas-homepage
    ports:
      - "8900:8000"
    environment:
      - LUCKY_ENABLED=true
      - LUCKY_BASE_URL=http://192.168.x.x:16601
      - LUCKY_OPEN_TOKEN=your_token
      - AUTO_DISCOVERY_INTERVAL=300
    restart: unless-stopped
```

### 环境变量

| 变量 | 默认值 | 说明 |
|---|---|---|
| `LUCKY_ENABLED` | `true` | 启用 Lucky 反代服务发现 |
| `LUCKY_BASE_URL` | `http://192.168.31.85:16601` | Lucky API 地址 |
| `LUCKY_OPEN_TOKEN` | - | Lucky OpenToken |
| `DOCKER_ENABLED` | `false` | 启用 Docker 容器发现 |
| `AUTO_DISCOVERY_INTERVAL` | `300` | 自动发现间隔（秒） |
| `HTTP_PROXY` | - | 图标代理 HTTP 代理地址 |

## 📸 截图

### 深空蓝主题 (默认)
![midnight](https://via.placeholder.com/800x450?text=Midnight+Theme)

### 明亮白主题
![daylight](https://via.placeholder.com/800x450?text=Daylight+Theme)

## 📂 项目结构

```
├── backend/
│   └── app/
│       ├── main.py           # FastAPI 入口 + SPA fallback
│       ├── config.py          # 配置管理
│       ├── api/               # REST API 路由
│       │   ├── services.py    # 服务 CRUD + 批量操作
│       │   ├── icons.py       # 图标代理 API
│       │   └── settings.py    # 全局设置
│       ├── core/              # Lucky API 客户端
│       ├── models/            # 数据模型
│       └── services/          # 自动发现引擎
├── frontend/
│   └── src/
│       ├── App.vue            # 主题管理
│       ├── style.css          # 6套主题 CSS 变量
│       ├── views/             # Home + Settings
│       ├── components/        # ServiceCard + StatusBadge + SearchBar
│       └── stores/            # Pinia 状态管理
├── Dockerfile
└── docker-compose.yml
```

## 📝 版本历史

### v0.1.0 (2026-05-03)

- 🎉 首个发布版本
- Lucky 反代服务自动发现
- 服务健康监测 (内网/公网双栈)
- 6 套配色主题
- 服务编辑、批量管理、备份导入导出
- 图标代理 (CDN 图标国内可达)
- 响应式布局

## 📜 License

MIT
