"""NAS Homepage - API路由 - 服务管理"""
import json
import logging
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query

from app.models import Service, ServiceCreate, ServiceUpdate
from app.services.service_manager import service_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/services", tags=["services"])


@router.get("", response_model=List[Service])
async def get_services(
    include_hidden: bool = Query(False, description="包含隐藏的服务"),
    filter_disabled: bool = Query(True, description="过滤掉未启用的服务"),
    category: Optional[str] = Query(None, description="按分类筛选")
):
    """获取所有服务列表"""
    services = service_manager.get_all(include_hidden=include_hidden)

    if filter_disabled:
        services = [s for s in services if s.is_visible]

    if category:
        services = [s for s in services if s.category == category]

    return services


@router.get("/categories/list")
async def get_categories():
    """获取所有分类"""
    services = service_manager.get_all()
    categories = set()
    for s in services:
        if s.category:
            categories.add(s.category)
    return sorted(list(categories))


# === 固定路径路由 (必须在 /{service_id} 之前) ===


@router.post("/batch/delete")
async def batch_delete_services(data: dict):
    """批量删除服务"""
    ids = data.get("ids", [])
    if not ids:
        raise HTTPException(status_code=400, detail="ids不能为空")

    deleted = []
    failed = []
    for sid in ids:
        if service_manager.delete(sid):
            deleted.append(sid)
        else:
            failed.append(sid)

    return {
        "deleted": deleted,
        "failed": failed,
        "message": f"已删除 {len(deleted)} 个服务"
    }


@router.post("/batch/hide")
async def batch_hide_services(data: dict):
    """批量隐藏/显示服务"""
    ids = data.get("ids", [])
    visible = data.get("visible", False)
    if not ids:
        raise HTTPException(status_code=400, detail="ids不能为空")

    updated = []
    for sid in ids:
        service = service_manager.update(sid, is_visible=visible)
        if service:
            updated.append(sid)

    return {
        "updated": updated,
        "message": f"已{'显示' if visible else '隐藏'} {len(updated)} 个服务"
    }


@router.post("/batch/reorder")
async def batch_reorder_services(data: dict):
    """批量更新排序"""
    orders = data.get("orders", [])
    if not orders:
        raise HTTPException(status_code=400, detail="orders不能为空")

    updated = []
    for item in orders:
        sid = item.get("id")
        order = item.get("order")
        if sid is not None and order is not None:
            service = service_manager.update(sid, order=order)
            if service:
                updated.append(sid)

    return {
        "updated": updated,
        "message": f"已更新 {len(updated)} 个服务排序"
    }


# === 回收站 ===


@router.get("/recycle/list")
async def get_recycle_bin():
    """获取回收站中的服务"""
    services = service_manager.get_deleted()
    return [s.model_dump(mode="json") for s in services]


@router.post("/recycle/{service_id}/restore")
async def restore_from_recycle(service_id: str):
    """从回收站恢复服务"""
    if not service_manager.restore(service_id):
        raise HTTPException(status_code=404, detail="回收站中找不到该服务")
    service = service_manager.get(service_id)
    return {"message": f"已恢复: {service.name}", "service": service.model_dump(mode="json")}


@router.post("/recycle/{service_id}/purge")
async def purge_from_recycle(service_id: str):
    """永久删除回收站中的服务"""
    service = service_manager.get(service_id)
    if not service or not service.is_deleted:
        raise HTTPException(status_code=404, detail="回收站中找不到该服务")
    name = service.name
    service_manager.purge(service_id)
    return {"message": f"已永久删除: {name}"}


@router.post("/recycle/purge-all")
async def purge_all_recycle():
    """清空回收站"""
    count = service_manager.empty_recycle_bin()
    return {"purged": count, "message": f"已清空回收站 {count} 个服务"}


@router.post("/dedupe")
async def dedupe_services():
    """一键去重：同内网IP:端口的服务合并为一个，多余项进入回收站"""
    removed = service_manager.dedupe()
    return {"removed": removed, "message": f"已合并 {removed} 个重复服务（可在回收站还原）"}


@router.get("/backup/export")
async def backup_export():
    """导出备份（所有服务+设置）"""
    services_data = [
        s.model_dump(mode="json") for s in service_manager.get_all(include_hidden=True)
    ]

    # 加载设置
    from app.api.settings import _load_persisted_settings
    settings_data = _load_persisted_settings()

    backup = {
        "version": "1.0",
        "exported_at": datetime.now().isoformat(),
        "services": services_data,
        "settings": settings_data,
    }

    return backup


@router.post("/backup/import")
async def backup_import(data: dict):
    """导入备份"""
    services_data = data.get("services", [])
    settings_data = data.get("settings", {})

    if not services_data and not settings_data:
        raise HTTPException(status_code=400, detail="备份数据为空")

    imported_services = 0
    for item in services_data:
        try:
            sid = item.get("id")
            if sid and sid in service_manager.services:
                # 更新已有
                service = service_manager.services[sid]
                for key, value in item.items():
                    if hasattr(service, key) and key != "id":
                        setattr(service, key, value)
            else:
                # 创建新服务
                service = Service(**item)
                service_manager.services[service.id] = service
            imported_services += 1
        except Exception as e:
            logger.warning(f"导入服务失败: {e}")

    # 导入设置
    if settings_data:
        from app.api.settings import _save_persisted_settings
        _save_persisted_settings(settings_data)

    service_manager.save()

    return {
        "imported_services": imported_services,
        "settings_imported": bool(settings_data),
        "message": f"已导入 {imported_services} 个服务"
    }


# === 动态路径路由 ===


@router.get("/{service_id}", response_model=Service)
async def get_service(service_id: str):
    """获取单个服务详情"""
    service = service_manager.get(service_id)
    if not service:
        raise HTTPException(status_code=404, detail="服务不存在")
    return service


@router.post("", response_model=Service)
async def create_service(data: ServiceCreate):
    """手动创建服务"""
    service = service_manager.create(
        name=data.name,
        lan_url=data.lan_url,
        wan_url=data.wan_url,
        description=data.description,
        category=data.category,
        icon_url=data.icon_url
    )
    return service


@router.put("/{service_id}", response_model=Service)
async def update_service(service_id: str, data: ServiceUpdate):
    """更新服务"""
    service = service_manager.update(
        service_id,
        **data.model_dump(exclude_unset=True)
    )
    if not service:
        raise HTTPException(status_code=404, detail="服务不存在")
    return service


@router.delete("/{service_id}")
async def delete_service(service_id: str):
    """删除服务"""
    success = service_manager.delete(service_id)
    if not success:
        raise HTTPException(status_code=404, detail="服务不存在")
    return {"message": "服务已删除"}


@router.post("/{service_id}/check")
async def check_service(service_id: str):
    """手动检测服务状态"""
    from app.services.auto_discovery import auto_discovery

    service = service_manager.get(service_id)
    if not service:
        raise HTTPException(status_code=404, detail="服务不存在")

    status = await auto_discovery.check_service_status(service_id)
    return {"service_id": service_id, "status": status}
