# -*- coding: utf-8 -*-
"""砚白配置IP - 模板管理弹窗（新增/编辑/删除）"""
import tkinter as tk
from tkinter import ttk, messagebox
import uuid
import config
import network_manager
import proxy_manager
import monitor


def _is_valid_ipv4(s):
    if not s or not s.strip():
        return False
    parts = s.strip().split(".")
    if len(parts) != 4:
        return False
    for p in parts:
        if not p.isdigit():
            return False
        if int(p) > 255:
            return False
    return True


def _default_template():
    return {
        "id": str(uuid.uuid4()),
        "name": "新模板",
        "ip": "192.168.0.139",
        "mask": "255.255.255.0",
        "gateway": "192.168.0.33",
        "dns1": "192.168.0.33",
        "dns2": "",
    }


class TemplateEditorWindow:
    """模板管理窗口：列表 + 新增/编辑/删除"""

    def __init__(self, parent, on_apply_callback=None, on_close=None):
        self.on_apply = on_apply_callback
        self.on_close = on_close
        self.win = tk.Toplevel(parent)
        self.win.title("砚白配置IP - 模板管理")
        self.win.geometry("560x380")
        self.win.minsize(400, 300)
        self.win.protocol("WM_DELETE_WINDOW", self._destroy_win)
        self._build_ui()
        self._load_list()

    def _destroy_win(self):
        if self.on_close:
            try:
                self.on_close()
            except Exception:
                pass
        self.win.destroy()

    def _build_ui(self):
        f = ttk.Frame(self.win, padding=10)
        f.pack(fill=tk.BOTH, expand=True)
        # 列表
        ttk.Label(f, text="网络模板列表").pack(anchor=tk.W)
        tree_f = ttk.Frame(f)
        tree_f.pack(fill=tk.BOTH, expand=True, pady=(4, 8))
        self.tree = ttk.Treeview(tree_f, columns=("name", "ip", "gateway"), show="headings", height=8)
        self.tree.heading("name", text="模板名称")
        self.tree.heading("ip", text="IP 地址")
        self.tree.heading("gateway", text="网关")
        self.tree.column("name", width=120)
        self.tree.column("ip", width=140)
        self.tree.column("gateway", width=140)
        sb = ttk.Scrollbar(tree_f)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=sb.set)
        sb.configure(command=self.tree.yview)
        # 按钮行
        btn_f = ttk.Frame(f)
        btn_f.pack(fill=tk.X, pady=4)
        ttk.Button(btn_f, text="新增", command=self._add).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_f, text="编辑", command=self._edit).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_f, text="删除", command=self._delete).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_f, text="应用此模板", command=self._apply_selected).pack(side=tk.LEFT, padx=8)
        ttk.Button(btn_f, text="关闭", command=self._destroy_win).pack(side=tk.RIGHT, padx=2)

    def _load_list(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for t in config.get_templates():
            iid = t.get("id") or str(uuid.uuid4())
            self.tree.insert("", tk.END, iid=iid, values=(t.get("name", ""), t.get("ip", ""), t.get("gateway", "")))

    def _get_selected_id(self):
        sel = self.tree.selection()
        if not sel:
            return None
        return sel[0]

    def _add(self):
        self._edit_dialog(_default_template(), is_new=True)

    def _edit(self):
        tid = self._get_selected_id()
        if not tid:
            messagebox.showinfo("提示", "请先选中一个模板")
            return
        templates = [t for t in config.get_templates() if (t.get("id") or "") == tid]
        if not templates:
            messagebox.showwarning("提示", "未找到对应模板，请刷新列表后重试")
            return
        self._edit_dialog(dict(templates[0]), is_new=False)

    def _edit_dialog(self, data, is_new):
        d = tk.Toplevel(self.win)
        d.title("新增模板" if is_new else "编辑模板")
        d.geometry("360x280")
        d.transient(self.win)
        f = ttk.Frame(d, padding=12)
        f.pack(fill=tk.BOTH, expand=True)
        entries = {}
        rows = [
            ("模板名称", "name"),
            ("IPv4 地址", "ip"),
            ("子网掩码", "mask"),
            ("网关", "gateway"),
            ("首选 DNS", "dns1"),
            ("备用 DNS", "dns2"),
        ]
        for i, (label, key) in enumerate(rows):
            ttk.Label(f, text=label + "：").grid(row=i, column=0, sticky=tk.W, pady=2)
            e = ttk.Entry(f, width=28)
            e.insert(0, data.get(key, ""))
            e.grid(row=i, column=1, sticky=tk.EW, pady=2, padx=(8, 0))
            entries[key] = e
        f.columnconfigure(1, weight=1)

        def save():
            new_data = {k: e.get().strip() for k, e in entries.items()}
            new_data["id"] = data.get("id") or str(uuid.uuid4())
            new_data["name"] = new_data["name"] or "未命名"
            if new_data.get("ip") and not _is_valid_ipv4(new_data["ip"]):
                messagebox.showerror("错误", "请输入有效的 IPv4 地址（如 192.168.0.1）")
                return
            if new_data.get("mask") and not _is_valid_ipv4(new_data["mask"]):
                messagebox.showerror("错误", "请输入有效的子网掩码")
                return
            if new_data.get("gateway") and not _is_valid_ipv4(new_data["gateway"]):
                messagebox.showerror("错误", "请输入有效的网关地址")
                return
            if new_data.get("dns1") and not _is_valid_ipv4(new_data["dns1"]):
                messagebox.showerror("错误", "请输入有效的首选 DNS 地址")
                return
            if new_data.get("dns2") and not _is_valid_ipv4(new_data["dns2"]):
                messagebox.showerror("错误", "请输入有效的备用 DNS 地址")
                return
            if is_new:
                templates = config.get_templates()
                templates.append(new_data)
                config.save_templates(templates)
            else:
                data_id = new_data.get("id")
                templates = [new_data if (t.get("id") == data_id) else t for t in config.get_templates()]
                config.save_templates(templates)
            self._load_list()
            d.destroy()

        btn_f = ttk.Frame(f)
        btn_f.grid(row=len(rows), column=0, columnspan=2, pady=12)
        ttk.Button(btn_f, text="保存", command=save).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_f, text="取消", command=d.destroy).pack(side=tk.LEFT, padx=4)

    def _delete(self):
        tid = self._get_selected_id()
        if not tid:
            messagebox.showinfo("提示", "请先选中一个模板")
            return
        if not messagebox.askyesno("确认", "确定要删除该模板吗？"):
            return
        all_templates = config.get_templates()
        templates = [t for t in all_templates if (t.get("id") or "") != tid]
        if len(templates) == len(all_templates):
            messagebox.showwarning("提示", "未找到对应模板，请刷新列表后重试")
            return
        config.save_templates(templates)
        self._load_list()

    def _apply_selected(self):
        tid = self._get_selected_id()
        if not tid:
            messagebox.showinfo("提示", "请先选中一个模板")
            return
        templates = [t for t in config.get_templates() if (t.get("id") or "") == tid]
        if not templates:
            messagebox.showwarning("提示", "未找到对应模板，请刷新列表后重试")
            return
        t = templates[0]
        iface = network_manager.get_connected_interface(config.get_preferred_interface())
        if not iface:
            messagebox.showerror("错误", "未找到已连接的以太网接口")
            return
        ok, err = network_manager.set_static_ip(
            iface,
            (t.get("ip") or "").strip(),
            (t.get("mask") or "255.255.255.0").strip(),
            (t.get("gateway") or "").strip(),
            (t.get("dns1") or "").strip() or None,
            (t.get("dns2") or "").strip() or None,
        )
        if ok:
            monitor.set_monitoring_paused(False)
            messagebox.showinfo("成功", "已应用模板：%s" % t.get("name", ""))
            if self.on_apply:
                self.on_apply()
        else:
            messagebox.showerror("失败", err or "应用失败")


def open_template_editor(parent, on_apply_callback=None, on_close=None):
    TemplateEditorWindow(parent, on_apply_callback, on_close)
