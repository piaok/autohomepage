"""NAS Homepage - API路由 - 自动发现"""
from fastapi import APIRouter, BackgroundTasks

from app.services.auto_discovery import auto_discovery
from app.config import settings

router = APIRouter(prefix="/discovery", tags=["discovery"])


@router.post("/scan")
async def trigger_scan(background_tasks: BackgroundTasks):
    """触发一次自动发现扫描"""
    if auto_discovery.is_scanning:
        return {"message": "扫描已在进行中", "status": auto_discovery.get_status()}

    background_tasks.add_task(auto_discovery.scan_all)
    return {"message": "扫描已启动", "status": auto_discovery.get_status()}


@router.get("/status")
async def get_discovery_status():
    """获取自动发现状态"""
    return auto_discovery.get_status()


@router.post("/lucky")
async def sync_from_lucky():
    """从Lucky同步服务"""
    if not settings.lucky_enabled:
        return {"error": "Lucky集成未启用"}

    results = await auto_discovery._scan_lucky()
    return {
        "message": "Lucky同步完成",
        "results": results
    }


@router.post("/docker")
async def sync_from_docker():
    """从Docker同步服务"""
    if not settings.docker_enabled:
        return {"error": "Docker集成未启用"}

    results = await auto_discovery._scan_docker()
    return {
        "message": "Docker同步完成",
        "results": results
    }
