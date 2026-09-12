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

    # Lucky 配置 (通过 .env 或环境变量提供，敏感信息勿写死在代码中)
    lucky_enabled: bool = Field(default=True, alias="LUCKY_ENABLED")
    lucky_base_url: str = Field(default="", alias="LUCKY_BASE_URL")
    lucky_api_token: Optional[str] = Field(default=None, alias="LUCKY_OPEN_TOKEN")

    # Docker 配置
    docker_enabled: bool = Field(default=True, alias="DOCKER_ENABLED")
    docker_socket: str = Field(default="/var/run/docker.sock", alias="DOCKER_SOCKET")

    # 自动发现配置
    auto_discovery_interval: int = Field(default=300, alias="AUTO_DISCOVERY_INTERVAL")

    # 健康检查是否校验HTTPS证书（自签证书环境可设为false）
    health_check_verify_tls: bool = Field(default=True, alias="HEALTH_CHECK_VERIFY_TLS")

    # 是否完全信任远程转发头（X-Forwarded-For等）。仅在内网可信环境可设为true
    trust_forward_headers: bool = Field(default=False, alias="TRUST_FORWARD_HEADERS")

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
