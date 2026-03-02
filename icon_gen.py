# -*- coding: utf-8 -*-
"""砚白配置IP - 极简托盘图标与 exe 图标"""
from PIL import Image, ImageDraw
import os

# 极简配色：深靛蓝底 + 纯白符号
_BG = (58, 80, 130)
_WHITE = (255, 255, 255)


def create_icon_image(size=64, bg=_BG, symbol_color=_WHITE):
    """极简图标：圆角方底 + 单一线条符号（横线 + 上方一点，喻意 IP/配置）。"""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    margin = size // 6
    radius = size // 5
    d.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=radius,
        fill=bg,
        outline=None,
    )
    cx, cy = size // 2, size // 2
    # 一条短横线
    w = max(1, size // 20)
    half_w = size // 4
    d.line(
        [(cx - half_w, cy), (cx + half_w, cy)],
        fill=symbol_color,
        width=w,
    )
    # 上方一个小圆点
    r = max(2, size // 12)
    d.ellipse(
        [cx - r, cy - size // 3 - r, cx + r, cy - size // 3 + r],
        fill=symbol_color,
    )
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


def save_ico(path, sizes=(16, 32, 48, 64, 128, 256)):
    """导出多尺寸 .ico 供 exe 使用。"""
    img = create_icon_image(256)
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), path)
    img.save(out, format="ICO", sizes=[(s, s) for s in sizes])
    return out


if __name__ == "__main__":
    save_ico("icon.ico")
    print("已生成 icon.ico，打包时请使用: PyInstaller ... --icon=icon.ico")
