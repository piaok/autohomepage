"""NAS Homepage - API路由 - 智能跳转"""
from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.responses import RedirectResponse, HTMLResponse

from app.services.service_manager import service_manager
from app.core.network import get_client_ip, get_network_type
from app.config import settings

# /go/* 路由挂在根路径（不在 /api 下）
go_router = APIRouter(tags=["proxy"])

# /network/* 路由挂在 /api 下
network_router = APIRouter(prefix="/network", tags=["network"])


@go_router.get("/go/{service_id}")
async def smart_redirect(
    service_id: str,
    request: Request,
    force: str = Query(None, description="强制使用 lan 或 wan"),
):
    """
    智能跳转 - 根据客户端IP自动选择最优地址
    - 内网访问: 优先使用LAN URL
    - 外网访问: 优先使用WAN URL
    - 使用 force 参数可强制指定
    """
    service = service_manager.get(service_id)
    if not service:
        raise HTTPException(status_code=404, detail="服务不存在")

    if not service.is_visible:
        raise HTTPException(status_code=403, detail="服务已隐藏")

    # 强制模式
    if force == "lan":
        if service.lan_url:
            return RedirectResponse(service.lan_url)
        raise HTTPException(status_code=400, detail="该服务未配置LAN地址")

    if force == "wan":
        if service.wan_url:
            return RedirectResponse(service.wan_url)
        raise HTTPException(status_code=400, detail="该服务未配置WAN地址")

    # 自动判断
    client_ip = get_client_ip(
        dict(request.headers),
        request.client.host if request.client else "unknown",
        settings.trusted_proxies
    )
    network_type = get_network_type(client_ip, settings.custom_lan_ranges)

    # 选择URL
    if network_type == "lan" and service.lan_url:
        url = service.lan_url
    elif service.wan_url:
        url = service.wan_url
    elif service.lan_url:
        # 外网访问但只有内网地址
        return HTMLResponse(
            content=f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>访问受限 - {service.name}</title>
                <style>
                    body {{ font-family: system-ui, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; text-align: center; }}
                    .warning {{ background: #fef3c7; border: 1px solid #f59e0b; border-radius: 8px; padding: 20px; }}
                    h1 {{ color: #92400e; }}
                    .info {{ color: #6b7280; margin-top: 20px; }}
                </style>
            </head>
            <body>
                <div class="warning">
                    <h1>⚠️ 服务仅限内网访问</h1>
                    <p><strong>{service.name}</strong> 只能在局域网内访问。</p>
                    <p class="info">LAN地址: {service.lan_url}</p>
                    <p class="info">您的IP: {client_ip} ({network_type})</p>
                </div>
            </body>
            </html>
            """,
            status_code=403
        )
    else:
        raise HTTPException(status_code=400, detail="该服务没有配置任何地址")

    return RedirectResponse(url)


@go_router.get("/go/{service_id}/lan")
async def force_lan_redirect(service_id: str):
    """强制跳转到内网地址"""
    service = service_manager.get(service_id)
    if not service:
        raise HTTPException(status_code=404, detail="服务不存在")

    if not service.lan_url:
        raise HTTPException(status_code=400, detail="该服务未配置LAN地址")

    return RedirectResponse(service.lan_url)


@go_router.get("/go/{service_id}/wan")
async def force_wan_redirect(service_id: str):
    """强制跳转到外网地址"""
    service = service_manager.get(service_id)
    if not service:
        raise HTTPException(status_code=404, detail="服务不存在")

    if not service.wan_url:
        raise HTTPException(status_code=400, detail="该服务未配置WAN地址")

    return RedirectResponse(service.wan_url)


@network_router.get("/info")
async def get_network_info(request: Request):
    """获取当前网络信息"""
    client_ip = get_client_ip(
        dict(request.headers),
        request.client.host if request.client else "unknown",
        settings.trusted_proxies
    )
    network_type = get_network_type(client_ip, settings.custom_lan_ranges)

    return {
        "client_ip": client_ip,
        "network_type": network_type,
        "is_lan": network_type == "lan",
        "headers": {
            "x-forwarded-for": request.headers.get("x-forwarded-for"),
            "x-real-ip": request.headers.get("x-real-ip"),
        },
        "direct_remote": request.client.host if request.client else None,
    }
