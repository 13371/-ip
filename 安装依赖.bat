@echo off
chcp 65001 >nul
title 砚白配置IP - 安装依赖
cd /d "%~dp0"
echo 正在安装依赖...
echo.
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo.
    echo 若提示 "python" 未找到，请先安装 Python 3.8+ 并勾选 "Add Python to PATH"。
    echo 或尝试: py -m pip install -r requirements.txt
    pause
) else (
    echo.
    echo 依赖安装完成。请使用「以管理员运行.bat」启动程序。
    pause
)
