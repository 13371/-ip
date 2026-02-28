# -*- coding: utf-8 -*-
"""砚白配置IP - 网络配置（netsh）"""
import subprocess
import sys


# netsh 超时（秒），避免卡死导致弹窗迟迟不出现
NETSH_TIMEOUT = 15


def _is_valid_ipv4(s):
    """仅允许标准 IPv4 格式，防止异常输入传入 netsh。"""
    if s is None or (isinstance(s, str) and not s.strip()):
        return False
    s = str(s).strip()
    parts = s.split(".")
    if len(parts) != 4:
        return False
    for p in parts:
        if not p.isdigit():
            return False
        if int(p) > 255:
            return False
    return True


def _run_netsh(args, check=True):
    cmd = ["netsh"] + args
    try:
        r = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=NETSH_TIMEOUT,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        if check and r.returncode != 0:
            return False, (r.stderr or r.stdout or "").strip()
        return True, (r.stdout or "").strip()
    except subprocess.TimeoutExpired:
        return False, "执行超时（请检查是否以管理员运行）"
    except Exception as e:
        return False, str(e)


def get_connected_interface():
    """
    获取当前已连接的以太网接口名称。
    解析 netsh interface show interface 输出，支持中文（已连接）与英文（Connected），
    接口名可能含空格（如「网络 3」），取第 4 列起为名称。
    """
    ok, out = _run_netsh(["interface", "show", "interface"], check=False)
    if not ok:
        return None
    for line in out.splitlines():
        line_lower = line.strip().lower()
        if "已连接" in line or "connected" in line_lower:
            parts = line.split()
            if len(parts) >= 4:
                # 列顺序一般为：管理状态 连接状态 类型 接口名称（名称可能含空格）
                name = " ".join(parts[3:]).strip()
                skip = ("admin", "state", "类型", "type", "interface", "接口")
                if name and name.lower() not in skip:
                    return name
            elif len(parts) >= 1:
                name = parts[0].strip()
                if name and name.lower() not in ("admin", "state", "类型", "type", "interface", "已连接", "connected"):
                    return name
    return None


def set_static_ip(interface_name, ip, mask, gateway, dns1=None, dns2=None):
    """设置静态 IP、子网掩码、网关和可选 DNS。"""
    if not interface_name:
        return False, "未找到已连接的以太网接口"
    ip, mask, gateway = (str(x or "").strip() for x in (ip, mask, gateway))
    if not _is_valid_ipv4(ip):
        return False, "IP 地址格式无效"
    if not _is_valid_ipv4(mask):
        return False, "子网掩码格式无效"
    if not _is_valid_ipv4(gateway):
        return False, "网关地址格式无效"
    if dns1 is not None and dns1:
        dns1 = str(dns1).strip()
        if not _is_valid_ipv4(dns1):
            return False, "首选 DNS 格式无效"
    if dns2 is not None and dns2:
        dns2 = str(dns2).strip()
        if not _is_valid_ipv4(dns2):
            return False, "备用 DNS 格式无效"
    # 设置地址
    addr_args = [
        "interface", "ip", "set", "address",
        f"name={interface_name}",
        "source=static",
        f"addr={ip}",
        f"mask={mask}",
        f"gateway={gateway}",
        "gwmetric=0",
    ]
    ok, err = _run_netsh(addr_args)
    if not ok:
        return False, f"设置 IP 失败: {err}"
    # DNS
    if dns1:
        ok2, err2 = _run_netsh([
            "interface", "ip", "set", "dns",
            f"name={interface_name}",
            "source=static",
            f"addr={dns1}",
            "register=PRIMARY",
        ])
        if not ok2:
            return False, f"设置 DNS 失败: {err2}"
    if dns2:
        _run_netsh([
            "interface", "ip", "add", "dns",
            f"name={interface_name}",
            f"addr={dns2}",
            "index=2",
        ], check=False)
    return True, ""


def set_dhcp(interface_name):
    """将指定接口改为 DHCP（IP 和 DNS 均为自动）。"""
    if not interface_name:
        return False, "未找到已连接的以太网接口"
    ok1, err1 = _run_netsh([
        "interface", "ip", "set", "address",
        f"name={interface_name}",
        "source=dhcp",
    ])
    if not ok1:
        return False, f"设置 DHCP 失败: {err1}"
    ok2, err2 = _run_netsh([
        "interface", "ip", "set", "dns",
        f"name={interface_name}",
        "source=dhcp",
    ])
    if not ok2:
        return False, f"设置 DNS 为 DHCP 失败: {err2}"
    return True, ""
