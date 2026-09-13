"""NAS Homepage - 数据模型"""
from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field


class ServiceSource(str, Enum):
    """服务来源"""
    LUCKY = "lucky"
    DOCKER = "docker"
    MANUAL = "manual"


class ServiceStatus(str, Enum):
    """服务状态"""
    ONLINE = "online"
    OFFLINE = "offline"
    CHECKING = "checking"
    UNKNOWN = "unknown"


class IconSource(str, Enum):
    """图标来源"""
    AUTO_DOCKER = "auto_docker"
    AUTO_LUCKY = "auto_lucky"
    CUSTOM = "custom"
    DEFAULT = "default"


class Service(BaseModel):
    """服务模型"""
    id: str = Field(..., description="唯一标识")
    name: str = Field(..., description="显示名称")
    description: Optional[str] = Field(None, description="描述")

    # 图标
    icon_url: Optional[str] = Field(None, description="图标URL")
    icon_source: IconSource = Field(IconSource.DEFAULT, description="图标来源")

    # 地址配置
    lan_url: Optional[str] = Field(None, description="局域网地址")
    wan_url: Optional[str] = Field(None, description="外网地址")

    # 来源信息
    source: ServiceSource = Field(ServiceSource.MANUAL, description="来源")
    lucky_id: Optional[str] = Field(None, description="Lucky中的ID")
    container_name: Optional[str] = Field(None, description="Docker容器名")

    # 显示控制
    category: Optional[str] = Field(None, description="分类")
    order: int = Field(0, description="排序")
    is_visible: bool = Field(True, description="是否显示")

    # 回收站 (软删除)
    is_deleted: bool = Field(False, description="是否已删除(回收站中)")
    deleted_at: Optional[datetime] = Field(None, description="删除时间")

    # 状态 (动态)
    status: ServiceStatus = Field(ServiceStatus.UNKNOWN, description="状态")
    last_check: Optional[datetime] = Field(None, description="最后检测时间")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "grafana-001",
                "name": "Grafana",
                "description": "监控仪表盘",
                "icon_url": "https://cdn.jsdelivr.net/gh/walkxcode/dashboard-icons/png/grafana.png",
                "icon_source": "auto_docker",
                "lan_url": "http://192.168.1.100:3000",
                "wan_url": "https://grafana.example.com",
                "source": "docker",
                "container_name": "grafana",
                "category": "监控",
                "order": 1,
                "is_visible": True,
                "status": "online"
            }
        }


class ServiceCreate(BaseModel):
    """创建服务请求"""
    name: str
    description: Optional[str] = None
    lan_url: Optional[str] = None
    wan_url: Optional[str] = None
    category: Optional[str] = None
    icon_url: Optional[str] = None


class ServiceUpdate(BaseModel):
    """更新服务请求"""
    name: Optional[str] = None
    description: Optional[str] = None
    lan_url: Optional[str] = None
    wan_url: Optional[str] = None
    category: Optional[str] = None
    icon_url: Optional[str] = None
    order: Optional[int] = None
    is_visible: Optional[bool] = None


class AppSettings(BaseModel):
    """应用设置"""
    # Lucky配置
    lucky_enabled: bool = True
    lucky_base_url: str = "http://lucky:8080"
    lucky_api_token: Optional[str] = None

    # Docker配置
    docker_enabled: bool = True
    docker_socket: str = "/var/run/docker.sock"

    # 图标配置
    auto_fetch_icons: bool = True
    icon_cache_days: int = 7

    # UI配置
    default_theme: str = "dark"
    show_status_badge: bool = True
    show_url_type: bool = True


class DiscoveryStatus(BaseModel):
    """自动发现状态"""
    last_scan: Optional[datetime] = None
    is_scanning: bool = False
    services_found: int = 0
    error_message: Optional[str] = None


class NetworkInfo(BaseModel):
    """网络信息"""
    client_ip: str
    network_type: str  # lan / wan
    user_agent: Optional[str] = None
