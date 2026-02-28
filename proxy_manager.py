# -*- coding: utf-8 -*-
"""砚白配置IP - 关闭系统代理"""
import winreg
import ctypes
import ctypes.wintypes

# 刷新代理设置使立即生效
INTERNET_OPTION_SETTINGS_CHANGED = 39
INTERNET_OPTION_REFRESH = 37
KEY = winreg.HKEY_CURRENT_USER
SUBKEY = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"


def disable_proxy():
    """关闭当前用户的代理：ProxyEnable=0，清空 AutoConfigURL。"""
    try:
        key = winreg.OpenKey(KEY, SUBKEY, 0, winreg.KEY_SET_VALUE)
        try:
            winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 0)
            try:
                winreg.SetValueEx(key, "AutoConfigURL", 0, winreg.REG_SZ, "")
            except FileNotFoundError:
                pass
        finally:
            winreg.CloseKey(key)
        _refresh_ie_proxy()
        return True, ""
    except Exception as e:
        return False, str(e)


def _refresh_ie_proxy():
    """通知系统代理设置已更改"""
    try:
        wininet = ctypes.windll.wininet
        wininet.InternetSetOptionW(0, INTERNET_OPTION_SETTINGS_CHANGED, 0, 0)
        wininet.InternetSetOptionW(0, INTERNET_OPTION_REFRESH, 0, 0)
    except Exception:
        pass
