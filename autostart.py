# -*- coding: utf-8 -*-
"""砚白配置IP - 开机启动（用计划任务以管理员身份运行，避免重启后无权限）"""
import sys
import os
import subprocess
import winreg

APP_NAME = "砚白配置IP"
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def _pythonw_and_script():
    """返回 (pythonw 完整路径, main.py 完整路径)。"""
    if getattr(sys, "frozen", False):
        return sys.executable, None
    script_dir = os.path.dirname(os.path.abspath(__file__))
    main_py = os.path.join(script_dir, "main.py")
    # 若用 python 启动，pythonw 可能在同目录
    exe = sys.executable
    if os.path.basename(exe).lower() == "python.exe":
        pythonw = os.path.join(os.path.dirname(exe), "pythonw.exe")
        if os.path.isfile(pythonw):
            exe = pythonw
    return exe, main_py


def _task_exists():
    r = subprocess.run(
        ["schtasks", "/query", "/tn", APP_NAME],
        capture_output=True,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )
    return r.returncode == 0


def get_autostart():
    """开机启动是否开启：以计划任务为准（任务存在即视为开启）。"""
    if _task_exists():
        return True
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_READ)
        try:
            winreg.QueryValueEx(key, APP_NAME)
            return True
        except FileNotFoundError:
            return False
        finally:
            winreg.CloseKey(key)
    except Exception:
        return False


def set_autostart(enabled):
    """
    开启时：创建计划任务（登录时以最高权限运行），并移除注册表 Run，避免重复启动且无权限。
    关闭时：删除计划任务，并移除 Run。
    """
    # 先清理旧的 Run 项，避免和计划任务重复
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE)
        try:
            winreg.DeleteValue(key, APP_NAME)
        except FileNotFoundError:
            pass
        finally:
            winreg.CloseKey(key)
    except Exception:
        pass

    if not enabled:
        if _task_exists():
            subprocess.run(
                ["schtasks", "/delete", "/tn", APP_NAME, "/f"],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )
        return True

    exe, main_py = _pythonw_and_script()
    if getattr(sys, "frozen", False):
        tr = f'"{exe}"' if " " in exe else exe
    else:
        tr = f'"{exe}" "{main_py}"'
    r = subprocess.run(
        [
            "schtasks", "/create", "/tn", APP_NAME,
            "/tr", tr,
            "/sc", "onlogon",
            "/rl", "highest",
            "/f",
        ],
        capture_output=True,
        text=True,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )
    return r.returncode == 0
