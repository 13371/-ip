@echo off
chcp 65001 >nul
title 砚白配置IP
:: 若未以管理员运行，则请求提升后重新运行本脚本
net session >nul 2>&1
if %errorlevel% neq 0 (
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)
cd /d "%~dp0"
:: 用 start 启动后立即退出，命令框自动关闭；pythonw 无黑窗
where pythonw >nul 2>&1
if %errorlevel% equ 0 (
    start "" pythonw "%~dp0main.py"
) else (
    start "" python "%~dp0main.py"
)
exit
