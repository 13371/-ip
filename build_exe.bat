@echo off
chcp 65001 >nul
title 砚白配置IP - 打包为 exe
cd /d "%~dp0"
set "PROJECT_ROOT=%~dp0"
set "PROJECT_ROOT=%PROJECT_ROOT:~0,-1%"
set PYINST_ICON=
echo 正在打包为单文件 exe（无需在其它电脑安装 Python）...
echo.

REM 关闭可能正在运行的 砚白配置IP.exe，避免打包时文件被占用
taskkill /f /im "砚白配置IP.exe" 2>nul
if %errorlevel% equ 0 echo 已关闭正在运行的程序，继续打包...
timeout /t 1 /nobreak >nul

REM 若缺少 icon.ico 则自动生成，避免打包报错
if not exist "icon.ico" (
    echo 未找到 icon.ico，正在生成...
    python -c "from icon_gen import save_ico; save_ico('icon.ico')"
    if not exist "icon.ico" (
        echo 无法生成 icon.ico，将不带图标打包。
        set NO_ICON=1
    )
)
if not defined NO_ICON set "PYINST_ICON=--icon=%PROJECT_ROOT%\icon.ico"

REM 输出到项目下的 pybuild_out（在已排除的 D:\配置ip 内，杀毒不会锁这里的 exe）
set "DIST_TMP=%PROJECT_ROOT%\pybuild_out"
if exist "%DIST_TMP%" rmdir /s /q "%DIST_TMP%" 2>nul
mkdir "%DIST_TMP%" 2>nul

python -m pip install pyinstaller -q
if %errorlevel% neq 0 (
    echo 请先安装 Python 并确保 python 可用。
    pause
    exit /b 1
)
REM --noupx 减少对 exe 的二次写入，降低被锁概率；--distpath 写到临时目录
python -m PyInstaller --onefile --windowed --name "砚白配置IP" --distpath "%DIST_TMP%" --workpath build\work --specpath build --clean --noupx --uac-admin %PYINST_ICON% main.py
if %errorlevel% neq 0 (
    echo 打包失败。若仍是「Permission denied」，请将 D:\配置ip 和 %TEMP% 都加入杀毒/Windows 安全排除项后再试。
    pause
    exit /b 1
)

if not exist "%DIST_TMP%\砚白配置IP.exe" (
    echo 未找到输出文件。
    pause
    exit /b 1
)
if not exist "dist" mkdir "dist"
copy /y "%DIST_TMP%\砚白配置IP.exe" "dist\砚白配置IP.exe" >nul
if %errorlevel% neq 0 (
    echo 复制到 dist 失败，请手动从 %DIST_TMP% 复制 砚白配置IP.exe 到 dist\。
    pause
    exit /b 1
)
rmdir /s /q "%DIST_TMP%" 2>nul
echo.
echo 打包完成。exe 位置: dist\砚白配置IP.exe
echo 将 dist\砚白配置IP.exe 复制到其它电脑即可运行，无需安装 Python 或任何依赖。
echo 在其它电脑上请右键「以管理员身份运行」该 exe。
pause
