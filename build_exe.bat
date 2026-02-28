@echo off
chcp 65001 >nul
title 砚白配置IP - 打包为 exe
cd /d "%~dp0"
echo 正在打包为单文件 exe（无需在其它电脑安装 Python）...
echo.
python -m pip install pyinstaller -q
if %errorlevel% neq 0 (
    echo 请先安装 Python 并确保 python 可用。
    pause
    exit /b 1
)
python -m PyInstaller --onefile --windowed --name "砚白配置IP" --uac-admin main.py
if %errorlevel% neq 0 (
    echo 打包失败。
    pause
    exit /b 1
)
echo.
echo 打包完成。exe 位置: dist\砚白配置IP.exe
echo 将 dist\砚白配置IP.exe 复制到其它电脑即可运行，无需安装 Python 或任何依赖。
echo 在其它电脑上请右键「以管理员身份运行」该 exe。
pause
