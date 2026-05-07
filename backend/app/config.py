"""NAS Homepage - 配置管理"""
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置"""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # 应用配置
    app_name: str = "NAS Homepage"
    app_version: str = "1.0.0"
    debug: bool = False

    # 服务器配置
    host: str = "0.0.0.0"
    port: int = 8000

    # Lucky 配置
    lucky_enabled: bool = Field(default=True, alias="LUCKY_ENABLED")
    lucky_base_url: str = Field(default="http://192.168.31.85:16601", alias="LUCKY_BASE_URL")
    lucky_api_token: Optional[str] = Field(default=None, alias="LUCKY_API_TOKEN")

    # Docker 配置
    docker_enabled: bool = Field(default=True, alias="DOCKER_ENABLED")
    docker_socket: str = Field(default="/var/run/docker.sock", alias="DOCKER_SOCKET")

    # 自动发现配置
    auto_discovery_interval: int = Field(default=300, alias="AUTO_DISCOVERY_INTERVAL")

    # 网络配置
    trusted_proxies: List[str] = Field(default_factory=list, alias="TRUSTED_PROXIES")
    custom_lan_ranges: List[str] = Field(default_factory=list, alias="CUSTOM_LAN_RANGES")
    http_proxy: Optional[str] = Field(default=None, alias="HTTP_PROXY_URL")

    # UI 配置
    default_theme: str = Field(default="dark", alias="THEME_DEFAULT")

    # 数据目录
    data_dir: str = Field(default="/app/data", alias="DATA_DIR")


# 全局配置实例
settings = Settings()
