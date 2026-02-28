# -*- coding: utf-8 -*-
"""砚白配置IP - 配置与模板管理（配置放在程序目录，管理员/普通用户共用）"""
import json
import os
import sys
import uuid

# 使用程序所在目录；打包为 exe 时用 exe 所在目录，便于拷贝到其他电脑
if getattr(sys, "frozen", False):
    _SCRIPT_DIR = os.path.dirname(sys.executable)
else:
    _SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(_SCRIPT_DIR, ".yanbai_ip_config")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")


def _ensure_dir():
    os.makedirs(CONFIG_DIR, exist_ok=True)


def _migrate_from_user_config():
    """若程序目录下无配置但用户目录有旧配置，则复制过来一次"""
    if os.path.exists(CONFIG_FILE):
        return
    old_dir = os.path.join(os.path.expanduser("~"), ".yanbai_ip_config")
    old_file = os.path.join(old_dir, "config.json")
    if os.path.isfile(old_file):
        try:
            _ensure_dir()
            with open(old_file, "r", encoding="utf-8") as f:
                data = f.read()
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                f.write(data)
        except Exception:
            pass


def load_config():
    """加载配置：模板列表、开机启动等"""
    _migrate_from_user_config()
    _ensure_dir()
    if not os.path.exists(CONFIG_FILE):
        return {"templates": [], "autostart": False}
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return {"templates": [], "autostart": False}
        if not isinstance(data.get("templates"), list):
            data["templates"] = []
        need_save = False
        for t in data["templates"]:
            if not isinstance(t, dict):
                continue
            if not (t.get("id") or "").strip():
                t["id"] = str(uuid.uuid4())
                need_save = True
        if need_save:
            save_config(data)
        return data
    except Exception:
        return {"templates": [], "autostart": False}


def save_config(data):
    """保存配置"""
    _ensure_dir()
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_templates():
    return load_config().get("templates", [])


def save_templates(templates):
    cfg = load_config()
    cfg["templates"] = templates
    save_config(cfg)


def get_autostart():
    return load_config().get("autostart", False)


def set_autostart(enabled):
    cfg = load_config()
    cfg["autostart"] = bool(enabled)
    save_config(cfg)
