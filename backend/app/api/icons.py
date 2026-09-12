"""NAS Homepage - 图标代理API

前端无法直接访问国外CDN（jsdelivr/selfh.st等），
通过后端代理转发，支持配置HTTP代理。
"""
import logging
from fastapi import APIRouter, Query, Response, HTTPException
from fastapi.responses import StreamingResponse
import httpx

from app.config import settings
from app.api.settings import _load_persisted_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/icons", tags=["icons"])

# 缓存：URL -> (content_type, bytes)
_cache: dict[str, tuple[str, bytes]] = {}
_CACHE_MAX = 500


def _get_proxy_url() -> str | None:
    """获取持久化的代理地址"""
    persisted = _load_persisted_settings()
    return persisted.get("http_proxy") or settings.http_proxy or None


@router.get("/proxy")
async def proxy_icon(url: str = Query(..., description="图标CDN地址")):
    """代理获取图标，支持通过HTTP代理访问"""
    # 安全：只允许已知CDN域名
    allowed_domains = [
        "cdn.jsdelivr.net", "fastly.jsdelivr.net", "gcore.jsdelivr.net",
        "cdn.selfh.st", "raw.githubusercontent.com",
    ]
    from urllib.parse import urlparse
    parsed = urlparse(url)
    hostname = parsed.hostname or ""
    # 精确匹配或子域匹配（避免 evil-cdn.jsdelivr.net 之类绕过 endswith）
    def _domain_allowed(host: str, allow: str) -> bool:
        return host == allow or host.endswith("." + allow)
    if parsed.scheme not in ("http", "https") or not any(
        hostname and _domain_allowed(hostname, d) for d in allowed_domains
    ):
        raise HTTPException(status_code=403, detail="不允许的域名")

    # 检查缓存
    if url in _cache:
        ct, data = _cache[url]
        return Response(content=data, media_type=ct, headers={"Cache-Control": "public, max-age=86400"})

    # 构建httpx客户端（可选代理）
    proxy_url = _get_proxy_url()
    client_kwargs = {"timeout": 10.0}
    if proxy_url:
        client_kwargs["proxy"] = proxy_url

    try:
        async with httpx.AsyncClient(**client_kwargs) as client:
            resp = await client.get(url, follow_redirects=True)
            resp.raise_for_status()

            content_type = resp.headers.get("content-type", "image/png")
            data = resp.content

            # 缓存
            if len(_cache) >= _CACHE_MAX:
                # 简单LRU：清除一半
                keys = list(_cache.keys())
                for k in keys[:_CACHE_MAX // 2]:
                    del _cache[k]
            _cache[url] = (content_type, data)

            return Response(content=data, media_type=content_type, headers={"Cache-Control": "public, max-age=86400"})

    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail="图标源返回错误")
    except Exception as e:
        logger.warning(f"图标代理获取失败: {url} -> {e}")
        raise HTTPException(status_code=502, detail=f"获取图标失败: {str(e)[:100]}")
