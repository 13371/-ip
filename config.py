# -*- coding: utf-8 -*-
"""砚白配置IP - 配置与模板管理（配置放在程序目录，管理员/普通用户共用）"""
import json
import os
import sys
import uuid

# 使用程序所在目录；打包为 exe 时用 exe 所在目录。若 exe 目录不可写（如只读 U 盘），则回退到 APPDATA
def _resolve_config_dir():
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    candidate = os.path.join(base, ".yanbai_ip_config")
    try:
        os.makedirs(candidate, exist_ok=True)
        test = os.path.join(candidate, ".write_test")
        with open(test, "w") as f:
            f.write("1")
        os.remove(test)
        return candidate
    except Exception:
        fallback = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "砚白配置IP")
        os.makedirs(fallback, exist_ok=True)
        # 若 exe 同目录有旧配置则复制到 APPDATA，便于拷贝过配置的其它电脑能读到模板
        try:
            old_cfg = os.path.join(candidate, "config.json")
            new_cfg = os.path.join(fallback, "config.json")
            if os.path.isfile(old_cfg) and not os.path.isfile(new_cfg):
                with open(old_cfg, "r", encoding="utf-8") as f:
                    data = f.read()
                with open(new_cfg, "w", encoding="utf-8") as f:
                    f.write(data)
        except Exception:
            pass
        return fallback


CONFIG_DIR = _resolve_config_dir()
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
        return {"templates": [], "autostart": False, "preferred_interface": None}
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return {"templates": [], "autostart": False, "preferred_interface": None}
        if not isinstance(data.get("templates"), list):
            data["templates"] = []
        if "preferred_interface" not in data:
            data["preferred_interface"] = None
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
        return {"templates": [], "autostart": False, "preferred_interface": None}


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


def get_preferred_interface():
    """用户选择的网卡名称，未选则为 None（自动取第一个已连接）。"""
    return load_config().get("preferred_interface")


def set_preferred_interface(name):
    """保存用户选择的网卡；传 None 表示恢复自动选择。"""
    cfg = load_config()
    cfg["preferred_interface"] = name if (name and name.strip()) else None
    save_config(cfg)
