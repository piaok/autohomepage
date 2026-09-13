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

    def get_all(self, include_hidden: bool = False, include_deleted: bool = False) -> List[Service]:
        """获取所有服务（默认排除回收站中的）"""
        services = list(self.services.values())
        if not include_deleted:
            services = [s for s in services if not s.is_deleted]
        if not include_hidden:
            services = [s for s in services if s.is_visible]
        return sorted(services, key=lambda s: (s.order, s.name))

    def get_deleted(self) -> List[Service]:
        """获取回收站中的服务（按删除时间倒序）"""
        services = [s for s in self.services.values() if s.is_deleted]
        return sorted(services, key=lambda s: s.deleted_at or datetime.min, reverse=True)

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
        """删除服务（软删除，进入回收站）"""
        service = self.services.get(service_id)
        if service:
            service.is_deleted = True
            service.deleted_at = datetime.now()
            self._save_data()
            logger.info(f"删除服务(回收站): {service.name}")
            return True
        return False

    def restore(self, service_id: str) -> bool:
        """从回收站恢复服务"""
        service = self.services.get(service_id)
        if service and service.is_deleted:
            service.is_deleted = False
            service.deleted_at = None
            self._save_data()
            logger.info(f"恢复服务: {service.name}")
            return True
        return False

    def purge(self, service_id: str) -> bool:
        """永久删除服务（从回收站彻底清除）"""
        if service_id in self.services:
            service = self.services.pop(service_id)
            self._save_data()
            logger.info(f"永久删除服务: {service.name}")
            return True
        return False

    def empty_recycle_bin(self) -> int:
        """清空回收站，返回彻底删除的数量"""
        deleted_ids = [sid for sid, s in self.services.items() if s.is_deleted]
        for sid in deleted_ids:
            del self.services[sid]
        self._save_data()
        logger.info(f"清空回收站: {len(deleted_ids)} 个服务")
        return len(deleted_ids)

    def _lan_key(self, url: Optional[str]) -> Optional[str]:
        """提取内网地址的归一化键（协议忽略，取 host:port）

        同默认局域网端口相同即视为同一个服务
        """
        if not url:
            return None
        host = url.split("//", 1)[-1]
        host = host.split("/", 1)[0].split("?", 1)[0]
        if not host:
            return None
        host = host.strip().lower()
        # 补默认端口（协议从原url推断，缺省80/443）
        if ":" not in host:
            proto = url.split("//", 1)[0]
            port = "443" if proto == "https:" else "80"
            host = f"{host}:{port}"
        return host

    def update_status(self, service_id: str, status: ServiceStatus):
        """更新服务状态"""
        if service_id in self.services:
            self.services[service_id].status = status
            self.services[service_id].last_check = datetime.now()
            # 不每次都保存，可以批量保存优化

    def create_or_update_from_discovery(self, source: ServiceSource,
                                        external_id: str, **kwargs) -> Optional[Service]:
        """
        根据自动发现结果创建或更新服务

        匹配优先级:
        1. source + external_id (lucky_id / container_name)
        2. 同内网键(src lans URL的 host:port) —— 同默认局域网端口相同即同一个服务，合并而不新建
        3. 目标已在回收站中 —— 不复活，跳过
        """
        existing = None
        matched_deleted_id = None

        # 1. 严格匹配
        for service in self.services.values():
            if service.source == source:
                if source == ServiceSource.LUCKY and service.lucky_id == external_id:
                    if service.is_deleted:
                        matched_deleted_id = service.id
                        continue
                    existing = service
                    break
                elif source == ServiceSource.DOCKER and service.container_name == external_id:
                    if service.is_deleted:
                        matched_deleted_id = service.id
                        continue
                    existing = service
                    break

        # 2. 按内网键合并 (仅lucky来源，避免同一内网端口多个服务卡片)
        if existing is None and matched_deleted_id is None and not self._is_deleted_key(source, external_id):
            new_lan_key = self._lan_key(kwargs.get("lan_url"))
            if new_lan_key:
                for service in self.services.values():
                    if service.is_deleted or service.source == source:
                        # source相同的已在严格匹配中找过；跳过被单独删除的记录由下面处理
                        continue
                    if self._lan_key(service.lan_url) == new_lan_key:
                        existing = service
                        break
            else:
                # 无内网地址时按公网域名合并
                wan = kwargs.get("wan_url")
                if wan:
                    yield_wan_key = wan.split("//", 1)[-1].split("/", 1)[0].strip().lower()
                    for service in self.services.values():
                        if service.is_deleted:
                            continue
                        swan = service.wan_url
                        if swan and swan.split("//", 1)[-1].split("/", 1)[0].strip().lower() == yield_wan_key:
                            existing = service
                            break

        # 服务被用户手动删除过 → 不自动复活
        if existing is None and matched_deleted_id is not None:
            logger.info(f"服务在回收站中，跳过自动创建: {external_id}")
            return None

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

    def _is_deleted_key(self, source: ServiceSource, external_id: str) -> bool:
        """检查该外部ID对应的服务是否在回收站中(不复活)"""
        if source == ServiceSource.LUCKY:
            return any(
                s.is_deleted and s.lucky_id == external_id
                for s in self.services.values()
            )
        if source == ServiceSource.DOCKER:
            return any(
                s.is_deleted and s.container_name == external_id
                for s in self.services.values()
            )
        return False

    def dedupe(self) -> int:
        """一键去重：同内网键(host:port)的服务合并为一个，多余项放入回收站，返回处理数量"""
        groups: Dict[Optional[str], List[Service]] = {}
        for service in self.services.values():
            if service.is_deleted:
                continue
            key = self._lan_key(service.lan_url)
            if not key:
                continue
            groups.setdefault(key, []).append(service)

        removed = 0
        for key, lst in groups.items():
            if len(lst) <= 1:
                continue
            # 保留主项: 手动来源优先(用户自定义) > order最小 > id字典序稳定
            keep = max(
                lst,
                key=lambda s: (s.source == ServiceSource.MANUAL, -s.order, s.id),
            )
            for extra in lst:
                if extra is keep or extra.id == keep.id:
                    continue
                # 补充主项缺失的信息
                if keep.category and not extra.category:
                    keep.category = extra.category
                if extra.description and not keep.description:
                    keep.description = extra.description
                extra.is_deleted = True
                extra.deleted_at = datetime.now()
                removed += 1
        self._save_data()
        logger.info(f"一键去重: {removed} 个重复项移入回收站")
        return removed

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
