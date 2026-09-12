"""NAS Homepage - 服务管理器"""
import json
import logging
import os
from datetime import datetime
from typing import List, Optional, Dict
import uuid

from app.config import settings
from app.models import Service, ServiceSource, ServiceStatus, IconSource

logger = logging.getLogger(__name__)


class ServiceManager:
    """服务管理器 - 负责服务的CRUD和数据持久化"""

    def __init__(self):
        self.data_file = os.path.join(settings.data_dir, "services.json")
        self.services: Dict[str, Service] = {}
        self._ensure_data_dir()
        self._load_data()

    def _ensure_data_dir(self):
        """确保数据目录存在"""
        os.makedirs(settings.data_dir, exist_ok=True)

    def _load_data(self):
        """从文件加载服务数据"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item in data:
                        service = Service(**item)
                        self.services[service.id] = service
                logger.info(f"加载了 {len(self.services)} 个服务")
            except Exception as e:
                # 解析失败时备份损坏文件，避免之后的新数据覆盖、彻底无法恢复
                backup_file = self.data_file + ".corrupt"
                try:
                    os.replace(self.data_file, backup_file)
                    logger.error(f"加载服务数据失败: {e}，原文件已备份到 {backup_file}")
                except OSError:
                    logger.error(f"加载服务数据失败: {e}")
                self.services = {}
        else:
            logger.info("服务数据文件不存在，创建新的")
            self.services = {}

    def _save_data(self):
        """保存服务数据到文件（原子写入，防止写一半崩溃丢数据）"""
        try:
            data = [service.model_dump() for service in self.services.values()]
            tmp_file = self.data_file + ".tmp"
            with open(tmp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
                f.flush()
                os.fsync(f.fileno())
            # os.replace 是原子操作：要么完整新文件，要么保留旧文件
            os.replace(tmp_file, self.data_file)
        except Exception as e:
            logger.error(f"保存服务数据失败: {e}")

    def get_all(self, include_hidden: bool = False) -> List[Service]:
        """获取所有服务"""
        services = list(self.services.values())
        if not include_hidden:
            services = [s for s in services if s.is_visible]
        return sorted(services, key=lambda s: (s.order, s.name))

    def get(self, service_id: str) -> Optional[Service]:
        """获取单个服务"""
        return self.services.get(service_id)

    def create(self, name: str, lan_url: Optional[str] = None,
               wan_url: Optional[str] = None, **kwargs) -> Service:
        """创建新服务"""
        service_id = str(uuid.uuid4())[:8]

        service = Service(
            id=service_id,
            name=name,
            lan_url=lan_url,
            wan_url=wan_url,
            source=ServiceSource.MANUAL,
            **kwargs
        )

        self.services[service_id] = service
        self._save_data()
        logger.info(f"创建服务: {name} ({service_id})")
        return service

    def update(self, service_id: str, **kwargs) -> Optional[Service]:
        """更新服务"""
        service = self.services.get(service_id)
        if not service:
            return None

        # 更新字段
        for key, value in kwargs.items():
            if hasattr(service, key):
                setattr(service, key, value)

        self._save_data()
        logger.info(f"更新服务: {service.name}")
        return service

    def delete(self, service_id: str) -> bool:
        """删除服务"""
        if service_id in self.services:
            service = self.services.pop(service_id)
            self._save_data()
            logger.info(f"删除服务: {service.name}")
            return True
        return False

    def update_status(self, service_id: str, status: ServiceStatus):
        """更新服务状态"""
        if service_id in self.services:
            self.services[service_id].status = status
            self.services[service_id].last_check = datetime.now()
            # 不每次都保存，可以批量保存优化

    def create_or_update_from_discovery(self, source: ServiceSource,
                                        external_id: str, **kwargs) -> Service:
        """
        根据自动发现结果创建或更新服务
        根据source和external_id判断是否是同一个服务
        """
        # 查找已存在的服务
        existing = None
        for service in self.services.values():
            if service.source == source:
                if source == ServiceSource.LUCKY and service.lucky_id == external_id:
                    existing = service
                    break
                elif source == ServiceSource.DOCKER and service.container_name == external_id:
                    existing = service
                    break

        if existing:
            # 更新现有服务 (保留用户自定义的字段)
            update_fields = ["lan_url", "wan_url", "status"]
            for field in update_fields:
                if field in kwargs:
                    setattr(existing, field, kwargs[field])

            # 如果用户没有自定义图标，更新图标
            if existing.icon_source in [IconSource.DEFAULT, IconSource.AUTO_LUCKY, IconSource.AUTO_DOCKER]:
                if "icon_url" in kwargs:
                    existing.icon_url = kwargs["icon_url"]
                    existing.icon_source = IconSource.AUTO_LUCKY if source == ServiceSource.LUCKY else IconSource.AUTO_DOCKER

            self._save_data()
            logger.info(f"更新发现的服务: {existing.name}")
            return existing
        else:
            # 创建新服务
            service_id = str(uuid.uuid4())[:8]
            service = Service(
                id=service_id,
                source=source,
                **kwargs
            )

            if source == ServiceSource.LUCKY:
                service.lucky_id = external_id
                service.icon_source = IconSource.AUTO_LUCKY
            elif source == ServiceSource.DOCKER:
                service.container_name = external_id
                service.icon_source = IconSource.AUTO_DOCKER

            self.services[service_id] = service
            self._save_data()
            logger.info(f"创建发现的服务: {service.name}")
            return service

    def get_by_container(self, container_name: str) -> Optional[Service]:
        """根据容器名查找服务"""
        for service in self.services.values():
            if service.container_name == container_name:
                return service
        return None

    def save(self):
        """公开的持久化方法（供其他模块调用，避免直接访问 _save_data）"""
        self._save_data()


# 全局实例
service_manager = ServiceManager()
