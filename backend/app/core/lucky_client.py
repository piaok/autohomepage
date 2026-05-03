"""NAS Homepage - Lucky API客户端"""
import logging
from typing import List, Dict, Optional
import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# Lucky API 基础路径
LUCKY_API_PREFIX = "/lucky/api"


class LuckyClient:
    """Lucky Web服务API客户端

    Lucky API 认证方式:
    - Header: openToken: XXXXXXXX

    核心 API:
    - GET /lucky/api/webservice/rules     完整规则列表
    - GET /lucky/api/webservice/rules_lite 精简规则列表

    注意:
    - base_url 存储用户可见的NAS局域网地址
    - _api_url 返回容器内可达的地址（用于API调用）
    """

    def __init__(self, base_url: str = None, open_token: Optional[str] = None):
        self.base_url = (base_url or settings.lucky_base_url).rstrip('/')
        self.open_token = open_token or settings.lucky_api_token
        self.client = httpx.AsyncClient(timeout=10.0)
        self._api_url: Optional[str] = None

    def _get_api_url(self) -> str:
        """获取容器内可达的Lucky API地址

        base_url可能是NAS局域网IP(192.168.x.x)，容器内可能无法直接访问
        需要替换为容器网关IP或Docker桥接IP
        """
        if self._api_url:
            return self._api_url

        # 尝试用base_url直连，如果通就用它
        import os
        import struct, socket

        url = self.base_url

        # 从base_url提取IP
        import re
        match = re.search(r'http[s]?://([^:/]+)', url)
        if not match:
            self._api_url = url
            return url

        host_ip = match.group(1)

        # 如果是Docker内网IP(172.x)或localhost，保持不变（容器内可达）
        if host_ip.startswith("172.") or host_ip in ("localhost", "127.0.0.1"):
            self._api_url = url
            return url

        # 是NAS局域网IP(192.168.x.x / 10.x.x.x)，替换为容器网关
        gateway = os.environ.get("HOST_GATEWAY")
        if not gateway:
            try:
                with open('/proc/net/route') as f:
                    for line in f:
                        fields = line.strip().split()
                        if len(fields) >= 3 and fields[1] == '00000000':
                            packed = int(fields[2], 16)
                            gateway = socket.inet_ntoa(struct.pack('<I', packed))
                            break
            except Exception:
                pass

        if gateway:
            self._api_url = url.replace(host_ip, gateway)
            logger.info(f"Lucky API地址: {url} → {self._api_url} (容器网关)")
        else:
            self._api_url = url

        return self._api_url

    def _get_headers(self) -> dict:
        """获取带认证的请求头"""
        headers = {}
        if self.open_token:
            headers["openToken"] = self.open_token
        return headers

    async def get_web_services(self) -> List[Dict]:
        """
        获取Lucky配置的Web服务列表

        返回数据结构:
        {
            "ret": 0,
            "ruleList": [
                {
                    "RuleKey": "xxx",
                    "RuleName": "nas",
                    "ListenPort": 8888,
                    "EnableTLS": true,
                    "Enable": true,
                    "ProxyList": [
                        {
                            "Key": "xxx",
                            "WebServiceType": "reverseproxy",
                            "Enable": true,
                            "Remark": "fnos",
                            "Domains": ["fn.20221204.xyz"],
                            "Locations": ["http://127.0.0.1:5666"]
                        }
                    ]
                }
            ]
        }
        """
        try:
            response = await self.client.get(
                f"{self._get_api_url()}{LUCKY_API_PREFIX}/webservice/rules",
                headers=self._get_headers()
            )
            response.raise_for_status()

            data = response.json()
            if data.get("ret") != 0:
                logger.error(f"Lucky API返回错误: {data.get('msg')}")
                return []

            rule_list = data.get("ruleList", [])
            logger.info(f"从Lucky获取到 {len(rule_list)} 个规则组")

            # 展平 ProxyList
            services = []
            for rule in rule_list:
                if not rule.get("Enable", True):
                    continue
                for proxy in rule.get("ProxyList", []):
                    if not proxy.get("Enable", True):
                        continue
                    # 构造统一的服务数据
                    service = {
                        "id": proxy.get("Key", ""),
                        "name": proxy.get("Remark", ""),
                        "rule_name": rule.get("RuleName", ""),
                        "rule_key": rule.get("RuleKey", ""),
                        "type": proxy.get("WebServiceType", ""),
                        "domains": proxy.get("Domains", []),
                        "locations": proxy.get("Locations", []),
                        "listen_port": rule.get("ListenPort"),
                        "enable_tls": rule.get("EnableTLS", False),
                    }
                    services.append(service)

            logger.info(f"解析出 {len(services)} 个活跃服务")
            return services

        except httpx.HTTPStatusError as e:
            logger.error(f"Lucky API HTTP错误: {e.response.status_code}")
            return []
        except httpx.RequestError as e:
            logger.error(f"Lucky API请求错误: {e}")
            return []
        except Exception as e:
            logger.error(f"Lucky API未知错误: {e}")
            return []

    async def get_rules_lite(self) -> List[Dict]:
        """获取精简版规则列表（只有Key和Name）"""
        try:
            response = await self.client.get(
                f"{self._get_api_url()}{LUCKY_API_PREFIX}/webservice/rules_lite",
                headers=self._get_headers()
            )
            response.raise_for_status()

            data = response.json()
            if data.get("ret") != 0:
                return []

            return data.get("list", [])

        except Exception as e:
            logger.error(f"Lucky rules_lite API错误: {e}")
            return []

    async def health_check(self) -> bool:
        """检查Lucky服务是否可用"""
        try:
            response = await self.client.get(
                f"{self._get_api_url()}{LUCKY_API_PREFIX}/webservice/rules_lite",
                headers=self._get_headers(),
                timeout=5.0
            )
            return response.status_code == 200
        except Exception:
            return False
