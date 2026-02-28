# -*- coding: utf-8 -*-
"""
砚白配置IP - 系统托盘一键切换手动IP/自动DHCP，多模板管理，断网自动切DHCP并关代理。
需在 Windows 10 及以上以管理员身份运行（修改网络需管理员权限）。
"""
__version__ = "1.0.0"
APP_NAME = "砚白配置IP"
DEVELOPER = "砚白"

import tkinter as tk
from tkinter import messagebox
import threading
import sys
import os

# 将项目目录加入路径，便于打包后仍可导入
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
import network_manager
import proxy_manager
import monitor
import autostart
from template_editor import open_template_editor
from icon_gen import get_tray_icon
from network_status_window import open_network_status


def _is_admin():
    """当前进程是否以管理员身份运行（修改网络需此权限）。"""
    if sys.platform != "win32":
        return True
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def _on_network_failure(tray_app=None):
    """断网时：切 DHCP + 关闭代理；若传入 tray_app 则在主线程弹出提示（根据是否成功区分文案）。"""
    dhcp_ok, dhcp_err = False, ""
    iface = network_manager.get_connected_interface()
    if iface:
        dhcp_ok, dhcp_err = network_manager.set_dhcp(iface)
    proxy_manager.disable_proxy()
    if tray_app is not None:
        def show_notify():
            if dhcp_ok:
                messagebox.showinfo("砚白配置IP", "检测到网络异常，已自动切换为自动 DHCP 并关闭代理。")
            else:
                messagebox.showerror(
                    "砚白配置IP",
                    "检测到网络异常，但因权限不足无法自动切换为 DHCP。\n\n"
                    "请退出本程序后，右键「以管理员运行.bat」重新启动；\n"
                    "若已开启「开机启动」，请取消勾选后再重新勾选，以便登录时以管理员身份运行。"
                )
        tray_app._schedule(show_notify)


def _apply_template(template):
    iface = network_manager.get_connected_interface()
    if not iface:
        return False, "未找到已连接的以太网接口"
    return network_manager.set_static_ip(
        iface,
        (template.get("ip") or "").strip(),
        (template.get("mask") or "255.255.255.0").strip(),
        (template.get("gateway") or "").strip(),
        (template.get("dns1") or "").strip() or None,
        (template.get("dns2") or "").strip() or None,
    )


def _switch_dhcp():
    iface = network_manager.get_connected_interface()
    if not iface:
        return False, "未找到已连接的以太网接口"
    return network_manager.set_dhcp(iface)


class TrayApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.root.protocol("WM_DELETE_WINDOW", self.root.withdraw)
        self.root.title("砚白配置IP")
        self.tray_icon = None
        self.tray_thread = None

    def _schedule(self, fn):
        self.root.after(0, fn)

    def _apply_template_by_id(self, template_id):
        def do():
            templates = [t for t in config.get_templates() if (t.get("id") or "") == template_id]
            if not templates:
                messagebox.showerror("错误", "模板不存在")
                return
            ok, err = _apply_template(templates[0])
            if ok:
                messagebox.showinfo("成功", "已应用模板：%s" % templates[0].get("name", ""))
            else:
                messagebox.showerror("失败", err or "应用失败")
        self._schedule(do)

    def _apply_template_by_data(self, template):
        """托盘点击时在后台线程执行 netsh，避免阻塞主线程导致弹窗很久才出"""
        def run_then_notify():
            ok, err = _apply_template(template)
            def show():
                if ok:
                    monitor.set_monitoring_paused(False)
                    messagebox.showinfo("成功", "已应用模板：%s" % template.get("name", ""))
                else:
                    messagebox.showerror("失败", err or "应用失败")
            self._schedule(show)
        threading.Thread(target=run_then_notify, daemon=True).start()

    def _do_switch_dhcp(self):
        def run_then_notify():
            ok, err = _switch_dhcp()
            def show():
                if ok:
                    monitor.set_monitoring_paused(True)
                    messagebox.showinfo("成功", "已切换到自动 DHCP")
                else:
                    messagebox.showerror("失败", err or "切换失败")
            self._schedule(show)
        threading.Thread(target=run_then_notify, daemon=True).start()

    def _do_open_template_editor(self):
        def do():
            open_template_editor(self.root, on_close=lambda: self._refresh_tray_menu())
        self._schedule(do)

    def _do_open_network_status(self):
        def do():
            open_network_status(self.root)
        self._schedule(do)

    def _toggle_autostart(self, icon, item):
        def do():
            cur = autostart.get_autostart()
            new = not cur
            if autostart.set_autostart(new):
                config.set_autostart(new)
                self._refresh_tray_menu()
            else:
                messagebox.showerror("错误", "无法修改开机启动")
        self._schedule(do)

    def _quit(self, icon, item):
        def do():
            if self.tray_icon:
                try:
                    self.tray_icon.stop()
                except Exception:
                    pass
            self.root.quit()
            self.root.destroy()
            os._exit(0)
        self._schedule(do)

    def _build_menu(self):
        import pystray
        templates = config.get_templates()
        items = []
        items.append(pystray.MenuItem("切换到自动 DHCP", self._on_switch_dhcp_clicked))
        items.append(pystray.Menu.SEPARATOR)
        for t in templates:
            # 用模板数据副本绑定到菜单，托盘点击时不再查 config，避免「模板不存在」
            tmpl = dict(t)
            name = tmpl.get("name", "未命名")[:20]
            items.append(pystray.MenuItem(name, lambda _, tpl=tmpl: self._apply_template_by_data(tpl)))
        if templates:
            items.append(pystray.Menu.SEPARATOR)
        items.append(pystray.MenuItem("管理模板", self._on_manage_clicked, default=True))
        items.append(pystray.MenuItem("网络状态详情", self._on_network_status_clicked))
        items.append(pystray.MenuItem("开机启动", self._toggle_autostart, checked=lambda _: autostart.get_autostart()))
        items.append(pystray.Menu.SEPARATOR)
        items.append(pystray.MenuItem("关于", self._on_about_clicked))
        items.append(pystray.MenuItem("退出", self._quit))
        return pystray.Menu(*items)

    def _on_switch_dhcp_clicked(self, icon, item):
        self._do_switch_dhcp()

    def _on_manage_clicked(self, icon, item):
        self._do_open_template_editor()

    def _on_network_status_clicked(self, icon, item):
        self._do_open_network_status()

    def _on_about_clicked(self, icon, item):
        def do():
            messagebox.showinfo(
                "关于",
                "%s\n\n版本：%s\n开发者：%s" % (APP_NAME, __version__, DEVELOPER),
            )
        self._schedule(do)

    def _refresh_tray_menu(self):
        """模板变更后刷新托盘菜单（需在主线程或托盘线程内调用）。"""
        if self.tray_icon:
            try:
                self.tray_icon.menu = self._build_menu()
            except Exception:
                pass

    def _run_tray(self):
        import pystray
        image = get_tray_icon()
        # pystray 需传入 Menu 实例，不能传 callable
        self.tray_icon = pystray.Icon("砚白配置IP", image, "砚白配置IP", self._build_menu())
        self.tray_icon.run()

    def run(self):
        monitor.set_failure_callback(lambda: _on_network_failure(self))
        monitor.start_monitor()
        self.tray_thread = threading.Thread(target=self._run_tray, daemon=True)
        self.tray_thread.start()
        self.root.mainloop()


def _sync_autostart():
    """以 config 为准，同步注册表开机启动项。"""
    want = config.get_autostart()
    if autostart.get_autostart() != want:
        autostart.set_autostart(want)


def main():
    _sync_autostart()
    app = TrayApp()
    if not _is_admin():
        def _warn_no_admin():
            messagebox.showwarning(
                "砚白配置IP",
                "当前未以管理员身份运行，无法修改网络配置（切换 DHCP/应用模板会失败）。\n\n"
                "请退出后右键「以管理员运行.bat」启动；\n"
                "或开启托盘菜单中的「开机启动」并重新勾选一次，以便每次登录时以管理员身份运行。"
            )
        app.root.after(800, _warn_no_admin)
    app.run()


if __name__ == "__main__":
    main()
