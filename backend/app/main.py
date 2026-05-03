"""NAS Homepage - FastAPI主入口"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse

from app.config import settings
from app.api import router as api_router

# 配置日志
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("NAS Homepage 启动中...")
    logger.info(f"Lucky集成: {'启用' if settings.lucky_enabled else '禁用'}")
    logger.info(f"Docker集成: {'启用' if settings.docker_enabled else '禁用'}")

    # 启动后台任务: 自动发现
    if settings.lucky_enabled or settings.docker_enabled:
        from app.services.auto_discovery import auto_discovery
        import asyncio

        async def periodic_discovery():
            while True:
                await asyncio.sleep(settings.auto_discovery_interval)
                await auto_discovery.scan_all()

        # 启动后台任务
        asyncio.create_task(periodic_discovery())
        logger.info(f"自动发现任务已启动，间隔: {settings.auto_discovery_interval}秒")

    yield

    # 关闭时执行
    logger.info("NAS Homepage 关闭中...")


# 创建FastAPI应用
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="NAS Homepage - 智能服务导航页",
    lifespan=lifespan
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("未处理的异常")
    return JSONResponse(
        status_code=500,
        content={"detail": "服务器内部错误"}
    )


# 注册API路由 (必须在 mount 之前)
app.include_router(api_router)

# 健康检查 (必须在 mount 之前)
@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "version": settings.app_version,
        "lucky_enabled": settings.lucky_enabled,
        "docker_enabled": settings.docker_enabled,
    }

# 静态文件 (前端构建产物)
import os
static_dir = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.exists(static_dir):
    # 挂载静态文件到 /assets 路径
    app.mount("/assets", StaticFiles(directory=os.path.join(static_dir, "assets")), name="static-assets")
    
    # SPA fallback: 所有未匹配的路由返回 index.html
    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str):
        """SPA路由回退 - 返回index.html让前端路由处理"""
        # 尝试匹配静态文件
        file_path = os.path.join(static_dir, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        # 否则返回 index.html (SPA fallback)
        return FileResponse(os.path.join(static_dir, "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
