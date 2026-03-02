# -*- coding: utf-8 -*-
"""砚白配置IP - 网络状态详情窗口"""
import tkinter as tk
from tkinter import ttk
import time

import config
import monitor
import network_manager


def _format_time(ts):
    if ts is None:
        return "—"
    try:
        return time.strftime("%H:%M:%S", time.localtime(ts))
    except Exception:
        return "—"


def open_network_status(parent):
    """打开网络状态详情窗口（可重复调用，每次新建一个窗口）。"""
    win = tk.Toplevel(parent)
    win.title("砚白配置IP - 网络状态详情")
    win.geometry("380x320")
    win.minsize(320, 260)

    f = ttk.Frame(win, padding=12)
    f.pack(fill=tk.BOTH, expand=True)

    # 标题
    ttk.Label(f, text="网络监测状态", font=("", 11, "bold")).pack(anchor=tk.W)

    # 动态更新的标签（用 StringVar 便于刷新）
    vars_map = {}

    def add_row(label, key, fmt="%s"):
        var = tk.StringVar(value="—")
        vars_map[key] = (var, fmt)
        row_f = ttk.Frame(f)
        row_f.pack(fill=tk.X, pady=2)
        ttk.Label(row_f, text=label + "：", width=18, anchor=tk.W).pack(side=tk.LEFT)
        ttk.Label(row_f, textvariable=var, anchor=tk.W).pack(side=tk.LEFT, fill=tk.X, expand=True)

    add_row("当前网络状态", "status")
    add_row("连续失败次数", "consecutive", "%s")
    add_row("触发阈值", "threshold", "%s 次")
    add_row("检测间隔", "interval", "%s 秒")
    add_row("冷却期", "cooldown", "%s")
    add_row("已触发自动切 DHCP 次数", "trigger_count", "%s 次")
    add_row("上次检测时间", "last_check_time", "%s")

    # 已选择的网卡（用户手动选择的，不会自动更换）
    preferred = config.get_preferred_interface()
    preferred_var = tk.StringVar(value=preferred if preferred else "自动（第一个已连接）")
    row_f = ttk.Frame(f)
    row_f.pack(fill=tk.X, pady=2)
    ttk.Label(row_f, text="已选网卡：", width=18, anchor=tk.W).pack(side=tk.LEFT)
    ttk.Label(row_f, textvariable=preferred_var, anchor=tk.W).pack(side=tk.LEFT, fill=tk.X, expand=True)

    # 当前实际使用的网卡（与已选一致，除非未选时取第一个已连接）
    iface = network_manager.get_connected_interface(config.get_preferred_interface())
    iface_var = tk.StringVar(value=iface or "未检测到")
    row_f2 = ttk.Frame(f)
    row_f2.pack(fill=tk.X, pady=2)
    ttk.Label(row_f2, text="当前使用网卡：", width=18, anchor=tk.W).pack(side=tk.LEFT)
    ttk.Label(row_f2, textvariable=iface_var, anchor=tk.W).pack(side=tk.LEFT, fill=tk.X, expand=True)

    def refresh():
        st = monitor.get_status()
        if st.get("paused"):
            vars_map["status"][0].set("DHCP 模式，未检测")
        else:
            last_ok = st.get("last_ok")
            if last_ok is True:
                vars_map["status"][0].set("正常")
            elif last_ok is False:
                vars_map["status"][0].set("异常")
            else:
                vars_map["status"][0].set("尚未检测")
        vars_map["consecutive"][0].set(str(st.get("consecutive_fail_count", 0)))
        vars_map["threshold"][0].set(str(monitor.FAIL_COUNT_TO_FALLBACK))
        vars_map["interval"][0].set(str(monitor.CHECK_INTERVAL))
        cooldown_until = st.get("cooldown_until")
        if cooldown_until and cooldown_until > time.time():
            left = int(cooldown_until - time.time())
            vars_map["cooldown"][0].set("冷却中，剩余 %d 秒" % left)
        else:
            vars_map["cooldown"][0].set("—")
        vars_map["trigger_count"][0].set(str(st.get("trigger_count", 0)))
        lt = st.get("last_check_time")
        vars_map["last_check_time"][0].set(_format_time(lt))
        # 刷新已选网卡与当前使用网卡
        pref = config.get_preferred_interface()
        preferred_var.set(pref if pref else "自动（第一个已连接）")
        cur = network_manager.get_connected_interface(config.get_preferred_interface())
        iface_var.set(cur or "未检测到")

    refresh()

    btn_f = ttk.Frame(f)
    btn_f.pack(fill=tk.X, pady=(12, 0))
    ttk.Button(btn_f, text="刷新", command=refresh).pack(side=tk.LEFT, padx=2)
    ttk.Button(btn_f, text="关闭", command=win.destroy).pack(side=tk.LEFT, padx=2)

    # 打开时自动刷新一次，并每 3 秒刷新
    def auto_refresh():
        if win.winfo_exists():
            refresh()
            win.after(3000, auto_refresh)
    win.after(500, auto_refresh)
