"""NAS Homepage - 自动发现服务"""
import logging
import httpx
from datetime import datetime
from typing import List, Dict, Optional

from app.config import settings
from app.models import ServiceSource, ServiceStatus, IconSource
from app.services.service_manager import service_manager
from app.core.docker_client import docker_client, icon_fetcher
from app.core.lucky_client import LuckyClient

logger = logging.getLogger(__name__)


class AutoDiscovery:
    """自动发现服务 - 扫描Lucky和Docker中的服务"""

    def __init__(self):
        self.is_scanning = False
        self.last_scan: Optional[datetime] = None
        self.scan_count = 0
        self.error_message: Optional[str] = None
        self._lucky_client: Optional[LuckyClient] = None
        self._nas_lan_ip: Optional[str] = None

    def _get_nas_lan_ip(self) -> str:
        """自动获取飞牛NAS的局域网IP

        Docker容器内获取NAS真实局域网IP的策略:
        1. 环境变量 NAS_LAN_IP（手动指定，最可靠）
        2. 通过Docker API查询host网络模式容器 → 读取宿主机IP
        3. 从 /proc/net/route 读取默认网关（可能是Docker网桥，不一定是局域网IP）
        4. 兜底 127.0.0.1
        """
        import os
        import struct, socket

        # 缓存
        if self._nas_lan_ip:
            return self._nas_lan_ip

        # 1. 手动指定（优先级最高）
        ip = os.environ.get("NAS_LAN_IP")
        if ip:
            self._nas_lan_ip = ip
            logger.info(f"NAS局域网IP(环境变量): {ip}")
            return ip

        # 2. 通过Docker API查询host网络容器的网络信息
        # host网络模式容器共享宿主机网络栈，可以获取宿主机真实IP
        try:
            import httpx
            docker_sock = os.environ.get("DOCKER_SOCKET", "/var/run/docker.sock")
            # 通过unix socket访问Docker API
            with httpx.Client(transport=httpx.HTTPTransport(uds=docker_sock), timeout=5.0) as client:
                # 获取host网络模式容器列表
                resp = client.get("http://localhost/containers/json")
                if resp.status_code == 200:
                    containers = resp.json()
                    for c in containers:
                        if c.get("HostConfig", {}).get("NetworkMode") == "host":
                            cid = c["Id"]
                            # BusyBox不支持hostname -I，用ip addr代替
                            exec_resp = client.post(
                                f"http://localhost/containers/{cid}/exec",
                                json={
                                    "AttachStdout": True,
                                    "AttachStderr": True,
                                    "Cmd": ["sh", "-c", "ip addr show | grep 'inet ' | grep -v '127.0.0.1\\|172.\\|docker\\|br-' | head -1 | awk '{print $2}' | cut -d/ -f1"]
                                }
                            )
                            if exec_resp.status_code == 201:
                                exec_id = exec_resp.json()["Id"]
                                start_resp = client.post(
                                    f"http://localhost/exec/{exec_id}/start",
                                    json={"Detach": False, "Tty": False}
                                )
                                if start_resp.status_code == 200:
                                    raw = start_resp.content
                                    # 解析Docker stream格式: 8字节header + payload
                                    result = ""
                                    i = 0
                                    while i < len(raw):
                                        if i + 8 > len(raw): break
                                        length = int.from_bytes(raw[i+4:i+8], 'big')
                                        result += raw[i+8:i+8+length].decode('utf-8', errors='replace')
                                        i += 8 + length
                                    detected_ip = result.strip()
                                    # 验证是局域网IP（192.168.x.x / 10.x.x.x / 172.16-31.x.x）
                                    import re
                                    if detected_ip and re.match(r'^(192\.168\.|10\.|172\.(1[6-9]|2[0-9]|3[01])\.)', detected_ip):
                                        self._nas_lan_ip = detected_ip
                                        logger.info(f"NAS局域网IP(Docker自动检测): {detected_ip}")
                                        return detected_ip
        except Exception as e:
            logger.warning(f"Docker API检测NAS IP失败: {e}")

        # 3. 从路由表获取默认网关（注意：可能是Docker网桥IP）
        try:
            with open('/proc/net/route') as f:
                for line in f:
                    fields = line.strip().split()
                    if len(fields) >= 3 and fields[1] == '00000000':
                        packed = int(fields[2], 16)
                        ip = socket.inet_ntoa(struct.pack('<I', packed))
                        if ip and ip != '0.0.0.0':
                            self._nas_lan_ip = ip
                            logger.info(f"NAS局域网IP(网关检测，可能是Docker网桥): {ip}")
                            return ip
        except Exception as e:
            logger.warning(f"自动检测网关失败: {e}")

        # 4. 兜底
        self._nas_lan_ip = "127.0.0.1"
        logger.warning("NAS局域网IP: 无法检测，使用127.0.0.1")
        return self._nas_lan_ip

    def _fix_lan_url(self, url: Optional[str]) -> Optional[str]:
        """将内网地址中的127.0.0.1/localhost替换为NAS局域网IP（用户可访问的地址）"""
        if not url:
            return url
        nas_ip = self._get_nas_lan_ip()
        return url.replace("127.0.0.1", nas_ip).replace("localhost", nas_ip)

    def _get_container_gateway_ip(self) -> str:
        """获取容器内可达的网关IP（用于健康检查）

        容器内健康检查不能用NAS局域网IP(192.168.x.x)，
        因为容器可能和NAS不在同一网段，需要通过Docker网关访问
        """
        import os
        import struct, socket

        ip = os.environ.get("HOST_GATEWAY")
        if ip:
            return ip

        try:
            with open('/proc/net/route') as f:
                for line in f:
                    fields = line.strip().split()
                    if len(fields) >= 3 and fields[1] == '00000000':
                        packed = int(fields[2], 16)
                        ip = socket.inet_ntoa(struct.pack('<I', packed))
                        if ip and ip != '0.0.0.0':
                            return ip
        except Exception:
            pass
        return "172.25.0.1"

    def _get_check_url(self, service) -> Optional[str]:
        """获取健康检查URL（容器内可达地址）

        优先级: wan_url > lan_url(替换为容器网关IP)
        """
        # wan_url通常用域名，容器内可达
        if service.wan_url:
            return service.wan_url

        # lan_url需要替换为容器网关IP才能从容器内访问
        url = service.lan_url
        if not url:
            return None

        gateway = self._get_container_gateway_ip()
        # lan_url存储的已经是NAS局域网IP(192.168.x.x)，替换为网关IP
        nas_ip = self._get_nas_lan_ip()
        url = url.replace(nas_ip, gateway).replace("127.0.0.1", gateway).replace("localhost", gateway)
        return url

    def get_status(self) -> dict:
        """获取扫描状态"""
        return {
            "is_scanning": self.is_scanning,
            "last_scan": self.last_scan.isoformat() if self.last_scan else None,
            "scan_count": self.scan_count,
            "error_message": self.error_message,
        }

    async def scan_all(self):
        """执行全量扫描"""
        if self.is_scanning:
            return

        self.is_scanning = True
        self.error_message = None
        total_found = 0

        try:
            # 1. 扫描Lucky
            if settings.lucky_enabled:
                lucky_count = await self._scan_lucky()
                total_found += lucky_count
                logger.info(f"Lucky扫描完成, 发现 {lucky_count} 个服务")

            # 2. 扫描Docker
            if settings.docker_enabled:
                docker_count = await self._scan_docker()
                total_found += docker_count
                logger.info(f"Docker扫描完成, 发现 {docker_count} 个服务")

            # 3. 健康检查
            await self._health_check_all()

            self.scan_count = total_found
            self.last_scan = datetime.now()
            logger.info(f"全量扫描完成, 共发现 {total_found} 个服务")

        except Exception as e:
            self.error_message = str(e)
            logger.error(f"扫描失败: {e}")
        finally:
            self.is_scanning = False

    async def _scan_lucky(self) -> int:
        """从Lucky扫描服务

        Lucky返回的真实数据结构:
        {
            "id": "Key", "name": "Remark",
            "domains": ["fn.20221204.xyz"],   # 子规则公网域名
            "locations": ["http://127.0.0.1:5666"],  # 反代目标(内网地址)
            "listen_port": 8888,  # 主规则监听端口（需拼到域名后）
            "enable_tls": true    # 主规则是否TLS（决定协议）
        }
        外网地址 = proto://domain:listen_port（非标准端口时）
        """
        try:
            client = self._get_lucky_client()
            services = await client.get_web_services()
            count = 0

            for svc in services:
                try:
                    lucky_id = str(svc.get("id", ""))
                    name = svc.get("name", f"Lucky-{lucky_id[:6]}")

                    if not name:
                        continue

                    # 公网地址: 子规则 Domains + 主规则 ListenPort + EnableTLS 组合
                    wan_url = None
                    domains = svc.get("domains", [])
                    if domains and isinstance(domains, list) and len(domains) > 0:
                        first_domain = domains[0]
                        enable_tls = svc.get("enable_tls", False)
                        listen_port = svc.get("listen_port")
                        proto = "https" if enable_tls else "http"
                        default_port = 443 if enable_tls else 80
                        # 非标准端口需要显式拼上
                        if listen_port and listen_port != default_port:
                            wan_url = f"{proto}://{first_domain}:{listen_port}"
                        else:
                            wan_url = f"{proto}://{first_domain}"

                    # 内网地址: 从 Locations 列表(反代目标)
                    # 自动替换127.0.0.1为NAS局域网IP
                    lan_url = None
                    locations = svc.get("locations", [])
                    if locations and isinstance(locations, list) and len(locations) > 0:
                        lan_url = self._fix_lan_url(locations[0])

                    # 图标
                    icon_url = icon_fetcher.get_icon_for_app(name)

                    service_manager.create_or_update_from_discovery(
                        source=ServiceSource.LUCKY,
                        external_id=lucky_id,
                        name=name,
                        lan_url=lan_url,
                        wan_url=wan_url,
                        icon_url=icon_url,
                        status=ServiceStatus.CHECKING,
                    )
                    count += 1

                except Exception as e:
                    logger.error(f"处理Lucky服务失败: {e}")
                    continue

            return count

        except Exception as e:
            logger.error(f"Lucky扫描失败: {e}")
            return 0

    async def _scan_docker(self) -> int:
        """从Docker扫描容器"""
        try:
            if not docker_client.is_connected():
                logger.warning("Docker未连接，跳过扫描")
                return 0

            containers = docker_client.get_running_containers()
            count = 0

            for container in containers:
                try:
                    name = container["name"]
                    labels = container.get("labels", {})
                    ports = container.get("ports", {})

                    # 跳过没有端口映射的容器
                    if not ports and "homepage.url" not in labels:
                        continue

                    # 提取URL (优先从label)
                    lan_url = labels.get("homepage.url")
                    if not lan_url and ports:
                        # 从端口映射构建URL，用NAS局域网IP代替localhost
                        first_port = next(iter(ports.values()))
                        lan_url = f"http://{self._get_nas_lan_ip()}:{first_port}"
                    elif lan_url:
                        lan_url = self._fix_lan_url(lan_url)

                    wan_url = labels.get("homepage.wan_url")

                    # 描述
                    description = labels.get("homepage.description", "")

                    # 分类
                    category = labels.get("homepage.category", "")

                    # 图标
                    icon_url = labels.get("homepage.icon")
                    if not icon_url:
                        icon_url = icon_fetcher.get_icon_from_container(container)

                    # 名称 (优先从label)
                    display_name = labels.get("homepage.name", name)

                    service_manager.create_or_update_from_discovery(
                        source=ServiceSource.DOCKER,
                        external_id=name,
                        name=display_name,
                        description=description,
                        lan_url=lan_url,
                        wan_url=wan_url,
                        icon_url=icon_url,
                        category=category,
                        status=ServiceStatus.CHECKING,
                    )
                    count += 1

                except Exception as e:
                    logger.error(f"处理Docker容器 {container.get('name', '?')} 失败: {e}")
                    continue

            return count

        except Exception as e:
            logger.error(f"Docker扫描失败: {e}")
            return 0

    async def _health_check_all(self):
        """对所有服务进行健康检查

        使用容器内可达地址（网关IP），而非用户访问地址（NAS局域网IP）
        """
        services = service_manager.get_all(include_hidden=True)
        async with httpx.AsyncClient(timeout=5.0, verify=False) as client:
            for service in services:
                check_url = self._get_check_url(service)

                if not check_url:
                    service_manager.update_status(service.id, ServiceStatus.UNKNOWN)
                    continue

                try:
                    response = await client.get(check_url, follow_redirects=True)
                    if response.status_code < 500:
                        service_manager.update_status(service.id, ServiceStatus.ONLINE)
                    else:
                        service_manager.update_status(service.id, ServiceStatus.OFFLINE)
                except Exception:
                    service_manager.update_status(service.id, ServiceStatus.OFFLINE)

        # 批量保存状态
        service_manager._save_data()

    async def check_service_status(self, service_id: str) -> str:
        """检查单个服务状态"""
        service = service_manager.get(service_id)
        if not service:
            return "unknown"

        check_url = self._get_check_url(service)

        if not check_url:
            return "unknown"

        try:
            async with httpx.AsyncClient(timeout=5.0, verify=False) as client:
                response = await client.get(check_url, follow_redirects=True)
                status = ServiceStatus.ONLINE if response.status_code < 500 else ServiceStatus.OFFLINE
        except Exception:
            status = ServiceStatus.OFFLINE

        service_manager.update_status(service_id, status)
        service_manager._save_data()
        return status.value

    def _get_lucky_client(self) -> LuckyClient:
        """获取Lucky客户端实例"""
        if self._lucky_client is None:
            self._lucky_client = LuckyClient()
        return self._lucky_client


# 全局实例
auto_discovery = AutoDiscovery()
