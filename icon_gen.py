# -*- coding: utf-8 -*-
"""砚白配置IP - 生成托盘图标与窗口图标"""
from PIL import Image, ImageDraw


def create_icon_image(size=64, bg=(66, 133, 244), symbol_color=(255, 255, 255)):
    """生成方形图标：浅蓝底 + 白色「网」风格符号（简约线条）。"""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # 圆角矩形背景
    margin = size // 8
    d.rounded_rectangle([margin, margin, size - margin, size - margin], radius=size // 6, fill=bg, outline=symbol_color, width=max(1, size // 24))
    # 简单“网络/IP”符号：类似 1 2 3 小点 + 线
    cx, cy = size // 2, size // 2
    r = size // 6
    for dx in (-size // 6, 0, size // 6):
        d.ellipse([cx + dx - r, cy - size // 8 - r, cx + dx + r, cy - size // 8 + r], fill=symbol_color)
    d.line([(cx - size // 4, cy + size // 8), (cx + size // 4, cy + size // 8)], fill=symbol_color, width=max(1, size // 16))
    return img


def get_tray_icon():
    return create_icon_image(64)


def get_tray_icon_bytes():
    """返回 (bytes, (width, height)) 供 pystray 使用。"""
    img = get_tray_icon()
    from io import BytesIO
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue(), img.size
