# -*- coding: utf-8 -*-
"""砚白配置IP - 网络配置（netsh）"""
import subprocess
import sys
import os

# netsh 超时（秒），避免卡死导致弹窗迟迟不出现
NETSH_TIMEOUT = 15


def _netsh_exe():
    """使用 System32 下 netsh 完整路径，避免其他电脑 PATH 异常导致找不到命令"""
    if sys.platform != "win32":
        return "netsh"
    root = os.environ.get("SystemRoot", "C:\\Windows")
    exe = os.path.join(root, "System32", "netsh.exe")
    return exe if os.path.isfile(exe) else "netsh"


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
    cmd = [_netsh_exe()] + args
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
            err = (r.stderr or r.stdout or "").strip()
            if not err or "access" in err.lower() or "denied" in err.lower() or "拒绝" in err or "权限" in err:
                err = "需要管理员权限，请右键本程序选择「以管理员身份运行」。" if not err else err
            return False, err
        return True, (r.stdout or "").strip()
    except subprocess.TimeoutExpired:
        return False, "执行超时（请检查是否以管理员运行）"
    except Exception as e:
        return False, str(e)


def get_all_interfaces():
    """
    获取所有网卡列表及连接状态。返回 [{"name": "以太网", "connected": True}, ...]。
    用于「选择网卡」界面，以及优先使用用户指定的网卡。
    """
    ok, out = _run_netsh(["interface", "show", "interface"], check=False)
    if not ok:
        return []
    result = []
    skip_headers = ("admin", "state", "类型", "type", "interface", "接口", "name", "名称", "---")
    for line in out.splitlines():
        parts = line.split()
        if len(parts) < 4:
            continue
        name = " ".join(parts[3:]).strip()
        if not name or name.lower() in skip_headers:
            continue
        connected = "已连接" in line or (len(parts) > 1 and "connected" in parts[1].lower())
        result.append({"name": name, "connected": connected})
    return result


def get_connected_interface(preferred=None):
    """
    获取要操作的网卡名称。
    - 若用户已手动选择网卡（preferred）且该网卡存在于系统中，则始终返回该网卡，不自动更换。
    - 若未选择或选择的网卡不存在，则返回第一个已连接的网卡。
    """
    interfaces = get_all_interfaces()
    all_names = [x["name"] for x in interfaces]
    connected = [x["name"] for x in interfaces if x["connected"]]
    # 用户已手动选择：只要该网卡存在就始终使用，不因未连接而自动换其他网卡
    if preferred and preferred in all_names:
        return preferred
    return connected[0] if connected else None


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
