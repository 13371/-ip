# -*- coding: utf-8 -*-
"""砚白配置IP - 网络监测（TCP 探测，比 ping 更可靠；带防抖与冷却）"""
import threading
import time
import socket
import sys

# 由 main 注入回调，避免循环依赖
_on_failure = None

# 探测间隔（秒）
CHECK_INTERVAL = 30
# 连续失败此次数后触发自动回退 DHCP
FAIL_COUNT_TO_FALLBACK = 5
# 回退后的冷却期（秒），期内不再触发，避免网络抖动反复切换
COOLDOWN_SECONDS = 300

# TCP 探测目标：任意一个连通即视为在线（禁 ping 网络更可靠）
_PROBE_TARGETS = [
    ("1.1.1.1", 443),
    ("8.8.8.8", 53),
]
_PROBE_TIMEOUT = 5

# 状态供「网络状态详情」读取（由监测线程更新）
_state = {
    "last_check_time": None,
    "last_ok": None,
    "consecutive_fail_count": 0,
    "trigger_count": 0,
    "paused": False,
    "cooldown_until": None,  # 冷却期结束时间戳，None 表示未在冷却
}
_state_lock = threading.Lock()

# 自动 DHCP 模式下不检测网络（由 main 在切换/应用模板时设置）
_monitoring_paused = False
_last_fallback_time = 0.0


def set_failure_callback(callback):
    global _on_failure
    _on_failure = callback


def set_monitoring_paused(paused):
    """自动 DHCP 时为 True，不执行探测；应用静态模板后设为 False。"""
    global _monitoring_paused
    _monitoring_paused = paused
    with _state_lock:
        _state["paused"] = paused


def get_status():
    """返回当前监测状态（用于网络状态详情窗口）。"""
    with _state_lock:
        return dict(_state)


def _tcp_probe():
    """TCP 探测：尝试连接 1.1.1.1:443 或 8.8.8.8:53，任意一个成功即视为在线。"""
    for host, port in _PROBE_TARGETS:
        try:
            s = socket.create_connection((host, port), timeout=_PROBE_TIMEOUT)
            s.close()
            return True
        except (socket.timeout, socket.error, OSError):
            continue
    return False


def _run_monitor_loop():
    """后台循环：每 checkInterval 秒 TCP 探测一次，连续失败 failCountToFallback 次触发回退，回退后进入冷却期。"""
    global _on_failure, _monitoring_paused, _last_fallback_time
    fail_count = 0
    while True:
        time.sleep(CHECK_INTERVAL)
        if _on_failure is None:
            continue
        if _monitoring_paused:
            continue
        now = time.time()
        if now < _last_fallback_time + COOLDOWN_SECONDS:
            with _state_lock:
                _state["cooldown_until"] = _last_fallback_time + COOLDOWN_SECONDS
            continue
        with _state_lock:
            _state["cooldown_until"] = None
        ok = _tcp_probe()
        with _state_lock:
            _state["last_check_time"] = now
            _state["last_ok"] = ok
            if ok:
                fail_count = 0
            _state["consecutive_fail_count"] = fail_count
        if ok:
            fail_count = 0
            continue
        fail_count += 1
        if fail_count >= FAIL_COUNT_TO_FALLBACK:
            fail_count = 0
            _last_fallback_time = now
            with _state_lock:
                _state["trigger_count"] = _state.get("trigger_count", 0) + 1
                _state["cooldown_until"] = now + COOLDOWN_SECONDS
            try:
                _on_failure()
            except Exception:
                pass


def start_monitor():
    t = threading.Thread(target=_run_monitor_loop, daemon=True)
    t.start()
