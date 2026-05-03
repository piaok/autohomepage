"""NAS Homepage - API路由初始化"""
from fastapi import APIRouter

from app.api import services, discovery, proxy, settings, icons

# /api/* 路由组
api_router = APIRouter(prefix="/api")
api_router.include_router(services.router)
api_router.include_router(discovery.router)
api_router.include_router(settings.router)
api_router.include_router(proxy.network_router)  # /api/network/*
api_router.include_router(icons.router)  # /api/icons/*

# 根路由组 (包含 /api 和 /go)
router = APIRouter()
router.include_router(api_router)
router.include_router(proxy.go_router)  # /go/*
