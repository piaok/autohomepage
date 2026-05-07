"""NAS Homepage - Docker客户端和图标获取"""
import logging
import re
from typing import Optional, Dict, List
import httpx
import docker
from docker.errors import DockerException

logger = logging.getLogger(__name__)

# 已知的应用图标映射
KNOWN_ICONS = {
    "grafana": "grafana",
    "prometheus": "prometheus",
    "plex": "plex",
    "jellyfin": "jellyfin",
    "emby": "emby",
    "qbittorrent": "qbittorrent",
    "transmission": "transmission",
    "sonarr": "sonarr",
    "radarr": "radarr",
    "lidarr": "lidarr",
    "prowlarr": "prowlarr",
    "bazarr": "bazarr",
    "nextcloud": "nextcloud",
    "homeassistant": "home-assistant",
    "home-assistant": "home-assistant",
    "portainer": "portainer",
    "vaultwarden": "vaultwarden",
    "jellyseerr": "jellyseerr",
    "overseerr": "overseerr",
    "nas-tools": "nas-tools",
    "moviepilot": "moviepilot",
    "alist": "alist",
    "openwrt": "openwrt",
    "synology": "synology",
    "unraid": "unraid",
    "truenas": "truenas",
    "omv": "openmediavault",
    "nginx": "nginx",
    "caddy": "caddy",
    "traefik": "traefik",
    "adguard": "adguard-home",
    "pi-hole": "pi-hole",
    "nastools": "nas-tools",
    "chinesesubfinder": "chinesesubfinder",
}


class DockerClient:
    """Docker客户端"""

    def __init__(self, socket_path: str = "/var/run/docker.sock"):
        self.socket_path = socket_path
        self.client = None
        self._connect()

    def _connect(self):
        """连接Docker"""
        try:
            self.client = docker.DockerClient(base_url=f"unix://{self.socket_path}")
            self.client.ping()
            logger.info("Docker连接成功")
        except DockerException as e:
            logger.warning(f"Docker连接失败: {e}")
            self.client = None

    def is_connected(self) -> bool:
        """检查是否已连接"""
        if self.client is None:
            return False
        try:
            self.client.ping()
            return True
        except:
            return False

    def get_running_containers(self) -> List[Dict]:
        """获取运行中的容器列表"""
        if not self.is_connected():
            return []

        try:
            containers = self.client.containers.list()
            result = []
            for container in containers:
                info = {
                    "id": container.id[:12],
                    "name": container.name,
                    "image": container.image.tags[0] if container.image.tags else container.image.id[:12],
                    "status": container.status,
                    "ports": self._extract_ports(container),
                    "labels": container.labels,
                }
                result.append(info)
            return result
        except Exception as e:
            logger.error(f"获取容器列表失败: {e}")
            return []

    def _extract_ports(self, container) -> Dict:
        """提取端口映射"""
        ports = {}
        try:
            container_ports = container.attrs.get("NetworkSettings", {}).get("Ports", {})
            for internal, externals in container_ports.items():
                if externals:
                    for ext in externals:
                        host_port = ext.get("HostPort")
                        if host_port:
                            ports[internal] = host_port
        except:
            pass
        return ports

    def get_container_by_name(self, name: str) -> Optional[Dict]:
        """根据名称获取容器"""
        if not self.is_connected():
            return None

        try:
            container = self.client.containers.get(name)
            return {
                "id": container.id[:12],
                "name": container.name,
                "image": container.image.tags[0] if container.image.tags else container.image.id[:12],
                "status": container.status,
            }
        except:
            return None


class IconFetcher:
    """图标获取器"""

    def __init__(self):
        self.cache: Dict[str, str] = {}
        self.icon_base_urls = [
            "https://cdn.jsdelivr.net/gh/walkxcode/dashboard-icons/png",
            "https://cdn.jsdelivr.net/gh/xushier/HD-Icons/border-radius",
            "https://cdn.selfh.st/icons",
        ]

    def get_icon_for_app(self, app_name: str) -> Optional[str]:
        """
        获取应用的图标URL
        优先从图标CDN获取，如果没有则返回None
        """
        if not app_name:
            return None

        app_name = app_name.lower().strip()

        # 检查缓存
        if app_name in self.cache:
            return self.cache[app_name]

        # 映射已知应用名
        mapped_name = KNOWN_ICONS.get(app_name, app_name)

        # 构建图标URL (优先使用 walkxcode 的图标库)
        icon_url = f"{self.icon_base_urls[0]}/{mapped_name}.png"

        # 简单缓存
        self.cache[app_name] = icon_url
        return icon_url

    def get_icon_from_container(self, container_info: Dict) -> Optional[str]:
        """
        从容器信息中提取应用图标
        策略:
        1. 从镜像名提取应用名
        2. 从容器标签获取 (如 homepage.icon)
        3. 从环境变量获取
        """
        # 1. 从镜像名提取
        image = container_info.get("image", "")
        app_name = self._extract_app_name(image)

        # 2. 检查标签
        labels = container_info.get("labels", {})
        if "homepage.icon" in labels:
            return labels["homepage.icon"]
        if "com.docker.compose.service" in labels:
            app_name = labels["com.docker.compose.service"]

        return self.get_icon_for_app(app_name)

    def _extract_app_name(self, image_name: str) -> str:
        """从镜像名提取应用名"""
        # linuxserver/plex:latest -> plex
        # grafana/grafana:9.0 -> grafana
        if not image_name:
            return ""

        # 移除digest和tag
        name = image_name.split('@')[0].split(':')[0]

        # 提取最后一部分
        parts = name.split('/')
        if len(parts) > 1:
            # 如果有组织名，取最后一个
            name = parts[-1]

        # 清理常见前缀/后缀
        name = re.sub(r'^(linuxserver/)?(lsio)?', '', name)
        name = re.sub(r'-docker$|-container$', '', name)

        return name.lower()

    async def verify_icon_url(self, url: str) -> bool:
        """验证图标URL是否可用"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.head(url, timeout=5)
                return response.status_code == 200
        except:
            return False


# 全局实例
docker_client = DockerClient()
icon_fetcher = IconFetcher()
