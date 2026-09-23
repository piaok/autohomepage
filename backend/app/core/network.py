"""NAS Homepage - 网络工具"""
import logging
import ipaddress
from typing import List

logger = logging.getLogger(__name__)


# 默认的内网地址范围
DEFAULT_PRIVATE_RANGES = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),  # 回环地址
    ipaddress.ip_network("::1/128"),       # IPv6回环
    ipaddress.ip_network("fc00::/7"),      # IPv6私有地址
]


def get_client_ip(request_headers: dict, remote_addr: str,
                  trusted_proxies: List[str] = None,
                  trust_forward_headers: bool = False) -> str:
    """
    获取真实的客户端IP地址

    支持以下头部:
    - X-Forwarded-For (最常用)
    - X-Real-IP
    - CF-Connecting-IP (Cloudflare)

    安全策略:
    - 直连IP(remote_addr)是内网/回环地址时(前面是本机或局域网反代，
      如Docker网关、Caddy、Nginx、Lucky)，信任转发头中的IP；
    - 也可通过 trusted_proxies 显式指定可信代理(支持CIDR)；
    - 外网直连(对端为公网IP)时不解析转发头，
      防止外部伪造 X-Forwarded-For 冒充内网；
    - trust_forward_headers=True 时无条件信任转发头
      (仅适用于完全可信的内网环境，不推荐)。

    Args:
        request_headers: 请求头字典
        remote_addr: 直接连接的远程地址
        trusted_proxies: 可信代理IP列表
        trust_forward_headers: 是否无条件信任转发头

    Returns:
        客户端真实IP地址
    """
    trusted_proxies = trusted_proxies or []
    remote = (remote_addr or "").split("%")[0]  # 去掉IPv6 scope id

    forward_trusted = (
        trust_forward_headers
        or remote in trusted_proxies
        or _ip_in_any(remote, trusted_proxies)
        # 默认信任来自内网/回环的直连对端(反代部署开箱即用)；
        # 这类对端本身就处于受信网络，伪造转发头无法由外网到达
        or (remote not in ("", "unknown") and is_private_ip(remote))
    )

    if forward_trusted:
        # 按优先级检查各种头部
        x_forwarded_for = request_headers.get("x-forwarded-for")
        if x_forwarded_for:
            # X-Forwarded-For 可能包含多个IP，格式: client, proxy1, proxy2
            # 从左边找到第一个非代理IP
            ips = [ip.strip() for ip in x_forwarded_for.split(",")]
            for ip in ips:
                if ip and ip not in trusted_proxies and not _ip_in_any(ip, trusted_proxies):
                    return ip
            # 如果全是代理IP，返回第一个
            return ips[0] if ips else remote_addr

        x_real_ip = request_headers.get("x-real-ip")
        if x_real_ip and x_real_ip not in trusted_proxies:
            return x_real_ip

        cf_connecting_ip = request_headers.get("cf-connecting-ip")
        if cf_connecting_ip:
            return cf_connecting_ip

    return remote_addr


def _ip_in_any(ip_str: str, networks: List[str]) -> bool:
    """检查IP是否落在任一网段/CIDR中（支持CIDR格式的trusted_proxies）"""
    if not ip_str:
        return False
    for net_str in networks:
        try:
            if ipaddress.ip_address(ip_str) in ipaddress.ip_network(net_str, strict=False):
                return True
        except (ValueError, TypeError):
            continue
    return False


def is_private_ip(ip_str: str, custom_ranges: List[str] = None) -> bool:
    """
    判断IP是否是内网地址

    Args:
        ip_str: IP地址字符串
        custom_ranges: 自定义内网范围 (CIDR格式)

    Returns:
        是否是内网地址
    """
    try:
        ip = ipaddress.ip_address(ip_str)

        # 检查默认私有范围
        for network in DEFAULT_PRIVATE_RANGES:
            if ip in network:
                return True

        # 检查自定义范围
        if custom_ranges:
            for range_str in custom_ranges:
                try:
                    network = ipaddress.ip_network(range_str, strict=False)
                    if ip in network:
                        return True
                except ValueError:
                    logger.warning(f"无效的网络范围: {range_str}")

        return False
    except ValueError:
        logger.warning(f"无效的IP地址: {ip_str}")
        return False


def get_network_type(ip_str: str, custom_ranges: List[str] = None) -> str:
    """
    获取网络类型

    Returns:
        "lan" - 内网
        "wan" - 外网
        "unknown" - 无法判断
    """
    if not ip_str or ip_str == "unknown":
        return "unknown"

    return "lan" if is_private_ip(ip_str, custom_ranges) else "wan"


def get_best_url(lan_url: str, wan_url: str, client_ip: str, custom_ranges: List[str] = None) -> str:
    """
    根据客户端IP选择最优URL

    策略:
    - 内网访问优先使用LAN URL
    - 外网访问优先使用WAN URL
    - 如果首选URL不存在，返回备选URL

    Args:
        lan_url: 内网地址
        wan_url: 外网地址
        client_ip: 客户端IP
        custom_ranges: 自定义内网范围

    Returns:
        最优URL
    """
    network_type = get_network_type(client_ip, custom_ranges)

    if network_type == "lan":
        return lan_url or wan_url
    else:
        return wan_url or lan_url
