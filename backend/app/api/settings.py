"""NAS Homepage - API路由 - 设置"""
import json
import os
import logging
from fastapi import APIRouter, HTTPException

from app.config import settings
from app.models import AppSettings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settings", tags=["settings"])

SETTINGS_FILE = os.path.join(settings.data_dir, "settings.json")


def _load_persisted_settings() -> dict:
    """从文件加载持久化设置"""
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载设置文件失败: {e}")
    return {}


def _save_persisted_settings(data: dict):
    """保存设置到文件"""
    os.makedirs(settings.data_dir, exist_ok=True)
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"保存设置文件失败: {e}")


@router.get("")
async def get_settings():
    """获取应用设置"""
    # 合并环境变量配置和持久化配置
    persisted = _load_persisted_settings()

    return {
        "lucky_enabled": persisted.get("lucky_enabled", settings.lucky_enabled),
        "lucky_base_url": persisted.get("lucky_base_url", settings.lucky_base_url),
        "lucky_api_token": "***" if (persisted.get("lucky_api_token") or settings.lucky_api_token) else None,
        "docker_enabled": persisted.get("docker_enabled", settings.docker_enabled),
        "docker_socket": persisted.get("docker_socket", settings.docker_socket),
        "auto_discovery_interval": persisted.get("auto_discovery_interval", settings.auto_discovery_interval),
        "default_theme": persisted.get("default_theme", settings.default_theme),
        "http_proxy": persisted.get("http_proxy", settings.http_proxy or ""),
    }


@router.put("")
async def update_settings(data: dict):
    """更新应用设置 (部分更新)"""
    # 允许更新的字段白名单
    allowed_fields = {
        "lucky_enabled", "lucky_base_url", "lucky_api_token",
        "docker_enabled", "docker_socket",
        "auto_discovery_interval", "default_theme", "http_proxy",
    }

    # 过滤非法字段
    updates = {k: v for k, v in data.items() if k in allowed_fields}
    if not updates:
        raise HTTPException(status_code=400, detail="没有有效的更新字段")

    # 类型校验
    if "auto_discovery_interval" in updates:
        try:
            updates["auto_discovery_interval"] = int(updates["auto_discovery_interval"])
            if updates["auto_discovery_interval"] < 30:
                raise ValueError()
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="auto_discovery_interval 必须 >= 30")

    if "lucky_enabled" in updates:
        updates["lucky_enabled"] = bool(updates["lucky_enabled"])
    if "docker_enabled" in updates:
        updates["docker_enabled"] = bool(updates["docker_enabled"])

    # 加载已有设置并合并
    persisted = _load_persisted_settings()
    persisted.update(updates)
    _save_persisted_settings(persisted)

    # 运行时更新 (环境变量级别的配置无法运行时修改，只改持久化层)
    logger.info(f"设置已更新: {list(updates.keys())}")

    return {
        "message": "设置已更新",
        "updated_fields": list(updates.keys()),
    }
